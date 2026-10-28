# SPDX-License-Identifier: AGPL-3.0-or-later
from types import SimpleNamespace
import pytest


@pytest.mark.parametrize('custom',[False,True])
def test_campaign_training_provider_is_explicit_and_default_stays_unchanged(monkeypatch,tmp_path,custom):
    from lll import prediction_calibration_study as campaign,structured_noisy_study as shared
    from lll import independent_noisy_study as scoring,prediction_family_state as families
    seen=[];saved={};provider=lambda:None;task={'payload':{'draw_seed':123,'case':{'unchanged':True}}}
    context=SimpleNamespace(directory=tmp_path,save=lambda name,value:saved.update({name:value}))
    policy=SimpleNamespace(case_recipe=lambda seed:{'original_seed':seed})
    monkeypatch.setattr(campaign,'_context',lambda *a,**kw:({'role':'calibration'},{'sha256':'a'*64},None))
    def run(t,c,**kw):
        assert t is task and c is context
        assert kw['r']=={'original_seed':123} and kw['payload']=={'unchanged':True}
        assert ('training_provider' in kw) is custom
        if custom:assert kw['training_provider'] is provider
        seen.append(True);return {'passed':False}
    monkeypatch.setattr(shared,'run_case',run)
    monkeypatch.setattr(scoring,'score_saved_case',lambda *a,**kw:{'maximum_standardized_error':2.})
    monkeypatch.setattr(families,'record',lambda *a,**kw:None)
    monkeypatch.setattr(families,'check',lambda *a,**kw:None)
    options={'training_provider':provider} if custom else {}
    result=campaign.evaluate(task,context,protocol=policy,**options)
    assert seen==[True] and result['passed'] is False and result['maximum_standardized_error']==2.
    assert saved['draw-identity.json']['calibration_draw'] is True


def test_invalid_campaign_provider_rejected_before_context_or_charges(monkeypatch):
    from lll import prediction_calibration_study as campaign
    def forbidden(*a,**kw):raise AssertionError('context reached before provider validation')
    monkeypatch.setattr(campaign,'_context',forbidden)
    with pytest.raises(ValueError,match='provider'):campaign.evaluate({},object(),training_provider=42)


def test_default_closed_report_needs_no_additional_method_callback():
    from lll.prediction_calibration_report import method_verification
    assert method_verification(SimpleNamespace(),object(),'identity',{'profile':False},{'converged':True})=={}


@pytest.mark.parametrize('converged',[False,True])
def test_closed_report_audits_explicit_method_without_relabeling(converged):
    from lll.prediction_calibration_report import method_verification
    study=object();spec={'profile':False};seen=[]
    def audit(s,i,p):
        assert s is study and i=='identity' and p is spec;seen.append(True)
        return dict(passed=converged,columns=26,linear_solves=2)
    result=method_verification(SimpleNamespace(audit_fit=audit),study,'identity',spec,{'converged':converged})
    assert seen==[True] and result=={'method_verification':dict(passed=converged,columns=26,linear_solves=2)}


@pytest.mark.parametrize('evidence',[{'passed':False},{'passed':1},None])
def test_closed_report_rejects_inconsistent_or_missing_method_proof(evidence):
    from lll.prediction_calibration_report import method_verification
    policy=SimpleNamespace(audit_fit=lambda *a:evidence)
    with pytest.raises(ValueError,match='method'):method_verification(policy,object(),'identity',{}, {'converged':True})


@pytest.mark.parametrize('validation_failure',[False,True])
def test_campaign_case_context_validates_before_scoring_and_preserves_failure(monkeypatch,tmp_path,validation_failure):
    from contextlib import contextmanager
    from lll import prediction_calibration_study as campaign,structured_noisy_study as shared
    from lll import independent_noisy_study as scoring,prediction_family_state as families
    events=[];provider=lambda:None;task={'payload':{'draw_seed':123,'case':{}}}
    context=SimpleNamespace(directory=tmp_path,save=lambda *a:None)
    policy=SimpleNamespace(case_recipe=lambda seed:{})
    def checked(*a,**kw):events.append('source_checked');return {'role':'calibration'},{'sha256':'a'*64},None
    monkeypatch.setattr(campaign,'_context',checked)
    @contextmanager
    def scope(t,c):
        assert t is task and c is context;events.append('enter')
        try:
            yield {'training_provider':provider};events.append('verify')
            if validation_failure:raise ValueError('controlled accounting failure')
        finally:events.append('journal_preserved')
    def run(*a,**kw):
        assert kw['training_provider'] is provider;events.append('run');return {'passed':False}
    monkeypatch.setattr(shared,'run_case',run)
    def score(*a,**kw):events.append('score');return {'maximum_standardized_error':2.}
    monkeypatch.setattr(scoring,'score_saved_case',score)
    monkeypatch.setattr(families,'record',lambda *a,**kw:events.append('record'))
    monkeypatch.setattr(families,'check',lambda *a,**kw:events.append('failure_rule'))
    if validation_failure:
        with pytest.raises(ValueError,match='accounting'):campaign.evaluate(task,context,protocol=policy,case_context=scope)
        assert 'score' not in events
    else:
        assert campaign.evaluate(task,context,protocol=policy,case_context=scope)['passed'] is False
        assert events.index('verify')<events.index('score')
    assert events[:3]==['source_checked','enter','run'] and events[-2:]==['record','failure_rule']
    assert events.index('journal_preserved')<events.index('record')
