# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.mark.parametrize('custom',[False,True])
def test_shared_case_explicit_training_provider_preserves_default_and_budget(tmp_path,monkeypatch,custom):
    from test_structured_noisy_study import context
    from lll import structured_noisy_study as worker,structured_noisy_training as training
    task,ctx=context(tmp_path);provider=lambda **kw:None;seen=[]
    def calculate(payload,r,**kw):
        assert ('training_provider' in kw) is custom
        if custom:assert kw['training_provider'] is provider
        kw['reserve_construction'](**training.limits(r,payload['law'])[1])
        kw['reserve'](native_calls=1,packet_visits=1);seen.append(1)
        return dict(native_calls=1,passed=False,scientific_decision='abstain')
    monkeypatch.setattr(training,'calculate',calculate)
    options=dict(training_provider=provider) if custom else {}
    result=worker.run_case(task,ctx,r=training.recipe(),payload=task['payload'],
        kernel_provider=lambda *a:(None,None),**options)
    assert seen==[1] and result['passed'] is False
    ctx.finish(result)


@pytest.mark.parametrize('custom',[False,True])
def test_training_protocol_provider_keeps_truth_guard_and_original_default(monkeypatch,custom):
    from lll import structured_noisy_training as training,airquantumgrav_noisy_inputs as inputs
    from lll import airquantumgrav_training_controls as controls,airquantumgrav_observation_truth as truth
    from lll import ilvis0_native_error_training as errors,generated_prediction as generated
    from lll.airquantumgrav_prediction import train_and_forecast
    chosen=lambda **kw:None
    monkeypatch.setattr(inputs,'construct',lambda *a,**k:dict(training_rows=[{'height_m':10.}],dt=[.005],times=[.1,.2]))
    monkeypatch.setattr(inputs,'error_law',lambda *a:None)
    monkeypatch.setattr(errors,'ErrorTrainingFactory',lambda **k:object())
    monkeypatch.setattr(errors,'ForecastErrorDiagnostic',lambda *a,**k:object())
    monkeypatch.setattr(controls,'_spec',lambda *a:({},1))
    checked=[]
    monkeypatch.setattr(truth,'receiver_samples',lambda **kw:checked.append('truth'))
    def calculate(*a,**kw):
        assert kw['train_and_forecast'] is (chosen if custom else train_and_forecast)
        with pytest.raises(ValueError,match='both forecasts'):kw['truth']([.2])
        kw['save']('forecast.json',{});kw['save']('forecast-error-diagnostic.json',{})
        kw['truth']([.2]);kw['reserve'](native_calls=1,packet_visits=1)
        return dict(native_calls=1)
    monkeypatch.setattr(generated,'calculate',calculate)
    r=training.recipe();spec=training.tasks(r)[0]['payload']
    options=dict(training_provider=chosen) if custom else {}
    result=training.calculate(spec,r,kernel_factory=None,noise_kernel=None,reserve=lambda **k:None,
        reserve_construction=lambda **k:None,save=lambda *a:None,check_continue=lambda:None,**options)
    assert checked==['truth'] and result['native_calls']==1


@pytest.mark.parametrize('stopping',['ordinary','near_zero'])
@pytest.mark.parametrize('custom',[False,True])
def test_counted_training_solver_provider_preserves_full_native_charge(monkeypatch,stopping,custom):
    import numpy as np
    from lll import ilvis0_training_forecast as training,ilvis0_shape as shape
    from lll import ilvis0_solver_trust_v2 as ordinary,ilvis0_near_zero as near
    charges=[];selected=[]
    class Problem:
        dt=[.005,.005];gps_times=[.1,.2]
        def residual_tangent(self,u,model):
            assert charges==[dict(native_calls=1,packet_visits=4)]
            return np.array([1.]),np.array([[0.]]),0
    monkeypatch.setattr(shape,'TangentProblem',Problem)
    def provider(which):
        def fit(p,m,**kw):
            selected.append(which);p.residual_tangent([0.],m)
            return dict(evaluations=1,converged=False)
        return fit
    monkeypatch.setattr(ordinary,'fit_candidate',provider('ordinary'))
    monkeypatch.setattr(near,'fit_candidate',provider('near_zero'))
    options=dict(solver_provider=provider('custom')) if custom else {}
    result=training.fit_training(Problem(),'control',start=[0.],maximum_evaluations=200,
        reserve=lambda **kw:charges.append(kw),stopping=stopping,**options)
    assert selected==['custom' if custom else stopping]
    assert result['converged'] is False and not result['prediction_receiver_positions_used_in_training']
