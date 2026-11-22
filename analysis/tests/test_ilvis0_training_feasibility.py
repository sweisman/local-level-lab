from fractions import Fraction as F

import numpy as np

from lll.ilvis0_coupled_training_score import certify
from lll.ilvis0_training_feasibility import loss_proposal, static_proposal


def test_phase_one_produces_a_checked_static_contradiction():
    lower, upper = np.array([-2.]), np.array([2.])
    a, b = [[1e-12], [-1.]], [-1e-12, -1.]
    _, weights, slack = static_proposal(lower, upper, a, b)
    assert slack>0
    zero = [(F(0), F(0))]
    assert certify([0], [0], zero, zero, lower, upper, a, b, weights,
                   increase=F(1,4), unshared=0)<0


def test_earlier_loss_can_exclude_a_statically_feasible_box():
    lower, upper = np.array([-2.]), np.array([2.])
    a, b = [[-1.]], [-1.]
    start, _, slack = static_proposal(lower, upper, a, b)
    assert slack==0.
    proposed = loss_proposal(np.ones((1,1)), np.zeros(1), lower, upper, a, b, start,
                             iterations=20)
    assert proposed['tangent_proposed']
    direction = proposed['direction']
    interval = [(F(direction[0]), F(direction[0]))]
    zero = [(F(0), F(0))]
    assert certify([0], direction, interval, zero, lower, upper, a, b, proposed['weights'],
                   increase=F(1,4), unshared=0)==-F(1,2)
