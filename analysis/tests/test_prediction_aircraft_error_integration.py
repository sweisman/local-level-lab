# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite matrix and freeze guards for the generated aircraft bridge."""
import pytest


def _context(tmp_path):
    import json
    from lll.prediction_aircraft_error_integration import recipe, tasks, SCOPE
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import prepare, TaskContext
    project = tmp_path/'project'
    project.mkdir()
    (project/'adapter.py').write_text('# finite integration fixture\n')
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


def test_integration_matrix_has_48_finite_distinct_tasks():
    from lll.prediction_aircraft_error_integration import recipe, tasks
    r = recipe()
    work = tasks(r)
    assert len(work) == len({task['identity'] for task in work}) == 48
    assert {task['payload']['model'] for task in work} == {
        'sphere_rotating', 'sphere_still', 'flat_still'}
    assert {task['payload']['profile'] for task in work} == {False, True}
    assert {task['payload']['sensor_case'] for task in work} == {
        'interior', 'z_gyro_boundary'}
    assert {task['payload']['clock_case'] for task in work} == {
        'nominal_200Hz', 'header_jitter'}
    assert {task['payload']['law'] for task in work} == {'increment', 'point'}
    assert r['rate_hz'] == 200 and r['duration_s'] == 2.
    assert r['workers'] == 4 and r['threads'] == 1
    assert r['maximum_evaluations'] == 8
    assert all(task['limits'] == dict(native_calls=2000, packet_visits=20000,
                                      bound_calls=0, bound_steps=0)
               for task in work)


def test_fresh_integration_study_requires_source_and_recovery_qualification(tmp_path):
    from lll.prediction_aircraft_error_integration import prepare
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None, recovery_qualification=None)
    assert not (tmp_path/'data').exists()


@pytest.mark.parametrize('law,expected', [('increment', 7308), ('point', 4914)])
def test_construction_limits_include_full_later_receiver_draw(law, expected):
    from lll.prediction_aircraft_error_integration import construction_limits, recipe
    assert construction_limits(recipe(), law) == dict(
        constructed_intervals=400, generated_samples=416,
        noise_normal_variates=expected)


def test_worker_prepays_work_and_preserves_scientific_abstention(tmp_path,
                                                                  monkeypatch):
    from lll import structured_noisy_study, airquantumgrav_dual_target_prediction
    from lll.prediction_aircraft_error_integration import run_case, recipe
    from lll.ilvis0_control_shards import _counts
    import json

    task, context = _context(tmp_path)
    monkeypatch.setattr(structured_noisy_study, '_kernels',
                        lambda *args: (lambda *args: None,
                                       lambda anchor: (None, None, {})))

    def fake_calculate(spec, configured, **kwargs):
        assert _counts(context.journal, context.task)['native_calls'] == 2000
        kwargs['reserve'](native_calls=1, packet_visits=1)
        kwargs['reserve_construction'](generated_samples=9,
                                         noise_normal_variates=60)
        return dict(native_calls=1, passed=False, converged=False,
                    scientific_decision='abstain',
                    dual_target=dict(scientific_decision='abstain',
                                     forecast_and_diagnostics_saved_before_later_truth=True,
                                     training_receiver_prefix_exact=True))

    monkeypatch.setattr(airquantumgrav_dual_target_prediction, 'calculate',
                        fake_calculate)
    result = run_case(task, context, r=recipe())
    assert result['passed'] is True
    assert result['generated_technical_integration_passed'] is True
    assert result['physical_prediction_passed'] is False
    assert result['converged'] is False
    assert result['scientific_decision'] == 'abstain'
    snapshot = json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['prepaid']['native_calls'] == 2000
    assert snapshot['attempted'] == dict(native_calls=1, packet_visits=1)
    context.finish(result)


def test_worker_keeps_charges_and_failure_artifacts(tmp_path, monkeypatch):
    from lll import structured_noisy_study, airquantumgrav_dual_target_prediction
    from lll.prediction_aircraft_error_integration import run_case, recipe
    import json

    task, context = _context(tmp_path)
    monkeypatch.setattr(structured_noisy_study, '_kernels',
                        lambda *args: (lambda *args: None,
                                       lambda anchor: (None, None, {})))

    def fails(spec, configured, **kwargs):
        kwargs['reserve'](native_calls=1, packet_visits=1)
        raise RuntimeError('preserved technical failure')

    monkeypatch.setattr(airquantumgrav_dual_target_prediction, 'calculate', fails)
    with pytest.raises(RuntimeError, match='preserved technical failure'):
        run_case(task, context, r=recipe())
    snapshot = json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['state'] == 'failed_or_interrupted'
    assert snapshot['attempted'] == dict(native_calls=1, packet_visits=1)
    assert (context.directory/'construction.sqlite').exists()
    context.finish(dict(passed=False, scientific_decision='abstain',
                        reason='preserved technical failure'))


def test_evaluate_rejects_changed_frozen_case_before_charging(tmp_path):
    from lll.prediction_aircraft_error_integration import evaluate
    task, context = _context(tmp_path)
    changed = dict(task, payload=dict(task['payload'], law='other'))
    with pytest.raises(ValueError, match='unchanged qualified'):
        evaluate(changed, context)
    assert not context.directory.exists()
