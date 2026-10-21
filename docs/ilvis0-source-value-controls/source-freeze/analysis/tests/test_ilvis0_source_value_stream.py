# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import importlib,importlib.util
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case as training_case
from lll.ilvis0_source_stream import SourceStream,load_stream
from lll.ilvis0_rotation_interval import vertical_interval


def implementation():
    name='lll.ilvis0_source_value_stream'
    assert importlib.util.find_spec(name) is not None,'rounded physical-source stream is not implemented'
    return importlib.import_module(name)


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):return load_stream(tmp_path_factory.mktemp('source-value'))[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
@pytest.mark.parametrize('point',[True,False])
def test_prefix_value_bounds_keep_source_identity_and_admit_norm_closure(model,profile,point,kernel):
    module=implementation()
    config,theta,dv,dt,center,lo,hi,reference,conditioning=training_case(model,profile,point=point)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    time=sum(float(v) for v in dt[:6])-config['limits'][25]*center[25]
    bounds=module.SourceValueStream(source,reference,lo,hi,time,maximum_packets=len(dt))
    with SourceStream(kernel,source,center,time,maximum_packets=len(dt)) as stream:
        for index in range(len(dt)):
            nominal=stream.append();frame=bounds.append()
            assert frame['packet_index']==index
            for phase,proof in enumerate(frame['phases']):
                assert proof.reference_binding==reference.binding
                assert proof.source_id==reference.parent.source_id
                assert proof.lower==tuple(lo) and proof.upper==tuple(hi)
                assert proof.phase==phase and proof.packet_index==index
                # Compare independently computed nominal values. These checks
                # use the actual propagated arithmetic allowance, no margin.
                for value,actual in zip((proof.a,proof.b),nominal['values'][phase],strict=True):
                    for axis in range(3):
                        assert abs(F(float(actual[axis]))-F(float(value.center[axis])))<=F(float(value.component_change[axis]))
                alo,ahi=proof.interval('a');blo,bhi=proof.interval('b')
                closure=vertical_interval(alo,ahi,blo,bhi,norm_identity=True,norm_error=proof.norm_error)
                assert F(closure['combined_lower'])<=F(closure['combined_upper'])


def test_packet_limit_and_source_mismatch_are_rejected(kernel):
    module=implementation()
    config,theta,dv,dt,center,lo,hi,reference,_=training_case(0,False)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    stream=module.SourceValueStream(source,reference,lo,hi,.04,maximum_packets=1)
    stream.append()
    with pytest.raises(ValueError,match='allowance'):stream.append()
    changed=dict(source,theta=theta.copy());changed['theta'][0,0]+=1e-5
    with pytest.raises(ValueError,match='source'):module.SourceValueStream(changed,reference,lo,hi,.04,maximum_packets=1)


def test_all_27_parameter_directions_and_clock_sides_are_contained(kernel):
    module=implementation()
    config,theta,dv,dt,center,_,_,reference,_=training_case(0,False)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    lo=center-.002;hi=center+.002
    time=sum(float(v) for v in dt[:6])-config['limits'][25]*center[25]
    bounds=module.SourceValueStream(source,reference,lo,hi,time,maximum_packets=len(dt))
    for _ in dt:frame=bounds.append()
    for column in range(27):
        for sign in (-1,1):
            point=center.copy();point[column]+=.002*sign
            with SourceStream(kernel,source,point,time,maximum_packets=len(dt)) as stream:
                for _ in dt:actual=stream.append()
            for phase,proof in enumerate(frame['phases']):
                for value,observed in zip((proof.a,proof.b),actual['values'][phase],strict=True):
                    assert np.all(abs(value.center-observed)<=value.component_change)


def test_literal_mount_metric_defect_and_input_immutability(kernel):
    module=implementation()
    from dataclasses import FrozenInstanceError
    from scipy.spatial.transform import Rotation
    from lll.ilvis0_transform_native import make_reference
    config,theta,dv,dt,center,lo,hi,old,_=training_case(0,False,point=True)
    config=dict(config,initial_r=Rotation.from_euler('xyz',[13.,-27.,5.],degrees=True).as_matrix())
    reference=make_reference(config,theta,dv,dt,lower=old.parent.lower,upper=old.parent.upper,center=center)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    stream=module.SourceValueStream(source,reference,lo,hi,.04,maximum_packets=len(dt))
    theta[:]=100.;dv[:]=100.;dt[:]=100.
    frame=stream.append();proof=frame['phases'][1]
    assert proof.norm_error>0
    alo,ahi=proof.interval('a');blo,bhi=proof.interval('b')
    assert vertical_interval(alo,ahi,blo,bhi,norm_identity=True,norm_error=proof.norm_error)
    assert not proof.a.center.flags.writeable and not proof.b.center.flags.writeable
    with pytest.raises(FrozenInstanceError):proof.norm_error=0
