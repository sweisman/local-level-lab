"""The noisy-stream oracle has two finite, recoverable tasks."""

from types import SimpleNamespace

import pytest


def _context(tmp_path):
    import json
    from lll.esa_oracle_study import recipe, tasks, SCOPE
    from lll.ilvis0_control_shards import prepare as prepare_runtime, TaskContext

    project = tmp_path/'project'
    project.mkdir()
    (project/'adapter.py').write_text('# oracle fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    output = tmp_path/'study'
    task = tasks()[0]
    prepare_runtime(output, project_root=project, tasks=[task],
        sources=['adapter.py'], inputs=dict(recipe='recipe.json'),
        adapter='adapter.py', workers=1, threads=1, maximum_wall_s=30,
        environment={'generated':True}, accounting_format='sqlite-v1',
        scope=SCOPE)
    context = TaskContext(output, 0, task['identity'])
    return context.manifest['tasks'][0], context


def test_oracle_study_declares_exact_original_streams_and_work():
    from lll.esa_oracle_study import tasks, recipe

    r = recipe()
    assert (r['workers'], r['threads'], r['maximum_wall_s']) == (2, 1, 3600.)
    assert [row['identity'] for row in tasks()] == ['increment', 'point']
    assert all(row['limits'] == dict(native_calls=1,
        packet_visits=243_000_000, bound_calls=0, bound_steps=0)
        for row in tasks())


def test_oracle_study_requires_qualification_before_staging(tmp_path):
    from lll.esa_oracle_study import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path)


def test_oracle_study_rejects_task_change_before_input_read():
    from lll.esa_oracle_study import evaluate, tasks, SCOPE

    task = dict(tasks()[0], index=0, shard=0)
    task['limits'] = dict(task['limits'], packet_visits=243_000_001)
    with pytest.raises(ValueError, match='unchanged oracle task'):
        evaluate(task, SimpleNamespace(manifest=dict(scope=SCOPE)))


def test_oracle_recovery_is_bound_to_exact_two_task_parent():
    from lll.esa_oracle_study import ID, SCOPE
    from lll.esa_oracle_study_recovery import SPEC

    assert SPEC.parent == 'data/'+ID
    assert SPEC.scope == SCOPE
    assert SPEC.task_count == SPEC.workers == 2
    assert SPEC.max_attempts_per_task == 2


def test_oracle_worker_charges_exact_native_work_before_execution(tmp_path,
                                                                monkeypatch):
    from lll import esa_oracle_study as study
    from lll.ilvis0_control_shards import _counts

    task, context = _context(tmp_path)
    def fake(task, context, reserve):
        assert _counts(context.journal,context.task)['native_calls'] == 1
        reserve(native_calls=1,packet_visits=243_000_000)
        return dict(passed=True,scientific_decision='abstain')
    monkeypatch.setattr(study,'execute_oracle',fake)
    assert study.run_case(task,context)['passed'] is True
    context.finish(dict(passed=True,scientific_decision='abstain'))


def test_oracle_worker_keeps_charged_failure(tmp_path, monkeypatch):
    import json
    from lll import esa_oracle_study as study

    task, context = _context(tmp_path)
    def fails(task,context,reserve):
        reserve(native_calls=1,packet_visits=1)
        raise RuntimeError('preserved oracle failure')
    monkeypatch.setattr(study,'execute_oracle',fails)
    with pytest.raises(RuntimeError,match='preserved oracle failure'):
        study.run_case(task,context)
    snapshot=json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['attempted']==dict(native_calls=1,packet_visits=1)
    assert snapshot['state']=='failed_or_interrupted'
