# SPDX-License-Identifier: AGPL-3.0-or-later
"""The remaining timing profile must cross both starts in both processing cases."""
import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_remaining_time_profile_worker.py')
    assert path.exists(), 'remaining timing profile launcher is missing'
    spec=importlib.util.spec_from_file_location('remaining_time_profile',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def inputs():
    sid='0e73879f98c3b701fd7c42df'
    controls=[dict(kind='control',source_identity=f'c{i}::case::model::control',
        fit=dict(active_parameters=['position_x','time_offset'],normalized_parameters=[0.,.1])) for i in range(2)]
    tasks=[]
    for case in ('bias1_unsubtracted','bias1_profiled_removal'):
        for role,t in (('primary',-.05),('repeat',-.52)):
            identity=f'{sid}::{case}::sphere_still::{role}'
            tasks.append(dict(identity=identity+'::old',source_identity=identity,kind='time_only',
                task=dict(segment_id=sid,case_id=case,model='sphere_still'),
                fit=dict(active_parameters=['position_x','time_offset'],normalized_parameters=[.2,t],
                         residual_sum_squares=10.),time_scale_s=.15))
    # The already-passing repeat was not part of the old diagnostic task list.
    untouched=tasks.pop(1);untouched['identity']=untouched.pop('source_identity')
    return dict(plan=dict(tasks=controls)),dict(plan=dict(tasks=tasks,untouched_passing_repeats=[untouched]))


def test_both_cases_cross_two_offsets_and_two_starts_without_mutating_sources():
    parent,old=inputs();before=copy.deepcopy((parent,old));plan=worker().make_plan(parent,old)
    assert (parent,old)==before
    assert len(plan['tasks'])==10 and plan['maximum_profile_starts']==8
    assert plan['maximum_native_evaluations']==654
    assert len({t['identity'] for t in plan['tasks']})==10
    profiles=plan['tasks'][2:]
    assert {(t['task']['case_id'],t['anchor_origin'],t['start_role']) for t in profiles}=={
        (case,anchor,start) for case in ('bias1_unsubtracted','bias1_profiled_removal')
        for anchor in ('primary','repeat') for start in ('primary','repeat')}
    assert sum(t['maximum_fit_calls']+t['maximum_diagnostic_calls'] for t in plan['tasks'])==654
    for item in profiles:
        assert item['start_full'][-1]==item['anchor_normalized']
        assert item['fit']['normalized_parameters'][-1]==(-.05 if item['start_role']=='primary' else -.52)


@pytest.mark.parametrize('failure',['missing','duplicate','layout','nan','outside','same_anchor','wrong_model'])
def test_invalid_sources_cannot_change_the_frozen_population(failure):
    parent,old=inputs();tasks=old['plan']['tasks']
    if failure=='missing':tasks.pop()
    if failure=='duplicate':tasks.append(copy.deepcopy(tasks[0]))
    if failure=='layout':tasks[0]['fit']['active_parameters'].reverse()
    if failure=='nan':tasks[0]['fit']['normalized_parameters'][-1]=float('nan')
    if failure=='outside':tasks[0]['fit']['normalized_parameters'][-1]=1.01
    if failure=='same_anchor':tasks[0]['fit']['normalized_parameters'][-1]=-.52
    if failure=='wrong_model':tasks[0]['task']['model']='flat_still'
    with pytest.raises(ValueError):worker().make_plan(parent,old)


def test_executor_preserves_the_completed_worker_and_fixes_only_checked_plumbing():
    module=worker();before=hashlib.sha256(module.TEMPLATE.read_bytes()).hexdigest()
    source=module.executor_source(module.TEMPLATE.read_text())
    compiled=module.build_executor()
    assert hashlib.sha256(module.TEMPLATE.read_bytes()).hexdigest()==before
    assert compiled.OUTPUT==module.OUTPUT and compiled.OLD==module.ORIGINAL
    assert compiled.__file__==str(Path(module.__file__).resolve())
    assert "'diagnostic','full_tangent'" not in source
    assert "maximum_evaluations=80" in source and 'position.verify_stability' in source
    assert compiled.make_plan(*inputs())['maximum_native_evaluations']==654
    with pytest.raises(ValueError):module.executor_source('unknown template')


def test_private_executor_changes_do_not_change_original_module_globals():
    module=worker();old=(module.parent.OUTPUT,module.parent.OLD,module.parent.make_plan)
    module.build_executor()
    assert (module.parent.OUTPUT,module.parent.OLD,module.parent.make_plan)==old
