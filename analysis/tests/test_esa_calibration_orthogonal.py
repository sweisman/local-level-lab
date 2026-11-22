# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact checks for the shape-contrast construction."""

from fractions import Fraction as F

from lll.calibration_orthogonal import annihilate_quadratics, box_lower


def test_nine_moments_vanish_exactly_and_earlier_taps_do_not_change():
    times = [F(11, 3), F(16, 3), F(7), F(9), F(55, 6)]
    taps = [F(i, 13) for i in range(21)]
    adjusted = annihilate_quadratics(taps, times)
    assert adjusted[:6] == taps[:6]
    for axis in range(3):
        for order in range(3):
            assert sum(adjusted[6+3*i+axis]*time**order for i, time in enumerate(times)) == 0
    assert adjusted[6+3:6+6] == taps[6+3:6+6]


def test_exact_full_box_lower_does_not_drop_a_small_nonzero_coefficient():
    direction = [F(2), F(-3), F(1, 10**22)]
    lower, upper = [-2, -1, -4], [1, 3, 10]
    assert box_lower(direction, lower, upper) == -13-F(4, 10**22)
