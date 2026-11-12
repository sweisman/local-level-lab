# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite attribution-study lifecycle and evidence boundaries."""

import json

import pytest


def test_component_study_has_ten_finite_reboot_safe_tasks():
    from lll.noise_component_study import recipe, tasks, construction_limits

    design = recipe()
    work = tasks()
    assert design['workers'] == 2 and design['threads'] == 1
    assert design['maximum_wall_s'] == 7200
    assert design['recovery']['version'] == 'lll-task-resume-v1'
    assert len(work) == len({task['identity'] for task in work}) == 10
    assert {task['payload']['variant'] for task in work} == set(
        __import__('lll.noise_component_decomposition',
                   fromlist=['variants']).variants())
    assert all(task['limits'] == dict(native_calls=1,
                                      packet_visits=432000000,
                                      bound_calls=0, bound_steps=0)
               for task in work)
    assert construction_limits() == dict(constructed_intervals=360000,
                                         generated_samples=362002,
                                         noise_normal_variates=6480012)
    assert design['original_reads'] == design['protected_reads'] == 0


def test_component_study_requires_qualifications_before_writing(tmp_path):
    from lll.noise_component_study import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path)
    assert not (tmp_path / 'data').exists()


def _context(tmp_path):
    from lll.noise_component_study import SCOPE, recipe, tasks
    from lll.ilvis0_control_shards import prepare, TaskContext
    from lll.airquantumgrav_inventory import environment

    project = tmp_path / 'project'
    project.mkdir()
    (project / 'adapter.py').write_text('# lifecycle fixture\n')
    (project / 'recipe.json').write_text(json.dumps(recipe()))
    (project / 'environment.json').write_text(json.dumps(environment()))
    (project / 'proof.json').write_text(json.dumps(dict(
        selected_binding=dict(hashes={}),
        parent_recipe=dict(limits={})) ))
    study = tmp_path / 'study'
    task = tasks()[0]
    prepare(study, project_root=project, tasks=[task],
            sources=['adapter.py'],
            inputs={'recipe': 'recipe.json', 'parent-proof': 'proof.json',
                    'qualification-environment': 'environment.json'},
            adapter='adapter.py', workers=1, threads=1,
            maximum_wall_s=30, environment={'generated': True},
            accounting_format='sqlite-v1', scope=SCOPE)
    context = TaskContext(study, 0, task['identity'])
    return context.task, context


def test_component_study_rejects_changed_task_before_construction(tmp_path):
    from lll.noise_component_study import evaluate

    task, context = _context(tmp_path)
    changed = dict(task, payload=dict(task['payload'], variant='full'))
    with pytest.raises(ValueError, match='unchanged'):
        evaluate(changed, context)
    assert not context.directory.exists()


def test_component_study_preserves_prepayment_if_construction_stops(
        tmp_path, monkeypatch):
    from lll import noise_component_study
    from lll.ilvis0_control_shards import _counts

    task, context = _context(tmp_path)
    monkeypatch.setattr(noise_component_study, 'kernel', lambda context: None)

    def fail(*args, **kwargs):
        assert _counts(context.journal, context.task)['native_calls'] == 1
        raise RuntimeError('controlled construction stop')

    monkeypatch.setattr(noise_component_study, 'build_material', fail)
    with pytest.raises(RuntimeError, match='controlled construction stop'):
        noise_component_study.evaluate(task, context)
    saved = json.loads((context.directory / 'native-prepayment.json').read_bytes())
    assert saved['state'] == 'failed_or_interrupted'
    assert saved['attempted']['native_calls'] == 0
    context.finish(dict(passed=False, reason='preserved control',
                        scientific_decision='abstain'))


def test_component_study_executes_through_frozen_adapter(tmp_path, monkeypatch):
    import importlib.util
    import sys
    from pathlib import Path

    import numpy as np
    from lll import noisy_realization_attribution
    from lll.noise_component_study import construction_limits

    path = Path(__file__).resolve().parents[1] / 'lll/noise_component_study.py'
    spec = importlib.util.spec_from_file_location(
        '_component_study_frozen_fixture', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        task, context = _context(tmp_path)
        monkeypatch.setattr(module, 'kernel', lambda context: None)

        def material(proof, *, reserve):
            limits = construction_limits()
            reserve(constructed_intervals=limits['constructed_intervals'],
                    generated_samples=limits['generated_samples'] - 1201,
                    noise_normal_variates=limits['noise_normal_variates'])
            clean = dict(theta=np.zeros((2, 3)), dv=np.zeros((2, 3)),
                         dt=np.array([.5, .5]),
                         times=.5 + np.arange(1200, dtype=float))
            components = dict(white_increments=np.zeros((2, 3)),
                              bias_increments=np.zeros((2, 3)))
            noisy = dict(theta=clean['theta'].copy(), dv=clean['dv'].copy(),
                         dt=clean['dt'].copy(),
                         noise=dict(gyro=components, accel=components))
            return clean, noisy

        def forecast(measured, known, *, reserve, **kwargs):
            reserve(native_calls=1, packet_visits=432000000)
            return np.zeros((1200, 3))

        monkeypatch.setattr(module, 'build_material', material)
        monkeypatch.setattr(noisy_realization_attribution,
                            'oracle_value_forecast', forecast)
        result = module.evaluate(task, context)
        assert result['passed'] and result['variant'] == 'clean'
        assert result['native_calls_attempted'] == 1
        saved = json.loads((context.directory /
                            'native-prepayment.json').read_bytes())
        assert saved['state'] == 'complete'
        assert saved['attempted']['packet_visits'] == 432000000
        context.finish(result)
    finally:
        sys.modules.pop(spec.name, None)
