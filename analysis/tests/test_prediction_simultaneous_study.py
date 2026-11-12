# SPDX-License-Identifier: AGPL-3.0-or-later
"""The independent-seed study freezes a finite mixture before outcomes."""
from lll.prediction_simultaneous_study import recipe, tasks
from test_native_structured_training import training_kernels


def _context(tmp_path):
    import json
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import prepare, TaskContext
    from lll.prediction_simultaneous_study import SCOPE
    project = tmp_path/'project'
    project.mkdir(parents=True)
    (project/'adapter.py').write_text('# generated whole-period fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    (project/'environment.json').write_text(json.dumps(environment()))
    output = tmp_path/'study'
    task = tasks()[0]
    prepare(output, project_root=project, tasks=[task], sources=['adapter.py'],
            inputs={'recipe':'recipe.json',
                    'numerical_environment':'environment.json'},
            adapter='adapter.py', workers=1, threads=1,
            maximum_wall_s=30, environment={'generated': True},
            accounting_format='sqlite-v1', scope=SCOPE)
    context = TaskContext(output, 0, task['identity'])
    return context.manifest['tasks'][0], context


def test_ninety_six_unique_noise_streams_and_finite_whole_period_policy():
    r = recipe()
    work = tasks(r)
    assert len(work) == 96
    assert len({task['identity'] for task in work}) == 96
    assert len({task['payload']['noise_seed'] for task in work}) == 96
    assert {task['payload']['model'] for task in work} == {
        'sphere_rotating', 'sphere_still', 'flat_still'}
    assert r['calibration_alpha'] == .0125
    assert r['simultaneous_alpha'] == .025
    assert r['workers'] == 4 and r['threads'] == 1
    assert r['maximum_evaluations'] == 200
    assert all(task['limits']['native_calls'] == 479632 for task in work)
    assert tasks(r) == work


def test_study_requires_source_and_recovery_qualification(tmp_path):
    import pytest
    from lll.prediction_simultaneous_study import prepare
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None, recovery_qualification=None)
    assert not (tmp_path/'data').exists()


def test_changed_frozen_case_is_rejected_before_charging(tmp_path):
    import pytest
    from lll.prediction_simultaneous_study import evaluate
    task, context = _context(tmp_path)
    changed = dict(task, payload=dict(task['payload'], noise_seed=17))
    with pytest.raises(ValueError, match='unchanged qualified'):
        evaluate(changed, context)
    assert not context.directory.exists()


def test_worker_prepays_and_keeps_failed_starts(tmp_path, monkeypatch):
    import json
    import pytest
    from lll import prediction_simultaneous_study as study
    from lll.ilvis0_control_shards import _counts
    task, context = _context(tmp_path)
    expected = study.construction_limits(study.case_recipe(study.recipe(), task),
                                         task['payload']['truth_law'])

    def fake(task, context, r, reserve_native, reserve_construction):
        assert _counts(context.journal, context.task)['native_calls'] == \
            task['limits']['native_calls']
        reserve_native(native_calls=1, packet_visits=1)
        reserve_construction(**expected)
        return dict(passed=True, native_calls=1,
                    scientific_decision='abstain')

    monkeypatch.setattr(study, 'run_generated_case', fake)
    result = study.run_case(task, context, r=study.case_recipe(study.recipe(), task))
    assert result['passed']
    snapshot = json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['prepaid']['native_calls'] == task['limits']['native_calls']
    context.finish(result)

    another, fresh = _context(tmp_path/'other')
    def fails(task, context, r, reserve_native, reserve_construction):
        reserve_native(native_calls=1, packet_visits=1)
        raise RuntimeError('preserved generated failure')
    monkeypatch.setattr(study, 'run_generated_case', fails)
    with pytest.raises(RuntimeError, match='preserved generated failure'):
        study.run_case(another, fresh, r=study.case_recipe(study.recipe(), another))
    failed = json.loads((fresh.directory/'native-prepayment.json').read_bytes())
    assert failed['state'] == 'failed_or_interrupted'


def test_short_generated_case_saves_two_target_scores_after_truth(
        training_kernels, monkeypatch):
    from types import SimpleNamespace
    from lll import structured_noisy_study, ilvis0_control_shards
    from lll.ilvis0_wide_tangent import load
    from lll.prediction_simultaneous_study import case_recipe, run_generated_case
    saved = {}
    charged = []

    def kernel_factory(anchor):
        tangent, metadata = load(
            training_kernels['directory'], gravity_anchor_height_m=anchor,
            expected_source_sha256=training_kernels['hashes'][
                'analysis/lll/ilvis0_tangent.cpp'])
        return None, tangent, dict(tangent=metadata)

    monkeypatch.setattr(structured_noisy_study, '_kernels',
                        lambda *args: (training_kernels['kernel'], kernel_factory))
    monkeypatch.setattr(ilvis0_control_shards, '_check_continue',
                        lambda *args: None)

    def save(name, value):
        assert name not in saved
        saved[name] = value

    context = SimpleNamespace(root=training_kernels['directory'], manifest={},
                              save=save, save_bytes=save)
    r = dict(recipe(), duration_s=2., rate_hz=200, queries=9,
             query_start_s=.1, query_step_s=.2, maximum_evaluations=8)
    task = tasks()[0]
    r = case_recipe(r, task)
    result = run_generated_case(task, context, r,
                                lambda **work: charged.append(work),
                                lambda **work: None)
    assert result['passed'] and result['scientific_decision'] == 'abstain'
    assert result['native_calls'] == sum(row['native_calls'] for row in charged)
    assert {'union-scores.json', 'later-receiver-report.json',
            'withheld-physical-truth.json'} <= saved.keys()
    assert set(result['union_scores']) == {
        'physical_position', 'receiver_measurement'}
