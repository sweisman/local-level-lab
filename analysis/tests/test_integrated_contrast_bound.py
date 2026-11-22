# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check exact adjoint weights for errors that accumulate through the path."""

from fractions import Fraction as F
from itertools import product

import pytest

from lll.integrated_contrast_bound import contrast_allowances, integrated_error_weights, symmetric_support


def test_integrated_weights_reach_the_exact_vertex_maximum():
    times = [F(0), F(1, 2), F(3)]
    taps = [(F(x), F(x)) for x in (1, -3, 2)]
    initial, velocities = integrated_error_weights(times, taps, axes=1)
    radii = [F(7), F(3), F(4)]
    values = []
    for signs in product((-1, 1), repeat=3):
        start, first, last = (sign*radius for sign, radius in zip(signs, radii, strict=True))
        path = [start, start+first/2, start+first/2+5*last/2]
        values.append(abs(sum(weight[0]*position for weight, position in zip(taps, path, strict=True))))
    assert initial == [(0, 0)]
    assert velocities == [(F(-1, 2), F(-1, 2)), (5, 5)]
    assert symmetric_support(initial+velocities, radii) == max(values) == F(43, 2)


def test_directional_enclosure_preserves_interleaved_axes_and_uncertainty():
    times = [F(11, 3), F(4)]
    taps = [(F(-3), F(-2)), (F(6), F(6)), (F(2), F(4)), (F(-9), F(-7))]
    initial, rates = integrated_error_weights(times, taps, axes=2)
    assert initial == [(-1, 2), (-3, -1)]
    assert rates == [(F(2, 3), F(4, 3)), (-3, F(-7, 3))]
    assert symmetric_support(initial+rates, [1, 2, 3, 4]) == 24
    with pytest.raises(ValueError, match='strictly ordered'):
        integrated_error_weights([4, 4], taps, axes=2)
    with pytest.raises(ValueError, match='nonnegative'):
        symmetric_support(initial, [-1, 0])


def test_allowance_uses_the_same_gap_and_assigns_cross_cut_interval_to_forecast():
    times = [F(0), F(1, 2), F(3)]
    taps = [(F(x), F(x)) for x in (1, -3, 2)]
    coefficients, gap, limits = contrast_allowances(times, taps, F(1, 5), axes=1, cut=2)
    assert coefficients == dict(independent_position=[6], initial_position=[0],
                                earlier_velocity=[F(1, 2)], later_velocity=[5])
    assert gap == F(12, 5)
    assert limits == dict(independent_position=F(1, 5), initial_position=None,
                          earlier_velocity=F(12, 5), later_velocity=F(6, 25),
                          uniform_velocity=F(12, 55))
