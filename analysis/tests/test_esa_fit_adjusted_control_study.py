"""The long known-answer control freezes two matched recordings."""

from types import SimpleNamespace

import pytest
from test_native_structured_training import training_kernels


def _context(tmp_path):
    import json
    from lll.esa_fit_adjusted_control_study import recipe, tasks, SCOPE
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import prepare as prepare_runtime, TaskContext

    project = tmp_path/'project'
    project.mkdir()
    (project/'adapter.py').write_text('# known-answer fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    (project/'environment.json').write_text(json.dumps(environment()))
    output = tmp_path/'study'
    task = tasks()[0]
    prepare_runtime(output, project_root=project, tasks=[task],
        sources=['adapter.py'], inputs=dict(recipe='recipe.json',
        numerical_environment='environment.json'), adapter='adapter.py',
        workers=1, threads=1, maximum_wall_s=30,
        environment={'generated':True}, accounting_format='sqlite-v1', scope=SCOPE)
    context = TaskContext(output, 0, task['identity'])
    return context.manifest['tasks'][0], context


def test_two_known_answer_cases_have_exact_600_report_training_support():
    from lll.esa_fit_adjusted_control_study import recipe, tasks, case_recipe

    r = recipe()
    work = tasks(r)
    assert (r['duration_s'], r['rate_hz'], r['queries']) == (900., 300, 900)
    assert (r['query_start_s'], r['query_step_s']) == (.5, 1.)
    assert r['maximum_evaluations'] == 200
    assert (r['workers'], r['threads'], r['maximum_wall_s']) == (2, 1, 7200.)
    assert [task['identity'] for task in work] == ['increment', 'point']
    assert [task['payload']['noise_seed'] for task in work] == [
        20261115001, 20261115002]
    assert all(task['payload']['model'] == 'sphere_rotating'
               and task['payload']['profile'] is False for task in work)
    assert all(task['limits'] == dict(native_calls=1_400_000,
        packet_visits=90_000_000_000, bound_calls=0, bound_steps=0)
        for task in work)
    assert case_recipe(r, work[0])['noise_by_law']['increment']['seed'] == \
        case_recipe(r, work[0])['noise_by_law']['point']['seed'] == 20261115001
    assert case_recipe(r, work[1])['noise_by_law']['increment']['seed'] == \
        case_recipe(r, work[1])['noise_by_law']['point']['seed'] == 20261115002


def test_known_answer_study_requires_qualification_before_staging(tmp_path):
    from lll.esa_fit_adjusted_control_study import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path)
    assert not (tmp_path/'data').exists()


def test_known_answer_study_rejects_changed_task_before_input_read():
    from lll.esa_fit_adjusted_control_study import SCOPE, tasks, evaluate

    task = dict(tasks()[0], index=0, shard=0)
    task['payload'] = dict(task['payload'], noise_seed=5)
    context = SimpleNamespace(manifest=dict(scope=SCOPE))
    with pytest.raises(ValueError, match='unchanged known-answer task'):
        evaluate(task, context)


def test_known_answer_worker_prepays_and_reuses_one_measured_stream(
        tmp_path, monkeypatch):
    import json
    from lll import esa_fit_adjusted_control_study as study
    from lll.ilvis0_control_shards import _counts

    task, context = _context(tmp_path)

    def fake(task, context, r, reserve_native, reserve_construction):
        assert _counts(context.journal, context.task)['native_calls'] == \
            task['limits']['native_calls']
        reserve_native(native_calls=1, packet_visits=1)
        reserve_construction(**study.construction_limits(r, 'increment'))
        return dict(passed=True, native_calls=1, scientific_decision='abstain',
                    same_measured_input_for_both_laws=True)

    monkeypatch.setattr(study, 'run_generated_case', fake)
    result = study.run_case(task, context,
                            r=study.case_recipe(study.recipe(), task))
    assert result['same_measured_input_for_both_laws'] is True
    snapshot = json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['attempted'] == dict(native_calls=1, packet_visits=1)
    context.finish(result)


def test_known_answer_worker_preserves_charged_failure(tmp_path, monkeypatch):
    import json
    from lll import esa_fit_adjusted_control_study as study

    task, context = _context(tmp_path)

    def fails(task, context, r, reserve_native, reserve_construction):
        reserve_native(native_calls=1, packet_visits=1)
        raise RuntimeError('preserved control failure')

    monkeypatch.setattr(study, 'run_generated_case', fails)
    with pytest.raises(RuntimeError, match='preserved control failure'):
        study.run_case(task, context,
                       r=study.case_recipe(study.recipe(), task))
    snapshot = json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['attempted'] == dict(native_calls=1, packet_visits=1)
    assert snapshot['state'] == 'failed_or_interrupted'
    context.finish(dict(passed=False, scientific_decision='abstain'))


def test_short_known_answer_pair_uses_identical_measured_inputs(
        training_kernels, monkeypatch):
    from lll import (esa_fit_adjusted_control_study as study,
                     structured_noisy_study, ilvis0_control_shards)
    from lll.ilvis0_wide_tangent import load

    fixture = training_kernels
    saved = {}
    calls = []

    def kernels(anchor):
        tangent, metadata = load(fixture['directory'],
            gravity_anchor_height_m=anchor,
            expected_source_sha256=fixture['hashes'][
                'analysis/lll/ilvis0_tangent.cpp'])
        return fixture['kernel'], tangent, dict(tangent=metadata)

    monkeypatch.setattr(structured_noisy_study, '_kernels',
                        lambda *args: (fixture['kernel'], kernels))
    monkeypatch.setattr(ilvis0_control_shards, '_check_continue',
                        lambda *args: None)
    context = SimpleNamespace(root=fixture['directory'],
        manifest=dict(sources=fixture['hashes']),
        save=lambda name, value: saved.setdefault(name, value),
        save_bytes=lambda name, value: saved.setdefault(name, value))
    task = study.preflight_task()
    result = study.run_generated_case(task, context,
        study.case_recipe(study.preflight_recipe(), task),
        lambda **work: calls.append(work), lambda **work: None)
    assert result['training_epochs'] == 6
    assert result['same_measured_input_for_both_laws'] is True
    assert 'increment/fit.json' in saved and 'point/fit.json' in saved
    assert saved['matched-fit-summary.json']['increment'][
        'input_binding_sha256'] == saved['matched-fit-summary.json']['point'][
        'input_binding_sha256']
    assert result['native_calls'] == sum(row['native_calls'] for row in calls)
