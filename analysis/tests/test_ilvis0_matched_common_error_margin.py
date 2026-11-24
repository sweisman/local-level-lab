import numpy as np
import pytest

from lll.ilvis0_matched_common_error_margin import accuracy_margin, rms_margin


def test_rms_margin_adds_error_to_every_existing_distance():
    distances = np.array([3., 4.])
    radius = rms_margin(distances, 10.)
    assert np.sqrt(np.mean((distances+radius)**2)) == pytest.approx(10.)
    assert rms_margin(np.array([10., 10.]), 10.) == 0.
    assert rms_margin(np.array([11., 11.]), 10.) == 0.


def test_accuracy_margin_uses_farthest_vertex_and_separate_axes():
    points = np.zeros((2, 3))
    hull = np.array([[[0., 0., 0.], [3., 4., 0.], [0., 0., 5.]]]*2)
    result = accuracy_margin(points, hull)
    assert result['all_limits_hold_at_zero']
    assert result['limiting_metric'] == 'horizontal_rms_m'
    assert result['additional_radius_m'] == 5.
    assert result['margins_m']['vertical_rms_m'] == 25.
