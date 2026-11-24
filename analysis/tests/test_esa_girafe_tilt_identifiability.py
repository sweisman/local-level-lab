import math

import pytest

from lll.esa_girafe_tilt_identifiability import orientation_sensitivity


def test_tilt_and_magnitude_are_separate():
    result = orientation_sensitivity([0., 0., 10.], [0.001, 0., 10.])
    assert result['minimum_rotation_rad'] == pytest.approx(math.atan(0.0001))
    assert result['rotation_axis_elevation_rad'] == 0.
    assert result['magnitude_change_mps2'] == pytest.approx(1e-6/(math.hypot(10., .001)+10.))


def test_parallel_forces_leave_only_magnitude_evidence():
    result = orientation_sensitivity([0., 0., 10.], [0., 0., 11.])
    assert result['minimum_rotation_rad'] == 0.
    assert result['rotation_axis_elevation_rad'] is None
    assert result['magnitude_change_mps2'] == 1.
