"""Saved-only bounded-aircraft totals keep technical and coverage claims apart."""
import pytest


def _row():
    bounded = dict(marginal_covered=[2, 1, 2], marginal_total=6,
                   median_width_by_axis=[.001, .002, 100.],
                   nonlinear_coverage_established=False)
    fixed = dict(marginal_covered=[1, 1, 1], marginal_total=6,
                 confidence_calibrated=False)
    result = dict(passed=True, scientific_decision='abstain',
                  bounded_technical_integration_passed=True,
                  physical_prediction_passed=True,
                  prediction=dict(accuracy=dict(passed=True)),
                  bounded=dict(physical_position=bounded,
                               receiver_measurement=bounded,
                               both_bounds_saved_before_later_truth=True,
                               scientific_decision='abstain'),
                  dual_target=dict(physical_position=fixed,
                                   receiver_measurement=fixed))
    return dict(identity='example', passed=True,
                scientific_decision='abstain', result=result,
                fit=dict(converged=True, stopping_rule_verified=True,
                         active_bounds=['gyro_bias_z']))


def test_aggregate_separates_passes_bounds_and_uncalibrated_counts():
    from lll.bounded_nonlinear_report import aggregate
    total = aggregate([_row()])
    assert total['completed'] == total['technical_passes'] == 1
    assert total['numerically_passing'] == total['physical_passing'] == 1
    assert total['prediction_accuracy_passing'] == 1
    assert total['active_bound_cases'] == 1
    assert total['marginal_counts']['physical_position'] == dict(
        bounded_covered=5, fixed_covered=3, total=6)
    assert total['median_case_width_by_axis']['physical_position'] == [
        .001, .002, 100.]
    assert total['nonlinear_coverage_established'] is False
    assert total['scientific_decision'] == 'abstain'


def test_aggregate_preserves_a_terminal_technical_failure():
    from lll.bounded_nonlinear_report import aggregate
    failed = dict(identity='error', passed=False,
                  scientific_decision='abstain', error_type='RuntimeError',
                  result=dict(passed=False))
    total = aggregate([_row(), failed])
    assert total['completed'] == 2 and total['technical_passes'] == 1
    assert total['errors'] == {'RuntimeError': 1}


def test_aggregate_rejects_a_calibrated_claim():
    from lll.bounded_nonlinear_report import aggregate
    row = _row()
    row['result']['dual_target']['physical_position']['confidence_calibrated'] = True
    with pytest.raises(ValueError, match='uncalibrated'):
        aggregate([row])


def test_render_reports_width_alongside_coverage():
    from lll.bounded_nonlinear_report import aggregate, render
    report = dict(verified=True, scientific_decision='abstain',
                  total=aggregate([_row()]))
    page = render(report)
    assert '5/6 generated coordinates' in page
    assert 'Median case interval width' in page
    assert 'height 100 m' in page
    assert 'not a' in page and 'calibrated 95%' in page


def test_render_preserves_all_failed_release_without_width_claim():
    from lll.bounded_nonlinear_report import aggregate, render
    failed = dict(identity='error', passed=False,
                  scientific_decision='abstain', error_type='ImportError',
                  result=dict(passed=False))
    page = render(dict(verified=True, scientific_decision='abstain',
                       total=aggregate([failed])))
    assert 'ImportError: 1' in page
    assert 'Median case interval width' not in page


def test_accuracy_is_separate_from_numerical_qualification():
    from lll.bounded_nonlinear_report import aggregate, render
    row = _row()
    row['fit']['converged'] = False
    row['fit']['stopping_rule_verified'] = False
    row['result']['physical_prediction_passed'] = False
    total = aggregate([row])
    assert total['prediction_accuracy_passing'] == 1
    assert total['numerically_passing'] == 0
    assert total['physical_passing'] == 0
    page = render(dict(verified=True, scientific_decision='abstain',
                       total=total, rows=[row]))
    assert 'example' in page and 'numerical stopping check' in page
