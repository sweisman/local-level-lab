# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known angle and axis conventions for the local platform rate check."""

import numpy as np
from scipy.spatial.transform import Rotation


def test_rate_conventions_are_finite_and_distinct():
    from lll.esa_girafe_platform_rate import CONVENTIONS

    assert len(CONVENTIONS) == len(set(CONVENTIONS)) == 96


def test_fixed_permutation_and_degree_scale_predict_a_known_unit_force_vector():
    from lll.esa_girafe_platform_rate import case_score, force_support

    t = np.arange(6001)/1000.
    omega = np.array([4., -3., 7.])
    force = Rotation.from_rotvec(t[:, None]*np.deg2rad(omega)).inv().apply([1., 6., -8.])
    reordered = np.tile([-omega[2], omega[0], -omega[1]], (len(t), 1))
    rows = np.column_stack((t, force, reordered))
    centers, means = force_support(rows)
    correct = case_score(rows, centers, means, ('degree_per_second', (1, 2, 0), (1, -1, -1)))
    wrong = case_score(rows, centers, means, ('radian_per_second', (1, 2, 0), (1, -1, -1)))
    for right, inaccurate in zip(correct, wrong, strict=True):
        assert right['gyro_prediction_rms_arcsec'] < 1e-4
        assert right['no_motion_rms_arcsec'] > 100.
        assert inaccurate['gyro_prediction_rms_arcsec'] > 100.
    assert [item['span_s'] for item in correct] == [.1, 1.]
