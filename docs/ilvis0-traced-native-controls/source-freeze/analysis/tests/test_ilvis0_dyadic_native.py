# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case
from lll.ilvis0_source_stream import load_stream
from lll.ilvis0_source_derivative_intervals import load_kernel


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    directory=tmp_path_factory.mktemp('dyadic-native')
    return load_stream(directory)[0],load_kernel(directory)[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_dyadic_candidate_exactly_preserves_native_bounds(model,profile,kernels):
    candidate=importlib.import_module('lll.ilvis0_dyadic_native')
    from lll import ilvis0_taylor_native as previous
    config,theta,dv,dt,center,lo,hi,reference,conditioning=case(model,profile)
    arguments=dict(time=.05,lower=lo,upper=hi,reference=reference,conditioning=conditioning,
        source_kernel=kernels[0],derivative_kernel=kernels[1])
    before=previous.enclose(config,theta,dv,dt,**arguments)
    after=candidate.enclose(config,theta,dv,dt,**arguments)
    np.testing.assert_array_equal(after.center,before.center)
    np.testing.assert_array_equal(after.unshared_remainder,before.unshared_remainder)
    for name in ('previous_coefficients','acceleration_coefficients','transform_coefficients'):
        np.testing.assert_array_equal(getattr(after,name).matrix,getattr(before,name).matrix)
    for name in ('source_derivative_steps','source_reference_steps','conditioning','source_initial_padding'):
        assert after.metadata[name]==before.metadata[name]
