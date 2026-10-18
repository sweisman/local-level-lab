# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import importlib.util

import numpy as np
import pytest

from lll import ilvis0_solver_boundary as old
from lll.ilvis0_boundary_controls import CONTROLS, problem_for, starts


def candidate():
    name = 'lll.ilvis0_solver_position'
    assert importlib.util.find_spec(name) is not None, 'separate position-stability solver missing'
    return importlib.import_module(name)


def meters(delta):
    return np.column_stack((delta, np.zeros((len(delta), 2))))


def verify(point, residual, jac, fresh, transform=meters):
    return candidate().verify_stability(point, residual, jac, fresh, transform)


def test_checks_actual_position_when_local_residual_gate_would_reject():
    # A stationary weakly constrained direction predicts 10 micrometres of
    # movement. The old 1e-6 residual gate rejects it despite negligible cost.
    point, residual, jac = np.array([0.]), np.array([-1e-5, 1.]), np.array([[1.], [0.]])
    calls = []
    def fresh(u, fresh=False):
        calls.append((u.copy(), fresh))
        return residual+jac@(u-point), jac, 0
    assert not old.verify_stability(point, residual, jac, fresh)['passed']
    assert not calls  # the old check rejects before an actual prediction
    result = verify(point, residual, jac, fresh)
    assert result['passed'] and result['fresh_stationarity'] <= 1e-4
    assert result['predicted_residual_step'] > 1e-6
    assert max(result['position_max_abs_neu_m']) == pytest.approx(1e-5)
    assert len(calls) == 1 and calls[0][1]


def test_large_actual_position_change_fails_even_when_cost_is_unchanged():
    residual, jac = np.array([-1e-5, 1.]), np.array([[1.], [0.]])
    def fresh(u, fresh=False):
        return np.array([1., -1e-5]), jac*0, 0
    result = verify(np.array([0.]), residual, jac, fresh)
    assert not result['passed']
    assert result['actual_cost_change'] == 0
    assert max(result['position_max_abs_neu_m']) > .01


def test_cost_increase_fails_even_with_tiny_position_change():
    residual, jac = np.array([-1e-5, 1.]), np.array([[1.], [0.]])
    result = verify(np.array([0.]), residual, jac,
                    lambda u, fresh=False: (residual*1.01, jac*0, 0),
                    lambda delta: meters(delta)*1e-6)
    assert not result['passed']
    assert result['actual_cost_change'] > 1e-8


@pytest.mark.parametrize('mode', ['rms', 'isolated_peak'])
def test_rms_and_single_epoch_limits_are_both_required(mode):
    residual, jac = np.array([-1e-5, 1.]), np.array([[1.], [0.]])
    positions = np.zeros((10000, 3))
    if mode == 'rms':
        positions[:, 1] = .002  # below the peak limit, above the RMS limit
    else:
        positions[0, 2] = .02  # below the RMS limit, above the peak limit
    result = verify(np.array([0.]), residual, jac,
                    lambda u, fresh=False: (residual, jac*0, 0), lambda delta: positions)
    assert not result['passed']


def test_fresh_stationarity_required_even_with_tiny_position_and_cost_change():
    residual, jac = np.array([-1e-5, 1.]), np.array([[1.], [0.]])
    result = verify(np.array([0.]), residual, jac,
                    lambda u, fresh=False: (residual, np.ones((2, 1)), 0))
    assert not result['passed'] and result['fresh_stationarity'] > 1e-4


def test_unwhitening_correlated_receiver_errors_matches_physical_units():
    gps = np.array([[.5, .2, 100.], [.6, .3, 150.]])
    problem = type('Problem', (), {})()
    problem.gps = gps
    problem.cholesky = np.linalg.cholesky(np.eye(6)*2+np.ones((6, 6))*.1)
    coordinates = np.array([[1e-9, -2e-9, .003], [-3e-9, 4e-9, -.002]])
    delta = np.linalg.solve(problem.cholesky, coordinates.ravel())
    result = candidate().physical_residual_step(problem, delta)
    assert result[:, 2] == pytest.approx(coordinates[:, 2])
    assert result[:, :2] == pytest.approx(coordinates[:, :2]*candidate().physical_metric(gps)[:, :2])


@pytest.mark.parametrize('name', CONTROLS)
@pytest.mark.parametrize('index', range(4))
def test_known_objectives_predictions_and_budget(name, index):
    problem, optimum, expected, unique = problem_for(name)
    original_gate = old.verify_stability
    fit = candidate().fit_candidate(problem, 'control', start=starts(len(optimum))[index],
                                    maximum_evaluations=200, physical_step=meters)
    point = np.array(fit['normalized_parameters'])
    assert fit['converged'] and fit['stability_verified']
    assert fit['residual_sum_squares'] == pytest.approx(expected, abs=1e-7, rel=0)
    assert np.linalg.norm(problem.residual(point)-problem.residual(optimum)) <= 1e-4
    if unique:
        assert point == pytest.approx(optimum, abs=1e-5)
    assert problem.calls == fit['evaluations'] <= 200
    assert fit['scientific_decision'] == 'abstain' and not fit['scientific_eligible']
    assert old.verify_stability is original_gate


def test_exhausted_nonstationary_fit_does_not_pass_new_gate():
    problem, optimum, _, _ = problem_for('exponential')
    fit = candidate().fit_candidate(problem, 'control', start=[-.8, -.8],
                                    maximum_evaluations=6, physical_step=meters)
    assert not fit['converged']
    assert problem.calls == fit['evaluations'] <= 6


def test_invalid_physical_transform_is_rejected():
    residual, jac = np.array([-1e-5, 1.]), np.array([[1.], [0.]])
    with pytest.raises(ValueError, match='physical'):
        verify(np.array([0.]), residual, jac,
               lambda u, fresh=False: (residual, jac, 0), lambda delta: np.array([np.nan]))
