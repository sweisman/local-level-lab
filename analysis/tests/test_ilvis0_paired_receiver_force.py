# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_paired_receiver_force import matched_support, paired_window


def test_support_requires_common_epochs_and_bounds_both_edge_gaps():
    good = list(range(5000, 35001, 1000))
    assert matched_support(good, 20000) == good
    assert matched_support(good[2:], 20000) is None
    assert matched_support(good[:-2], 20000) is None
    assert matched_support([tag for tag in good if tag != 21000], 20000) is None


def test_paired_force_captures_known_vertical_acceleration_difference():
    t = np.linspace(-15., 15., 31)
    left = np.column_stack((np.full(len(t), .3), np.full(len(t), -.5), 1500.+.01*t**2))
    right = left.copy()
    right[:, 2] += 10.+.015*t**2
    rows = paired_window(t, left, right)
    nodes, weights = np.polynomial.legendre.leggauss(8)
    field = 2.*7.292115e-5*np.cos(.3)
    rotation_difference = weights@(
        np.hypot(9.80665+.02, field*.02*15.*nodes)
        - np.hypot(9.80665+.05, field*.05*15.*nodes))/2.
    expected = dict(sphere_rotating=rotation_difference, sphere_still=-.03,
                    flat_still=-.03, flat_geographic_field=rotation_difference)
    for row in rows:
        np.testing.assert_allclose(row['center_acceleration_difference_neu_mps2'], [0., 0., -.03],
                                   rtol=0., atol=1e-12)
        for model, difference in row['mean_force_difference_mps2'].items():
            np.testing.assert_allclose(difference, expected[model], rtol=0., atol=1e-12)
