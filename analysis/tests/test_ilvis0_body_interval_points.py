# SPDX-License-Identifier: AGPL-3.0-or-later
"""Point and exact-clock checks for source-interval integration."""
from fractions import Fraction as F
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case as training_case
from lll.ilvis0_source_norm_preflight import body_bound
from lll.ilvis0_source_stream import SourceStream,load_stream


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):return load_stream(tmp_path_factory.mktemp('body-point'))[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
@pytest.mark.parametrize('boundary_side',[-1,0,1])
@pytest.mark.xfail(strict=True,raises=ValueError,
    reason='Unqualified source rounding: docs/ilvis0-body-interval/POINT_DIAGNOSIS.md; not a passing scientific gate')
def test_point_interval_covers_supplied_source_center_at_packet_boundary(model,profile,boundary_side,kernel):
    from lll.ilvis0_body_interval import BodyInterval
    config,theta,dv,dt,center,lo,hi,reference,conditioning=training_case(model,profile,point=True)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    time=sum(float(v) for v in dt[:6])-config['limits'][25]*center[25]
    if boundary_side:time=float(np.nextafter(time,float('inf') if boundary_side>0 else -float('inf')))
    baseline,_=body_bound(source,reference,lo,hi,time)
    with SourceStream(kernel,source,center,time,maximum_packets=len(dt)) as stream:
        for _ in dt:frame=stream.append()
    interval=BodyInterval(reference,conditioning,lo,hi)
    try:result=interval.bound(baseline,frame['values'][1],frame['jacobian'][1])
    except ValueError as error:
        if str(error)!='source norm closure contradicts the supplied interval':
            raise AssertionError('unexpected failure in the known source-rounding regression') from error
        raise
    # No generic numerical margin: a point reference discrepancy must be
    # included in the actual component allowance that will be propagated.
    for actual,value in zip(frame['values'][1],(result.a,result.b),strict=True):
        for axis in range(3):
            assert abs(F(float(actual[axis]))-F(float(value.center[axis])))<=F(float(value.component_change[axis]))
            assert abs(F(float(actual[axis]))-F(float(value.center[axis])))<=F(float(value.component_remainder[axis]))
