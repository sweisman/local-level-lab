# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest
from lll.ilvis0_matrix_gram import check,check_lifted

IDENTITY=[[1,0,0],[0,1,0],[0,0,1]]


def test_identity_and_signed_permutations_preserve_gram():
    for matrix in (IDENTITY,[[0,-1,0],[1,0,0],[0,0,1]],[[0,0,1],[-1,0,0],[0,-1,0]]):
        row=check(IDENTITY,matrix,[0,0,0],allowance=0)
        assert not row['incompatible'] and row['exact_defect_squared']=='0'


def test_gain_removal_and_nonorthogonal_initial_matrix_use_exact_invariant():
    initial=[[2,0,0],[0,3,0],[0,0,4]]
    gains=[F(1,10),F(-1,3),F(1,2)]
    rotated=[[0,-2,0],[3,0,0],[0,0,4]]
    matrix=[[F(v)/(1+gains[j]) for j,v in enumerate(row)] for row in rotated]
    row=check(initial,matrix,gains,allowance=0)
    assert not row['incompatible']
    assert row['exact_defect_squared']==row['reference_defect_squared']=='298'
    assert check(initial,IDENTITY,[0,0,0],allowance=0)['incompatible']


def test_stretch_and_unit_length_nonorthogonal_columns_are_flagged():
    assert check(IDENTITY,[[F(10001,10000),0,0],[0,1,0],[0,0,1]],[0,0,0])['incompatible']
    assert check(IDENTITY,[[1,1,0],[0,0,0],[0,0,1]],[0,0,0])['incompatible']


def test_gram_is_necessary_and_does_not_establish_proper_rotation():
    row=check(IDENTITY,[[-1,0,0],[0,1,0],[0,0,1]],[0,0,0],allowance=0)
    assert not row['incompatible']
    assert row['physical_realizability_established'] is False


def test_declared_numerical_allowance_is_reported_separately():
    row=check(IDENTITY,[[1.+1e-12,0,0],[0,1,0],[0,0,1]],[0,0,0])
    assert not row['incompatible'] and F(row['exact_defect_squared'])>0
    assert row['allowance']=='1/100000000'


def test_lifted_column_order_and_all_51_coordinates():
    ref=dict(center=IDENTITY,jacobian=[[[0]*27 for _ in range(3)] for _ in range(3)],caps=[1]*9)
    point=[F(0)]*51;limits=[F(0)]*27;center=[F(0)]*27
    assert not check_lifted(IDENTITY,ref,limits,center,point)['incompatible']
    point[43]=F(1,10)
    assert check_lifted(IDENTITY,ref,limits,center,point)['incompatible']
    with pytest.raises(ValueError):check_lifted(IDENTITY,ref,limits,center,point[:27])


@pytest.mark.parametrize('initial,matrix,gains',[(IDENTITY,IDENTITY,[-1,0,0]),
    (IDENTITY,[[1,2]], [0,0,0]),(IDENTITY,IDENTITY,[float('nan'),0,0])])
def test_invalid_fields_are_rejected(initial,matrix,gains):
    with pytest.raises(ValueError):check(initial,matrix,gains)
