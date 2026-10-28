# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import math
import pytest


def fixture():
    active=['time_offset']+['p'+str(i) for i in range(26)]
    branches=[dict(side=side,spacing_s=h,feasible=True,analytic=[1.,2.],difference=[1.,2.],
        jacobian=[[1.]+[0.]*26,[2.]+[0.]*26],error_norm=0.,comparison_scale=1e-8+1e-6*math.sqrt(5.))
        for h in (1e-5,1e-6,1e-7) for side in (-1,1)]
    record=dict(identity='case',saved_converged=False,fit=dict(active_parameters=active,residual_sum_squares=3.),
                artifact_sha256={'fit.json':'a'*64})
    d=dict(active_parameters=active,columns=27,source_fit_sha256='a'*64,original_saved_converged=False,
        input_replay_exact=True,baseline=dict(cost=3.),repeatability=dict(exact=True),
        full_correction_replayed=True,evaluations=24,labels_changed=False,nonlinear_fit_starts=0,
        stopping_probe=dict(passed=None,not_executed=True),branches=branches,
        corrections=[dict(kind=k,actual_cost_delta=1.,predicted_cost_delta=-1.,residual_remainder_norm=.1)
                     for k in ('full','time_only','other_only')])
    return record,d


def test_boundary_report_keeps_failed_labels_separate_from_derivative_agreement():
    from lll.timing_boundary_report import summarize
    record,d=fixture();row,curves=summarize(record,d)
    assert row['original_fit_converged'] is False and row['timing_derivatives_agree'] is True
    assert len(curves)==6 and row['evaluations']==24
    assert 'converged' not in row and row['labels_changed'] is False


@pytest.mark.parametrize('change',['source','columns','label','scale'])
def test_boundary_report_rejects_changed_scope_or_forged_derivative_metrics(change):
    from lll.timing_boundary_report import summarize
    record,d=fixture();d=copy.deepcopy(d)
    if change=='source':d['source_fit_sha256']='b'*64
    elif change=='columns':d['columns']=26
    elif change=='label':d['original_saved_converged']=True
    else:d['branches'][0]['comparison_scale']=1.
    with pytest.raises(ValueError):summarize(record,d)


def test_boundary_native_bindings_use_the_diagnostic_environment_key(monkeypatch):
    from types import SimpleNamespace
    from lll.timing_boundary_report import kernel_bindings
    from lll import compensated_prediction_release
    environment={'compiler':'fixture'}
    study=SimpleNamespace(manifest={'sources':{}},read=lambda *a,**kw:b'bound',
        input=lambda key:{'environment':environment}[key])
    def native_bindings(view):
        assert view.input('qualification-environment') is environment
        assert view.manifest is study.manifest
        assert view.read('source',raw=True)==b'bound'
        return {'source':'verified'}
    monkeypatch.setattr(compensated_prediction_release,'native_bindings',native_bindings)
    assert kernel_bindings(study)=={'source':'verified'}
