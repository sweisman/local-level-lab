# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import numpy as np
import pytest


def solver():
    return importlib.import_module('lll.ilvis0_solver_refinement')


class Bounds:
    def __init__(self, n):
        self.active = tuple(f'p{i}' for i in range(n))

    def decode(self, point):
        if np.any(abs(np.asarray(point)) > 1):
            raise ValueError('outside bounds')
        return dict(zip(self.active, point))


class Linear:
    def __init__(self, matrix, target, floor=1.):
        self.matrix = np.asarray(matrix, float)
        self.target = np.asarray(target, float)
        self.floor = floor
        self.bounds = Bounds(self.matrix.shape[1])
        self.calls = 0

    def residual_tangent(self, point, model):
        self.calls += 1
        return (np.r_[self.matrix@point-self.target, self.floor],
                np.vstack([self.matrix, np.zeros(self.matrix.shape[1])]), 0)


@pytest.mark.parametrize('matrix,target,optimum', [
    (np.eye(2), [.2, -.4], [.2, -.4]),
    (np.eye(2), [1.5, -.4], [1., -.4]),
    ([[1., 1.], [2., 2.]], [.6, 1.2], [.3, .3]),
    (np.diag([1e4, 1e-4]), [2e3, -4e-5], [.2, -.4]),
])
def test_known_optima_converge_without_changing_feasible_problem(matrix, target, optimum):
    p = Linear(matrix, target)
    result = solver().fit_candidate(p, 'sphere_rotating')
    assert result['converged']
    point = np.array(result['normalized_parameters'])
    assert np.all(abs(point) <= 1)
    expected = np.linalg.norm(p.matrix@np.asarray(optimum)-p.target)**2 + p.floor**2
    assert result['residual_sum_squares'] == pytest.approx(expected, abs=1e-7)
    assert result['exact_projected_gradient_relative'] <= 1e-4
    assert result['stability_verified']
    assert result['evaluations'] == p.calls <= 198
    assert np.asarray(result['right_singular_vectors']).shape == (2, 2)
    assert result['scientific_decision'] == 'abstain'


def test_small_gradient_at_budget_limit_is_not_convergence():
    p = Linear(np.eye(2)*1e-6, [.1, .1])
    result = solver().fit_candidate(p, 'flat_still', maximum_evaluations=4)
    assert result['exact_projected_gradient_relative'] <= 1e-4
    assert not result['converged']
    assert result['evaluations'] == p.calls <= 2


def test_stability_needs_stationarity_and_repeated_small_measurement_steps():
    monitor = solver().StableStop()
    a = np.array([0., 0.]); r = np.array([2., 1.]); j = np.eye(2)
    for _ in range(5):
        assert not monitor.observe(a, r, j)
    assert monitor.stationarity > 1e-4
    for _ in range(3):
        accepted = monitor.observe(a, r, np.zeros_like(j))
    assert accepted
    assert monitor.streak == 3


def test_outward_bound_gradient_is_projected_but_inward_gradient_is_not():
    m = solver()
    assert m.projected_stationarity(np.array([1.]), np.array([-1.]), np.ones((1, 1)))[0] == 0.
    assert m.projected_stationarity(np.array([1.]), np.array([1.]), np.ones((1, 1)))[0] == 1.


def test_invalid_budget_and_nonfinite_measurements_are_rejected():
    p = Linear([[1.]], [0.])
    with pytest.raises(ValueError, match='allowance'):
        solver().fit_candidate(p, 'flat_still', maximum_evaluations=201)
    p.target[:] = np.nan
    with pytest.raises(ValueError, match='nonfinite'):
        solver().fit_candidate(p, 'flat_still')


def test_nonlinear_known_optimum_uses_verified_scaled_callback():
    class Rosenbrock:
        bounds = Bounds(2)
        def residual_tangent(self, point, model):
            x, y = point
            return (np.array([10*(y-x*x), 1-x, 1.]),
                    np.array([[-20*x, 10.], [-1., 0.], [0., 0.]]), 0)
    result = solver().fit_candidate(Rosenbrock(), 'flat_still', start=[-.9, .9])
    assert result['converged']
    assert result['termination'] == 'scaled_stable_callback'
    assert not result['solver_reported_success']  # SciPy reports callback StopIteration honestly.
    assert result['stopping_rule_verified'] and result['stable_accepted_iterations'] >= 3
    assert result['residual_sum_squares'] == pytest.approx(1., abs=1e-7)
