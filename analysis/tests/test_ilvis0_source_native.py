# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib,importlib.util
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case
from test_ilvis0_regrouped_history import native
from lll.ilvis0_shape import load_tangent
from lll.ilvis0_source_stream import load_stream


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    directory=tmp_path_factory.mktemp('source-native')
    return load_tangent(directory)[0],load_stream(directory)[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_installed_source_keeps_native_centers_and_all_51_columns(model,profile,kernels):
    name='lll.ilvis0_source_native'
    assert importlib.util.find_spec(name) is not None,'rounded source is not integrated into native propagation'
    candidate=importlib.import_module(name)
    from lll import ilvis0_compiled_native as old
    config,theta,dv,dt,center,lo,hi,reference,conditioning=case(model,profile)
    kwargs=dict(time=.05,lower=lo,upper=hi,reference=reference,conditioning=conditioning)
    baseline=old.enclose(config,theta,dv,dt,**kwargs)
    result=candidate.enclose(config,theta,dv,dt,**kwargs,source_kernel=kernels[1])
    np.testing.assert_array_equal(result.center,baseline.center)
    for key in ('previous_coefficients','acceleration_coefficients','transform_coefficients'):
        np.testing.assert_array_equal(getattr(result,key).matrix,getattr(baseline,key).matrix)
    assert result.metadata['source_norm_interval_installed']
    assert result.metadata['rounded_source_prefixes']==result.metadata['used_packet_count']
    assert result.metadata['conditioning']==baseline.metadata['conditioning']
    value,jac=native(kernels[0],config,theta,dv,dt,.05,center)
    design=result.design(jac,reference)
    assert design.shape==(3,51);np.testing.assert_array_equal(design[:,:27],jac)
    metric=np.array([6371000.,6371000.,1.])
    assert np.max(abs(result.center-value)*metric)<1e-6
    for sign in (-1,1):
        probe=center.copy();probe[12]+=.08*sign;probe[13]-=.08*sign
        actual,_=native(kernels[0],config,theta,dv,dt,.05,probe)
        gamma=reference.normalized_values_at(probe)
        error=abs((actual-value-design@np.r_[probe-center,gamma])*metric)
        assert np.all(error<=result.unshared_remainder*metric+1e-5)
