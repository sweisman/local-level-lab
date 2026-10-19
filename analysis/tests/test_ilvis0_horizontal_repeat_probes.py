# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path(__file__).with_name('ilvis0_horizontal_repeat_probes.py')
    assert path.exists(),'fixed-point worker missing'
    spec=importlib.util.spec_from_file_location('repeat_probe_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixture():
    rows=[];pairs=[];endpoints=[]
    for case,model in (('bias1_unsubtracted','sphere_still'),('bias1_profiled_removal','sphere_still'),('bias1_unsubtracted','flat_still')):
        pairs.append(dict(segment_id='target',case_id=case,model=model,passed=False))
        for role,p in (('primary',[0.,0.]),('repeat',[.2,.1])):
            identity='::'.join(('target',case,model,role))
            rows.append(dict(identity=identity,segment_id='target',case_id=case,model=model,role=role,fit=dict(normalized_parameters=p,active_parameters=['time_offset','gravity_delta'])))
            endpoints.append(dict(identity=identity,corrections=[dict(method='range_scaled',step=[.01,0.],feasible=True)]))
    for role in ('primary','repeat'):
        identity='::'.join(('control','bias1_unsubtracted','sphere_rotating',role))
        rows.append(dict(identity=identity,segment_id='control',case_id='bias1_unsubtracted',model='sphere_rotating',role=role,fit=dict(normalized_parameters=[0.,0.],active_parameters=['time_offset','gravity_delta'])))
        endpoints.append(dict(identity=identity,corrections=[dict(method='range_scaled',step=[.01,0.],feasible=True)]))
    selected=[dict(segment=dict(segment_id='control',imu_type=8)),dict(segment=dict(segment_id='target',imu_type=21))]
    return rows,pairs,endpoints,selected


def test_exact_eight_identities_and_twenty_eight_points():
    result=module().tasks(*fixture())
    assert len(result)==8 and sum(len(r['points']) for r in result)==28
    assert all(-1<=v<=1 for r in result for p in r['points'] for v in p['point'])
    target=next(r for r in result if r['role']=='primary' and r['model']=='sphere_still')
    assert target['points'][1]['point']==[.2,0.]
    assert target['points'][2]['point']==[.1,.05]


def test_changed_failed_pair_population_is_rejected():
    rows,pairs,endpoints,selected=fixture();pairs.pop()
    with pytest.raises(ValueError):module().tasks(rows,pairs,endpoints,selected)
