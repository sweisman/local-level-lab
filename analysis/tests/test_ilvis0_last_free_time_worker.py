# SPDX-License-Identifier: AGPL-3.0-or-later
"""Final-stretch continuation retains both cases, free timing and finite charges."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_last_free_time_worker.py')
    assert path.exists(), 'final-stretch free-time launcher is missing'
    spec=importlib.util.spec_from_file_location('last_free_time',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def inputs():
    import json
    from test_ilvis0_remaining_free_time_worker import inputs as fixture
    return json.loads(json.dumps(fixture()).replace('0e73879f98c3b701fd7c42df','b4e44ddc0f130ecd45674c78'))


def test_exact_final_population_selects_verified_lower_cost_offsets():
    module=worker();executor=module.build_executor()
    manifest=json.loads((module.PARENT/'manifest.json').read_text())
    summary=json.loads((module.PARENT/'summary.json').read_text())
    before=copy.deepcopy((manifest,summary));plan=executor.make_plan(manifest,summary)
    assert before==(manifest,summary)
    assert plan['version']==module.VERSION
    assert (plan['maximum_starts'],plan['maximum_optimizer_starts'],plan['maximum_native_evaluations'])==(6,4,342)
    assert plan['numerical_threads']==4 and plan['retries']==0
    assert sum(t['maximum_fit_calls']+t['maximum_diagnostic_calls'] for t in plan['tasks'])==342
    from lll.ilvis0_profile_seeded import select_seed
    targets=[t for t in plan['tasks'] if t['kind']=='target']
    assert {(t['task']['case_id'],t['start_role']) for t in targets}=={
        (case,role) for case in module.CASES for role in ('primary','repeat')}
    for task in targets:
        assert task['task']['segment_id']==module.SID and task['task']['model']=='sphere_still'
        assert len(task['profiles'])==2 and max(task['anchors'])==1.
        seed=select_seed(task['profiles'],task['anchors'],task['fit']['active_parameters'])
        assert seed['anchor_normalized']==min(task['anchors'])
        assert task['fit']['active_parameters'].count('time_offset')==1
        assert all(Path(p['evidence_file']).parent==module.PARENT for p in task['profiles'])


@pytest.mark.parametrize('failure',['missing','duplicate','failed','pair','control','cross_case','layout','time'])
def test_failed_or_mixed_evidence_blocks_new_starts(failure):
    manifest,summary=inputs()
    if failure=='missing':summary['results'].pop()
    if failure=='duplicate':summary['results'].append(copy.deepcopy(summary['results'][-1]))
    if failure=='failed':summary['results'][-1]['conditional_converged']=False
    if failure=='pair':summary['pair_repeatability'][0]['agreement_passed']=False
    if failure=='control':summary['results'][0]['conditional_converged']=False
    if failure=='cross_case':manifest['plan']['tasks'][-1]['task']['case_id']='other'
    if failure=='layout':manifest['plan']['tasks'][-1]['fit']['active_parameters'].reverse()
    if failure=='time':summary['results'][-1]['normalized_parameters'][-1]=.9
    with pytest.raises(ValueError):worker().build_executor().make_plan(manifest,summary)


def test_private_executor_keeps_full_gates_and_qualified_source_checks():
    module=worker();before=hashlib.sha256(module.TEMPLATE.read_bytes()).hexdigest()
    old=(module.parent.OUTPUT,module.parent.VERSION,module.parent.parent.PARENT)
    executor=module.build_executor()
    assert before==hashlib.sha256(module.TEMPLATE.read_bytes()).hexdigest()
    assert old==(module.parent.OUTPUT,module.parent.VERSION,module.parent.parent.PARENT)
    assert executor.PARENT==executor.ENDPOINTS==executor.CONTROLS==module.PARENT
    assert executor.OUTPUT==module.OUTPUT and executor.VERSION==module.VERSION
    assert executor.TESTS==50
    assert executor.prepare.__globals__['source_plan'] is executor.source_plan
    source=module.executor_source(module.parent.parent.TEMPLATE.read_text())
    assert 'maximum_evaluations=80' in source and 'verify_stability' in source
    assert 'for directory in lock_directories(OUTPUT,PARENT,ENDPOINTS,CONTROLS):' in source
    assert 'test_ilvis0_last_free_time_worker.py' in source
    assert '../ilvis0-last-time-profile-20261018/RESULTS.md' in source
    assert executor.lock_directories(module.PARENT,module.PARENT/'.',module.OUTPUT)==[
        module.PARENT.resolve(),module.OUTPUT.resolve()]


def test_each_processing_case_requires_two_distinct_final_endpoints():
    module=worker();executor=module.build_executor()
    rows=[dict(identity=f'{module.SID}::{case}::sphere_still::free_time_{role}',kind='target',converged=True)
          for case in module.CASES for role in ('primary','repeat')]
    assert len(executor.case_groups(rows))==2
    rows[-1]['identity']=rows[0]['identity']
    with pytest.raises(ValueError):executor.case_groups(rows)


def test_qualification_pins_new_and_inherited_sources_without_original_reads():
    module=worker();executor=module.build_executor();sources=executor.sources()
    assert str(Path(module.__file__).resolve()) in sources
    assert str(Path(__file__).resolve()) in sources
    assert str(module.ROOT/'analysis/tests/ilvis0_last_time_profile_worker.py') in sources
    assert executor.source_plan()['version']==module.VERSION
