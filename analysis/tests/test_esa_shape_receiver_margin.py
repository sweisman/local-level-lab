# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

import numpy as np
import pytest

from lll.esa_shape_receiver_margin import acceleration_basis, coefficient_enclosure, radius


def test_piecewise_acceleration_leaves_earlier_reports_fixed_and_integrates_twice():
    times = [0., 1., 2., 3., 4.]
    basis = acceleration_basis(times, cut=3, blocks=2)
    assert basis == [
        [0, 0], [0, 0], [0, 0], [Fraction(1, 2), 0],
        [Fraction(3, 2), Fraction(1, 2)],
    ]


def test_acceleration_calculation_preserves_signed_cancellation():
    basis = [[Fraction(1), Fraction(3)], [Fraction(1), Fraction(4)]]
    lower = np.array([[2., -1., 0.], [-3., 2., 0.]])
    upper = lower.copy()
    low, high = coefficient_enclosure(basis, lower, upper)
    assert low == high == [[-1, 1, 0], [-6, 5, 0]]
    assert radius(13., low, high) == pytest.approx(1.)
