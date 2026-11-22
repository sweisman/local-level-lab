# SPDX-License-Identifier: AGPL-3.0-or-later
"""The shifted control keeps the native derivative and a known zero."""

import numpy as np
import pytest

from lll.turning_known_optimum import ShiftedProblem, start_point


class TinyProblem:
    def residual_tangent(self, point, model):
        assert model == 'control'
        x, y = point
        return np.array([x*x + y, x-y]), np.array([[2*x, 1], [1, -1]]), 2


def test_shifted_problem_has_exact_known_zero_and_unchanged_jacobian():
    base = TinyProblem()
    target = np.array([.2, -.3])
    target_residual, _, _ = base.residual_tangent(target, 'control')
    shifted = ShiftedProblem(base, target_residual, 'control')
    residual, jac, boundaries = shifted.residual_tangent(target, 'control')
    assert np.array_equal(residual, np.zeros(2))
    assert np.array_equal(jac, np.array([[.4, 1], [1, -1]]))
    assert boundaries == 2
    with pytest.raises(ValueError, match='unchanged model'):
        shifted.residual_tangent(target, 'other')


def test_two_declared_starts_are_feasible_and_distinct():
    target = np.array([.2, -.999, .1])
    assert np.array_equal(start_point(target, 0), np.zeros(3))
    near = start_point(target, 1)
    assert np.all(abs(near) <= .95)
    assert not np.array_equal(near, target)
    with pytest.raises(ValueError, match='declared start'):
        start_point(target, 2)
