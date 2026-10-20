# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_transform_native as candidate
from lll.ilvis0_shape import load_tangent
from test_ilvis0_native_box_bounds import configuration
from test_ilvis0_regrouped_history import native


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_changing_force_native_centres_and_51_column_probes(model,profile,tmp_path):
    config=configuration();config.update(model=model,profile=profile)
    n=13;dt=np.full(n,.005);theta=np.tile([1e-5,-2e-5,3e-6],(n,1))
    dv=np.c_[1e-5*np.sin(np.arange(n)),2e-5*np.cos(np.arange(n)),np.full(n,-.04905)]
    lo=np.full(27,-.2);hi=np.full(27,.5);center=np.full(27,.1);time=.05
    reference=candidate.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    report=candidate.enclose(config,theta,dv,dt,time=time,lower=lo,upper=hi,reference=reference)
    kernel=load_tangent(tmp_path)[0];value,jac=native(kernel,config,theta,dv,dt,time,center)
    scale=np.array([6371000.,6371000.,1.]);assert np.max(abs(value-report.center)*scale)<1e-6
    design=report.design(jac,reference);assert design.shape==(3,51)
    np.testing.assert_array_equal(design[:,:27],jac)
    for point in (lo,hi,np.linspace(-.1,.4,27)):
        actual,_=native(kernel,config,theta,dv,dt,time,point);gamma=reference.normalized_values_at(point)
        assert gamma.shape==(24,) and np.all(abs(gamma)<=1+1e-11)
        error=(actual-value-design@np.r_[point-center,gamma])*scale
        assert np.all(abs(error)<=report.unshared_remainder*scale+1e-5)
    changed=dv.copy();changed[0,0]+=.001
    with pytest.raises(ValueError,match='source'):
        candidate.enclose(config,theta,changed,dt,time=time,lower=lo,upper=hi,reference=reference)


def test_varying_radial_force_gain_error_is_shared_not_recharged(tmp_path):
    config=configuration();config.update(model=2,profile=False,initial_v=np.array([150.,0.,0.]))
    config['limits'][:]=0.;config['limits'][18]=.15
    n=400;dt=np.full(n,.005);theta=np.zeros((n,3));dv=np.c_[.005*.05*np.sin(np.arange(n)*.01),np.zeros(n),np.full(n,-9.81*.005)]
    lo=-np.ones(27);hi=np.ones(27);center=np.zeros(27)
    reference=candidate.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    report=candidate.enclose(config,theta,dv,dt,time=1.8,lower=lo,upper=hi,reference=reference)
    scale=np.array([6371000.,6371000.,1.]);assert np.max(report.unshared_remainder*scale)<1e-5
    kernel=load_tangent(tmp_path)[0];value,jac=native(kernel,config,theta,dv,dt,1.8,center)
    assert np.max(abs(value-report.center)*scale)<1e-6
    for gain in (-1.,.7,1.):
        point=np.zeros(27);point[18]=gain;actual,_=native(kernel,config,theta,dv,dt,1.8,point)
        error=(actual-value-report.design(jac,reference)@np.r_[point-center,reference.normalized_values_at(point)])*scale
        assert np.all(abs(error)<=report.unshared_remainder*scale+1e-5)
