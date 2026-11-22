from lll.ilvis0_matched_four_group_audit import disposition, error_summary


def test_four_group_audit_keeps_open_unsealed_and_failed_fit_outcomes_distinct():
    assert disposition(None, open_study=True) == 'pending'
    assert disposition(None) == 'unsealed'
    assert disposition({'passed': False, 'error_type': 'BudgetStopped'}) == 'budget_stopped'
    assert disposition({'passed': False, 'converged': False}) == 'numerical_nonpass'
    assert disposition({'passed': True, 'converged': False}) == 'numerical_nonpass'
    assert disposition({'passed': True, 'converged': True, 'forecast_saved_before_scoring': True}) == 'scorable'


def test_four_group_audit_checks_peak_height_even_with_passing_height_rms():
    errors = [[0., 0., 0.] for _ in range(29)] + [[0., 0., -151.]]
    summary = error_summary(list(range(30)), errors)
    assert summary['accuracy']['checks']['vertical_rms_m']
    assert not summary['accuracy']['checks']['maximum_absolute_up_m']
    assert not summary['accuracy']['passed']
    assert summary['mean_neu_m'][2] == -151/30
