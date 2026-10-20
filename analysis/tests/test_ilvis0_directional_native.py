# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_directional_native as candidate,ilvis0_transform_native as old
from lll.ilvis0_directional_acceleration import DirectionalAcceleration
from lll.ilvis0_shape import load_tangent
from test_ilvis0_native_box_bounds import configuration
from test_ilvis0_regrouped_history import native


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    return load_tangent(tmp_path_factory.mktemp('directional-kernel'))[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_directional_propagation_preserves_centres_columns_and_probe_containment(model,profile,kernel):
    config=configuration();config.update(model=model,profile=profile)
    n=13;dt=np.full(n,.005);theta=np.tile([1e-5,-2e-5,3e-6],(n,1))
    dv=np.c_[1e-5*np.sin(np.arange(n)),2e-5*np.cos(np.arange(n)),np.full(n,-.04905)]
    lo=np.full(27,-.2);hi=np.full(27,.5);center=np.full(27,.1);time=.05
    reference=old.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    proof=DirectionalAcceleration(reference,lo,hi)
    kwargs=dict(time=time,lower=lo,upper=hi,reference=reference)
    baseline=old.enclose(config,theta,dv,dt,**kwargs)
    report=candidate.enclose(config,theta,dv,dt,conditioning=proof,**kwargs)
    np.testing.assert_array_equal(report.center,baseline.center)
    for name in ('previous_coefficients','acceleration_coefficients','transform_coefficients'):
        np.testing.assert_array_equal(getattr(report,name).matrix,getattr(baseline,name).matrix)
    assert report.metadata['conditioning']['preserves_shared_remainders']
    assert report.metadata['retained_acceleration_remainder']==reference.acceleration.remainder
    value,jac=native(kernel,config,theta,dv,dt,time,center);scale=np.array([6371000.,6371000.,1.])
    assert np.max(abs(value-report.center)*scale)<=1e-6
    design=report.design(jac,reference)
    assert design.shape==(3,51);np.testing.assert_array_equal(design[:,:27],jac)
    for point in (lo,hi,np.linspace(-.1,.4,27)):
        actual,_=native(kernel,config,theta,dv,dt,time,point)
        error=abs((actual-value-design@np.r_[point-center,reference.normalized_values_at(point)])*scale)
        assert np.all(error<=report.unshared_remainder*scale+1e-5)


def test_missing_or_wrong_physical_domain_is_rejected():
    config=configuration();dt=np.full(4,.005);theta=np.zeros((4,3));dv=np.tile([0.,0.,-.04905],(4,1))
    lo=-np.ones(27);hi=np.ones(27);center=np.zeros(27)
    reference=old.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    proof=DirectionalAcceleration(reference,lo,hi);kwargs=dict(time=.01,lower=lo,upper=hi,reference=reference)
    with pytest.raises(ValueError,match='directional'):candidate.enclose(config,theta,dv,dt,conditioning=None,**kwargs)
    kwargs['lower']=lo.copy();kwargs['lower'][0]=-.5
    with pytest.raises(ValueError,match='domain'):candidate.enclose(config,theta,dv,dt,conditioning=proof,**kwargs)
