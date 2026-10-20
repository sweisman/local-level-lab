# SPDX-License-Identifier: AGPL-3.0-or-later
import ctypes

import numpy as np
import pytest
from lll import ilvis0_regrouped_history as grouped
from lll.ilvis0_shape import load_tangent
from test_ilvis0_native_box_bounds import configuration


def native(kernel,config,theta,dv,dt,time,point):
    result=np.empty((1,3));jac=np.empty((3,27));warning=ctypes.c_int()
    assert kernel(len(dt),theta,dv,dt,1,np.array([time]),config['initial_c'],config['initial_v'],
        config['initial_r'],config['limits'],point,config['model'],int(config['profile']),
        config['gravity'],config['radius'],result,jac,ctypes.byref(warning))==0
    return result[0],jac


def test_shared_time_and_force_cancel_in_independent_flat_constant_motion():
    config=configuration();config.update(model=2,profile=False,initial_v=np.array([150.,0.,0.]))
    config['limits'][:]=0.;config['limits'][25]=.15
    n=400;dt=np.full(n,.005);theta=np.zeros((n,3));dv=np.tile([0.,0.,-9.81*.005],(n,1))
    report=grouped.enclose(config,theta,dv,dt,time=1.8,lower=-np.ones(27),upper=np.ones(27),center=np.zeros(27))
    expected=config['initial_c']+np.array([150.*1.8/config['radius'],0.,0.])
    np.testing.assert_allclose(report['center'],expected,rtol=0,atol=1e-10)
    assert report['remainder'][0]*config['radius']<1e-5
    assert report['remainder'][2]<1e-5
    assert report['independent_clock_remainder_s']>.4 and report['clock_remainder_s']<1e-12
    assert not report['floating_point_enclosure_verified']


def test_nonzero_asymmetric_bounds_contain_original_native_values_and_remainders(tmp_path):
    config=configuration();n=13;dt=np.full(n,.005);theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1))
    lo=np.full(27,-.2);hi=np.full(27,.5);center=np.full(27,.1);time=.05
    report=grouped.enclose(config,theta,dv,dt,time=time,lower=lo,upper=hi,center=center)
    kernel=load_tangent(tmp_path)[0];nominal,jac=native(kernel,config,theta,dv,dt,time,center)
    scale=np.array([6371000.,6371000.,1.]);assert np.max(abs((report['center']-nominal)*scale))<1e-6
    for point in (lo,hi,np.linspace(-.1,.4,27)):
        actual,_=native(kernel,config,theta,dv,dt,time,point)
        assert np.all(abs((actual-nominal-jac@(point-center))*scale)<=report['remainder']*scale+1e-6)
    assert report['parameter_count']==27 and report['force_gravity_regrouped']


def test_every_tangent_column_matches_finite_difference_of_regrouped_point_map(tmp_path):
    config=configuration();n=8;dt=np.full(n,.005);theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1))
    point=np.linspace(-.1,.1,27);time=.025;kernel=load_tangent(tmp_path)[0]
    _,jac=native(kernel,config,theta,dv,dt,time,point);step=.002;differences=[]
    for axis in range(27):
        delta=np.zeros(27);delta[axis]=step
        left=grouped.enclose(config,theta,dv,dt,time=time,lower=point-delta,upper=point-delta,center=point-delta)['center']
        right=grouped.enclose(config,theta,dv,dt,time=time,lower=point+delta,upper=point+delta,center=point+delta)['center']
        differences.append((right-left)/(2*step))
    scale=np.array([6371000.,6371000.,1.])
    np.testing.assert_allclose((np.array(differences).T-jac)*scale[:,None],0.,rtol=0,atol=2e-5)


def test_invalid_time_support_and_box_remain_unsupported():
    config=configuration();dt=np.full(3,.005);theta=np.zeros((3,3));dv=theta.copy()
    with pytest.raises(ValueError):grouped.enclose(config,theta,dv,dt,time=0.,lower=-np.ones(27),upper=np.ones(27),center=np.zeros(27))
    with pytest.raises(ValueError,match='time allowance'):
        grouped.enclose(config,theta,dv,dt,time=.01,lower=-np.ones(27),upper=np.ones(27),center=np.zeros(27),maximum_seconds=0)
