"""Finite dual-target study controls; no native builds or observed data."""

import json

import pytest


def test_dual_target_tasks_have_exact_four_operator_passes():
    from lll.generated_esa_dual_target_pilot import recipe, preflight_recipe, tasks
    from lll.structured_noisy_training import limits
    full, short = recipe(), preflight_recipe()
    assert [full['noise_by_law'][k]['seed'] for k in ('increment','point')] == [650101,650102]
    assert short['noise_by_law']['increment']['seed'] == 650000
    assert full['workers']*full['threads'] == 2
    assert len(tasks(full)) == 2 and len(tasks(short)) == 1
    for r in (full,short):
        for task in tasks(r):
            base = limits(r,task['payload']['law'])[0]
            addition = 3*(round(r['duration_s']*r['rate_hz'])+r['queries'])
            assert task['limits']['native_calls'] == base['native_calls']+addition
            assert task['limits']['packet_visits'] == base['packet_visits']+addition
            assert task['limits']['bound_calls'] == base['bound_calls']


def test_changed_task_rejected_before_work():
    from lll.generated_esa_dual_target_pilot import evaluate, tasks, recipe, SCOPE
    class Context:
        manifest={'scope':SCOPE}
    task=tasks(recipe())[0]
    with pytest.raises(ValueError,match='unchanged finite'):
        evaluate(dict(task,payload=dict(task['payload'],start=1)),Context())


def test_training_provider_uses_same_factory_for_both_targets(monkeypatch):
    from lll import generated_esa_dual_target_pilot as study
    from lll.ilvis0_native_error_training import ForecastErrorDiagnostic, ErrorTrainingFactory
    seen={}
    def fake_train(**kwargs):
        seen.update(kwargs)
        return {'ok':True}
    monkeypatch.setattr('lll.airquantumgrav_prediction.train_and_forecast',fake_train)
    def fake_dual(a,b,*args,**kwargs):
        seen['targets']=(a,b)
        return {'prediction_target':'physical_position'}
    monkeypatch.setattr('lll.dual_target_forecast_wrapper.evaluate',fake_dual)
    factory=ErrorTrainingFactory.__new__(ErrorTrainingFactory)
    physical=ForecastErrorDiagnostic.__new__(ForecastErrorDiagnostic)
    physical.factory=factory
    physical.target='physical_position'
    physical.policy='last-training-transform-v1'
    physical.bound_margin=1e-6
    physical.rank_rtol=1e-10
    physical.estimability_rtol=1e-8
    physical.estimability_atol=1e-10
    result=study.dual_training(forecast_error_diagnostic=physical,save=lambda *a:None)
    assert result=={'ok':True}
    assert callable(seen['forecast_error_diagnostic'])
    seen['forecast_error_diagnostic'](None,None,None,theta=None,dv=None,dt=None,
                                      times=None,reserve=lambda **work:None)
    assert seen['targets'][0] is physical
    assert seen['targets'][1].factory is factory
    assert seen['targets'][1].target == 'receiver_measurement'


def test_artifact_gate_requires_both_targets(tmp_path,monkeypatch):
    from lll import generated_esa_dual_target_pilot as study
    task=study.tasks(study.preflight_recipe())[0]
    class Context:
        manifest={'scope':study.PREFLIGHT_SCOPE}
        root=tmp_path
        artifacts={}
        def input_path(self,name):
            path=tmp_path/name
            path.write_text(json.dumps(study.preflight_recipe() if name=='recipe' else
                                       __import__('lll.airquantumgrav_inventory',fromlist=['environment']).environment()))
            return path
    monkeypatch.setattr(study,'_run_case',lambda *a:{'passed':False})
    with pytest.raises(ValueError,match='both target'):
        study.evaluate(task,Context())
