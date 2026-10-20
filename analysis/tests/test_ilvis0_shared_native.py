# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_shared_native as shared
from test_ilvis0_native_box_bounds import configuration
from test_ilvis0_regrouped_history import native
from lll.ilvis0_shape import load_tangent


def test_north_velocity_time_product_is_shared_without_narrowing_its_domain(tmp_path):
    config=configuration();config.update(model=2,profile=False,initial_v=np.array([150.,0.,0.]))
    config['limits'][:]=0.;config['limits'][3]=20.;config['limits'][25]=.15
    n=400;dt=np.full(n,.005);theta=np.zeros((n,3));dv=np.tile([0.,0.,-9.81*.005],(n,1))
    lo=-np.ones(27);hi=np.ones(27);center=np.zeros(27)
    reference=shared.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    result=shared.enclose(config,theta,dv,dt,time=1.8,lower=lo,upper=hi,reference=reference)
    assert result.unshared_remainder[0]*config['radius']<1e-5
    kernel=load_tangent(tmp_path)[0];nominal,jac=native(kernel,config,theta,dv,dt,1.8,center)
    point=center.copy();point[3]=.7;point[25]=-.8
    actual,_=native(kernel,config,theta,dv,dt,1.8,point)
    augmented=result.design(jac,reference)
    residual=actual-nominal-jac@point-result.coefficients.matrix@reference.normalized_values_at(point)
    assert abs(residual[0])*config['radius']<1e-5 and augmented.shape==(3,33)
    assert reference.lower[3]==-1 and reference.upper[3]==1


def test_static_lever_error_is_factored_even_with_nonzero_expansion_center(tmp_path):
    config=configuration();config.update(model=2,profile=False,initial_v=np.zeros(3))
    config['limits'][:]=0.;config['limits'][:3]=[.1,.1,1.];config['limits'][21:24]=[10.,10.,10.]
    dt=np.array([.005]);theta=np.zeros((1,3));dv=np.array([[0.,0.,-.04905]])
    lo=-np.ones(27);hi=np.ones(27);center=np.zeros(27);center[2]=.2;center[21:24]=[.1,-.1,.05]
    reference=shared.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    result=shared.enclose(config,theta,dv,dt,time=0.,lower=lo,upper=hi,reference=reference)
    assert np.max(result.unshared_remainder*np.array([6371000.,6371000.,1.]))<1e-5
    kernel=load_tangent(tmp_path)[0];nominal,jac=native(kernel,config,theta,dv,dt,0.,center)
    point=np.linspace(-.7,.8,27);actual,_=native(kernel,config,theta,dv,dt,0.,point)
    error=actual-nominal-jac@(point-center)-result.coefficients.matrix@reference.normalized_values_at(point)
    assert np.max(abs(error)*np.array([6371000.,6371000.,1.]))<1e-5


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_native_centers_and_factored_remainders_at_nonzero_calibration(model,profile,tmp_path):
    config=configuration();config.update(model=model,profile=profile)
    n=13;dt=np.full(n,.005);theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1))
    lo=np.full(27,-.2);hi=np.full(27,.5);center=np.full(27,.1);time=.05
    reference=shared.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    report=shared.enclose(config,theta,dv,dt,time=time,lower=lo,upper=hi,reference=reference)
    kernel=load_tangent(tmp_path)[0];nominal,jac=native(kernel,config,theta,dv,dt,time,center)
    scale=np.array([6371000.,6371000.,1.]);assert np.max(abs(report.center-nominal)*scale)<1e-6
    for point in (lo,hi,np.linspace(-.1,.4,27)):
        actual,_=native(kernel,config,theta,dv,dt,time,point)
        residual=actual-nominal-jac@(point-center)-report.coefficients.matrix@reference.normalized_values_at(point)
        assert np.all(abs(residual)*scale<=report.unshared_remainder*scale+1e-5)
    assert report.report()['enclosure_parameter_count']==33
    changed=theta.copy();changed[0,0]+=.0001
    with pytest.raises(ValueError,match='source'):shared.enclose(config,changed,dv,dt,time=time,lower=lo,upper=hi,reference=reference)
