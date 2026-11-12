"""The 24-case technical study preserves finite charges and source binding."""
import pytest


def test_standalone_frozen_adapter_has_no_relative_imports():
    import ast
    import importlib.util
    from pathlib import Path
    path = Path(__file__).parents[1]/'lll/bounded_nonlinear_study.py'
    tree = ast.parse(path.read_text())
    assert not [node for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.level]
    spec = importlib.util.spec_from_file_location('_frozen_bounded_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert len(module.tasks()) == 24


def _context(tmp_path):
    import json
    from lll.bounded_nonlinear_study import recipe, tasks, SCOPE
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import prepare, TaskContext
    project = tmp_path/'project'
    project.mkdir()
    (project/'adapter.py').write_text('# bounded nonlinear fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    (project/'environment.json').write_text(json.dumps(environment()))
    output = tmp_path/'study'
    task = tasks()[0]
    prepare(output, project_root=project, tasks=[task],
            sources=['adapter.py'],
            inputs={'recipe':'recipe.json',
                    'numerical_environment':'environment.json'},
            adapter='adapter.py', workers=1, threads=1,
            maximum_wall_s=30, environment={'generated':True},
            accounting_format='sqlite-v1', scope=SCOPE)
    context = TaskContext(output, 0, task['identity'])
    return context.manifest['tasks'][0], context


def test_bounded_nonlinear_matrix_has_24_cases_and_finite_limits():
    from lll.bounded_nonlinear_study import (recipe, tasks, limits,
                                             construction_limits)
    r = recipe()
    work = tasks(r)
    assert len(work) == len({task['identity'] for task in work}) == 24
    assert {task['payload']['model'] for task in work} == {
        'sphere_rotating', 'sphere_still', 'flat_still'}
    assert {task['payload']['profile'] for task in work} == {False, True}
    assert {task['payload']['law'] for task in work} == {'increment', 'point'}
    assert {task['payload']['sensor_case'] for task in work} == {
        'interior', 'z_gyro_boundary'}
    assert r['duration_s'] == 120. and r['maximum_evaluations'] == 200
    assert r['workers'] == 4 and r['threads'] == 1
    assert r['noise_by_law']['increment']['seed'] == 271828
    assert limits(r) == dict(native_calls=239816,
                             packet_visits=1506051012,
                             bound_calls=0, bound_steps=0)
    assert construction_limits(r, 'increment') == dict(
        constructed_intervals=36000, generated_samples=36199,
        noise_normal_variates=649206)
    assert construction_limits(r, 'point') == dict(
        constructed_intervals=36000, generated_samples=36199,
        noise_normal_variates=433212)


def test_bounded_study_requires_source_and_recovery_qualification(tmp_path):
    from lll.bounded_nonlinear_study import prepare
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None, recovery_qualification=None)
    assert not (tmp_path/'data').exists()


def test_bounded_worker_prepays_and_preserves_abstention(tmp_path, monkeypatch):
    import json
    from lll import bounded_nonlinear_study as study
    from lll.ilvis0_control_shards import _counts
    task, context = _context(tmp_path)
    expected = study.construction_limits(study.recipe(), 'increment')

    def fake(task, context, r, reserve_native, reserve_construction, check):
        assert _counts(context.journal, context.task)['native_calls'] == task['limits']['native_calls']
        reserve_native(native_calls=1, packet_visits=1)
        reserve_construction(**expected)
        return dict(native_calls=1, passed=False,
                    bounded=dict(scientific_decision='abstain',
                                 both_bounds_saved_before_later_truth=True))

    monkeypatch.setattr(study, 'run_generated_case', fake)
    result = study.run_case(task, context, r=study.recipe())
    assert result['passed'] and result['bounded']['scientific_decision'] == 'abstain'
    assert result['physical_prediction_passed'] is False
    snapshot = json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['prepaid']['native_calls'] == task['limits']['native_calls']
    assert snapshot['attempted'] == dict(native_calls=1, packet_visits=1)
    context.finish(result)


def test_bounded_worker_preserves_charged_failure(tmp_path, monkeypatch):
    import json
    from lll import bounded_nonlinear_study as study
    task, context = _context(tmp_path)

    def fails(task, context, r, reserve_native, reserve_construction, check):
        reserve_native(native_calls=1, packet_visits=1)
        raise RuntimeError('preserved bounded failure')

    monkeypatch.setattr(study, 'run_generated_case', fails)
    with pytest.raises(RuntimeError, match='preserved bounded failure'):
        study.run_case(task, context, r=study.recipe())
    snapshot = json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['attempted'] == dict(native_calls=1, packet_visits=1)
    assert snapshot['state'] == 'failed_or_interrupted'
    assert (context.directory/'construction.sqlite').exists()
    context.finish(dict(passed=False, scientific_decision='abstain'))


def test_bounded_evaluate_rejects_changed_case_before_charging(tmp_path):
    from lll.bounded_nonlinear_study import evaluate
    task, context = _context(tmp_path)
    changed = dict(task, payload=dict(task['payload'], law='other'))
    with pytest.raises(ValueError, match='unchanged qualified'):
        evaluate(changed, context)
    assert not context.directory.exists()
