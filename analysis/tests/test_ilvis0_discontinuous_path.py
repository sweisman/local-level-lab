# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


def zero_jumps(n):return [[[0,0] for _ in range(3)] for _ in range(n)]


def fixture():
    return dict(initial=[[0,0]]*3,derivative_start=[[0,0]]*3,derivative_end=[[3,3]]*3,
        partition=[0,F(1,4),1],smooth_second_bounds=[[6]*3]*2,
        value_jump_bounds=[[0]*3],slope_jump_bounds=[[0]*3],
        residual_jump_intervals=[[[2,2]]*3],endpoint_jump_intervals=[[[1,1]]*3,[[3,3]]*3])


def test_cubic_with_actual_residual_and_endpoint_jumps_has_known_enclosure():
    from lll.ilvis0_discontinuous_path import enclose
    row=enclose(**fixture())
    # r(0)=0, start jump1, smooth integral1, interior jump2, end jump3.
    assert row['exact_lower']==['7']*3 and row['exact_upper']==['8']*3
    assert row['endpoint_derivatives_are_one_sided']
    assert not row['continuous_residual_assumed']


def test_signed_jump_intervals_are_preserved_without_turning_everything_positive():
    from lll.ilvis0_discontinuous_path import enclose
    args=fixture();args.update(derivative_start=[[0,0]]*3,derivative_end=[[0,0]]*3,
        smooth_second_bounds=[[0]*3]*2,residual_jump_intervals=[[[F(-2,3),F(-1,3)]]*3],
        endpoint_jump_intervals=zero_jumps(2))
    row=enclose(**args)
    assert row['exact_lower']==['-2/3']*3 and row['exact_upper']==['-1/3']*3
    assert all(F(v)<=F(-2,3) for v in row['lower'])


def test_explicit_zero_residual_jumps_reproduce_the_continuous_primitive():
    from lll.ilvis0_discontinuous_path import enclose
    from lll.ilvis0_piecewise_trapezoid import enclose as reference
    args=fixture();args['residual_jump_intervals']=zero_jumps(1);args['endpoint_jump_intervals']=zero_jumps(2)
    row=enclose(**args)
    old=reference(**{k:v for k,v in args.items() if k not in ('residual_jump_intervals','endpoint_jump_intervals')},
        residual_continuous=True)
    assert row['exact_lower']==old['exact_lower'] and row['exact_upper']==old['exact_upper']
    assert row['input_binding']!=old['input_binding']
    assert not row['trajectory_jump_bounds_verified'] and not row['numerical_coverage_qualified']


@pytest.mark.parametrize('change',['missing','reversed','nonfinite','endpoints'])
def test_no_missing_jump_is_silently_replaced_with_zero(change):
    from lll.ilvis0_discontinuous_path import enclose
    args=fixture()
    if change=='missing':args['residual_jump_intervals']=[]
    if change=='reversed':args['residual_jump_intervals']=[[[1,-1]]*3]
    if change=='nonfinite':args['residual_jump_intervals']=[[[0,float('inf')]]*3]
    if change=='endpoints':args['endpoint_jump_intervals']=[]
    with pytest.raises(ValueError):enclose(**args)
