"""A last earlier GNSS velocity can form a receiver-only forecast."""

import math

import numpy as np
import pytest


def test_constant_reported_velocity_follows_known_spherical_path():
    from lll.receiver_only_velocity import forecast_velocity
    from lll.receiver_only_forecast import RADIUS_M

    future = np.array([11.0, 12.0])
    result = forecast_velocity(10.0, [0.0, 0.0, 1000.0],
                               [0.0, 100.0, 2.0], future)
    assert np.allclose(result['coordinates'][:, 0], 0.0, atol=1e-13)
    assert np.allclose(result['coordinates'][:, 1],
                       [100/(RADIUS_M+1000), 200/(RADIUS_M+1000)], atol=1e-13)
    assert np.allclose(result['coordinates'][:, 2], [1002.0, 1004.0])
    assert result['imu_samples_used'] == 0
    assert result['later_positions_used'] is False
    with pytest.raises(ValueError):
        forecast_velocity(10.0, [0.0, 0.0, 1000.0], [0.0, 100.0, 0.0], [9.0])
