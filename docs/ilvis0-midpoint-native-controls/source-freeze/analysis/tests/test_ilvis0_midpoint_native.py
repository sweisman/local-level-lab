# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import importlib.util
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case


def test_native_candidate_changes_only_the_explicit_source_stream_binding():
    name='lll.ilvis0_midpoint_native';spec=importlib.util.find_spec(name)
    assert spec is not None,'midpoint native candidate is missing'
    previous=Path(importlib.util.find_spec('lll.ilvis0_direct_native').origin).read_text()
    candidate=Path(spec.origin).read_text()
    original='from .ilvis0_direct_source_taylor import SourceDirectStream as SourceValueStream'
    replacement='from .ilvis0_midpoint_source import SourceMidpointStream as SourceValueStream'
    assert previous.count(original)==1
    assert candidate==previous.replace(original,replacement)


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    directory=tmp_path_factory.mktemp('midpoint-native')
    return load_stream(directory)[0],load_kernel(directory)[0],load_point(directory)[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_complete_native_reports_match_exactly_for_every_candidate(model,profile,kernels):
    from lll import ilvis0_direct_native as previous,ilvis0_midpoint_native as candidate
    config,theta,dv,dt,center,lo,hi,reference,conditioning=case(model,profile)
    arguments=dict(time=.05,lower=lo,upper=hi,reference=reference,conditioning=conditioning,
        source_kernel=kernels[0],derivative_kernel=kernels[1],point_kernel=kernels[2])
    before=previous.enclose(config,theta,dv,dt,**arguments)
    after=candidate.enclose(config,theta,dv,dt,**arguments)
    assert before.report()==after.report()
    np.testing.assert_array_equal(before.center,after.center)
    np.testing.assert_array_equal(before.unshared_remainder,after.unshared_remainder)
