# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math
import numpy as np
import pytest
from lll import ilvis0_interval_calibration as interval


def includes(box,value):return box.lo<=value<=box.hi


def test_product_and_inverse_keep_every_physical_derivative():
    x=interval.Jet.variable(.5,1.,0);y=interval.Jet.variable(.1,.2,25)
    result=x*y/(1+x)
    assert len(result.derivative)==27
    for a in (.5,.75,1.):
        for b in (.1,.15,.2):
            assert includes(result.value,a*b/(1+a))
            assert includes(result.derivative[0],b/(1+a)**2)
            assert includes(result.derivative[25],a/(1+a))
    assert all(g.lo==g.hi==0. for j,g in enumerate(result.derivative) if j not in (0,25))
    with pytest.raises(ValueError):1/interval.Jet.variable(-1.,1.,0)


def test_square_is_not_an_independent_product_of_two_copies():
    x=interval.Jet.variable(-1.,1.,3);square=x.square()
    assert square.value.lo>=0. and includes(square.value,1.)
    assert includes(square.derivative[3],-2.) and includes(square.derivative[3],2.)


def test_exact_input_endpoints_are_rounded_outward_instead_of_collapsed():
    point=interval.Jet.constant(F(1,3));variable=interval.Jet.variable(F(1,3),F(2,3),0)
    assert includes(point.value,F(1,3))
    assert includes(variable.value,F(1,3)) and includes(variable.value,F(2,3))


def test_exponential_at_zero_has_the_correct_signed_generator():
    zero=interval.Jet.constant(0.);z=interval.Jet.variable(0.,0.,2)
    result=interval.exp_skew([zero,zero,z])
    assert includes(result[0][1].derivative[2],-1.)
    assert includes(result[1][0].derivative[2],1.)
    assert includes(result[0][0].value,1.)
    assert result[0][0].derivative[26].lo==result[0][0].derivative[26].hi==0.


def test_rotation_intervals_contain_independent_trigonometric_values_and_derivatives():
    zero=interval.Jet.constant(0.);z=interval.Jet.variable(-.3,.4,2)
    r=interval.exp_skew([zero,zero,z])
    for angle in np.linspace(-.3,.4,15):
        assert includes(r[0][0].value,math.cos(angle))
        assert includes(r[0][1].value,-math.sin(angle))
        assert includes(r[0][0].derivative[2],-math.sin(angle))
        assert includes(r[0][1].derivative[2],-math.cos(angle))


def test_three_axis_exponential_contains_an_independent_rodrigues_reference():
    vector=np.array([.1,-.2,.3]);theta=np.linalg.norm(vector);x,y,z=vector
    k=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    expected=np.eye(3)+math.sin(theta)/theta*k+(1-math.cos(theta))/theta**2*(k@k)
    answer=interval.exp_skew([interval.Jet.constant(float(v)) for v in vector])
    for i in range(3):
        for j in range(3):assert includes(answer[i][j].value,expected[i,j])


def test_mean_value_relationships_preserve_the_existing_51_coordinates():
    lower=[0.]*27;upper=[0.]*27;center=[0.]*27
    lower[0]=.5;upper[0]=1.;center[0]=.75
    lower[25]=.1;upper[25]=.2;center[25]=.15
    x=interval.Jet.variable(.5,1.,0);clock=interval.Jet.variable(.1,.2,25)
    zero=interval.Jet.constant(0.)
    mapped=[x*clock]+[zero]*23;at_center=[interval.Jet.constant(.75)*interval.Jet.constant(.15)]+[zero]*23
    cuts=interval.couple(mapped,at_center,lower,upper,center)
    assert cuts['parameter_count']==51 and len(cuts['design'])==48
    assert all(len(row)==51 for row in cuts['design'])
    # Verify the exported inequalities with independent exact arithmetic.
    for a in (.5,.75,1.):
        for b in (.1,.15,.2):
            point=list(map(F,center))+[F(a)*F(b)]+[F(0)]*23;point[0]=F(a);point[25]=F(b)
            assert all(sum((F(c)*v for c,v in zip(row,point)),F(0))<=F(bound)
                for row,bound in zip(cuts['design'],cuts['upper']))
    with pytest.raises(ValueError):interval.couple(mapped[:-1],at_center,lower,upper,center)


@pytest.mark.parametrize('call',[
    lambda:interval.Jet.variable(1.,-1.,0),lambda:interval.Jet.variable(0.,1.,27),
    lambda:interval.Jet.constant(math.nan),
    lambda:interval.exp_skew([interval.Jet.constant(9.)]*3),
])
def test_unsupported_domains_are_rejected(call):
    with pytest.raises(ValueError):call()
