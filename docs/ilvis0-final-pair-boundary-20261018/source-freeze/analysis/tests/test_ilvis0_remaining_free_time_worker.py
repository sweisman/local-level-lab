# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two-case free-time continuation must preserve scope, gates and receipts."""
import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_remaining_free_time_worker.py')
    assert path.exists(), 'remaining free-time launcher is missing'
    spec=importlib.util.spec_from_file_location('remaining_free_time',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def inputs():
    sid='0e73879f98c3b701fd7c42df';tasks=[];results=[];pairs=[]
    for i in range(2):
        identity=f'control{i}'
        tasks.append(dict(identity=identity,source_identity=identity,kind='control',
            fit=dict(active_parameters=['position_x','time_offset'],normalized_parameters=[0.,.1]),task={}))
        results.append(dict(identity=identity,kind='control',status='complete',conditional_converged=True))
    for case in ('bias1_unsubtracted','bias1_profiled_removal'):
        for anchor,t in (('primary',-.05),('repeat',-.52)):
            pairs.append(dict(anchor_role=case+'__'+anchor,both_conditional_fits_passed=True,agreement_passed=True))
            for start in ('primary','repeat'):
                identity=f'{sid}::{case}::{anchor}::{start}'
                tasks.append(dict(identity=identity,source_identity=f'{sid}::{case}::sphere_still::{start}',kind='profile',
                    task=dict(segment_id=sid,case_id=case,model='sphere_still'),
                    fit=dict(active_parameters=['position_x','time_offset']),
                    anchor_origin=anchor,start_role=start,anchor_role=case+'__'+anchor,anchor_normalized=t))
                results.append(dict(identity=identity,kind='profile',status='complete',conditional_converged=True,
                    normalized_parameters=[.2,t],residual_sum_squares=10.+t*t,
                    linearization_file=identity.replace('::','-')+'.gz',linearization_sha256='a'*64))
    return dict(plan=dict(tasks=tasks)),dict(state='complete',controls_passed=True,results=results,pair_repeatability=pairs)


def test_exact_two_cases_two_starts_two_anchors_and_fresh_controls():
    values=inputs();before=copy.deepcopy(values);plan=worker().make_plan(*values)
    assert values==before
    assert len(plan['tasks'])==6 and len({t['identity'] for t in plan['tasks']})==6
    assert plan['maximum_starts']==6 and plan['maximum_optimizer_starts']==4
    assert plan['maximum_native_evaluations']==342 and plan['retries']==0 and plan['numerical_threads']==4
    assert sum(t['maximum_fit_calls']+t['maximum_diagnostic_calls'] for t in plan['tasks'])==342
    assert {(t['task']['case_id'],t['start_role']) for t in plan['tasks'][2:]}=={
        (case,role) for case in worker().CASES for role in ('primary','repeat')}
    for t in plan['tasks'][2:]:
        assert len(t['profiles'])==2 and len(set(t['anchors']))==2
        assert {r['source_identity'].rsplit('::',1)[-1] for r in t['profiles']}=={t['start_role']}
        assert {r['active_parameters'][-1] for r in t['profiles']}=={'time_offset'}


@pytest.mark.parametrize('failure',['missing','duplicate','failed','pair','control','cross_case','layout','time'])
def test_incomplete_or_mixed_profiles_block_preparation(failure):
    manifest,summary=inputs()
    if failure=='missing':summary['results'].pop()
    if failure=='duplicate':summary['results'].append(copy.deepcopy(summary['results'][-1]))
    if failure=='failed':summary['results'][-1]['conditional_converged']=False
    if failure=='pair':summary['pair_repeatability'][0]['agreement_passed']=False
    if failure=='control':summary['results'][0]['conditional_converged']=False
    if failure=='cross_case':manifest['plan']['tasks'][-1]['task']['case_id']='other'
    if failure=='layout':manifest['plan']['tasks'][-1]['fit']['active_parameters'].reverse()
    if failure=='time':summary['results'][-1]['normalized_parameters'][-1]=.9
    with pytest.raises(ValueError):worker().make_plan(manifest,summary)


def test_each_case_requires_its_own_primary_repeat_pair():
    module=worker();rows=[dict(identity=f'{module.SID}::{case}::sphere_still::free_time_{role}',
        kind='target',converged=True) for case in module.CASES for role in ('primary','repeat')]
    groups=module.case_groups(rows)
    assert len(groups)==2 and all(len(v)==2 for v in groups.values())
    rows[-1]['identity']=rows[0]['identity']
    with pytest.raises(ValueError):module.case_groups(rows)


def test_executor_preserves_original_modules_and_full_gate():
    module=worker();before=hashlib.sha256(module.TEMPLATE.read_bytes()).hexdigest()
    original=(module.parent.OUTPUT,module.parent.make_plan)
    source=module.executor_source(module.TEMPLATE.read_text());executor=module.build_executor()
    assert hashlib.sha256(module.TEMPLATE.read_bytes()).hexdigest()==before
    assert original==(module.parent.OUTPUT,module.parent.make_plan)
    assert executor.OUTPUT==module.OUTPUT and executor.PARENT==module.PARENT
    assert executor.__file__==str(Path(module.__file__).resolve())
    assert 'maximum_evaluations=80' in source and 'verify_stability' in source
    assert "'diagnostic','tangent'" in source
    assert 'compare_cases(results,OUTPUT,base,assumption)' in source
    assert executor.source_plan is module.source_plan
    with pytest.raises(ValueError):module.executor_source('unknown executor')
