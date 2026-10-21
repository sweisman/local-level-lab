# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case
from test_ilvis0_dyadic_native import kernels


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_trace_preserves_every_existing_report_field(model,profile,kernels):
    from lll import ilvis0_dyadic_native as previous
    candidate=importlib.import_module('lll.ilvis0_traced_native')
    config,theta,dv,dt,center,lo,hi,ref,proof=case(model,profile)
    arguments=dict(time=.05,lower=lo,upper=hi,reference=ref,conditioning=proof,
        source_kernel=kernels[0],derivative_kernel=kernels[1])
    before=previous.enclose(config,theta,dv,dt,**arguments).report()
    after=candidate.enclose(config,theta,dv,dt,trace_stride=2,**arguments).report()
    trace=after.pop('propagation_trace')
    assert after==before
    assert 1<=len(trace['rows'])<=32
    assert trace['rows'][-1]['packet_index']==after['used_packet_count']-1
    assert all(np.all(np.isfinite(row['departure_remainder'])) for row in trace['rows'])
    assert trace['nested_allowances_are_not_additive']


def test_trace_requires_a_bounded_positive_stride(kernels):
    candidate=importlib.import_module('lll.ilvis0_traced_native')
    config,theta,dv,dt,center,lo,hi,ref,proof=case(0,False)
    with pytest.raises(ValueError,match='stride'):
        candidate.enclose(config,theta,dv,dt,time=.05,lower=lo,upper=hi,reference=ref,
            conditioning=proof,source_kernel=kernels[0],derivative_kernel=kernels[1],trace_stride=0)
