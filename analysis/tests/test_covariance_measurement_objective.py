# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

import covariance_measurement_objective as objective


def test_whitening_matches_full_inverse_with_shared_cross_terms():
    C=np.array([[4.,1.5],[1.5,1.]])
    r=np.array([2.,-.7]);J=np.array([[1.,2.],[3.,4.]])
    W=objective.FrozenWhitening(C)
    assert W.apply(r)@W.apply(r)==pytest.approx(r@np.linalg.solve(C,r))
    assert W.apply(J).T@W.apply(J)==pytest.approx(J.T@np.linalg.solve(C,J))
    assert abs(r@np.linalg.solve(C,r)-np.sum(r*r/np.diag(C)))>.1
    assert W.logdet==pytest.approx(np.linalg.slogdet(C)[1])


def test_units_change_normalization_but_not_quadratic_or_parameter_information():
    C=np.array([[4.,.3],[.3,1.]])
    r=np.array([2.,-.7]);scale=np.array([1e6,1e-3])
    before=objective.FrozenWhitening(C);after=objective.FrozenWhitening(C*scale[:,None]*scale[None,:])
    assert np.sum(after.apply(r*scale)**2)==pytest.approx(np.sum(before.apply(r)**2))
    assert after.logdet-before.logdet==pytest.approx(2*np.log(scale).sum())


@pytest.mark.parametrize('C',[np.array([[1.,1.],[1.,1.]]),np.array([[1.,2.],[2.,1.]]),np.array([[1.,.4],[.2,1.]]),np.array([[np.nan]])])
def test_bad_covariance_is_rejected_without_regularization(C):
    with pytest.raises(ValueError):objective.FrozenWhitening(C)


def test_gls_response_matches_closed_form_penalized_solution_and_covariance():
    C=np.array([[4.,.7],[.7,1.]])
    G=np.array([[-2.],[3.]]);P=np.array([[.5]]);W=objective.FrozenWhitening(C)
    response,residual,curvature=objective.local_response(G,P,W)
    normal=G.T@np.linalg.solve(C,G)+P.T@P
    expected=-np.linalg.solve(normal,G.T@np.linalg.inv(C))
    assert response==pytest.approx(expected)
    assert residual==pytest.approx(np.eye(2)+G@expected)
    assert curvature==pytest.approx(np.linalg.inv(normal))
    # Deterministic penalties make sampling covariance distinct from curvature.
    assert not np.allclose(response@C@response.T,curvature,rtol=1e-5,atol=1e-10)


def test_complete_objective_signs_and_jacobian_match_direct_perturbation():
    from test_continuous_measurement_motion import equation_fixture
    eq,z,_=equation_fixture('wind_tas');n=len(eq.residual(z))+len(eq.auxiliary(z))
    C=np.eye(n);C[0,-1]=C[-1,0]=.4
    working=objective.FrozenCovarianceObjective(eq,C)
    J=working.jacobian(z);direction=np.linspace(-.01,.01,len(z))
    step=1e-4
    direct=(working.residual(z+step*direction)-working.residual(z-step*direction))/(2*step)
    assert J@direction==pytest.approx(direct,rel=2e-3,abs=1e-8)
    scores=working.scores(z)
    assert scores['penalized_least_squares']==pytest.approx(np.sum(working.residual(z)**2))
    assert working.raw_jacobian(z)[:len(eq.residual(z))]==pytest.approx(-eq.parameter_jacobian(z))
