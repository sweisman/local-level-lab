# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact primal and contrast checks for a calibration margin."""

from fractions import Fraction as F

import numpy as np
import pytest

from lll.calibration_maximum_margin import (
    exact_contrast, exact_discrepancy, propose, smooth_rows,
)


def test_exact_primal_and_contrast_close_a_known_margin():
    times = [0., 1., 2., 3.]
    base = [F(5), F(0), F(0)]+[F(0)]*12
    matrix = np.zeros((15, 2))
    matrix[0] = [-1., 1.]
    metric = [2.]+[1.]*14
    lower, upper = [0., 0.], [1., 2.]
    choice = propose(base, matrix, metric, lower, upper, times, method='highs-ds')
    assert choice['point'] is not None
    assert exact_discrepancy(base, matrix, metric, lower, upper, times,
                             choice['point'], choice['smooth']) == 3
    result = exact_contrast(base, matrix, metric, lower, upper, times, choice['taps'])
    assert result['bound'] == F(3, 2)


def test_exact_smooth_corrections_reject_out_of_box_witnesses():
    times = [F(3), F(4), F(7)]
    matrix = [[F(1, 7)]]*9
    metric = [F(2, 3)]*9
    smooth = [F(1, 8), F(0), F(0)]+[F(0)]*6
    base = [-sum(c*v for c, v in zip(smooth, row, strict=True))
            for row in smooth_rows(times, 9)]
    assert exact_discrepancy(base, matrix, metric, [0], [1], times, [0], smooth) == 0
    with pytest.raises(ValueError, match='box'):
        exact_discrepancy(base, matrix, metric, [0], [1], times, [2], smooth)


def test_both_sides_keep_roundoff_in_original_physical_units():
    matrix = [[F(1, 3)]]*3+[[F(0)]]*9
    lower = upper = [F(1, 3)]
    metric = [F(1, 3)]*12
    base = [F(0)]*12
    exact = exact_discrepancy(base, matrix, metric, lower, upper, [0, 1, 2], [F(1, 3)], [0]*9)
    assert exact == F(1, 27)
    assert exact_contrast(base, matrix, metric, lower, upper, [0, 1, 2], [1]+[0]*11)['bound'] == exact/2
