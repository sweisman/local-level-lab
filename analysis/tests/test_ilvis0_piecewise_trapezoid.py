# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import pytest


def enclose(nodes,smooth,value_jumps,slope_jumps,start,end,initial=None,**kwargs):
    from lll.ilvis0_piecewise_trapezoid import enclose as bound
    return bound(initial=[[0,0]]*3 if initial is None else initial,
        derivative_start=[[start,start]]*3,derivative_end=[[end,end]]*3,
        partition=nodes,smooth_second_bounds=[[v]*3 for v in smooth],
        value_jump_bounds=[[v]*3 for v in value_jumps],slope_jump_bounds=[[v]*3 for v in slope_jumps],
        residual_continuous=kwargs.get('residual_continuous',True))


def test_affine_derivative_has_zero_quadrature_error():
    row=enclose([0,1],[0],[],[],0,2)
    assert row['exact_lower']==row['exact_upper']==['1']*3
    assert row['error_radius']==[0.]*3 and not row['clock_partition_verified']


def test_cubic_residual_uses_the_exact_smooth_trapezoid_error_allowance():
    row=enclose([0,F(1,3),1],[6,6],[0],[0],0,3)
    assert row['exact_error_radius']==['1/2']*3
    assert all(F(a)<=1<=F(b) for a,b in zip(row['lower'],row['upper']))


@pytest.mark.parametrize('cut',[F(1,4),F(1,2),F(3,4)])
def test_derivative_step_is_enclosed_by_the_value_jump_term(cut):
    row=enclose([0,cut,1],[0,0],[1],[0],0,1)
    actual=1-cut
    assert row['exact_error_radius']==[str(abs(F(1,2)-cut))]*3
    assert F(row['exact_lower'][0])<=actual<=F(row['exact_upper'][0])


def test_derivative_hinge_requires_the_slope_jump_term():
    cut=F(1,3);row=enclose([0,cut,1],[0,0],[0],[1],0,1-cut)
    actual=(1-cut)**2/2
    assert F(row['exact_lower'][0])==actual
    assert row['exact_error_radius']==['1/9']*3


def test_independent_piecewise_quadratic_integral_is_enclosed():
    nodes=[F(0),F(1,4),F(2,3),F(1)];coefficients=[(F(1,5),F(-3,10),F(2,5)),
        (F(-1,2),F(2),F(-3,4)),(F(1,7),F(1,9),F(-1,11))]
    def value(c,x):a,b,d=c;return a+b*x+d*x*x
    def slope(c,x):_,b,d=c;return b+2*d*x
    actual=sum((a*(v-u)+b*(v*v-u*u)/2+d*(v**3-u**3)/3
        for (a,b,d),u,v in zip(coefficients,nodes,nodes[1:])),F(0))
    jumps=[abs(value(coefficients[i+1],x)-value(coefficients[i],x)) for i,x in enumerate(nodes[1:-1])]
    slopes=[abs(slope(coefficients[i+1],x)-slope(coefficients[i],x)) for i,x in enumerate(nodes[1:-1])]
    row=enclose(nodes,[2*abs(c[2]) for c in coefficients],jumps,slopes,
        value(coefficients[0],0),value(coefficients[-1],1))
    assert F(row['exact_lower'][0])<=actual<=F(row['exact_upper'][0])
    assert not row['native_derivative_bounds_verified'] and row['mathematical_enclosure_verified']


@pytest.mark.parametrize('change',['missing_jump','missing_slope','negative','nonfinite','bad_partition','discontinuous'])
def test_unsupported_or_incomplete_inputs_are_rejected(change):
    args=dict(nodes=[0,F(1,2),1],smooth=[0,0],value_jumps=[0],slope_jumps=[0],start=0,end=1)
    if change=='missing_jump':args['value_jumps']=[]
    if change=='missing_slope':args['slope_jumps']=[]
    if change=='negative':args['smooth']=[-1,0]
    if change=='nonfinite':args['smooth']=[float('inf'),0]
    if change=='bad_partition':args['nodes']=[0,1,F(1,2)]
    if change=='discontinuous':args['residual_continuous']=False
    with pytest.raises(ValueError):enclose(**args)


def test_endpoint_and_initial_intervals_are_preserved_outward():
    from lll.ilvis0_piecewise_trapezoid import enclose as bound
    row=bound(initial=[['-1/10','1/10']]*3,derivative_start=[[0,'1/10']]*3,
        derivative_end=[[2,'21/10']]*3,partition=[0,1],smooth_second_bounds=[[0]*3],
        value_jump_bounds=[],slope_jump_bounds=[],residual_continuous=True)
    assert row['exact_lower']==['9/10']*3 and row['exact_upper']==['6/5']*3
    assert F(row['lower'][0])<=F(9,10) and F(row['upper'][0])>=F(6,5)
