# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_solver_controls as controls
from lll import ilvis0_solver_verified_stop as solver


def test_exact_optimum_probe_requires_fresh_measured_evaluation():
    calls=[]; point=np.array([.3]); residual=np.array([0.,1.]); jac=np.array([[1.],[0.]])
    def evaluate(u,fresh=False):
        assert fresh; calls.append(u.copy())
        return np.r_[u-.3,1.],jac,0
    result=solver.verify_stability(point,residual,jac,evaluate)
    assert result['passed'] and len(calls)==1
    assert result['fresh_stationarity']<=1e-4


def test_stationarity_alone_cannot_validate_wrong_nonlinear_probe():
    def evaluate(u,fresh=False):
        return np.array([100.*u[0]**2+1.,0.]),np.array([[200.*u[0]],[0.]]),0
    result=solver.verify_stability(np.array([0.]),np.array([1.,0.]),
        np.array([[1e-10],[0.]]),evaluate)
    assert not result['passed']


def test_nonstationary_point_cannot_enter_probe():
    def forbidden(*args,**kwargs): raise AssertionError('no fresh call allowed')
    result=solver.verify_stability(np.array([0.]),np.array([-.3,1.]),
        np.array([[1.],[0.]]),forbidden)
    assert not result['passed'] and result['reason']=='not_stationary'


def test_probe_keeps_bound_minimum_inside_box():
    def evaluate(u,fresh=False):
        assert np.all(abs(u)<=1.)
        return np.r_[u-2.,1.],np.array([[1.],[0.]]),0
    result=solver.verify_stability(np.array([1.]),np.array([-1.,1.]),
        np.array([[1.],[0.]]),evaluate)
    assert result['passed']


@pytest.mark.parametrize('name',controls.ANALYTIC)
def test_verified_solver_recovers_known_optima_with_original_finite_budget(name):
    problem,optimum,cost,unique=controls.analytic_problem(name)
    for start in controls.starts(len(optimum),3):
        fit=solver.fit_candidate(problem,'control',start=start,maximum_evaluations=200)
        assert fit['converged'],fit['message']
        assert fit['evaluations']+2<=200
        assert abs(fit['residual_sum_squares']-cost)<=1e-7
        if unique: assert np.max(abs(np.array(fit['normalized_parameters'])-optimum))<=1e-5
        assert not fit['scientific_eligible']


def test_exhausted_budget_is_not_automatically_convergence():
    problem,_,_,_=controls.analytic_problem('interior')
    f=solver.fit_candidate(problem,'control',maximum_evaluations=6)
    assert f['evaluations']+2<=6
    assert not f['converged'] or f['stability_probe']['passed']


def test_verified_exit_is_recorded_without_inventing_scipy_success(monkeypatch):
    problem,optimum,_,_=controls.analytic_problem('interior')
    def stopped(fun,point,**kwargs):
        fun(optimum)
        raise controls.EvaluationLimit('test exhaustion')
    monkeypatch.setattr(solver,'least_squares',stopped)
    f=solver.fit_candidate(problem,'control',maximum_evaluations=6)
    assert f['converged'] and f['stopping_rule_verified']
    assert not f['solver_reported_success']
    assert f['termination']=='fresh_bounded_stability'
    assert f['evaluations']==problem.calls and f['evaluations']+2<=6


def test_unverified_exit_preserves_failure(monkeypatch):
    problem,_,_,_=controls.analytic_problem('interior')
    def stopped(fun,point,**kwargs):
        fun(point)
        raise controls.EvaluationLimit('test exhaustion')
    monkeypatch.setattr(solver,'least_squares',stopped)
    f=solver.fit_candidate(problem,'control',maximum_evaluations=6)
    assert not f['converged'] and not f['stopping_rule_verified']
    assert f['stability_probe'] is None


@pytest.mark.parametrize('name',['mixed_interior','mixed_boundary'])
def test_full_dimension_poorly_conditioned_controls(name):
    from lll import ilvis0_solver_screen as screen
    problem,optimum=screen.mixed_problem(name)
    expected=problem.residual_tangent(optimum,'reference')[0]
    for start in controls.starts(27,3):
        f=solver.fit_candidate(problem,'control',start=start)
        residual=problem.residual_tangent(np.array(f['normalized_parameters']),'control')[0]
        assert f['converged']
        assert abs(f['residual_sum_squares']-1.)<=1e-7
        assert np.linalg.norm(residual-expected)<=1e-4
        assert f['evaluations']+2<=200


def test_staged_initialization_and_counted_probe_preserve_total_allowance():
    problem,_,_,_=controls.analytic_problem('interior')
    problem.bounds.active=('attitude_x','gyro_bias_x')
    f=solver.fit_candidate(problem,'control',maximum_evaluations=80)
    assert f['initialization_evaluations']>0
    assert f['initialization_x_scale']=='jac' and f['full_stage_x_scale']==1.
    assert f['converged'] and f['evaluations']==problem.calls
    assert f['evaluations']+2<=80
