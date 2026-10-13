# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_recovery_screen as screen


@pytest.mark.parametrize('name', ['coupled_interior', 'coupled_boundary'])
def test_coupled_controls_have_known_answers_and_observed_condition_scale(name):
    problem, optimum = screen.coupled_problem(name)
    residual, jac, _ = problem.residual_tangent(optimum, 'control')
    assert np.all(abs(optimum) <= 1)
    assert residual @ residual == pytest.approx(1.)
    assert np.linalg.cond(jac) == pytest.approx(1e8, rel=1e-6)
    if name.endswith('boundary'):
        assert optimum[0] == 1. and optimum[1] == -1.


@pytest.mark.parametrize('variant', ['trf', 'dogbox'])
def test_screen_preserves_fresh_checks_and_finite_evaluation_accounting(variant):
    row = screen.run_one('boundary', 0, variant)
    assert row['passed'] and row['converged']
    assert row['evaluations'] <= 600
    assert row['observed_fit_starts'] == row['native_predictions'] == 0
    assert row['stationarity_tolerance'] == 1e-4
    assert row['scientific_decision'] == 'abstain'


def test_invalid_variant_is_not_run():
    with pytest.raises(ValueError):
        screen.run_one('boundary', 0, 'unsupported')
