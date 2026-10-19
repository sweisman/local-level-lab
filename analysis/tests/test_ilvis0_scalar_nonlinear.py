# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_scalar_nonlinear as solver
from ilvis0_scalar_nonlinear_controls import fixture,FIXTURES,STARTS


LIMITS=np.array([.15,.15,.15,.25,.25,.25,.05])


def test_analytic_derivatives_at_interior_and_near_bounds():
    rng=np.random.default_rng(928);body=rng.normal(size=(24,3))+[0.,0.,-9.81]
    force=rng.normal(size=(24,3))+[0.,0.,-9.81]
    problem=solver.Problem(body,force,LIMITS)
    for x in (np.zeros(7),np.array([.95,-.95,.8,.9,-.9,.7,-.8])):
        actual=problem.jacobian(x)
        for column in range(7):
            step=np.zeros(7);step[column]=1e-6
            expected=(problem.residual(x+step)-problem.residual(x-step))/(2e-6)
            np.testing.assert_allclose(actual[:,column],expected,atol=3e-9,rtol=1e-6)


def test_planted_constant_gain_can_fit_without_unique_parameters():
    body=np.tile([0.,0.,-9.8],(20,1));force=np.tile([0.,0.,-9.81],(20,1))
    result=solver.fit(solver.Problem(body,force,LIMITS),np.zeros(7))
    assert result['passed'] and result['rms_mps2']<1e-8
    assert len(result['point'])==7
    assert result['calls']<=402 and result['fresh_endpoint_checked']
    assert result['observed_starts']==0 and not result['global_optimum_established']


def test_low_budget_is_preserved_as_failure_without_retry():
    rng=np.random.default_rng(18);body=rng.normal(size=(20,3))+[0.,0.,-9.8]
    force=rng.normal(size=(20,3))+[0.,0.,-9.81]
    result=solver.fit(solver.Problem(body,force,LIMITS),np.zeros(7),max_evaluations=1)
    assert not result['passed'] and result['calls']<=4
    assert result['solver_status']==0 and result['fresh_endpoint_checked']


def test_projected_stationarity_treats_boundary_signs_correctly():
    assert solver.stationarity(np.array([1.,-1.]),np.array([-3.,4.]))==0.
    assert solver.stationarity(np.array([1.,-1.]),np.array([.1,-.2]))==pytest.approx(.2)


@pytest.mark.parametrize('point',[np.ones(6),np.full(7,np.nan),np.full(7,1.001)])
def test_bad_points_fail_closed(point):
    problem=solver.Problem(np.ones((5,3)),np.ones((5,3)),LIMITS)
    with pytest.raises(ValueError):problem.residual(point)


@pytest.mark.parametrize('limits',[np.zeros(7),np.ones(6),np.ones(7)])
def test_invalid_bounds_fail_closed(limits):
    with pytest.raises(ValueError):solver.Problem(np.ones((5,3)),np.ones((5,3)),limits)


def test_undefined_zero_magnitude_fails_instead_of_supplying_derivative():
    problem=solver.Problem(np.zeros((5,3)),np.ones((5,3)),LIMITS)
    with pytest.raises(ValueError,match='nonzero'):problem.jacobian(np.zeros(7))


@pytest.mark.parametrize('name',FIXTURES)
def test_independently_planted_solution_and_three_starts(name):
    body,force,planted=fixture(name);problem=solver.Problem(body,force,LIMITS)
    assert np.linalg.norm(problem.residual(planted/LIMITS))<1e-10
    results=[solver.fit(problem,start) for start in STARTS]
    assert all(r['passed'] for r in results),[(r['solver_status'],r['stationarity']) for r in results]
    assert max(r['rms_mps2'] for r in results)<=1e-7
    for left,right in zip(results,results[1:]):
        assert np.sqrt(np.mean((np.array(left['residual_mps2'])-right['residual_mps2'])**2))<=1e-7
