# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path

import pytest


def worker():
    p=Path(__file__).with_name('ilvis0_last_field_worker.py')
    assert p.exists(), 'last-stretch field worker is missing'
    spec=importlib.util.spec_from_file_location('last_field_worker',p)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def inputs():
    from test_ilvis0_final_pair_worker import inputs as previous
    cm,cs,om,_=previous();targets=[]
    for case in ('bias1_unsubtracted','bias1_profiled_removal'):
        for original in om['plan']['tasks']:
            item=copy.deepcopy(original)
            identity=item['source_identity'].replace('370cec66878c4c1cf84b4ceb','b4e44ddc0f130ecd45674c78').replace('bias1_profiled_removal',case)
            item.update(source_identity=identity,identity=identity+'::boundary_diagnostic')
            item['task'].update(segment_id='b4e44ddc0f130ecd45674c78',case_id=case)
            item['fit'].update(epoch_file='epochs.gz',epoch_sha256='hash')
            targets.append(item)
    return cm,cs,dict(plan=dict(tasks=targets))


def test_exact_two_case_four_endpoint_scope_preserves_inputs():
    values=inputs();before=copy.deepcopy(values);plan=worker().make_plan(*values)
    assert values==before and len(plan['tasks'])==6
    assert len({t['identity'] for t in plan['tasks']})==6
    assert plan['maximum_starts']==6 and plan['maximum_native_evaluations']==110
    assert plan['maximum_optimizer_starts']==0 and plan['maximum_affine_solves']==10
    assert plan['numerical_threads']==4 and plan['retries']==0
    assert [t['maximum_diagnostic_calls'] for t in plan['tasks']]==[3,3,26,26,26,26]
    assert {t['task']['case_id'] for t in plan['tasks'][2:]}=={'bias1_unsubtracted','bias1_profiled_removal'}
    assert all(t['task']['model']=='sphere_rotating' for t in plan['tasks'][2:])


def test_missing_duplicate_or_wrong_model_is_rejected():
    module=worker()
    for bad in ('missing','duplicate','model','bounds','controls'):
        cm,cs,om=inputs()
        if bad=='missing':om['plan']['tasks'].pop()
        if bad=='duplicate':om['plan']['tasks'].append(copy.deepcopy(om['plan']['tasks'][0]))
        if bad=='model':om['plan']['tasks'][0]['task']['model']='sphere_still'
        if bad=='bounds':om['plan']['tasks'][0]['fit']['normalized_parameters'][0]=1.1
        if bad=='controls':cs['results'][0]['passed']=False
        with pytest.raises(ValueError):module.make_plan(cm,cs,om)


def test_private_executor_preserves_native_gates_and_six_identity_accounting():
    module=worker();p=Path(module.parent.parent.parent.__file__);before=p.read_bytes()
    executor=module.build_executor()
    assert p.read_bytes()==before and executor.OUTPUT==module.OUTPUT
    assert executor.__file__==str(Path(module.__file__).resolve())
    source=module.executor_source(module.parent.parent.parent.parent.TEMPLATE.read_text())
    assert 'from lll.ilvis0_scaled_branch import check_endpoint' in source
    assert "len(book.read('starts'))>6 or len(calls)>110" in source
    assert 'previous.check_full(scope,identity,full' in source
    assert executor.source_plan is module.source_plan and executor.compare_cases is module.compare_cases
    assert executor.prepare.func.__globals__['source_plan'] is module.source_plan
    import gzip
    import json
    plan=executor.source_plan()
    assert len(plan['tasks'])==6
    for task in plan['tasks']:
        if task['kind']!='target':continue
        context=json.loads(gzip.decompress(module.parent.parent.source_context(task)))
        assert context['normalized_parameters']==task['exact_point']
        assert context['gps']==[[r['latitude_rad'],r['longitude_rad'],r['height_m']]
            for r in task['task']['selected']['segment']['receiver_fixes']]


def test_case_specific_repeat_failure_blocks_full_qualification(tmp_path):
    import gzip
    import hashlib
    import json
    from types import SimpleNamespace
    import numpy as np
    module=worker();tasks=module.make_plan(*inputs())['tasks'];rows=[]
    for i,t in enumerate(tasks):
        row=dict(identity=t['identity'],kind=t['kind'],passed=True)
        if t['kind']=='target':
            payload=dict(times_s=[0.,1.],gps=[[.5,.1,1000.]]*2,
                active_parameters=['time_offset'],residual=[0.]*6)
            path=tmp_path/f'{i}.gz';path.write_bytes(gzip.compress(json.dumps(payload).encode(),mtime=0))
            row.update(linearization_file=path.name,linearization_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        rows.append(row)
    base=SimpleNamespace(sensitivity=SimpleNamespace(coordinate_covariance=lambda *a:np.eye(6)))
    result=module.compare_cases(rows,tasks,tmp_path,base,None)
    assert result['agreement_passed'] and set(result['cases'])==set(module.CASES)
    rows[2]['passed']=False
    failed=module.compare_cases(rows,tasks,tmp_path,base,None)
    assert not failed['agreement_passed']
    assert not failed['cases']['bias1_unsubtracted']['agreement_passed']
    assert failed['cases']['bias1_profiled_removal']['agreement_passed']
