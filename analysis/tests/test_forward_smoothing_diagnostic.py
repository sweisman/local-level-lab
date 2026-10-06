# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from forward_smoothing_diagnostic import diagnose, matched_filter


def test_matching_filter_has_no_cross_gap_or_missing_sample_support():
    t = np.r_[np.arange(80.), np.arange(100., 180.)]
    values = np.column_stack([np.r_[np.ones(80), np.full(80, 100.)]])
    valid = np.ones(len(t), bool)
    valid[35] = False
    filtered, keep = matched_filter(t, values, valid)
    assert not keep[20:51].any()
    assert not keep[65:95].any()
    np.testing.assert_allclose(filtered[keep & (t < 80), 0], 1.)
    np.testing.assert_allclose(filtered[keep & (t >= 100), 0], 100.)


def test_independent_coordinated_turn_with_noisy_gps_preserves_known_direction():
    # Independently construct smooth physical frames, without synthesize or science fitting.
    t = np.arange(0., 300., .05)
    bank = np.radians(15)*np.exp(-((t-130)/25)**2)
    heading = np.cumsum(9.80665*np.tan(bank)/260)*.05
    mount = Rotation.from_euler('ZYX', [27., 4., 2.], degrees=True).as_matrix()
    frames = Rotation.from_euler('ZYX', np.column_stack([heading, t*0, bank])).as_matrix() @ mount
    gyro = Rotation.from_matrix(np.swapaxes(frames[:-1], 1, 2) @ frames[1:]).as_rotvec()/.05
    gyro = np.vstack([gyro, gyro[-1]])
    gps_t = np.arange(1., 299.)
    bearing = np.degrees(np.interp(gps_t, t, heading))+np.random.default_rng(74).normal(0, .1, len(gps_t))
    result = diagnose(t, gyro, gps_t, np.full(len(gps_t), 260.), bearing, mount.T @ [0, 0, -1])
    assert result['available']
    assert result['r2'] > .8
    assert np.dot(result['axis'], mount.T @ [1, 0, 0]) > .999
    assert result['accepted_for_science'] is False
    assert result['uncertainty_available'] is False


def test_gps_noise_without_roll_does_not_create_a_forward_reference():
    t = np.arange(0., 300., .05)
    gt = np.arange(1., 299.)
    bearing = np.random.default_rng(74).normal(0, .1, len(gt))
    result = diagnose(t, np.zeros((len(t), 3)), gt, np.full(len(gt), 260.), bearing, [0, 0, -1])
    assert not result['available']


def test_short_support_cannot_cross_a_large_course_step_in_a_gap():
    gt = np.r_[np.arange(10.), np.arange(50., 60.)]
    gyro_t = np.r_[np.arange(0., 10., .05), np.arange(50., 60., .05)]
    result = diagnose(gyro_t, np.zeros((len(gyro_t), 3)), gt, np.full(len(gt), 260.),
                      np.r_[np.zeros(10), np.full(10, 90.)], [0, 0, -1])
    assert not result['available']
    assert result['samples'] == 0


def test_missing_gyro_or_gps_outside_gyro_support_is_unavailable():
    gt = np.arange(100.)
    assert not diagnose([], np.empty((0, 3)), gt, np.full(100, 260.), np.zeros(100), [0, 0, -1])['available']
    assert not diagnose(np.arange(10.), np.zeros((10, 3)), gt,
                        np.full(100, 260.), np.zeros(100), [0, 0, -1])['available']


def test_invalid_timestamps_are_rejected():
    with pytest.raises(ValueError, match='increasing'):
        diagnose(np.arange(100.), np.zeros((100, 3)), [0., 2., 1.], np.full(3, 260.), np.zeros(3), [0, 0, -1])
