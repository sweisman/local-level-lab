# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check outward necessary rows and projection back to physical coordinates."""

from fractions import Fraction as F
from itertools import product


def test_midpoint_row_encloses_every_signed_endpoint_including_rounding():
    from lll.esa_linked_coordinates import relaxed_row

    pairs = [(F(1, 3), F(2, 3)), (F(-5, 7), F(-1, 7))]
    lower, upper = [-2., .25], [1., 1.5]
    row, right = relaxed_row(pairs, F(2, 9), lower, upper)
    for coefficients, point in product(product(*pairs), product(*zip(lower, upper))):
        discrepancy = sum((F(c)-actual)*F(x) for c, actual, x in zip(row, coefficients, point, strict=True))
        assert F(right) >= F(2, 9)+discrepancy


def test_projection_preserves_feasible_points_in_the_original_box():
    from lll.esa_linked_coordinates import physical_box

    lower, upper, center = [-1., -1.], [1., 1.], [F(1, 3), F(-2, 3)]
    displacement = [dict(parameter_index=0, lower=-.25, upper=.25),
                    dict(parameter_index=1, lower=-.5, upper=.25)]
    lo, hi = physical_box(lower, upper, center, displacement)
    assert -1. <= lo[0] <= F(1, 3)-F(1, 4) <= F(1, 3)+F(1, 4) <= hi[0] <= 1.
    assert lo[1] == -1.
    assert F(hi[1]) >= F(-2, 3)+F(1, 4)
