"""A GPS-only turn estimate is trained before its future path is scored."""

import math

import numpy as np
import pytest


def test_known_circular_motion_uses_only_earlier_velocity():
    from lll.receiver_only_constant_turn import forecast_constant_turn
    from lll.receiver_only_forecast import RADIUS_M

    radius = RADIUS_M + 1000.0
    speed = 100.0
    turn = 0.01
    training_times = np.arange(-59.0, 1.0)
    course = turn * training_times
    training_velocity = np.column_stack((speed*np.cos(course),
                                         speed*np.sin(course),
                                         np.zeros(len(course))))
    future_times = np.arange(1.0, 121.0)
    result = forecast_constant_turn(training_times, training_velocity,
                                    [0.0, 0.0, 1000.0], future_times)
    assert result['course_rate_rads'] == pytest.approx(turn, abs=1e-13)
    assert result['training_velocity_reports_used'] == 60
    assert result['imu_samples_used'] == 0
    assert result['later_positions_used'] is False
    for elapsed in (30, 60, 120):
        index = elapsed-1
        north_m = speed*math.sin(turn*elapsed)/turn
        east_m = speed*(1-math.cos(turn*elapsed))/turn
        predicted = result['coordinates'][index]
        assert predicted[0]*radius == pytest.approx(north_m, abs=10)
        assert predicted[1]*radius == pytest.approx(east_m, abs=10)
        assert predicted[2] == pytest.approx(1000)


def test_course_wrap_and_invalid_training_support():
    from lll.receiver_only_constant_turn import forecast_constant_turn

    times = np.arange(60.0)
    course = np.deg2rad(179.0 + 0.1*times)
    velocities = np.column_stack((100*np.cos(course),
                                  100*np.sin(course), np.zeros(60)))
    output = forecast_constant_turn(times, velocities,
                                    [0.0, 0.0, 100.0], [60.0])
    assert output['course_rate_rads'] == pytest.approx(math.radians(0.1))
    with pytest.raises(ValueError, match='60 earlier'):
        forecast_constant_turn(times[:-1], velocities[:-1],
                               [0.0, 0.0, 100.0], [60.0])
    with pytest.raises(ValueError, match='later times'):
        forecast_constant_turn(times, velocities,
                               [0.0, 0.0, 100.0], [59.0])
