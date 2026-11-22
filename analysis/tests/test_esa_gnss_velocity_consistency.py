"""GNSS position derivatives use the ellipsoid metric and actual time tags."""

import math

import numpy as np
import pytest


def test_wgs84_position_derivative_matches_known_eastward_motion():
    from lll.esa_gnss_velocity_consistency import diagnose

    t = np.array([0.0, 0.8, 2.1, 3.5, 5.0])
    latitude = np.full(len(t), 64.0)
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    phi = math.radians(64.0)
    east_scale = (a / math.sqrt(1 - e2 * math.sin(phi)**2) + 1000.0) * math.cos(phi)
    longitude = np.degrees(80.0 * t / east_scale)
    height = np.full(len(t), 1000.0)
    reported = np.tile([0.0, 80.0, 0.0], (len(t), 1))
    result = diagnose(t, latitude, longitude, height, reported)
    assert result['interior_epochs'] == 3
    assert max(result['rms_difference_mps']) < 1e-6
    assert result['first_and_last_derivative_epochs_excluded'] is True

    with pytest.raises(ValueError, match='increasing'):
        diagnose([0, 1, 1, 3, 4], latitude, longitude, height, reported)


def test_sealed_fit_gate_uses_boolean_passed_receipt():
    from lll.esa_gnss_velocity_consistency import sealed_fit_ready

    completion = {'state': 'complete'}
    summary = {'completed': 2, 'total': 2, 'passed': True}
    assert sealed_fit_ready(completion, summary)
    assert not sealed_fit_ready(completion, dict(summary, passed=False))
