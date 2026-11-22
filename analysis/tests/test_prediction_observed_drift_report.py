"""A saved-only prediction diagnostic must report actual error growth."""
import math

import pytest


def test_linear_later_error_has_correct_slope_and_rms():
    from lll.prediction_observed_drift_report import summarize_drift

    errors = [[0., 0., 0.] for _ in range(4)]
    errors += [[2., 10., 0.], [4., 10., 0.],
               [6., 10., 0.], [8., 10., 0.]]
    result = summarize_drift(errors, list(range(8)), 4)
    assert result['prediction_epochs'] == 4
    assert result['axes']['north']['later_rms_m'] == pytest.approx(math.sqrt(30.))
    assert result['axes']['north']['later_slope_m_per_min'] == pytest.approx(120.)
    assert result['axes']['north']['later_linear_explained_fraction'] == pytest.approx(1.)
    assert result['axes']['east']['later_slope_m_per_min'] == pytest.approx(0.)
    assert result['axes']['east']['later_linear_explained_fraction'] is None


def test_nonmonotone_times_are_rejected():
    from lll.prediction_observed_drift_report import summarize_drift

    with pytest.raises(ValueError, match='increasing'):
        summarize_drift([[0., 0., 0.]] * 8,
                        [0., 1., 2., 3., 4., 5., 5., 7.], 4)


def test_training_tail_trend_is_estimated_without_later_errors():
    from lll.prediction_observed_drift_report import summarize_drift

    errors = [[float(t), 0., 0.] for t in range(8)]
    result = summarize_drift(errors, list(range(8)), 4)
    north = result['axes']['north']
    assert north['training_tail_epochs'] == 4
    assert north['training_tail_slope_m_per_min'] == pytest.approx(60.)
    assert north['training_tail_extrapolated_first_m'] == pytest.approx(4.)
    assert north['training_tail_extrapolated_last_m'] == pytest.approx(7.)


def test_receiver_motion_summary_uses_same_split_and_tail():
    from lll.prediction_observed_drift_report import summarize_motion

    rows = [dict(time_s=float(t), north_mps=10. if t < 4 else 20.,
                 east_mps=0., up_mps=1. if t < 4 else 2.)
            for t in range(8)]
    result = summarize_motion(rows, 4)
    assert result['training_tail_epochs'] == 4
    assert result['training_tail_mean_speed_mps'] == pytest.approx(10.)
    assert result['later_mean_speed_mps'] == pytest.approx(20.)
    assert result['later_mean_up_mps'] == pytest.approx(2.)


def test_training_handoff_detects_a_changed_native_difference():
    from lll.prediction_observed_drift_report import training_handoff_discrepancy_m

    receiver = [[0., 0., 100.]]
    forecast = [[0.000001, 0., 100.]]
    assert training_handoff_discrepancy_m(
        forecast, receiver, [[0.000001, 0., 0.]]) < 1e-8
    assert 6. < training_handoff_discrepancy_m(
        forecast, receiver, [[0., 0., 0.]]) < 7.


def test_receiver_reference_uses_only_earlier_positions():
    from lll.prediction_observed_drift_report import receiver_reference

    radius = 6378137.
    times = list(range(45))
    positions = [[10.*t/radius, 0., 100.] for t in times]
    exact = receiver_reference(times, positions, 40)
    changed = [row[:] for row in positions]
    for row in changed[40:]:
        row[0] += 0.0001
    shifted = receiver_reference(times, changed, 40)
    assert exact['linear']['horizontal_rms_m'] < 0.1
    assert exact['geodesic']['horizontal_rms_m'] < 0.1
    assert shifted['linear']['horizontal_rms_m'] > 600.
    assert shifted['geodesic']['horizontal_rms_m'] > 600.
    expected_velocity = 10.*(radius+100.)/radius
    assert exact['linear']['north_east_up_velocity_mps'][0] == pytest.approx(expected_velocity)
    assert shifted['linear']['north_east_up_velocity_mps'][0] == pytest.approx(expected_velocity)


def test_generated_reference_keeps_training_and_later_errors_separate():
    from lll.prediction_observed_drift_report import compare_generated_reference

    rows = [dict(converged=True,
                 training=dict(horizontal_rms_m=2., accuracy=dict(passed=True)),
                 prediction=dict(horizontal_rms_m=80., accuracy=dict(passed=False)))
            for _ in range(23)]
    rows.append(dict(converged=True,
                     training=dict(horizontal_rms_m=4., accuracy=dict(passed=True)),
                     prediction=dict(horizontal_rms_m=90., accuracy=dict(passed=False))))
    result = compare_generated_reference(rows, observed_training_m=40.,
                                         observed_later_m=249.)
    assert result['training_horizontal_rms_m']['maximum'] == pytest.approx(4.)
    assert result['later_horizontal_rms_m']['maximum'] == pytest.approx(90.)
    assert result['training_accuracy_passed'] == 24
    assert result['later_accuracy_passed'] == 0
    assert result['observed_training_exceeds_generated_max'] is True
    assert result['observed_later_exceeds_generated_max'] is True
