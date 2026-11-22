# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-angle controls for the two-stop ground motion diagnostic."""

import numpy as np
from scipy.spatial.transform import Rotation


def test_gyro_predicts_the_signed_force_direction_from_known_tilts():
    from lll.esa_ground_tilt_closure import tilt_pairs

    angle = np.linspace(0., .15, 11)**2
    # Body turns about X with respect to an otherwise fixed force vector.
    force = np.column_stack((np.zeros(11), -np.sin(angle), -np.cos(angle)))
    increments = Rotation.from_rotvec(np.outer(np.diff(angle), [1., 0., 0.]))
    result = tilt_pairs(force, increments, span=1)
    assert result['pairs'] == 10
    assert result['gyro_prediction_rms_arcsec'] < 1e-9
    assert result['no_motion_rms_arcsec'] > 100
    assert result['centered_change_similarity'] > .99999
    reversed_result = tilt_pairs(force, increments.inv(), span=1)
    assert reversed_result['centered_change_similarity'] < -.999


def test_composition_preserves_order_of_distinct_body_turns():
    from lll.esa_ground_tilt_closure import tilt_pairs

    steps = Rotation.from_rotvec([[.1, 0., 0.], [0., .15, 0.]])
    first = np.array([0., 0., -1.])
    second = steps[0].inv().apply(first)
    third = steps[1].inv().apply(second)
    result = tilt_pairs(np.stack((first, second, third)), steps, span=2)
    assert result['pairs'] == 1
    assert result['gyro_prediction_rms_arcsec'] < 1e-9


def test_yaw_about_force_has_no_tilt_signal():
    from lll.esa_ground_tilt_closure import tilt_pairs

    force = np.tile([0., 0., -1.], (11, 1))
    rates = Rotation.from_rotvec(np.outer(np.linspace(0., .15, 10), [0., 0., 1.]))
    result = tilt_pairs(force, rates, span=1)
    assert result['gyro_prediction_rms_arcsec'] == result['no_motion_rms_arcsec'] == 0.
    assert result['centered_change_similarity'] is None


def test_integration_uses_partial_native_intervals_at_bin_centers():
    from lll.esa_ground_tilt_closure import gyro_steps

    edges = np.array([0., .3, .65, 1., 1.4])
    rates = np.outer([0., 4., 3., 1.], [1., 0., 0.])
    centers = np.array([.2, .6, 1.2])
    steps = gyro_steps(edges, rates, centers)
    np.testing.assert_allclose(steps.as_rotvec()[:, 0], [1.2, 1.45], atol=1e-12)
