# SPDX-License-Identifier: AGPL-3.0-or-later
from dataclasses import fields
import importlib
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    directory=tmp_path_factory.mktemp('midpoint-source')
    return load_stream(directory)[0],load_kernel(directory)[0],load_point(directory)[0]


def same_value(a,b):
    for name in ('center','component_change','component_remainder'):
        np.testing.assert_array_equal(getattr(a,name),getattr(b,name))
    assert a.change==b.change and a.remainder==b.remainder


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
@pytest.mark.parametrize('point',(False,True))
def test_midpoint_certificates_and_next_packet_state_match_exactly(model,profile,point,kernels):
    module=importlib.import_module('lll.ilvis0_midpoint_source')
    from lll.ilvis0_direct_source_taylor import SourceDirectStream,DirectBodyInterval
    from lll.ilvis0_source_stream import SourceStream
    config,theta,dv,dt,center,lo,hi,reference,conditioning=case(model,profile,point=point)
    inputs=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    # Place the query on a packet boundary; the domain crosses both clock sides.
    query=sum(float(v) for v in dt[:6])-config['limits'][25]*center[25]
    args=dict(maximum_packets=len(dt),derivative_kernel=kernels[1],point_kernel=kernels[2])
    original=SourceDirectStream(inputs,reference,lo,hi,query,**args)
    candidate=module.SourceMidpointStream(inputs,reference,lo,hi,query,**args)
    body=DirectBodyInterval(reference,conditioning,lo,hi,direct_source_binding=original.direct.source_binding)
    numerical=SourceStream(kernels[0],inputs,center,query,maximum_packets=len(dt))
    try:
        for _ in dt:
            before=original.append();after=candidate.append();row=numerical.append()
            assert len(after['phases'])==1 and after['packet_index']==before['packet_index']
            a=before['phases'][0];b=after['phases'][0]
            assert a.report()==b.report()
            same_value(a.a,b.a);same_value(a.b,b.b)
            for name in ('center','change','remainder'):
                np.testing.assert_array_equal(getattr(original.body,name),getattr(candidate.body,name))
            assert original.elapsed==candidate.elapsed and original.visits==candidate.visits
            for name in a.derivative_frame:
                np.testing.assert_array_equal(a.derivative_frame[name],b.derivative_frame[name])
            for field in fields(a.direct_frame):
                np.testing.assert_array_equal(getattr(a.direct_frame,field.name),getattr(b.direct_frame,field.name))
            old_bound=body.bound(a,row,phase=0);new_bound=body.bound(b,row,phase=0)
            same_value(old_bound.a,new_bound.a);same_value(old_bound.b,new_bound.b)
            np.testing.assert_array_equal(old_bound.jacobian,new_bound.jacobian)
            assert old_bound.details==new_bound.details
            with pytest.raises(ValueError):body.bound(b,row,phase=1)
        with pytest.raises(ValueError):candidate.append()
    finally:
        original.close();candidate.close();numerical.close()
    with pytest.raises(ValueError):candidate.append()
