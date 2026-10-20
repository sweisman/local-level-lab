# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_acceleration_native as candidate
from test_ilvis0_native_box_bounds import configuration
from test_ilvis0_regrouped_history import native
from lll.ilvis0_shape import load_tangent


def test_constant_reference_acceleration_and_clock_are_factored_without_narrowing(tmp_path):
    config=configuration();config.update(model=2,profile=False,initial_v=np.array([150.,0.,0.]))
    config['limits'][:]=0.;config['limits'][3]=20.;config['limits'][12]=.25
    config['limits'][24]=.05;config['limits'][25]=.15;config['limits'][21]=10.
    n=400;dt=np.full(n,.005);theta=np.zeros((n,3));dv=np.tile([.02*.005,0.,-9.81*.005],(n,1))
    lo=-np.ones(27);hi=np.ones(27);center=np.zeros(27);center[21]=.1
    terms=candidate.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    report=candidate.enclose(config,theta,dv,dt,time=1.8,lower=lo,upper=hi,reference=terms)
    scale=np.array([6371000.,6371000.,1.])
    assert np.max(report.unshared_remainder*scale)<1e-5
    kernel=load_tangent(tmp_path)[0];value,jac=native(kernel,config,theta,dv,dt,1.8,center)
    assert np.max(abs(value-report.center)*scale)<1e-6
    point=np.full(27,.7);actual,_=native(kernel,config,theta,dv,dt,1.8,point)
    gamma=np.r_[terms.reference.normalized_values_at(point),terms.normalized_values_at(point)]
    augmented=report.design(jac,terms)
    error=actual-value-augmented@np.r_[point-center,gamma]
    assert np.max(abs(error)*scale)<1e-5 and augmented.shape==(3,42)
    assert terms.reference.lower[3]==-1 and terms.reference.upper[3]==1


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_native_centers_and_factored_probes_all_models(model,profile,tmp_path):
    config=configuration();config.update(model=model,profile=profile)
    n=13;dt=np.full(n,.005);theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1))
    lo=np.full(27,-.2);hi=np.full(27,.5);center=np.full(27,.1);time=.05
    terms=candidate.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    report=candidate.enclose(config,theta,dv,dt,time=time,lower=lo,upper=hi,reference=terms)
    kernel=load_tangent(tmp_path)[0];value,jac=native(kernel,config,theta,dv,dt,time,center)
    scale=np.array([6371000.,6371000.,1.]);assert np.max(abs(value-report.center)*scale)<1e-6
    for point in (lo,hi,np.linspace(-.1,.4,27)):
        actual,_=native(kernel,config,theta,dv,dt,time,point)
        gamma=np.r_[terms.reference.normalized_values_at(point),terms.normalized_values_at(point)]
        error=actual-value-report.design(jac,terms)@np.r_[point-center,gamma]
        assert np.all(abs(error)*scale<=report.unshared_remainder*scale+1e-5)
    changed=theta.copy();changed[0,0]+=.001
    with pytest.raises(ValueError,match='source'):
        candidate.enclose(config,changed,dv,dt,time=time,lower=lo,upper=hi,reference=terms)
