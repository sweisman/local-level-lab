# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_solver_controls as controls
from lll import ilvis0_solver_recovery as recovery


@pytest.mark.parametrize('name', controls.ANALYTIC)
@pytest.mark.parametrize('scale', ['jac', 1.0])
def test_known_answers_and_repeatability(name, scale):
    problem, optimum, cost, unique = controls.analytic_problem(name)
    predictions = []
    for start in controls.starts(len(optimum), 3):
        before = problem.calls
        fit = recovery.fit_candidate(problem, 'control', start=start,
                                     maximum_evaluations=600, x_scale=scale)
        assert fit['converged'], fit
        assert fit['evaluations'] == problem.calls - before
        assert fit['evaluations'] <= 600
        assert abs(fit['residual_sum_squares'] - cost) <= 1e-7
        point = np.array(fit['normalized_parameters'])
        if unique:
            assert np.max(abs(point - optimum)) <= 1e-5
        predictions.append(problem.residual_tangent(point, 'control')[0])
        assert not fit['scientific_eligible']
        assert fit['stationarity_tolerance'] == 1e-4
    assert all(np.linalg.norm(p - predictions[0]) <= 1e-4 for p in predictions)


@pytest.mark.parametrize('name', ['mixed_interior', 'mixed_boundary'])
def test_full_dimension_weak_directions(name):
    from lll import ilvis0_solver_screen as screen
    problem, optimum = screen.mixed_problem(name)
    expected = problem.residual_tangent(optimum, 'control')[0]
    for start in controls.starts(27, 3):
        fit = recovery.fit_candidate(problem, 'control', start=start)
        actual = problem.residual_tangent(np.array(fit['normalized_parameters']), 'control')[0]
        assert fit['converged']
        assert np.linalg.norm(actual - expected) <= 1e-4


def test_budget_exhaustion_alone_remains_failure(monkeypatch):
    problem, _, _, _ = controls.analytic_problem('interior')
    def exhausted(fun, point, **kwargs):
        fun(point)
        raise controls.EvaluationLimit('test exhaustion')
    monkeypatch.setattr(recovery, 'least_squares', exhausted)
    result = recovery.fit_candidate(problem, 'control', start=np.zeros(2), maximum_evaluations=6)
    assert not result['converged']
    assert result['evaluations'] == problem.calls <= 6


def test_stationary_exact_solution_requires_fresh_stability(monkeypatch):
    problem, optimum, _, _ = controls.analytic_problem('interior')
    def exhausted(fun, point, **kwargs):
        fun(optimum)
        raise controls.EvaluationLimit('test exhaustion')
    monkeypatch.setattr(recovery, 'least_squares', exhausted)
    result = recovery.fit_candidate(problem, 'control', start=optimum, maximum_evaluations=6)
    assert result['converged'] and result['stability_probe']['passed']
    assert not result['solver_reported_success']
    assert result['evaluations'] == problem.calls <= 6


@pytest.mark.parametrize('budget', [0, 5, 601, float('inf'), True])
def test_reject_unfrozen_budget(budget):
    problem, optimum, _, _ = controls.analytic_problem('interior')
    with pytest.raises(ValueError):
        recovery.fit_candidate(problem, 'control', start=optimum, maximum_evaluations=budget)
    assert problem.calls == 0


def test_requires_explicit_feasible_warm_start():
    problem, _, _, _ = controls.analytic_problem('interior')
    for start in (None, np.ones(2) * 2, np.array([np.nan, 0]), np.zeros(3)):
        with pytest.raises(ValueError):
            recovery.fit_candidate(problem, 'control', start=start)
    assert problem.calls == 0


@pytest.fixture(scope='module')
def value_kernel(tmp_path_factory):
    from lll import ilvis0_exploratory as explore
    return explore.load_kernel(tmp_path_factory.mktemp('recovery-control-kernel'))[0]


@pytest.mark.parametrize('name', controls.MOTION)
def test_independent_increments_and_receiver_controls(name, value_kernel):
    native, model, truth, tolerance = controls.motion_problem(name, value_kernel)
    # These fixtures originally whiten at millimetre scale. Their independent
    # finite differences cannot certify nanometre prediction stability. Use
    # 0.1 m-scale control uncertainties; physical answer tolerances stay fixed.
    # This changes only software fixtures, never the archived fit covariance.
    native.cholesky = native.cholesky.copy() * 100
    for start in controls.starts(len(native.bounds.active), 2):
        p = controls.DifferenceProblem(native, maximum_predictions=200)
        fit = recovery.fit_candidate(p, model, start=start,
                                     maximum_evaluations=180 // (1 + 2 * len(start)))
        assert fit['converged'], fit
        point = np.array(fit['normalized_parameters'])
        actual = p.residual(point, model)
        optimum = np.array([truth[k] / native.bounds.limits[k] for k in native.bounds.active])
        expected = p.residual(optimum, model)
        assert fit['residual_sum_squares'] <= float(expected @ expected) + 1e-7
        assert max(abs(fit['parameters'][k] - v) for k, v in truth.items()) <= tolerance
        assert np.linalg.norm(native.cholesky @ (actual - expected)) <= 1e-7
        assert p.predictions <= 200


def test_floating_point_limited_control_is_not_falsely_certified(value_kernel):
    native, model, _, _ = controls.motion_problem('bias', value_kernel)
    p = controls.DifferenceProblem(native)
    fit = recovery.fit_candidate(p, model, start=np.zeros(1), maximum_evaluations=60)
    assert fit['solver_reported_success'] and not fit['converged']
    assert fit['stability_probe']['reason'] == 'fresh_probe_not_stable'
