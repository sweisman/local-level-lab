# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_solver_controls as controls


@pytest.mark.parametrize('name', ['interior', 'boundary', 'redundant', 'scaled', 'nonlinear', 'gain_offset'])
def test_known_control_optimum_is_independent_and_stationary(name):
    p, optimum, expected, unique = controls.analytic_problem(name)
    r, j, _ = p.residual_tangent(optimum, 'control')
    assert r@r == pytest.approx(expected, abs=1e-10)
    gradient = j.T@r
    inward = gradient.copy()
    inward[(optimum >= 1)&(gradient < 0)] = 0
    assert np.max(abs(inward)) < 1e-8
    assert p.calls == 1


def test_short_globe_controls_are_generated_without_prediction_kernel():
    for name in ('stationary_rotating', 'stationary_still', 'east_rotating', 'east_still'):
        p, model, truth, tolerance = controls.globe_problem(name, kernel=None)
        assert len(p.dt) == 200
        assert p.gps.shape == (7, 3)
        assert p.bounds.active == ('accel_bias_x',)
        assert truth == {'accel_bias_x': .04}
        if name.startswith('stationary'):
            assert np.all(p.gps == p.gps[0])
        else:
            assert np.all(np.diff(p.gps[:, 1]) > 0)
        assert np.any(p.theta != 0) == (name != 'stationary_still')


@pytest.mark.parametrize('name', ['bias', 'effective_orientation', 'gain', 'timing'])
def test_existing_analytic_motion_controls_keep_explicit_processing_hypothesis(name):
    p, model, truth, tolerance = controls.motion_problem(name, kernel=None)
    assert model == 'flat_still'
    assert len(p.dt) == 200
    assert truth and tolerance > 0


def test_finite_difference_adapter_counts_every_prediction_and_checks_allowance():
    class Problem:
        bounds = controls.ControlBounds(2)
        def residual(self, u, model):
            return np.asarray(u)*2
    p = controls.DifferenceProblem(Problem(), maximum_predictions=5)
    residual, jac, _ = p.residual_tangent(np.array([1., 0.]), 'control')
    assert np.allclose(jac, np.eye(2)*2)
    assert p.predictions == 5
    with pytest.raises(controls.EvaluationLimit):
        p.residual_tangent(np.zeros(2), 'control')
    assert p.predictions == 5


def test_control_start_list_has_fixed_size_and_deterministic_randomness():
    assert len(controls.identities()) == 34
    assert len(set(controls.identities())) == 34
    assert np.array_equal(controls.starts(2, 3), controls.starts(2, 3))


def test_known_interior_recovery_counts_calls_and_does_not_claim_sensor_qualification():
    result = controls.run_one('interior', 0)
    assert result['passed']
    assert result['actual_evaluations'] == result['fit']['evaluations'] <= 200
    assert result['observed_fit_starts'] == 0
    assert result['scientific_decision'] == 'abstain'
    assert result['independent_archive_confirmation'] is False
