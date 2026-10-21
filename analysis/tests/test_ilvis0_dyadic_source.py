# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest


@pytest.mark.parametrize('kind',('ordinary','tiny','mixed','nonbinary'))
def test_affine_radius_exactly_reproduces_fraction_reference(kind):
    from lll.ilvis0_dyadic_source import affine_radius
    from lll.ilvis0_source_reference import affine_radius as original
    generator=np.random.default_rng(123)
    rows=generator.normal(size=27);lo=-generator.random(27);hi=generator.random(27)
    center=generator.normal(size=27)
    if kind=='tiny':rows=rows*2.**-1000
    elif kind=='mixed':rows[0]=2.**500;rows[1]=2.**-1000
    elif kind=='nonbinary':rows=list(rows);rows[4]=F(1,3)
    args=(F(-2,3),F(7,9),.125,rows,lo,hi,center)
    assert affine_radius(*args)==original(*args)


@pytest.mark.parametrize('phase',(0,1))
def test_mean_value_radius_exactly_reproduces_fraction_reference(phase):
    from lll.ilvis0_dyadic_source import mean_value_radius
    from lll.ilvis0_source_derivative_intervals import mean_value_radius as original
    generator=np.random.default_rng(456)
    values=generator.normal(size=(2,2,3));point=np.stack((values-.001,values+.002),axis=-1)
    rows=generator.normal(size=(2,2,3,27))
    jacobian=np.stack((rows-.03,rows+.02),axis=-1)
    rows[0,0,0,0]=np.nextafter(0.,1.)
    jacobian[0,0,0,0]=[0.,np.nextafter(0.,1.)]
    frame=dict(point_values=point,jacobian=jacobian,
        lower=[-1.]*27,upper=[1.]*27,center=generator.uniform(-2,2,27))
    expected=original(frame,values,rows,phase=phase)
    actual=mean_value_radius(frame,values,rows,phase=phase)
    np.testing.assert_array_equal(actual,expected)
    assert not actual.flags.writeable


def test_all_27_columns_and_interval_order_are_required():
    from lll.ilvis0_dyadic_source import mean_value_radius,affine_radius
    with pytest.raises(ValueError):affine_radius(1.,0.,0.,[0.]*27,[-1.]*27,[1.]*27,[0.]*27)
    frame=dict(point_values=np.zeros((2,2,3,2)),jacobian=np.zeros((2,2,3,26,2)),
        lower=[-1.]*27,upper=[1.]*27,center=[0.]*27)
    with pytest.raises(ValueError):mean_value_radius(frame,np.zeros((2,2,3)),np.zeros((2,2,3,27)),phase=0)
