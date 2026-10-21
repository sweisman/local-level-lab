# SPDX-License-Identifier: AGPL-3.0-or-later
from dataclasses import replace
from fractions import Fraction as F
import importlib,importlib.util
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case as training_case
from lll.ilvis0_source_stream import SourceStream,load_stream
from lll.ilvis0_source_value_stream import SourceValueStream
from lll.ilvis0_source_norm_preflight import body_bound


def implementation():
    name='lll.ilvis0_rounded_body_interval'
    assert importlib.util.find_spec(name) is not None,'rounded trained-source adapter is not implemented'
    return importlib.import_module(name)


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):return load_stream(tmp_path_factory.mktemp('rounded-body'))[0]


def frames(kernel,source,reference,lo,hi,time,point):
    with SourceValueStream(source,reference,lo,hi,time,maximum_packets=len(source['dt'])) as bounds,SourceStream(
            kernel,source,point,time,maximum_packets=len(source['dt'])) as native:
        for _ in source['dt']:proof=bounds.append();frame=native.append()
    return proof['phases'][1],frame


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
@pytest.mark.parametrize('point',[True,False])
@pytest.mark.parametrize('side',[-1,0,1])
def test_training_ranges_and_unchanged_centers_survive_clock_boundary(model,profile,point,side,kernel):
    module=implementation()
    config,theta,dv,dt,center,lo,hi,ref,conditioning=training_case(model,profile,point=point)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    time=sum(float(v) for v in dt[:6])-config['limits'][25]*center[25]
    if side:time=float(np.nextafter(time,float('inf') if side>0 else -float('inf')))
    proof,frame=frames(kernel,source,ref,lo,hi,time,center)
    old,_=body_bound(source,ref,lo,hi,time)
    a0=ref.acceleration.center.copy();a0[2]-=ref.acceleration.gravity+ref.parent.limits[24]*center[24]
    chosen=np.asarray([a0,old.center])
    adapter=module.RoundedBodyInterval(ref,conditioning,lo,hi)
    result=adapter.bound(proof,frame,phase=1,centers=chosen)
    np.testing.assert_array_equal(result.a.center,chosen[0]);np.testing.assert_array_equal(result.b.center,chosen[1])
    assert result.jacobian.shape==(2,3,27) and not result.jacobian.flags.writeable
    assert result.details['parent_conditioning_binding']==conditioning.binding
    assert result.details['explicit_rounding_bridge']
    probes=[center]
    if not point:
        for sign in (-1,1):
            probe=center.copy();probe[12]+=.08*sign;probe[13]-=.08*sign;probes.append(probe)
    for probe in probes:
        with SourceStream(kernel,source,probe,time,maximum_packets=len(dt)) as native:
            for _ in dt:actual=native.append()
        for value,observed,row in zip((result.a,result.b),actual['values'][1],frame['jacobian'][1],strict=True):
            for axis in range(3):
                error=F(float(observed[axis]))-F(float(value.center[axis]))
                linear=sum((F(float(j))*F(float(x-z)) for j,x,z in zip(row[axis],probe,center,strict=True)),F(0))
                assert abs(error)<=F(float(value.component_change[axis]))
                assert abs(error-linear)<=F(float(value.component_remainder[axis]))


def test_mismatched_source_phase_and_uncertified_nominal_values_are_rejected(kernel):
    module=implementation()
    config,theta,dv,dt,center,lo,hi,ref,conditioning=training_case(0,False)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    proof,frame=frames(kernel,source,ref,lo,hi,.04,center)
    adapter=module.RoundedBodyInterval(ref,conditioning,lo,hi)
    with pytest.raises(ValueError,match='identity'):adapter.bound(replace(proof,source_id='other'),frame,phase=1)
    with pytest.raises(ValueError,match='phase'):adapter.bound(proof,frame,phase=0)
    changed=dict(frame,values=frame['values'].copy());changed['values'][1,1,2]+=1.
    with pytest.raises(ValueError,match='reference'):adapter.bound(proof,changed,phase=1)


def test_every_prefix_phase_and_deliberately_changed_reference_rows_remain_bounded(kernel):
    module=implementation()
    config,theta,dv,dt,center,lo,hi,ref,conditioning=training_case(0,False)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt);time=.04
    adapter=module.RoundedBodyInterval(ref,conditioning,lo,hi);saved=[]
    with SourceValueStream(source,ref,lo,hi,time,maximum_packets=len(dt)) as physical,SourceStream(
            kernel,source,center,time,maximum_packets=len(dt)) as native:
        for _ in dt:
            proof=physical.append();frame=native.append();changed=dict(frame,jacobian=frame['jacobian'].copy())
            changed['jacobian'][:,1,2,12]+=.01
            saved.append([(adapter.bound(box,changed,phase=phase),changed['jacobian'][phase])
                for phase,box in enumerate(proof['phases'])])
    probe=center.copy();probe[12]+=.08;probe[13]-=.08
    with SourceStream(kernel,source,probe,time,maximum_packets=len(dt)) as native:
        for cases in saved:
            actual=native.append()
            for phase,(bounded,rows) in enumerate(cases):
                for value,observed,row in zip((bounded.a,bounded.b),actual['values'][phase],rows,strict=True):
                    for axis in range(3):
                        delta=F(float(observed[axis]))-F(float(value.center[axis]))
                        linear=sum((F(float(j))*(F(float(x))-F(float(z))) for j,x,z in zip(
                            row[axis],probe,center,strict=True)),F(0))
                        assert abs(delta)<=F(float(value.component_change[axis]))
                        assert abs(delta-linear)<=F(float(value.component_remainder[axis]))
