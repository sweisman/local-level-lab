# SPDX-License-Identifier: AGPL-3.0-or-later
"""Outward score and exact joint-inequality controls."""

from fractions import Fraction as F
from itertools import product


def test_score_rounding_covers_all_coefficient_and_box_endpoints():
    from lll.esa_linked_joint_score import score_objective

    coeffs = [(F(2, 7), F(3, 7)), (F(-2, 3), F(-1, 3))]
    lo, hi = [-1., .25], [2., 1.]
    objective, padding = score_objective(coeffs, lo, hi)
    for coeff, point in product(product(*coeffs), product(*zip(lo, hi))):
        score = sum(c*F(x) for c, x in zip(coeff, point, strict=True))
        rounded = sum(F(c)*F(x) for c, x in zip(objective, point, strict=True))
        assert score <= rounded+F(padding)


def test_joint_score_preserves_a_constraint_separate_projections_lose():
    from lll.esa_linked_joint_score import checked_score

    assert checked_score([0., 0.], [1., 1.], [[1., 1.]], [1.], [1., 1.], [1.], .125) == F(9, 8)
