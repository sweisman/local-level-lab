"""Saved-only stopping diagnosis keeps every numerical failure."""

from lll.ilvis0_remaining_stopping_audit import classify, summarize


def _fit(*, passed, reason, evaluations=20, at_bound=2):
    fit=dict(converged=passed, evaluations=evaluations,
                maximum_evaluations=200, active_bounds=['x']*at_bound,
                exact_projected_gradient_relative=(0.0002 if reason=='not_stationary'
                                                   else 0.00002),
                stationarity_tolerance=0.0001,
                stability_probe=dict(passed=passed, reason=reason))
    if reason=='fresh_position_probe_not_stable':
        fit['stability_policy']={'relative_cost_tolerance':1e-8}
        fit['stability_probe'].update(actual_cost_change=2e-8,
            fresh_stationarity=2e-5,position_rms_neu_m=[0,0,0],
            position_max_abs_neu_m=[0,0,0],
            position_rms_tolerance_m=.001,position_max_tolerance_m=.01)
    return fit


def test_stationarity_failure_is_not_renamed_a_pass():
    row=classify(_fit(passed=False, reason='not_stationary'))
    assert row['passed'] is False
    assert row['probe_reason']=='not_stationary'
    assert row['stationarity_passed'] is False
    assert row['allowance_exhausted'] is False


def test_summary_preserves_failed_and_passing_starts():
    fits=[_fit(passed=True, reason='fresh_position_stability_verified'),
          _fit(passed=False, reason='not_stationary', evaluations=83),
          _fit(passed=False, reason='fresh_position_probe_not_stable')]
    report=summarize(fits)
    assert report['starts']==3
    assert report['passing']==1
    assert report['nonpassing']==2
    assert report['reasons']=={'fresh_position_stability_verified':1,
                               'not_stationary':1,
                               'fresh_position_probe_not_stable':1}
    assert report['allowance_exhausted']==0
    assert report['maximum_evaluations_used']==83


def test_fresh_probe_failure_components_are_counted_separately():
    fit=_fit(passed=False, reason='fresh_position_probe_not_stable')
    fit['stability_policy']={'relative_cost_tolerance':1e-8}
    fit['stability_probe'].update(actual_cost_change=2e-8,
        fresh_stationarity=2e-4,position_rms_neu_m=[.002,0,0],
        position_max_abs_neu_m=[0,.02,0],
        position_rms_tolerance_m=.001,position_max_tolerance_m=.01)
    del fit['stability_policy']
    row=classify(fit)
    assert row['failed_components']==['cost','fresh_stationarity',
                                      'position_rms','position_maximum']
    assert summarize([fit])['failed_component_counts']=={
        'cost':1,'fresh_stationarity':1,'position_rms':1,
        'position_maximum':1}
