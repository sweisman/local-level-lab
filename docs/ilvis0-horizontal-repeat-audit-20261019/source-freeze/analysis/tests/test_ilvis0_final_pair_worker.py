# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_final_pair_worker.py')
    assert path.exists(), 'focused final-pair worker is missing'
    spec=importlib.util.spec_from_file_location('final_pair_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def inputs():
    sid='370cec66878c4c1cf84b4ceb';controls=[];results=[];targets=[]
    for i in range(2):
        identity=f'control{i}';point=[.1,.2]
        controls.append(dict(identity=identity,kind='control',task=dict(segment_id='control',case_id='bias1_unsubtracted',model='sphere_rotating'),
            fit=dict(active_parameters=['time_offset','gravity_delta'],normalized_parameters=point)))
        results.append(dict(identity=identity,kind='control',status='complete',passed=True,normalized_parameters=point,
            residual_sum_squares=1.,linearization_file=f'{i}.gz',linearization_sha256='hash'))
    for role in ('primary','repeat'):
        identity=f'{sid}::bias1_profiled_removal::sphere_rotating::{role}'
        targets.append(dict(identity=identity+'::boundary_diagnostic',source_identity=identity,kind='time_only',stage='stage',
            task=dict(segment_id=sid,case_id='bias1_profiled_removal',model='sphere_rotating'),
            fit=dict(active_parameters=['time_offset','gravity_delta'],normalized_parameters=[.1,.2],residual_sum_squares=2.,
                linearization_file=role+'.gz',linearization_sha256='hash')))
    audit=dict(state='complete',reports=[dict(source_identity=targets[0]['source_identity'],needs_correction_investigation=True)])
    return dict(plan=dict(tasks=controls)),dict(state='complete',results=results),dict(plan=dict(tasks=targets)),audit


def test_exact_saved_profiled_pair_and_fresh_controls_with_fixed_allowance():
    values=inputs();before=copy.deepcopy(values);plan=worker().make_plan(*values)
    assert values==before and len(plan['tasks'])==4 and len({r['identity'] for r in plan['tasks']})==4
    assert plan['maximum_native_evaluations']==58 and plan['maximum_optimizer_starts']==0
    assert plan['maximum_starts']==4 and plan['numerical_threads']==4 and plan['retries']==0
    assert [t['maximum_diagnostic_calls'] for t in plan['tasks']]==[3,3,26,26]
    assert [t['start_role'] for t in plan['tasks'][2:]]==['primary','repeat']
    assert all(t['exact_point']==t['fit']['normalized_parameters'] for t in plan['tasks'][2:])
    assert all(t['task']['segment_id']=='370cec66878c4c1cf84b4ceb' for t in plan['tasks'][2:])
    assert not plan['scientific_stopping_limits_changed']


@pytest.mark.parametrize('bad',['missing','duplicate','control','wrong_case','wrong_model','point','audit','layout'])
def test_wrong_scope_or_incomplete_sources_fail_closed(bad):
    cm,cs,om,a=inputs()
    if bad=='missing':om['plan']['tasks'].pop()
    if bad=='duplicate':om['plan']['tasks'].append(copy.deepcopy(om['plan']['tasks'][0]))
    if bad=='control':cs['results'][0]['passed']=False
    if bad=='wrong_case':om['plan']['tasks'][0]['task']['case_id']='bias1_unsubtracted'
    if bad=='wrong_model':om['plan']['tasks'][0]['task']['model']='sphere_still'
    if bad=='point':om['plan']['tasks'][0]['fit']['normalized_parameters'][0]=float('nan')
    if bad=='audit':a['reports'][0]['needs_correction_investigation']=False
    if bad=='layout':om['plan']['tasks'][0]['fit']['active_parameters'].pop()
    with pytest.raises(ValueError):worker().make_plan(cm,cs,om,a)


def test_private_executor_keeps_completed_workers_and_scientific_gates_unchanged():
    module=worker();before=module.parent.TEMPLATE.read_bytes();executor=module.build_executor()
    assert module.parent.TEMPLATE.read_bytes()==before
    assert executor.OUTPUT==module.OUTPUT and executor.STOPPED==module.PARENT
    assert executor.__file__==str(Path(module.__file__).resolve())
    assert executor.source_plan is module.source_plan and executor.sources is module.sources
    source=module.executor_source(before.decode())
    assert 'from lll.ilvis0_representable_boundary import check_endpoint' in source
    assert 'previous.check_full(scope,identity,full' in source and 'len(calls)>58' in source
    with pytest.raises(ValueError):module.executor_source('changed template')


def test_repeat_report_retains_profiled_case_identity(tmp_path):
    import gzip
    import hashlib
    import json
    from types import SimpleNamespace
    import numpy as np
    module=worker();tasks=module.make_plan(*inputs())['tasks'];rows=[]
    for i,t in enumerate(tasks):
        row=dict(identity=t['identity'],kind=t['kind'],passed=True)
        if t['kind']=='target':
            data=dict(times_s=[0.,1.],gps=[[.5,.1,1000.]]*2,active_parameters=['time_offset'],residual=[0.]*6)
            p=tmp_path/f'{i}.gz';p.write_bytes(gzip.compress(json.dumps(data).encode(),mtime=0))
            row.update(linearization_file=p.name,linearization_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        rows.append(row)
    base=SimpleNamespace(sensitivity=SimpleNamespace(coordinate_covariance=lambda *args:np.eye(6)))
    result=module.compare_cases(rows,tasks,tmp_path,base,None)
    assert result['agreement_passed'] and result['case_id']=='bias1_profiled_removal'
    rows[-1]['passed']=False
    assert not module.compare_cases(rows,tasks,tmp_path,base,None)['agreement_passed']


def test_adding_saved_context_preserves_every_original_array():
    import gzip
    import json
    original=dict(active_parameters=['time_offset'],normalized_parameters=[.1],residual=[1.,2.,3.],jacobian=[[1.]]*3)
    before=copy.deepcopy(original);gps=[[.5,.1,1000.]];epochs=dict(times_s=[0.])
    result=json.loads(gzip.decompress(worker().context_bytes(original,epochs,gps)))
    assert original==before and all(result[k]==v for k,v in before.items())
    assert result['times_s']==[0.] and result['gps']==gps
    with pytest.raises(ValueError):worker().context_bytes(original,dict(times_s=[]),gps)
