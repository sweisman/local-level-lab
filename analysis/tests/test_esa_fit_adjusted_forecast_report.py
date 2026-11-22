"""Independent coordinate scoring for saved generated future forecasts."""

import numpy as np
import pytest


def test_position_errors_neu_zero_and_vertical_metre():
    from lll.esa_fit_adjusted_forecast_report import position_errors_neu

    truth = np.array([[0., 0., 100.], [.6, -.4, 1200.]])
    assert position_errors_neu(truth, truth) == pytest.approx(np.zeros((2, 3)))
    predicted = truth.copy()
    predicted[:, 2] += 1.
    error = position_errors_neu(predicted, truth)
    assert error[:, 0] == pytest.approx([0., 0.], abs=1e-8)
    assert error[:, 1] == pytest.approx([0., 0.], abs=1e-8)
    assert error[:, 2] == pytest.approx([1., 1.], abs=1e-8)


def test_position_errors_neu_rejects_changed_shape():
    from lll.esa_fit_adjusted_forecast_report import position_errors_neu

    with pytest.raises(ValueError, match='aligned'):
        position_errors_neu([[0., 0., 0.]], [[0., 0., 0.], [0., 0., 0.]])


def test_position_errors_neu_recovers_small_north_and_east_offsets():
    from lll.airquantumgrav_truth import A, E2
    from lll.esa_fit_adjusted_forecast_report import position_errors_neu

    truth = np.array([[0., 0., 0.]])
    predicted = truth.copy()
    predicted[0, 0] = 1/(A*(1-E2))
    predicted[0, 1] = 1/A
    result = position_errors_neu(predicted, truth)[0]
    assert result[0] == pytest.approx(1., abs=1e-6)
    assert result[1] == pytest.approx(1., abs=1e-6)
    assert result[2] == pytest.approx(0., abs=1e-6)


def test_direct_sensor_calibration_distance_uses_declared_limits():
    from lll.esa_fit_adjusted_forecast_report import calibration_truth_distance

    names = [f'gyro_bias_{axis}' for axis in 'xyz'] + [
        f'accel_bias_{axis}' for axis in 'xyz'] + [
        f'gyro_gain_{axis}' for axis in 'xyz'] + [
        f'accel_gain_{axis}' for axis in 'xyz'] + ['time_offset']
    fit = dict(active_parameters=names,
               normalized_parameters=[-.5]+[0.]*12)
    truth = {name:0. for name in names}
    truth[names[0]] = .25
    limits = {name:1. for name in names}
    result = calibration_truth_distance(fit, truth, limits)
    assert result['maximum_absolute_difference_normalized'] == pytest.approx(.75)
    assert result['parameters'][names[0]]['truth_normalized'] == pytest.approx(.25)
