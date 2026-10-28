# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def records():
    p=[[.5,.2,1000.],[.50001,.20001,1001.],[.50002,.20002,1002.]]
    return {s:dict(fit=dict(converged=True,residual_sum_squares=200.,active_parameters=['x']*26),
        forecast=dict(coordinates=copy.deepcopy(p),training_epochs=2),
        training=dict(coordinates=p[:2]),binding={'same':'observations'}) for s in (0,1)}


def test_optimizer_report_accepts_same_predictions_without_parameter_agreement():
    from lll.coordinate_optimizer_report import compare_starts
    r=records();r[0]['fit']['normalized_parameters']=[-.5]*26;r[1]['fit']['normalized_parameters']=[.5]*26
    result=compare_starts(r)
    assert result['passed'] and result['relative_cost_difference']==0.


def test_optimizer_report_preserves_failed_or_missing_start_pairs():
    from lll.coordinate_optimizer_report import compare_starts
    r=records();r[1]['fit']['converged']=False
    assert compare_starts(r)['passed'] is False
    assert compare_starts({0:r[0]})['passed'] is False


@pytest.mark.parametrize('change',['cost','track','binding'])
def test_optimizer_report_rejects_disagreement(change):
    from lll.coordinate_optimizer_report import compare_starts
    r=records()
    if change=='cost':r[1]['fit']['residual_sum_squares']+=.01
    elif change=='track':r[1]['forecast']['coordinates'][0][2]+=.1
    else:
        r[1]['binding']={}
        with pytest.raises(ValueError):compare_starts(r)
        return
    assert compare_starts(r)['passed'] is False


@pytest.mark.parametrize('converged,accurate',[(True,True),(False,True),(True,False)])
def test_optimizer_case_audit_loads_full_shared_bundle_and_combines_status(monkeypatch,converged,accurate):
    from lll.coordinate_optimizer_report import audit_case
    from lll.structured_noisy_publication import CASE_ARTIFACTS
    from lll import structured_noisy_report
    class Saved:
        def artifact(self,identity,name):
            assert identity=='case';return {'name':name}
    result={'passed':converged and accurate};seen=[]
    def checking(spec,outcome,saved,*,r):
        assert set(saved)==set(CASE_ARTIFACTS)
        assert {'training-receiver.json','forecast-binding.json'}<=set(saved)
        assert outcome is result;seen.append(True)
        return dict(converged=converged,accurate=accurate)
    monkeypatch.setattr(structured_noisy_report,'check_case',checking)
    saved,checked=audit_case(Saved(),'case',spec={},result=result,r={})
    assert seen==[True] and checked['passed']==result['passed']
    assert len(saved)==len(CASE_ARTIFACTS)
