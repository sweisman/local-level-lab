# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from lll.ilvis0_directional_values import Value,add,scale,scalar_product,cross


def test_small_tilt_keeps_vertical_change_quadratic_through_vector_operations():
    eps=F(1,1000)
    force=Value([0.,0.,-1.],[eps,0.,eps**2/2],[eps**3/6,0.,eps**2/2])
    result=add(scale(force,2.),Value([0.,0.,2.],[0.]*3,[0.]*3))
    assert result.component(2).change<1.00000001e-6
    assert result.legacy().change>0.002
    for t in np.linspace(-1,1,65):
        angle=float(eps)*t;actual=np.array([-2*np.sin(angle),0.,2-2*np.cos(angle)])
        linear=np.array([-2*float(eps)*t,0.,0.])
        assert np.all(abs(actual-result.center)<=result.change+2e-15)
        assert np.all(abs(actual-result.center-linear)<=result.remainder+2e-15)


def test_center_rounding_is_included_even_for_fixed_inputs():
    a=Value([.1,.2,.3],[0.]*3,[0.]*3);result=scale(a,.1)
    for c,x,d,r in zip(result.center,a.center,result.change,result.remainder):
        error=abs(F(c)-F(.1)*F(x))
        assert F(d)>=error and F(r)>=error


def test_exact_fractional_scale_does_not_hide_conversion_error():
    value=Value(.1,0.,0.);result=scale(value,F(1,3))
    error=abs(F(result.center.item())-F(.1)/3)
    assert F(result.change.item())>=error and F(result.remainder.item())>=error


def test_cross_preserves_zero_coordinates_and_exact_constant_result():
    a=Value([1.,0.,0.],[.1,0.,0.],[.01,0.,0.]);b=Value([0.,2.,0.],[0.,.2,0.],[0.,.02,0.])
    result=cross(a,b)
    assert result.center.tolist()==[0.,0.,2.]
    assert result.change[:2].tolist()==result.remainder[:2].tolist()==[0.,0.]
    assert result.change[2]>=.42 and result.remainder[2]>=.06


@pytest.mark.parametrize('operation',['add','scale','product','cross'])
def test_exact_polynomial_truth_and_derivative_are_enclosed(operation):
    c=[F(1),F(-2),F(3)];l=[F(1,4),F(-1,8),F(1,16)];q=[F(1,32),F(1,64),F(-1,128)]
    d=[F(-1),F(1),F(2)];m=[F(-1,8),F(1,4),F(1,16)];s=[F(1,64),F(-1,32),F(1,128)]
    def value(center,first,second):
        return Value(list(map(float,center)),[float(abs(a)+abs(b)) for a,b in zip(first,second)],list(map(lambda x:float(abs(x)),second)))
    a=value(c,l,q);b=value(d,m,s)
    def cp(x,y):return [x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0]]
    if operation=='add':out=add(a,b);first=[x+y for x,y in zip(l,m)]
    elif operation=='scale':out=scale(a,-.5);first=[-v/2 for v in l]
    elif operation=='product':out=scalar_product(Value(float(c[0]),float(abs(l[0])+abs(q[0])),float(abs(q[0]))),b);first=[c[0]*x+l[0]*y for x,y in zip(m,d)]
    else:out=cross(a,b);first=[x+y for x,y in zip(cp(c,m),cp(l,d))]
    for k in range(-32,33):
        t=F(k,32);x=[a+b*t+v*t*t for a,b,v in zip(c,l,q)];y=[a+b*t+v*t*t for a,b,v in zip(d,m,s)]
        if operation=='add':actual=[a+b for a,b in zip(x,y)]
        elif operation=='scale':actual=[-v/2 for v in x]
        elif operation=='product':actual=[x[0]*v for v in y]
        else:actual=cp(x,y)
        for j,truth in enumerate(actual):
            assert abs(truth-F(out.center[j]))<=F(out.change[j])
            assert abs(truth-F(out.center[j])-first[j]*t)<=F(out.remainder[j])


def test_values_are_immutable_and_legacy_export_is_conservative():
    value=Value([1.,2.,3.],[.1,.2,.3],[.01,.02,.03])
    with pytest.raises(ValueError):value.change[0]=0
    with pytest.raises(ValueError):value.center[0]=0
    assert F(value.legacy().change)**2>=sum(F(v)**2 for v in value.change)
    assert F(value.legacy().remainder)**2>=sum(F(v)**2 for v in value.remainder)


@pytest.mark.parametrize('bad',[[-1.,0.,0.],[float('nan'),0.,0.],[0.,0.]])
def test_bad_component_radii_are_rejected(bad):
    with pytest.raises(ValueError):Value([0.]*3,bad,[0.]*3)
