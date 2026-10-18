# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import fcntl
import importlib.util
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_remaining_boundary_worker.py')
    assert path.exists(), 'remaining boundary launcher is missing'
    spec=importlib.util.spec_from_file_location('remaining_boundary',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def inputs():
    sid='0e73879f98c3b701fd7c42df';tasks=[];results=[];audit=[]
    for i in range(2):
        identity=f'c{i}';tasks.append(dict(identity=identity,kind='control',task={},fit=dict(active_parameters=['position_x','time_offset'])))
        results.append(dict(identity=identity,kind='control',status='complete',converged=True,
            normalized_parameters=[.1,.2],residual_sum_squares=10.,linearization_file=f'c{i}.gz',linearization_sha256='a'*64))
    for case in ('bias1_unsubtracted','bias1_profiled_removal'):
        for role in ('primary','repeat'):
            identity=f'{sid}::{case}::sphere_still::free_time_{role}'
            tasks.append(dict(identity=identity,kind='target',start_role=role,
                task=dict(segment_id=sid,case_id=case,model='sphere_still'),fit=dict(active_parameters=['position_x','time_offset'])))
            results.append(dict(identity=identity,kind='target',status='complete',converged=False,
                active_parameters=['position_x','time_offset'],normalized_parameters=[.2,-.3],
                residual_sum_squares=20.,linearization_file=identity.replace('::','-')+'.gz',linearization_sha256='b'*64))
            audit.append(dict(identity=identity,clock_geometry=dict(original_point=-.3)))
    return dict(plan=dict(tasks=tasks)),dict(state='complete',results=results),dict(state='complete',targets=audit)


def test_all_four_endpoints_and_two_controls_have_exact_finite_scope():
    values=inputs();before=copy.deepcopy(values);plan=worker().make_plan(*values)
    assert values==before and len(plan['tasks'])==6
    assert len({t['identity'] for t in plan['tasks']})==6
    assert plan['maximum_native_evaluations']==110 and plan['maximum_optimizer_starts']==0
    assert plan['maximum_geometry_queries']==804096 and plan['maximum_affine_solves']==10
    assert plan['numerical_threads']==4 and plan['retries']==0
    assert [t['maximum_diagnostic_calls'] for t in plan['tasks']]==[3,3,26,26,26,26]
    for task in plan['tasks'][2:]:
        assert task['exact_point']==task['fit']['normalized_parameters']
        assert task['source_identity']+'::remaining_cluster_check'==task['identity']


@pytest.mark.parametrize('change',['missing','duplicate','control','case','model','point','audit','unexpected_pass'])
def test_failed_or_changed_evidence_cannot_start_a_new_diagnostic(change):
    manifest,summary,audit=inputs()
    if change=='missing':summary['results'].pop()
    if change=='duplicate':summary['results'].append(copy.deepcopy(summary['results'][-1]))
    if change=='control':summary['results'][0]['converged']=False
    if change=='case':manifest['plan']['tasks'][-1]['task']['case_id']='other'
    if change=='model':manifest['plan']['tasks'][-1]['task']['model']='disc'
    if change=='point':summary['results'][-1]['normalized_parameters'][-1]=float('nan')
    if change=='audit':audit['targets'][-1]['clock_geometry']['original_point']=-.2
    if change=='unexpected_pass':summary['results'][-1]['converged']=True
    with pytest.raises(ValueError):worker().make_plan(manifest,summary,audit)


def test_identical_source_paths_get_one_real_exclusive_lock(tmp_path):
    module=worker();directories=module.unique_directories(tmp_path,tmp_path/'.',tmp_path)
    assert directories==[tmp_path.resolve()]
    with (directories[0]/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)


def test_executor_keeps_final_gates_and_completed_sources_unchanged():
    module=worker();before=module.TEMPLATE.read_bytes();executor=module.build_executor()
    assert module.TEMPLATE.read_bytes()==before and executor.OUTPUT==module.OUTPUT
    assert executor.__file__==str(Path(module.__file__).resolve())
    assert executor.TESTS==18 and executor.source_plan is module.source_plan
    source=module.executor_source(before.decode())
    assert 'previous.check_full(scope,identity,full' in source
    assert 'from lll.ilvis0_clustered_boundary import check_endpoint' in source
    assert 'diagnostic_limit=26' in source and 'len(calls)>110' in source
    assert 'compare_cases(results,m[' in source
    assert 'unique_directories(OUTPUT,STOPPED,AUDIT)' in source
    with pytest.raises(ValueError):module.executor_source('changed template')


def test_repeat_checks_do_not_pool_agreement_across_processing_cases(tmp_path):
    import gzip
    import hashlib
    import json
    from types import SimpleNamespace
    import numpy as np
    module=worker();tasks=module.make_plan(*inputs())['tasks'];rows=[]
    for i,task in enumerate(tasks):
        row=dict(identity=task['identity'],kind=task['kind'],passed=True)
        if task['kind']=='target':
            residual=[20.,0.,0.,20.,0.,0.]
            if task['task']['case_id']=='bias1_profiled_removal' and task['start_role']=='repeat':residual[2]=.1
            payload=dict(times_s=[0.,1.],gps=[[.5,.1,1000.],[.5,.1,1000.]],
                active_parameters=['time_offset'],residual=residual)
            path=tmp_path/f'{i}.gz';path.write_bytes(gzip.compress(json.dumps(payload).encode(),mtime=0))
            row.update(linearization_file=path.name,linearization_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        rows.append(row)
    base=SimpleNamespace(sensitivity=SimpleNamespace(coordinate_covariance=lambda *args:np.eye(6)))
    result=module.compare_cases(rows,tasks,tmp_path,base,None)
    assert result['cases']['bias1_unsubtracted']['agreement_passed']
    assert not result['cases']['bias1_profiled_removal']['agreement_passed']
    assert not result['agreement_passed']
