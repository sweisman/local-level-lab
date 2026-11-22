# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

from lll.ground_grid_score import score_sensitivity


def test_grid_bound_integrates_the_linear_midpoint_kernel():
    times = [0, 1, 2]
    taps = [(1, 0, 0), (4, 5, 6)]
    assert score_sensitivity(times, taps, []) == (0, Fraction(1, 3))
    assert score_sensitivity(times, taps, [1]) == (1, 0)


def test_grid_bound_accumulates_signed_interpolation_weights_before_norm():
    times = [0, 1, 2, 3, 4]
    taps = [(2, 0, 0), (-1, 0, 0), (2, 0, 0), (90, 0, 0)]
    assert score_sensitivity(times, taps, [2]) == (1, Fraction(16, 3))
