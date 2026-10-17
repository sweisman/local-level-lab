# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import importlib.util

import numpy as np
import pytest


def controls():
    name = 'lll.ilvis0_boundary_controls'
    assert importlib.util.find_spec(name) is not None, 'fixed nonlinear control matrix is missing'
    return importlib.import_module(name)


@pytest.mark.parametrize('name', ['curved_boundary', 'exponential', 'curved_redundant', 'nonlinear27'])
def test_control_exact_derivatives_and_known_reference(name):
    problem, optimum, cost, _ = controls().problem_for(name)
    point = np.linspace(-.4, .4, len(optimum))
    residual, jac, _ = problem.residual_tangent(point, 'control')
    difference = np.empty_like(jac)
    for i in range(len(point)):
        delta = np.zeros_like(point)
        delta[i] = 1e-5
        a = problem.residual_tangent(point+delta, 'control')[0]
        b = problem.residual_tangent(point-delta, 'control')[0]
        difference[:, i] = (a-b)/(2e-5)
    np.testing.assert_allclose(jac, difference, rtol=1e-6, atol=1e-6)
    answer, _, _ = problem.residual_tangent(optimum, 'control')
    assert float(answer@answer) == pytest.approx(cost, abs=1e-10)
    assert residual.shape == answer.shape


def test_screen_records_real_evaluations_and_independent_answer():
    result = controls().run_one('curved_boundary', 3, 'boundary_bvls')
    assert result['passed']
    assert result['actual_evaluations'] == result['fit']['evaluations'] <= 200
    assert result['prediction_error'] <= 1e-4
    assert result['observed_fit_starts'] == 0
    assert result['scientific_decision'] == 'abstain'


def test_fixed_starts_are_feasible_and_reproducible():
    matrix = controls()
    for n in (2, 27):
        first, second = matrix.starts(n), matrix.starts(n)
        assert len(first) == 4
        for a, b in zip(first, second):
            np.testing.assert_array_equal(a, b)
            assert np.all(abs(a) <= 1)
        assert np.all(1-abs(first[3]) > 0)
        assert np.all(1-abs(first[3]) <= 1e-12)
