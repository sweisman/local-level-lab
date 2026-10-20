# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import sys
from types import SimpleNamespace
import numpy as np
from lll import ilvis0_propagation_trace as trace,ilvis0_acceleration_native as native
from lll.ilvis0_sharded_native import plain
from lll.ilvis0_orientation_cover import sector
import ilvis0_native_training_worker as generator


def test_observer_preserves_exact_report_and_records_both_midpoint_calls():
    case=generator.case_inputs(dict(model=0,profile=False,packets=100));config=case['configuration'];box=sector(4)
    theta=np.array(case['theta']);dv=np.array(case['dv']);dt=np.array(case['dt'])
    reference=native.make_reference(config,theta,dv,dt,lower=box['lower'],upper=box['upper'],center=box['center'])
    kwargs=dict(time=.3,lower=box['lower'],upper=box['upper'],reference=reference)
    expected=native.enclose(config,theta,dv,dt,**kwargs).report()
    report,records=trace.observe(config,theta,dv,dt,**kwargs)
    assert json.dumps(plain(report.report()),sort_keys=True)==json.dumps(plain(expected),sort_keys=True)
    assert len(records)==report.metadata['used_packet_count']
    assert all(len(row['increments'])==2 for row in records)
    assert all('reference_action' in item and 'difference_action' in item for row in records for item in row['increments'])
    assert sys.gettrace() is None


def test_standalone_adapter_seals_compressed_trace_with_one_bound_charge(tmp_path):
    case=generator.case_inputs(dict(model=0,profile=False,packets=100));box=sector(4)
    reference=native.make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center'])
    report=native.enclose(case['configuration'],case['theta'],case['dv'],case['dt'],time=.3,
        lower=box['lower'],upper=box['upper'],reference=reference)
    source=tmp_path/'case.json';source.write_text(json.dumps(plain(case)))
    bundle=tmp_path/'expected.json';bundle.write_text(json.dumps(plain(dict(expected=dict(report.report(),reference=reference.report())))))
    charges=[];saved={};artifacts=[]
    context=SimpleNamespace(directory=tmp_path,input_path=lambda key=None:source if key=='case' else bundle,
        charge=lambda **kw:charges.append(kw),save=lambda key,value:saved.__setitem__(key,value),note_file=artifacts.append)
    answer=trace.evaluate(dict(identity='trace-fixture',payload=dict(case_key='case')),context)
    assert answer['passed'] and answer['exact_report_match']
    assert charges==[dict(bound_calls=1,bound_steps=100)]
    assert artifacts==[tmp_path/'trace.json.gz'] and artifacts[0].exists()
