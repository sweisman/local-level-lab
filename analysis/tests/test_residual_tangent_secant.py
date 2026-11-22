# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.residual_curvature_solver import fit_candidate, residual_secant


@pytest.mark.parametrize('multiplier', [2., -3.])
def test_residual_secant_recovers_signed_rank_one_curvature(multiplier):
    direction = np.array([1.2, -.4, .2])
    step = np.array([.1, -.05, .2])
    residual = np.array([multiplier, 9.])
    first = np.array([[3., 1., 0.], [6., 8., 4.]])
    second = first+np.vstack((direction*(direction@step), np.zeros(3)))
    curvature = residual_secant(step, residual, first, second)
    assert curvature == pytest.approx(multiplier*np.outer(direction, direction), abs=1e-12)


def test_residual_secant_declines_an_uninformative_step():
    first = np.eye(2)
    second = first+np.array([[0., 1.], [0., 0.]])
    assert residual_secant(np.array([1., 0.]), np.array([1., 0.]), first, second) is None
    assert residual_secant(np.zeros(2), np.ones(2), first, first) is None


def test_residual_secant_solver_counts_only_actual_trials_and_fresh_checks():
    class Problem:
        calls = 0

        class bounds:
            @staticmethod
            def decode(point):
                assert len(point) == 1 and abs(point[0]) <= 1.

        def residual_tangent(self, point, model):
            self.calls += 1
            d = point[0]-.2
            return [100.+d*d, .1*d], [[2*d], [.1]], 0

    problem = Problem()

    def change(before, after):
        return ((after[0]-before[0])*((before[0]-.2)+(after[0]-.2)), .1*(after[0]-before[0]))

    fit = fit_candidate(problem, 'generated', start=[.1], maximum_evaluations=40,
                        physical_step=lambda v: [[v[0], v[1], 0.]], residual_change=change,
                        secant_curvature=True)
    assert fit['converged'] and fit['secant_curvature_updates'] > 0
    assert fit['normalized_parameters'] == pytest.approx([.2], abs=1e-8)
    assert fit['evaluations'] == problem.calls == 1+len(fit['step_history'])+2
