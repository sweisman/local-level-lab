# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known answers exercise actual bounded nonlinear steps and unchanged gates."""
import importlib
import importlib.util

import numpy as np
import pytest

from lll.ilvis0_solver_controls import Analytic, analytic_problem


def candidate():
    name = 'lll.ilvis0_solver_boundary'
    assert importlib.util.find_spec(name) is not None, 'boundary-aware solver is missing'
    return importlib.import_module(name)


def curved_boundary():
    # The first residual decreases throughout the box. At x=1, y=.2 cancels
    # the second residual, so the exact minimum is .9**2 + constant 1.
    return Analytic(lambda u: np.array([u[0]+.1*u[0]**3-2.,
                                      2*u[1]+.3*u[0]**2-.7]),
                    lambda u: np.array([[1+.3*u[0]**2, 0.], [.6*u[0], 2.]]))


@pytest.mark.parametrize('start', [np.array([np.nextafter(1., 0.), 0.]),
                                  np.array([-1., -1.]), np.zeros(2)])
def test_recovers_known_curved_boundary_and_fresh_stopping(start):
    problem = curved_boundary()
    original = start.copy()
    fit = candidate().fit_candidate(problem, 'control', start=start, maximum_evaluations=200)
    assert fit['converged'] and fit['stability_verified']
    assert fit['exact_projected_gradient_relative'] <= 1e-4
    assert fit['normalized_parameters'] == pytest.approx([1., .2], abs=1e-6)
    assert fit['residual_sum_squares'] == pytest.approx(1.81, abs=1e-8)
    assert problem.calls == fit['evaluations'] <= 200
    assert fit['scientific_decision'] == 'abstain'
    assert not fit['scientific_eligible']
    np.testing.assert_array_equal(start, original)


@pytest.mark.parametrize('name', ['interior', 'boundary', 'redundant', 'scaled',
                                 'nonlinear', 'gain_offset'])
def test_independent_predictions_and_objectives(name):
    problem, optimum, expected, unique = analytic_problem(name)
    fit = candidate().fit_candidate(problem, 'control', start=[-.8, .8], maximum_evaluations=200)
    point = np.array(fit['normalized_parameters'])
    assert fit['converged'] and fit['stability_verified']
    assert fit['residual_sum_squares'] == pytest.approx(expected, abs=1e-7, rel=0)
    assert np.linalg.norm(problem.residual(point)-problem.residual(optimum)) <= 1e-4
    if unique:
        np.testing.assert_allclose(point, optimum, atol=1e-5, rtol=0)
    assert problem.calls == fit['evaluations'] <= 200


def test_rejected_full_step_is_shortened_using_actual_nonlinear_cost():
    # Newton's first step for exp(4*x)-exp(2) overshoots from -.8.
    problem = Analytic(lambda u: np.array([np.exp(4*u[0])-np.exp(2), u[1]-.2]),
                       lambda u: np.diag([4*np.exp(4*u[0]), 1.]))
    fit = candidate().fit_candidate(problem, 'control', start=[-.8, -.8], maximum_evaluations=200)
    assert fit['converged']
    assert fit['normalized_parameters'] == pytest.approx([.5, .2], abs=1e-6)
    assert any(not row['accepted'] for row in fit['step_history'])
    accepted = [row['cost'] for row in fit['step_history'] if row['accepted']]
    assert all(a >= b for a, b in zip(accepted, accepted[1:]))


def test_budget_exhaustion_does_not_claim_convergence():
    problem = Analytic(lambda u: np.array([np.exp(4*u[0])-np.exp(2), u[1]-.2]),
                       lambda u: np.diag([4*np.exp(4*u[0]), 1.]))
    fit = candidate().fit_candidate(problem, 'control', start=[-.8, -.8], maximum_evaluations=6)
    assert not fit['converged']
    assert fit['termination'] == 'unresolved'
    assert problem.calls == fit['evaluations'] <= 6


@pytest.mark.parametrize('start', [[1.01, 0.], [float('nan'), 0.], [0.]])
def test_invalid_start_rejected_before_evaluation(start):
    problem = curved_boundary()
    with pytest.raises(ValueError):
        candidate().fit_candidate(problem, 'control', start=start)
    assert problem.calls == 0


@pytest.mark.parametrize('budget', [True, 5, 601, 200.0])
def test_invalid_budget_rejected_before_evaluation(budget):
    problem = curved_boundary()
    with pytest.raises(ValueError):
        candidate().fit_candidate(problem, 'control', start=[0., 0.], maximum_evaluations=budget)
    assert problem.calls == 0
