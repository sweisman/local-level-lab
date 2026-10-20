# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from lll.ilvis0_axis_rotation_bounds import bound


@pytest.mark.parametrize('axis',[0,1,2])
def test_rotation_about_the_measured_axis_cannot_change_its_component(axis):
    lo=[0.,0.,0.];hi=lo.copy();lo[axis]=-100.;hi[axis]=100.
    value=bound(lo,hi,axis=axis)
    assert value['parallel_lower']=='1' and value['parallel_upper']=='1'
    assert value['transverse_squared_upper']=='0'


def test_tilt_is_quadratic_in_the_parallel_component_even_with_large_yaw():
    value=bound([F(-1,100),F(-1,200),-20],[F(1,100),F(1,200),20],axis=2)
    assert F(value['parallel_lower'])==1-F(1,16000)
    assert F(value['transverse_squared_upper'])==F(1,8000)


def test_large_tilt_keeps_unit_vector_limits():
    value=bound([-10]*3,[10]*3,axis=2)
    assert value['parallel_lower']=='-1'
    assert value['transverse_squared_upper']=='1'
    assert value['displacement_squared_upper']=='4'


@pytest.mark.parametrize('axis',[0,1,2])
def test_independent_rotation_samples_obey_analytic_bounds(axis):
    lo=np.array([-.017,-.011,-1.7]);hi=np.array([.023,.031,2.1])
    result=bound(lo.tolist(),hi.tolist(),axis=axis)
    points=np.random.default_rng(471+axis).uniform(lo,hi,size=(128,3))
    unit=np.eye(3)[axis];actual=Rotation.from_rotvec(points).apply(np.tile(unit,(128,1)))
    parallel=actual[:,axis];transverse=np.sum(np.delete(actual,axis,axis=1)**2,axis=1)
    assert min(parallel)>=float(F(result['parallel_lower']))-2e-15
    assert max(parallel)<=1+2e-15
    assert max(transverse)<=float(F(result['transverse_squared_upper']))+2e-15
    assert max(np.sum((actual-unit)**2,axis=1))<=float(F(result['displacement_squared_upper']))+4e-15


@pytest.mark.parametrize('lo,hi,axis',[
    ([0]*3,[0]*3,True),([0]*2,[0]*2,2),([1,0,0],[0,0,0],2),
    ([0,0,float('nan')],[0]*3,2)])
def test_invalid_domains_rejected(lo,hi,axis):
    with pytest.raises(ValueError):bound(lo,hi,axis=axis)
