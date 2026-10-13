# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_solver_controls as controls
from lll import ilvis0_recovery_screen as screen
from lll import ilvis0_solver_rectangular as solver


def test_near_boundary_control_recovers_known_answer_without_looser_checks():
    # Another optimizer may also pass on a different BLAS/platform. Its failure
    # is not a requirement; known-answer recovery and fresh checks are.
    problem, optimum = screen.coupled_problem('coupled_boundary')
    start = np.where(np.arange(27) % 2 == 0, .99998, -.99998)
    result = solver.fit_candidate(problem, 'control', start=start)
    assert result['converged'] and result['stability_probe']['passed']
    actual = problem.residual_tangent(np.array(result['normalized_parameters']), 'control')[0]
    expected = problem.residual_tangent(optimum, 'control')[0]
    assert np.linalg.norm(actual-expected) <= 1e-4
    assert result['residual_sum_squares'] == pytest.approx(1., abs=1e-7, rel=0)
    assert result['stationarity_tolerance'] == 1e-4
    assert result['evaluations'] <= 600
    assert not result['scientific_eligible']


@pytest.mark.parametrize('name', controls.ANALYTIC)
def test_known_answers_from_three_starts(name):
    for start in controls.starts(2, 3):
        problem, optimum, cost, unique = controls.analytic_problem(name)
        result = solver.fit_candidate(problem, 'control', start=start)
        assert result['converged'] and result['stability_probe']['passed']
        assert result['evaluations'] == problem.calls
        assert abs(result['residual_sum_squares']-cost) <= 1e-7
        if unique:
            assert np.max(abs(np.array(result['normalized_parameters'])-optimum)) <= 1e-5
        local = result['local_linearization']
        assert len(local['jacobian'][0]) == 2
        assert local['active_parameters'] == list(problem.bounds.active)


def test_every_tangent_is_traced_and_charged():
    problem, optimum, _, _ = controls.analytic_problem('boundary')
    result = solver.fit_candidate(problem, 'control', start=np.zeros(2))
    trace = result['evaluation_trace']
    assert len(trace) == result['evaluations'] == problem.calls
    assert [r['evaluation'] for r in trace] == list(range(1, len(trace)+1))
    assert trace[-1]['fresh']
    assert all('normalized_step_norm' in r and 'improves_best_cost' in r for r in trace)


def test_unstationary_budget_failure_is_not_promoted(monkeypatch):
    problem, _, _, _ = controls.analytic_problem('interior')
    def exhausted(fun, point, **kwargs):
        fun(point)
        raise controls.EvaluationLimit('test exhaustion')
    monkeypatch.setattr(solver, 'least_squares', exhausted)
    result = solver.fit_candidate(problem, 'control', start=np.zeros(2), maximum_evaluations=6)
    assert not result['converged']
    assert result['evaluations'] <= 6


@pytest.mark.parametrize('budget', [5, 601, True, float('inf')])
def test_invalid_budget_rejected_before_evaluation(budget):
    problem, optimum, _, _ = controls.analytic_problem('interior')
    with pytest.raises(ValueError):
        solver.fit_candidate(problem, 'control', start=optimum, maximum_evaluations=budget)
    assert problem.calls == 0


@pytest.fixture(scope='module')
def value_kernel(tmp_path_factory):
    from lll import ilvis0_exploratory as explore
    return explore.load_kernel(tmp_path_factory.mktemp('rectangular-control-kernel'))[0]


@pytest.mark.parametrize('name', controls.MOTION)
def test_independent_motion_controls(name, value_kernel):
    native, model, truth, tolerance = controls.motion_problem(name, value_kernel)
    # Match the already justified software-fixture uncertainty. Archival
    # covariance and every physical truth tolerance remain unchanged.
    native.cholesky = native.cholesky.copy()*100
    for start in controls.starts(len(native.bounds.active), 2):
        problem = controls.DifferenceProblem(native, maximum_predictions=200)
        fit = solver.fit_candidate(problem, model, start=start,
                maximum_evaluations=180//(1+2*len(start)))
        assert fit['converged'] and fit['stability_probe']['passed'], fit
        assert max(abs(fit['parameters'][k]-v) for k, v in truth.items()) <= tolerance
        actual = problem.residual(np.array(fit['normalized_parameters']), model)
        exact = np.array([truth[k]/native.bounds.limits[k] for k in native.bounds.active])
        expected = problem.residual(exact, model)
        assert np.linalg.norm(native.cholesky @ (actual-expected)) <= 1e-7
        assert problem.predictions <= 200
