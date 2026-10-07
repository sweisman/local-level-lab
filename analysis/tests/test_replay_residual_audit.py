# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent physical counterexample and gap handling for the saved-data audit."""
import numpy as np
import pytest

from audit_replay_residuals import mean_bins, segment_gradient, unit


def test_acceleration_changes_apparent_up_without_any_body_rotation():
    # Fixed IMU orientation and changing horizontal acceleration: no actual tilt rate.
    times = np.arange(9.)*60
    angle_rate = 2e-4
    angle = angle_rate*times
    force = np.column_stack([9.81*np.tan(angle), np.zeros(len(times)), np.full(len(times), -9.81)])
    apparent_up = unit(force)
    bins = dict(t=times, seg=np.zeros(len(times), int))
    tilt = np.cross(segment_gradient(apparent_up, bins), apparent_up)
    # The existing gravity-only correction produces a false y-axis rotation.
    assert tilt[1:-1, 1] == pytest.approx(np.full(7, angle_rate), rel=3e-5)
    assert np.max(np.abs(tilt[:, (0, 2)])) == 0
    true_up = np.tile([0., 0., -1.], (len(times), 1))
    assert np.max(np.abs(segment_gradient(true_up, bins))) == 0


def test_derivative_does_not_bridge_segments():
    bins = dict(t=np.array([0., 60., 120., 300., 360.]), seg=np.array([0, 0, 1, 2, 2]))
    values = np.array([[0., 0., 0.], [60., 0., 0.], [1000., 0., 0.], [2000., 0., 0.], [2120., 0., 0.]])
    assert segment_gradient(values, bins)[:, 0].tolist() == [1., 1., 0., 2., 2.]


def test_bin_average_uses_saved_half_open_intervals():
    times = np.arange(10.)
    bins = dict(t=np.array([2., 7.]), dt=np.array([4., 4.]))
    average, counts = mean_bins(times[:, None], times, bins)
    assert average[:, 0].tolist() == [1.5, 6.5]
    assert counts.tolist() == [4, 4]
    with pytest.raises(ValueError, match='empty'):
        mean_bins(times[:, None], times, dict(t=np.array([100.]), dt=np.array([1.])))
