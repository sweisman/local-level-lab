# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_native_box_bounds as bounds
from lll.ilvis0_shape import load_tangent


def configuration():
    limits=np.r_[[.01]*3,[2.]*3,[10.]*3,[2e-6]*3,[.01]*3,[.001]*6,[2.]*3,.01,.001,1.]
    return dict(initial_c=np.array([-.8,1.,10000.]),initial_v=np.array([150.,-20.,.1]),initial_r=np.eye(3),
        limits=limits,model=0,profile=True,gravity=9.81,radius=6371000.)


def test_asymmetric_box_bound_contains_native_changes_and_remainders(tmp_path):
    import ctypes
    config=configuration();n=13;dt=np.full(n,.005)
    theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1));time=.05
    lower=np.full(27,-.2);upper=np.full(27,.5);center=np.full(27,.1)
    report=bounds.enclose(config,theta,dv,dt,time=time,lower=lower,upper=upper,center=center)
    kernel=load_tangent(tmp_path)[0]
    def predict(point):
        out=np.empty((1,3));jac=np.empty((3,27));b=ctypes.c_int()
        assert kernel(n,theta,dv,dt,1,np.array([time]),config['initial_c'],config['initial_v'],config['initial_r'],
            config['limits'],point,0,1,9.81,6371000.,out,jac,ctypes.byref(b))==0
        return out[0],jac
    nominal,jac=predict(center);scale=np.array([6371000.,6371000.,1.])
    assert np.max(abs((report['center']-nominal)*scale))<1e-6
    for point in (lower,upper,np.linspace(-.1,.4,27)):
        actual,_=predict(point)
        error=abs((actual-nominal-jac@(point-center))*scale)
        assert np.all(error<=report['remainder']*scale+1e-6)
    assert report['parameter_count']==27 and not report['floating_point_enclosure_verified']


def test_center_and_timing_must_remain_inside_supported_box():
    config=configuration();theta=np.zeros((3,3));dv=np.zeros((3,3));dt=np.full(3,.005)
    with pytest.raises(ValueError):bounds.enclose(config,theta,dv,dt,time=.01,lower=np.zeros(27),upper=np.ones(27),center=-np.ones(27))
    with pytest.raises(ValueError):bounds.enclose(config,theta,dv,dt,time=0.,lower=-np.ones(27),upper=np.ones(27),center=np.zeros(27))
