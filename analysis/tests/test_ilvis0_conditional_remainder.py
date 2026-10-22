# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math

import pytest


def test_change_bound_does_not_replace_a_larger_cancelling_taylor_remainder():
    from lll.ilvis0_conditional_remainder import enclose
    # f(x)=sin(100x)/100 has derivative1 at0 and |f(x)-f(0)|<=.01.
    value=enclose([[1.],[0.],[0.]],[-1.],[1.],[0.],[.01,0.,0.],100.)
    actual=math.sin(100.)/100.-1.
    assert abs(actual)>.01 and abs(actual)<=value['remainder_upper']<1.011
    assert value['remainder_upper']>.01


def test_exact_asymmetric_linear_box_and_outward_norm():
    from lll.ilvis0_conditional_remainder import enclose
    value=enclose([[2.,-1.],[0.,3.],[1.,0.]],[-1.,2.],[2.,4.],[0.,0.],[.1,.2,.3],100.)
    assert value['linear_lower']==['-6','6','-1'] and value['linear_upper']==['2','12','2']
    expected=[F(.1)+6,F(.2)+12,F(.3)+2]
    for radius,exact in zip(value['component_upper'],expected):assert F(radius)>=exact
    assert F(value['remainder_upper'])**2>=sum((x*x for x in expected),F(0))


def test_original_norm_cap_is_retained_and_never_widened():
    from lll.ilvis0_conditional_remainder import enclose
    value=enclose([[100.],[0.],[0.]],[-1.],[1.],[0.],[20.,0.,0.],.5)
    assert value['remainder_upper']==.5
    assert value['component_upper'][0]==.5
    zero=enclose([[0.],[0.],[0.]],[-1.],[1.],[0.],[0.,0.,0.],0.)
    assert zero['remainder_upper']==0.


@pytest.mark.parametrize('change',[
    dict(component_change=[-1.,0.,0.]),dict(original_remainder=-1.),
    dict(upper=[-2.]),dict(center=[math.nan]),dict(jacobian=[[1.],[0.]]),
])
def test_bad_inputs_are_not_repaired(change):
    from lll.ilvis0_conditional_remainder import enclose
    args=dict(jacobian=[[1.],[0.],[0.]],lower=[-1.],upper=[1.],center=[0.],component_change=[1.,1.,1.],original_remainder=2.)
    with pytest.raises(ValueError):enclose(**dict(args,**change))


def test_inconsistent_bounds_are_not_silently_used_to_discard_a_region():
    from lll.ilvis0_conditional_remainder import enclose
    with pytest.raises(ValueError):enclose([[100.],[0.],[0.]],[1.],[2.],[0.],[0.,0.,0.],1.)
