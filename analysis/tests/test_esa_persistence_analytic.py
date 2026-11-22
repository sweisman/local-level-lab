# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_joint_persistence import BOUNDS
from lll.esa_persistence_analytic import fit_analytic


@pytest.mark.parametrize('outside', [False, True])
def test_analytic_solver_recovers_interior_and_bound_active_optima(outside):
    target = np.array([.7, -.6, .3, -.2, .8, 1.])
    if outside:
        target[-1] = BOUNDS[-1][1]+2.
    weights = np.array([1., 2., .5, .75, 3., 1.5])
    charge, calls = [], []

    def objective(point):
        calls.append(tuple(point))
        assert len(charge) == len(calls)
        delta = point-target
        return float(delta @ (weights*delta)), 2.*weights*delta

    result = fit_analytic(objective, np.zeros(6), maximum=80, reserve=lambda: charge.append(1))
    expected = np.clip(target, *np.asarray(BOUNDS).T)
    assert result['converged']
    assert len(calls) == len(set(calls)) == result['evaluations']
    np.testing.assert_allclose(result['parameters'], expected, atol=1e-5)


def test_analytic_budget_retains_best_charged_score():
    evaluated = {}

    def objective(point):
        delta = np.asarray(point)-2.
        objective_value = float(delta@delta)
        evaluated[tuple(point)] = objective_value
        return objective_value, 2.*delta

    result = fit_analytic(objective, np.zeros(6), maximum=2, reserve=lambda: None)
    assert result['evaluations'] == len(evaluated) == 2
    assert result['parameters'] == list(min(evaluated, key=evaluated.get))
    assert result['negative_log_score'] == min(evaluated.values())
    assert not result['converged']
    assert result['status'] == 'evaluation_limit'
