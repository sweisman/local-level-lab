"""The bounded law-family release retains exact cases, charges and failures."""
import pytest
from test_native_structured_training import training_kernels


def _context(tmp_path):
    import json
    from lll.prediction_paired_bound_study import recipe, tasks, SCOPE
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import prepare, TaskContext
    project = tmp_path/'project'
    project.mkdir()
    (project/'adapter.py').write_text('# bound-family fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    (project/'environment.json').write_text(json.dumps(environment()))
    output = tmp_path/'study'
    task = tasks()[0]
    prepare(output, project_root=project, tasks=[task], sources=['adapter.py'],
            inputs={'recipe':'recipe.json',
                    'numerical_environment':'environment.json'},
            adapter='adapter.py', workers=1, threads=1,
            maximum_wall_s=30, environment={'generated':True},
            accounting_format='sqlite-v1', scope=SCOPE)
    context = TaskContext(output, 0, task['identity'])
    return context.manifest['tasks'][0], context


def test_bound_family_matrix_has_twenty_four_distinct_cases():
    from lll.prediction_paired_bound_study import recipe, tasks, limits
    r = recipe()
    work = tasks(r)
    assert len(work) == len({task['identity'] for task in work}) == 24
    assert {task['payload']['model'] for task in work} == {
        'sphere_rotating', 'sphere_still', 'flat_still'}
    assert {task['payload']['profile'] for task in work} == {False, True}
    assert {task['payload']['truth_law'] for task in work} == {
        'increment', 'point'}
    assert {task['payload']['sensor_case'] for task in work} == {
        'interior', 'z_gyro_boundary'}
    assert all(task['limits'] == limits(r) for task in work)
    assert limits(r)['native_calls'] == 479632
    assert r['workers'] == 4 and r['threads'] == 1


def test_bound_family_study_requires_source_and_recovery_qualification(tmp_path):
    from lll.prediction_paired_bound_study import prepare
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None, recovery_qualification=None)
    assert not (tmp_path/'data').exists()


def test_bound_family_worker_prepays_and_preserves_abstention(tmp_path, monkeypatch):
    import json
    from lll import prediction_paired_bound_study as study
    from lll.ilvis0_control_shards import _counts
    task, context = _context(tmp_path)
    expected = study.construction_limits(study.recipe(), 'increment')

    def fake(task, context, r, reserve_native, reserve_construction):
        assert _counts(context.journal, context.task)['native_calls'] == task['limits']['native_calls']
        reserve_native(native_calls=1, packet_visits=1)
        reserve_construction(**expected)
        return dict(passed=True, native_calls=1,
                    scientific_decision='abstain', numerical_passing_fits=0)

    monkeypatch.setattr(study, 'run_generated_case', fake)
    result = study.run_case(task, context, r=study.recipe())
    assert result['passed'] and result['scientific_decision'] == 'abstain'
    snapshot = json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['prepaid']['native_calls'] == task['limits']['native_calls']
    assert snapshot['attempted'] == dict(native_calls=1, packet_visits=1)
    context.finish(result)


def test_bound_family_worker_preserves_charged_failure(tmp_path, monkeypatch):
    import json
    from lll import prediction_paired_bound_study as study
    task, context = _context(tmp_path)

    def fails(task, context, r, reserve_native, reserve_construction):
        reserve_native(native_calls=1, packet_visits=1)
        raise RuntimeError('preserved bound-family failure')

    monkeypatch.setattr(study, 'run_generated_case', fails)
    with pytest.raises(RuntimeError, match='preserved bound-family failure'):
        study.run_case(task, context, r=study.recipe())
    snapshot = json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['attempted'] == dict(native_calls=1, packet_visits=1)
    assert snapshot['state'] == 'failed_or_interrupted'
    context.finish(dict(passed=False, scientific_decision='abstain'))


def test_bound_family_evaluate_rejects_changed_frozen_case(tmp_path):
    from lll.prediction_paired_bound_study import evaluate
    task, context = _context(tmp_path)
    changed = dict(task, payload=dict(task['payload'], truth_law='other'))
    with pytest.raises(ValueError, match='unchanged qualified'):
        evaluate(changed, context)
    assert not context.directory.exists()


def test_short_bound_family_case_saves_scores_after_truth(
        training_kernels, monkeypatch):
    from types import SimpleNamespace
    from lll import structured_noisy_study, ilvis0_control_shards
    from lll.ilvis0_wide_tangent import load
    from lll.prediction_paired_bound_study import recipe, run_generated_case
    kernels = training_kernels
    saved = {}
    charges = []

    def kernel_factory(anchor):
        tangent, metadata = load(
            kernels['directory'], gravity_anchor_height_m=anchor,
            expected_source_sha256=kernels['hashes']['analysis/lll/ilvis0_tangent.cpp'])
        return None, tangent, dict(tangent=metadata)

    monkeypatch.setattr(structured_noisy_study, '_kernels',
                        lambda *args: (kernels['kernel'], kernel_factory))
    monkeypatch.setattr(ilvis0_control_shards, '_check_continue',
                        lambda *args: None)

    def save(name, value):
        assert name not in saved
        saved[name] = value

    context = SimpleNamespace(root=kernels['directory'], manifest={},
                              save=save, save_bytes=save)
    r = dict(recipe(), duration_s=2., rate_hz=200, queries=9,
             query_start_s=.1, query_step_s=.2, maximum_evaluations=8)
    task = dict(payload=dict(model='sphere_rotating', latitude_deg=55.,
                             profile=False, start=0,
                             policy_id='reported-short-v1',
                             truth_law='increment', sensor_case='interior'))
    result = run_generated_case(task, context, r,
                                lambda **work: charges.append(work),
                                lambda **work: None)
    assert result['passed'] and result['scientific_decision'] == 'abstain'
    assert result['native_calls'] == sum(row['native_calls'] for row in charges)
    assert {'union-scores.json', 'later-receiver-report.json',
            'withheld-physical-truth.json'} <= saved.keys()
    assert set(result['union_scores']) == {
        'physical_position', 'receiver_measurement'}
