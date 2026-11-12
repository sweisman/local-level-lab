# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite lifecycle checks for the same-operator conditioning comparison."""
import json

import pytest


def test_conditioning_study_has_one_finite_observation_free_task():
    from lll.noise_conditioning_study import recipe, tasks, construction_limits

    design = recipe()
    work = tasks()
    assert design['workers'] == design['threads'] == 1
    assert design['maximum_wall_s'] == 3600
    assert design['recovery']['version'] == 'lll-task-resume-v1'
    assert len(work) == 1
    assert work[0]['identity'] == 'increment-1200-conditioning'
    assert work[0]['limits'] == dict(native_calls=361200,
                                     packet_visits=361200,
                                     bound_calls=0, bound_steps=0)
    assert construction_limits() == dict(generated_samples=361201,
                                         constructed_intervals=360000,
                                         summary_epochs=400)
    assert design['original_reads'] == design['protected_reads'] == 0


def test_conditioning_study_requires_qualifications_before_writing(tmp_path):
    from lll.noise_conditioning_study import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path)
    assert not (tmp_path / 'data').exists()


def _context(tmp_path):
    from lll.noise_conditioning_study import SCOPE, recipe, tasks
    from lll.ilvis0_control_shards import prepare, TaskContext
    from lll.airquantumgrav_inventory import environment

    project = tmp_path / 'project'
    project.mkdir()
    (project / 'adapter.py').write_text('# lifecycle fixture\n')
    (project / 'recipe.json').write_text(json.dumps(recipe()))
    (project / 'environment.json').write_text(json.dumps(environment()))
    study = tmp_path / 'study'
    task = tasks()[0]
    prepare(study, project_root=project, tasks=[task],
            sources=['adapter.py'],
            inputs={'recipe': 'recipe.json',
                    'qualification-environment': 'environment.json'},
            adapter='adapter.py', workers=1, threads=1,
            maximum_wall_s=30, environment={'generated': True},
            accounting_format='sqlite-v1', scope=SCOPE)
    context = TaskContext(study, 0, task['identity'])
    return context.task, context


def test_conditioning_study_rejects_changed_task_before_work(tmp_path):
    from lll.noise_conditioning_study import evaluate

    task, context = _context(tmp_path)
    changed = dict(task, payload=dict(task['payload'], law='point'))
    with pytest.raises(ValueError, match='unchanged'):
        evaluate(changed, context)
    assert not context.directory.exists()


def test_conditioning_study_preserves_prepaid_work_after_failure(
        tmp_path, monkeypatch):
    from lll import noise_conditioning_study, generated_noise_benchmark
    from lll.ilvis0_control_shards import _counts

    task, context = _context(tmp_path)
    monkeypatch.setattr(noise_conditioning_study, 'kernel',
                        lambda context: None)

    def fail(**kwargs):
        assert _counts(context.journal, context.task)['native_calls'] == 361200
        raise RuntimeError('controlled construction stop')

    monkeypatch.setattr(generated_noise_benchmark, 'material', fail)
    with pytest.raises(RuntimeError, match='controlled construction stop'):
        noise_conditioning_study.evaluate(task, context)
    saved = json.loads((context.directory / 'native-prepayment.json').read_bytes())
    assert saved['state'] == 'failed_or_interrupted'
    assert saved['attempted']['native_calls'] == 0
    context.finish(dict(passed=False, reason='preserved control',
                        scientific_decision='abstain'))
