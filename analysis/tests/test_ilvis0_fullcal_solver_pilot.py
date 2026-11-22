"""Four-task full-calibration generated solver pilot definition."""

from pathlib import Path

import pytest

from lll import ilvis0_fullcal_solver_pilot as pilot


def test_four_tasks_share_one_generated_truth_and_have_finite_work():
    recipe=pilot.recipe()
    tasks=pilot.tasks(recipe)
    assert len(tasks)==4
    assert len({row['identity'] for row in tasks})==4
    assert {row['payload']['solver'] for row in tasks}=={'near_zero','trust_v2'}
    assert {row['payload']['start'] for row in tasks}=={0,1}
    assert all(row['payload']['model']=='sphere_rotating' for row in tasks)
    assert all(row['payload']['law']=='increment' for row in tasks)
    assert all(row['limits']==tasks[0]['limits'] for row in tasks)
    assert tasks[0]['limits']['native_calls']>0
    assert recipe['duration_s']==60.
    assert recipe['queries']==59


def test_short_preflight_is_separate_and_cannot_spend_full_task_allowance():
    short=pilot.preflight_recipe()
    task=pilot.tasks(short)
    assert short['duration_s']==10.
    assert short['queries']==9
    assert short['maximum_evaluations']==8
    assert len(task)==1
    assert task[0]['limits']['native_calls']<pilot.tasks()[0]['limits']['native_calls']


def test_prepare_rejects_unguarded_numerical_environment(tmp_path,monkeypatch):
    from lll import airquantumgrav_inventory as inventory
    actual=inventory.environment
    def unguarded():
        value=actual()
        value['numerical_environment']={key:None
            for key in value['numerical_environment']}
        return value
    monkeypatch.setattr(inventory,'environment',unguarded)
    with pytest.raises(ValueError,match='guarded numerical environment'):
        pilot.prepare(tmp_path,qualification='unused',preflight=True)


def test_source_freeze_includes_native_noise_and_recovery():
    names=pilot.sources(Path('.'))
    assert 'analysis/lll/ilvis0_tangent.cpp' in names
    assert 'analysis/lll/ilvis0_noise_bridge.cpp' in names
    assert 'analysis/tests/test_ilvis0_fullcal_solver_pilot.py' in names
    assert 'test_reboot_resume_skips_sealed_and_preserves_charges' in pilot.required_tests()


def test_evaluator_rejects_changed_task_before_shared_worker(monkeypatch):
    from types import SimpleNamespace
    task=pilot.tasks()[0].copy()
    task['payload']=dict(task['payload'],start=3)
    context=SimpleNamespace(manifest=dict(scope=pilot.SCOPE))
    with pytest.raises(ValueError,match='unchanged finite generated task'):
        pilot.evaluate(task,context)


def test_worker_keeps_failed_physical_screen_separate_from_technical_completion(
        tmp_path,monkeypatch):
    from types import SimpleNamespace
    from lll.airquantumgrav_inventory import environment
    from lll.studies.artifacts import encoded
    from lll import structured_noisy_study
    recipe=tmp_path/'recipe';recipe.write_bytes(encoded(pilot.recipe()))
    env=tmp_path/'environment';env.write_bytes(encoded(environment()))
    def fake_run(task,context,*,r,payload,training_provider):
        assert task['payload']['solver']=='near_zero'
        assert 'solver' not in payload
        assert callable(training_provider)
        return dict(passed=False,forecast_saved_before_scoring=True,
                    training_epochs=39,prediction_epochs=20,
                    original_reads=0,protected_reads=0)
    monkeypatch.setattr(structured_noisy_study,'run_case',fake_run)
    context=SimpleNamespace(manifest=dict(scope=pilot.SCOPE),
        input_path=lambda key:{'recipe':recipe,'environment':env}[key])
    result=pilot.evaluate(pilot.tasks()[0],context)
    assert result['passed'] and result['technical_completion_only']
    assert result['physical_accuracy_passed'] is False
    assert result['scientific_decision']=='abstain'
