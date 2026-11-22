# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
from scipy.spatial.transform import Rotation

from lll.force_accel_calibration import corrected_directions
from lll.force_joint_calibration import joint_directions, replay_score


def material():
    rng = np.random.default_rng(677)
    axes = Rotation.from_rotvec(rng.normal(size=(12, 3))).as_matrix()
    channels = axes*(rng.normal(size=(12, 3)) + [0., 0., 9.8])[:, None, :]
    derivatives = rng.normal(scale=.005, size=(2, 12, 3, 3, 6))
    limits = np.full(3, .1), np.full(3, .02)
    return axes, channels, derivatives, limits, rng.uniform(-.5, .5, size=12)


def test_all_twelve_directions_follow_the_corrected_force_derivative():
    axes, channels, (dchannels, daxes), limits, point = material()
    args = channels, axes, dchannels, daxes, *limits
    direction, jac = joint_directions(point, *args)
    shifted_channels = channels+dchannels@point[6:]
    shifted_axes = axes+daxes@point[6:]
    direct, _ = corrected_directions(shifted_channels, shifted_axes, point[:6], *limits)
    np.testing.assert_allclose(direction, direct, atol=1e-14)
    h = 1e-5
    for axis in np.eye(12):
        a, b = (joint_directions(point+s*h*axis, *args)[0] for s in (-1., 1.))
        np.testing.assert_allclose((b-a)/(2*h), jac@axis, atol=1e-10)


def test_exact_earlier_replay_gate_ignores_later_force_mismatch():
    axes, channels, _, limits, point = material()
    direction, _ = corrected_directions(channels, axes, point[:6], *limits)
    reference = Rotation.from_rotvec([.2, .1, -.1]).apply(direction)
    baseline = replay_score(reference, channels, axes, point, *limits, direction[:8], training=8)
    reference[8:] *= -1.
    altered = replay_score(reference, channels, axes, point, *limits, direction[:8], training=8)
    assert baseline['passed'] and altered['passed']
    assert altered['exact_training_mean_squared_chord'] == baseline['exact_training_mean_squared_chord']
    assert altered['exact_later_rms_deg'] > 179.
    mismatched = replay_score(reference, channels, axes, point, *limits, -direction[:8], training=8)
    assert not mismatched['passed']
