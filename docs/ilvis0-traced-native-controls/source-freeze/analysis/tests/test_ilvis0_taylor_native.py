# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib,importlib.util
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case
from lll.ilvis0_source_stream import load_stream
from lll.ilvis0_source_derivative_intervals import load_kernel


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    directory=tmp_path_factory.mktemp('taylor-native')
    return load_stream(directory)[0],load_kernel(directory)[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_taylor_source_preserves_centers_rows_and_only_tightens_bounds(model,profile,kernel):
    name='lll.ilvis0_taylor_native'
    assert importlib.util.find_spec(name) is not None,'batched native candidate is missing'
    candidate=importlib.import_module(name)
    from lll import ilvis0_source_native_v2 as reference
    config,theta,dv,dt,center,lo,hi,ref,conditioning=case(model,profile)
    args=dict(time=.05,lower=lo,upper=hi,reference=ref,conditioning=conditioning,source_kernel=kernel[0])
    before=reference.enclose(config,theta,dv,dt,**args)
    after=candidate.enclose(config,theta,dv,dt,**args,derivative_kernel=kernel[1])
    for field in ('center',):
        np.testing.assert_array_equal(getattr(after,field),getattr(before,field))
    for field in ('previous_coefficients','acceleration_coefficients','transform_coefficients'):
        np.testing.assert_array_equal(getattr(after,field).matrix,getattr(before,field).matrix)
    assert after.metadata['conditioning']==before.metadata['conditioning']
    assert after.metadata['rounded_source_prefixes']==before.metadata['rounded_source_prefixes']
    assert np.all(after.unshared_remainder<=before.unshared_remainder)
    assert after.metadata['source_mean_value_interval_installed']
