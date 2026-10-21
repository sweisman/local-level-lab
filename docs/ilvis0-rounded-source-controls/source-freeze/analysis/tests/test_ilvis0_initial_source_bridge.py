# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import importlib,importlib.util
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case as training_case


def implementation():
    name='lll.ilvis0_initial_source_bridge'
    assert importlib.util.find_spec(name) is not None,'initial-source reference bridge is not implemented'
    return importlib.import_module(name)


@pytest.mark.parametrize('point',[True,False])
def test_bridge_keeps_reference_domain_and_all_columns(point):
    module=implementation()
    *_,lo,hi,reference,conditioning=training_case(0,False,point=point)
    proof=module.certify(reference,lo,hi)
    assert proof['reference_binding']==reference.binding
    assert proof['source_id']==reference.parent.source_id
    assert proof['lower']==list(lo) and proof['upper']==list(hi)
    assert np.asarray(proof['row_lower']).shape==np.asarray(proof['row_upper']).shape==(3,27)
    assert proof['nonlinear_cap_sufficient']
    assert all(F(v)>=0 for v in proof['padding'])
    if point:
        assert any(F(v)>0 for v in proof['padding'])
        assert max(map(F,proof['padding']))<F(1,10**10)
    assert not proof['training_adapter_qualified']


def test_point_padding_covers_physical_source_and_gravity_subtraction_rounding():
    module=implementation()
    from lll.ilvis0_source_value_stream import SourceValueStream
    config,theta,dv,dt,center,lo,hi,reference,conditioning=training_case(0,False,point=True)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    proof=module.certify(reference,lo,hi)
    with SourceValueStream(source,reference,lo,hi,.04,maximum_packets=1) as stream:
        physical=stream.append()['phases'][0]
    actual_lo,actual_hi=physical.interval('a')
    for axis in range(3):
        base=F(reference.acceleration.center[axis])
        if axis==2:base-=F(reference.acceleration.gravity)+F(reference.parent.limits[24])*F(center[24])
        pad=F(proof['padding'][axis])
        assert max(actual_lo[axis],base-pad)<=min(actual_hi[axis],base+pad)


def test_bridge_rejects_domain_outside_its_reference():
    module=implementation()
    *_,lo,hi,reference,_=training_case(0,False)
    with pytest.raises(ValueError,match='domain'):module.certify(reference,reference.parent.lower-.01,hi)
