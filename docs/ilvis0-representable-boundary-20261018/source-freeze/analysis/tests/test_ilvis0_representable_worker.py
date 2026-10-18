# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_representable_worker.py')
    assert path.exists(), 'representable boundary launcher is missing'
    spec=importlib.util.spec_from_file_location('representable_worker',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def inputs():
    from test_ilvis0_remaining_boundary_worker import inputs as base
    manifest,summary,_=base();audits=[]
    for task,row in zip(manifest['plan']['tasks'],summary['results']):
        task['identity']+='::remaining_cluster_check';row['identity']=task['identity']
        row['passed']=row['kind']=='control' or task['task']['case_id']=='bias1_profiled_removal'
        row['reason']='two_sided_boundary_stability' if row['passed'] else 'side_geometry_unsupported'
        row['search']=dict(point=-.3000001)
        if not row['passed']:
            audits.append(dict(identity=row['identity'],knot_normalized=-.3000001,probe_guard_passed=False,
                probes_distinct=True,adjacent_clock_states_distinct=True,clock_state_matches=[True]*4))
    summary['repeatability']=dict(cases={'bias1_profiled_removal':dict(agreement_passed=True,both_full_fits_passed=True)})
    return manifest,summary,dict(state='complete',targets=audits)


def test_exact_two_failed_sources_and_controls_have_58_call_scope():
    values=inputs();before=copy.deepcopy(values);plan=worker().make_plan(*values)
    assert values==before and len(plan['tasks'])==4 and len({t['identity'] for t in plan['tasks']})==4
    assert plan['maximum_native_evaluations']==58 and plan['maximum_optimizer_starts']==0
    assert plan['maximum_starts']==4 and plan['maximum_geometry_queries']==402048
    assert plan['maximum_affine_solves']==6 and plan['numerical_threads']==4 and plan['retries']==0
    assert [t['maximum_diagnostic_calls'] for t in plan['tasks']]==[3,3,26,26]
    assert all(t['task']['case_id']=='bias1_unsubtracted' for t in plan['tasks'][2:])
    assert all(t['exact_point']==t['fit']['normalized_parameters'] for t in plan['tasks'][2:])
    assert plan['geometry_guard_changed'] and not plan['scientific_stopping_limits_changed']


@pytest.mark.parametrize('bad',['missing','duplicate','control','profile_pair','model','point','audit'])
def test_incomplete_or_changed_sources_block_new_diagnostic(bad):
    manifest,summary,audit=inputs()
    if bad=='missing':summary['results'].pop()
    if bad=='duplicate':summary['results'].append(copy.deepcopy(summary['results'][2]))
    if bad=='control':summary['results'][0]['passed']=False
    if bad=='profile_pair':summary['repeatability']['cases']['bias1_profiled_removal']['agreement_passed']=False
    if bad=='model':manifest['plan']['tasks'][2]['task']['model']='flat_still'
    if bad=='point':summary['results'][2]['normalized_parameters'][-1]=2.
    if bad=='audit':audit['targets'][0]['clock_state_matches'][0]=False
    with pytest.raises(ValueError):worker().make_plan(manifest,summary,audit)


def test_executor_source_isolation_and_unchanged_native_scope():
    module=worker();before=module.TEMPLATE.read_bytes();old=(module.parent.PARENT,module.parent.OUTPUT,module.parent.make_plan)
    executor=module.build_executor()
    assert module.TEMPLATE.read_bytes()==before and (module.parent.PARENT,module.parent.OUTPUT,module.parent.make_plan)==old
    assert executor.OUTPUT==module.OUTPUT and executor.STOPPED==module.PARENT and executor.AUDIT==module.AUDIT
    assert executor.__file__==str(Path(module.__file__).resolve()) and executor.TESTS==31
    assert executor.source_plan is module.source_plan and executor.sources is module.sources
    source=module.executor_source(before.decode())
    assert 'from lll.ilvis0_representable_boundary import check_endpoint' in source
    assert 'diagnostic_limit=26' in source and 'len(calls)>58' in source
    assert 'previous.check_full(scope,identity,full' in source
    with pytest.raises(ValueError):module.executor_source('changed source')


def test_only_the_single_case_primary_repeat_pair_is_compared(tmp_path):
    import gzip
    import hashlib
    import json
    from types import SimpleNamespace
    import numpy as np
    module=worker();tasks=module.make_plan(*inputs())['tasks'];rows=[]
    for i,task in enumerate(tasks):
        row=dict(identity=task['identity'],kind=task['kind'],passed=True)
        if task['kind']=='target':
            payload=dict(times_s=[0.,1.],gps=[[.5,.1,1000.],[.5,.1,1000.]],active_parameters=['time_offset'],residual=[20.,0.,0.,20.,0.,0.])
            path=tmp_path/f'{i}.gz';path.write_bytes(gzip.compress(json.dumps(payload).encode(),mtime=0))
            row.update(linearization_file=path.name,linearization_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        rows.append(row)
    base=SimpleNamespace(sensitivity=SimpleNamespace(coordinate_covariance=lambda *args:np.eye(6)))
    result=module.compare_cases(rows,tasks,tmp_path,base,None)
    assert result['agreement_passed'] and result['both_endpoints_passed']
    rows[-1]['passed']=False
    assert not module.compare_cases(rows,tasks,tmp_path,base,None)['agreement_passed']
