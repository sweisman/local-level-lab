from fractions import Fraction

import numpy as np
import pytest

from lll.ilvis0_linked_training_support import propose_direction, split_support, support


def test_shared_component_enters_both_earlier_constraint_and_later_score():
    residual = np.array([2.])
    design = np.array([[1., 1.]])
    objective = np.array([1., 1.])
    lower = np.array([-1., -1.])
    upper = -lower
    direction, _ = propose_direction(design, residual, objective, lower, upper, 2.75)
    projected = [(direction[0], direction[0])]*2
    support_bound = support(residual, direction, projected, [(1, 1)]*2,
                            lower, upper, increase=Fraction(9, 4), unshared=Fraction(1, 4))
    assert support_bound['upper'] == .75
    assert support_bound['box_upper'] == 2.


def test_coefficient_rounding_interval_and_negative_box_edge_are_preserved():
    interval = [(Fraction(-2), Fraction(-1))]
    result = support([1], [-1], interval, [(Fraction(-3), Fraction(-2))],
                     [-1], [0], increase=3, unshared=0)
    assert result['upper'] == 3.
    with pytest.raises(ValueError, match='ordered interval'):
        support([1], [1], [(2, 1)], [(1, 1)], [-1], [1], increase=3, unshared=0)


def test_split_support_keeps_signed_training_change_in_shared_coefficients():
    box, shared = split_support([(1, 2), (-2, -1)], [(2, 3), (1, 2)], [-1, -1], [1, 1],
                                multiplier=2, bound=5, shared_start=1)
    assert box == 12
    assert shared == [(3, 6)]
