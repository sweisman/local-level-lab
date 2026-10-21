# SPDX-License-Identifier: AGPL-3.0-or-later
"""Native integration checks; distinct from frozen end-to-end qualification."""
import importlib
import importlib.util
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case
from test_ilvis0_regrouped_history import native
from lll.ilvis0_shape import load_tangent


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    return load_tangent(tmp_path_factory.mktemp('compiled-native'))[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_compiled_propagation_preserves_centers_rows_and_nonlinear_containment(model,profile,kernel,tmp_path):
    name='lll.ilvis0_compiled_native'
    assert importlib.util.find_spec(name) is not None,'compiled native propagation is not implemented'
    candidate=importlib.import_module(name)
    from lll import ilvis0_cached_native as reference
    from lll.ilvis0_compiled_transport import configure_backend
    configure_backend(tmp_path)
    config,theta,dv,dt,center,lo,hi,ref,conditioning=case(model,profile)
    kwargs=dict(time=.05,lower=lo,upper=hi,reference=ref,conditioning=conditioning)
    old=reference.enclose(config,theta,dv,dt,**kwargs)
    result=candidate.enclose(config,theta,dv,dt,**kwargs)
    np.testing.assert_array_equal(result.center,old.center)
    for field in ('previous_coefficients','acceleration_coefficients','transform_coefficients'):
        np.testing.assert_array_equal(getattr(result,field).matrix,getattr(old,field).matrix)
    assert result.metadata['conditioning']==old.metadata['conditioning']
    assert result.metadata['compiled_outward_arithmetic']
    assert not result.report()['floating_point_enclosure_verified']
    assert not result.report()['observational_coverage_qualified']
    value,jac=native(kernel,config,theta,dv,dt,.05,center)
    design=result.design(jac,ref)
    assert design.shape==(3,51)
    np.testing.assert_array_equal(design[:,:27],jac)
    metric=np.array([6371000.,6371000.,1.])
    assert np.max(abs(value-result.center)*metric)<1e-6
    for sign in (-1,1):
        probe=center.copy();probe[12]+=.08*sign;probe[13]-=.08*sign
        actual,_=native(kernel,config,theta,dv,dt,.05,probe)
        gamma=ref.normalized_values_at(probe)
        error=abs((actual-value-design@np.r_[probe-center,gamma])*metric)
        assert np.all(error<=result.unshared_remainder*metric+1e-5)
