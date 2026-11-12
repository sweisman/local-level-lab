"""Training-only constant-velocity receiver baseline controls."""

import numpy as np
import pytest

from lll.receiver_only_forecast import forecast


def test_linear_track_is_predicted_without_future_positions():
    radius = 6378137.0
    latitude = 0.5
    times = np.arange(120.0)
    future = np.arange(120.0, 131.0)
    coordinates = np.column_stack((
        latitude + 220.0 * times / radius,
        -0.7 + 40.0 * times / (radius * np.cos(latitude)),
        10000.0 + 0.2 * times,
    ))
    actual = np.column_stack((
        latitude + 220.0 * future / radius,
        -0.7 + 40.0 * future / (radius * np.cos(latitude)),
        10000.0 + 0.2 * future,
    ))
    result = forecast(times, coordinates, future)
    assert result["training_window_points"] == 61
    assert result["later_positions_used"] is False
    assert result["imu_samples_used"] == 0
    np.testing.assert_allclose(result["coordinates"], actual, rtol=0, atol=1e-8)


def test_longitude_wrap_does_not_create_a_false_turn():
    times = np.arange(100.0)
    future = np.array([100.0, 101.0])
    longitudes = (np.pi - 0.001 + 0.00002 * times + np.pi) % (2 * np.pi) - np.pi
    coordinates = np.column_stack((np.zeros(len(times)), longitudes, np.ones(len(times))))
    result = forecast(times, coordinates, future)
    expected = (np.pi - 0.001 + 0.00002 * future + np.pi) % (2 * np.pi) - np.pi
    np.testing.assert_allclose(result["coordinates"][:, 1], expected, rtol=0, atol=1e-10)


def test_short_or_nonforward_training_is_rejected():
    with pytest.raises(ValueError, match="30"):
        forecast(np.arange(20.0), np.zeros((20, 3)), np.array([21.0]))
    with pytest.raises(ValueError, match="increasing"):
        forecast(np.arange(40.0), np.zeros((40, 3)), np.array([39.0]))
