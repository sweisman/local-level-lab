# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case
from test_ilvis0_regrouped_history import native
from lll.ilvis0_shape import load_tangent


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):return load_tangent(tmp_path_factory.mktemp('component-native'))[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_training_condition_and_all_columns_survive_component_transport(model,profile,kernel):
    from lll import ilvis0_component_native as candidate,ilvis0_conditioned_transform_native as old
    config,theta,dv,dt,center,lo,hi,reference,conditioning=case(model,profile)
    kwargs=dict(time=.05,lower=lo,upper=hi,reference=reference,conditioning=conditioning)
    baseline=old.enclose(config,theta,dv,dt,**kwargs);report=candidate.enclose(config,theta,dv,dt,**kwargs)
    np.testing.assert_array_equal(report.center,baseline.center)
    for name in ('previous_coefficients','acceleration_coefficients','transform_coefficients'):
        np.testing.assert_array_equal(getattr(report,name).matrix,getattr(baseline,name).matrix)
    assert report.metadata['conditioning']['applies_only_to_training_region']
    value,jac=native(kernel,config,theta,dv,dt,.05,center);design=report.design(jac,reference)
    assert design.shape==(3,51);np.testing.assert_array_equal(design[:,:27],jac)
    scale=np.array([6371000.,6371000.,1.]);assert np.max(abs(value-report.center)*scale)<1e-6
    for sign in (-1,1):
        probe=center.copy();probe[12]+=.08*sign;probe[13]-=.08*sign
        actual,_=native(kernel,config,theta,dv,dt,.05,probe)
        gamma=reference.normalized_values_at(probe)
        error=abs((actual-value-design@np.r_[probe-center,gamma])*scale)
        assert np.all(error<=report.unshared_remainder*scale+1e-5)
