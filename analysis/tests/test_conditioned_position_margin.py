# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check both directions of the conditioning map against rational algebra."""

from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np

from lll.calibration_maximum_margin import smooth_rows
from lll.calibration_orthogonal import annihilate_quadratics
from lll.conditioned_position_margin import (conditional_transfer, forward_intervals, lower_certificate,
                                             propose, reverse_intervals, upper_certificate)


def factors():
    return SimpleNamespace(
        epoch_count=5, observation_dimension=3, state_dimension=1,
        _transition=np.array([[[.5]], [[.75]], [[.25]], [[.5]], [[.5]]]),
        _observation=np.array([[[1.], [0.], [0.]], [[2.], [0.], [0.]],
                               [[1.], [2.], [0.]], [[1.], [0.], [1.]], [[0.], [1.], [0.]]]),
        _gain=np.array([[[.25, 0., 0.]], [[.125, 0., 0.]], [[0., 0., 0.]],
                        [[0., 0., 0.]], [[0., 0., 0.]]]),
    )


def assert_contains(bounds, expected):
    for (left, right), value in zip(bounds, expected, strict=True):
        assert left <= value <= right
        assert right-left <= F(1, 10**100)


def test_conditional_forward_and_adjoint_match_independent_closed_form():
    operator = factors()
    vector = [F(13, 7), F(1), F(2), F(-11, 5), F(9), F(3)]
    # At cut two, the scalar state is (1/8)*first + (1/8)*second.
    mean = (vector[0]+vector[3])/8
    future = [mean, 2*mean, 0, mean/4, 0, mean/4, 0, mean/8, 0]
    assert_contains(forward_intervals(operator, vector, cut=2), future)
    np.testing.assert_allclose(conditional_transfer(operator, cut=2)@np.asarray(vector, float),
                               np.asarray(future, float))
    weights = [F(9, 13), F(-3, 7), F(4), F(5), F(11), F(-8), F(7), F(5, 2), F(6)]
    contribution = (weights[0]+2*weights[1]+(weights[3]+weights[5])/4+weights[7]/8)/8
    reverse = [contribution, 0, 0, contribution, 0, 0]
    assert_contains(reverse_intervals(operator, weights, cut=2), reverse)


def test_conditional_linear_program_and_certificates_agree():
    operator = factors()
    times = [0, 1, 2, 3]
    # Extend the last epoch so a quadratic cannot explain all four future values.
    for name in ('_transition', '_observation', '_gain'):
        matrix = getattr(operator, name)
        setattr(operator, name, np.concatenate([matrix, matrix[-1:]], axis=0))
    operator.epoch_count += 1
    nominal = [F(0)]*17 + [F(8)]
    physical = np.zeros((18, 1))
    physical[-1, 0] = 1.
    metric, limits = [1.]*18, ([-1.], [1.])
    smooth = smooth_rows(times, len(nominal))
    args = operator, nominal, physical, metric, *limits
    fit = propose(*args, smooth, cut=2, iterations=200)
    assert fit['status'] == 0
    upper = upper_certificate(*args, smooth, fit, cut=2)
    tokens = annihilate_quadratics(fit['later_taps'], times)
    lower, _ = lower_certificate(*args, tokens, cut=2)
    # Third difference weights have L1 norm 8. The two earlier taps add
    # 3/32 each. Calibration reduces the nominal third difference to 7.
    assert lower <= F(56, 131) <= upper
    assert float(upper-lower) < 1e-10
