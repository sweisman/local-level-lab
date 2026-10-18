# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def trial():
    import ilvis0_prediction_trial
    return ilvis0_prediction_trial


def test_exact_six_primary_case_identities():
    w=trial()
    assert len(w.identities())==len(set(w.identities()))==6
    assert w.scope()['cases']==w.clock.base.primary_cases()
    assert w.scope()['initialization']=='training_receiver_and_training_imu_only'


def test_prediction_start_charges_cannot_retry_or_change_scope(tmp_path):
    w=trial(); p=tmp_path/'starts.jsonl'
    w.charge(p,w.identities()[0],'freeze')
    with pytest.raises(ValueError): w.charge(p,w.identities()[0],'freeze')
    with pytest.raises(ValueError): w.charge(p,'outside','freeze')
    with pytest.raises(ValueError): w.journal(p,'other')


def test_completed_trial_cannot_load_native_kernel(tmp_path,monkeypatch):
    w=trial(); (tmp_path/'completion.json').write_text('{}')
    def forbidden(*args,**kwargs): raise AssertionError('completed work must not start')
    monkeypatch.setattr(w.clock.base.explore,'load_kernel',forbidden)
    with pytest.raises(ValueError,match='completed'): w.run(tmp_path)


def test_prepare_cannot_fit_or_spawn(monkeypatch):
    w=trial(); calls=[]
    monkeypatch.setattr(w.sys,'argv',['trial','--prepare-only'])
    monkeypatch.setattr(w,'prepare',lambda output:calls.append(output))
    def forbidden(*args,**kwargs): raise AssertionError('prepare cannot start work')
    monkeypatch.setattr(w,'run',forbidden); monkeypatch.setattr(w.subprocess,'Popen',forbidden)
    w.main(); assert calls==[w.OUTPUT]


def test_prediction_profile_uses_prediction_cost_and_preserves_fit_status():
    w=trial(); rows=[dict(case_id='one',fits=[dict(model='flat_still',converged=False,
        residual_sum_squares=1.,prediction_diagnostics={'prediction':{'primary_conditional_cost':99.}})])]
    def inspect(cases):
        fit=cases[0]['fits'][0]
        assert fit['residual_sum_squares']==99.
        assert not fit['converged']
        return {'checked':True}
    assert w.prediction_profile(rows,inspect)=={'checked':True}
    assert rows[0]['fits'][0]['residual_sum_squares']==1.
