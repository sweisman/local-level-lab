"""Small dense-reference gates for a future long-recording receiver likelihood."""

import numpy as np
import pytest

from lll.ilvis0_error_model import Spec,covariance


def _case():
    times=np.array([0.,.9,2.2,4.0,4.7,8.5,11.3])
    spec=Spec(white=np.diag([.09,.16,.25]),
        components=((5.,np.diag([.04,.01,.09])),),
        offset=np.diag([.01,.04,.01]),
        drift=np.diag([.04,.01,.04]),
        drift_origin_s=0.,drift_span_s=12.)
    formal=np.repeat(np.array([[[.03,.004,0.],
                                [.004,.05,0.],
                                [0.,0.,.08]]]),len(times),axis=0)
    transforms=np.array([np.diag([1e-5*(1+.01*i),
                                  1.2e-5*(1-.01*i),1.])
                         for i in range(len(times))])
    rng=np.random.default_rng(183)
    residual=rng.normal(size=3*len(times))
    jacobian=rng.normal(size=(3*len(times),4))
    return times,spec,formal,transforms,residual,jacobian


@pytest.mark.parametrize('axes',[(0,1,2),(0,1),(2,)])
def test_structured_whitening_matches_dense_marginal(axes):
    from lll.ilvis0_structured_receiver_likelihood import StructuredWhitening
    times,spec,formal,transforms,residual,jacobian=_case()
    operator=StructuredWhitening(times,spec,formal_blocks=formal,
                                 transforms=transforms,axes=axes)
    saved=operator.apply(residual,jacobian)
    dense=covariance(times,spec,transforms).copy()
    for i,block in enumerate(formal):
        dense[3*i:3*i+3,3*i:3*i+3]+=transforms[i]@block@transforms[i].T
    indices=[3*i+j for i in range(len(times)) for j in axes]
    factor=np.linalg.cholesky(dense[np.ix_(indices,indices)])
    wanted_residual=np.linalg.solve(factor,residual[indices])
    wanted_jacobian=np.linalg.solve(factor,jacobian[indices])
    np.testing.assert_allclose(saved['residual'],wanted_residual,rtol=1e-8,atol=1e-8)
    np.testing.assert_allclose(saved['jacobian'],wanted_jacobian,rtol=1e-8,atol=1e-8)
    assert saved['quadratic']==pytest.approx(wanted_residual@wanted_residual,rel=1e-8)
    assert saved['log_determinant']==pytest.approx(
        2*np.log(np.diag(factor)).sum(),rel=1e-8,abs=1e-8)


def test_structured_whitening_rejects_reversed_time_and_bad_formal_blocks():
    from lll.ilvis0_structured_receiver_likelihood import StructuredWhitening
    times,spec,formal,transforms,_,_=_case()
    with pytest.raises(ValueError):
        StructuredWhitening(times[::-1],spec,formal_blocks=formal,
                            transforms=transforms)
    bad=formal.copy();bad[0,0,0]=-1.
    with pytest.raises(ValueError):
        StructuredWhitening(times,spec,formal_blocks=bad,
                            transforms=transforms)


def test_two_correlated_ou_components_match_dense_objective():
    from lll.ilvis0_structured_receiver_likelihood import StructuredWhitening
    times=np.array([0.,.5,1.8,2.1,4.2,8.,11.,15.])
    spec=Spec(white=np.diag([.12,.08,.2]),
        components=((2.,[[.1,.025,0.],[.025,.06,0.],[0.,0.,.08]]),
                    (25.,[[.05,0.,.01],[0.,.02,0.],[.01,0.,.05]])),
        offset=np.diag([.02,.03,.02]),
        drift=np.diag([.03,.02,.04]),drift_origin_s=-2.,drift_span_s=20.)
    rng=np.random.default_rng(94)
    residual=rng.normal(size=3*len(times))
    jacobian=rng.normal(size=(3*len(times),2))
    result=StructuredWhitening(times,spec).apply(residual,jacobian)
    lower=np.linalg.cholesky(covariance(times,spec))
    np.testing.assert_allclose(result['residual'],
                               np.linalg.solve(lower,residual),rtol=1e-9,atol=1e-9)
    np.testing.assert_allclose(result['jacobian'],
                               np.linalg.solve(lower,jacobian),rtol=1e-9,atol=1e-9)


def test_receiver_likelihood_reuses_shared_innovations_operator():
    from lll.ilvis0_structured_receiver_likelihood import StructuredWhitening
    from lll.state_space_covariance import LinearInnovations
    times,spec,formal,transforms,_,_=_case()
    operator=StructuredWhitening(times,spec,formal_blocks=formal,
                                 transforms=transforms)
    assert isinstance(operator.operator,LinearInnovations)


def test_independently_generated_irregular_histories_whiten_to_unit_noise():
    from lll.ilvis0_structured_receiver_likelihood import StructuredWhitening
    times=np.array([0.,.3,1.8,4.1,4.5,7.9])
    spec=Spec(white=np.diag([.09,.16,.25]),
        components=((1.5,np.diag([.04,.02,.06])),
                    (20.,np.diag([.03,.01,.04]))),
        offset=np.diag([.02,.03,.04]),
        drift=np.diag([.01,.04,.02]),drift_origin_s=-1.,drift_span_s=10.)
    formal=np.repeat(np.array([[[.02,.005,0.],
                                [.005,.03,0.],
                                [0.,0.,.01]]]),len(times),axis=0)
    operator=StructuredWhitening(times,spec,formal_blocks=formal)
    rng=np.random.default_rng(9206)
    draws=[]
    for _ in range(1200):
        offset=rng.multivariate_normal(np.zeros(3),spec.offset)
        drift=rng.multivariate_normal(np.zeros(3),spec.drift)
        states=[rng.multivariate_normal(np.zeros(3),matrix)
                for _,matrix in spec.components]
        history=[]
        for i,t in enumerate(times):
            if i:
                for j,(tau,matrix) in enumerate(spec.components):
                    decay=np.exp(-(t-times[i-1])/tau)
                    states[j]=decay*states[j]+rng.multivariate_normal(
                        np.zeros(3),(1-decay*decay)*matrix)
            white=rng.multivariate_normal(np.zeros(3),spec.white+formal[i])
            history.extend(offset+(t-spec.drift_origin_s)/spec.drift_span_s*drift+
                           sum(states)+white)
        draws.append(operator.apply(np.array(history),
                                    np.empty((3*len(times),0)))['residual'])
    samples=np.array(draws)
    assert np.max(np.abs(samples.mean(axis=0)))<.10
    np.testing.assert_allclose(np.diag(np.cov(samples,rowvar=False)),
                               np.ones(3*len(times)),atol=.12,rtol=0)
    off_diagonal=np.cov(samples,rowvar=False)-np.diag(
        np.diag(np.cov(samples,rowvar=False)))
    assert np.max(np.abs(off_diagonal))<.18


def test_structured_objective_gradient_matches_finite_difference():
    from lll.ilvis0_structured_receiver_likelihood import StructuredWhitening
    times,spec,formal,transforms,residual,jacobian=_case()
    operator=StructuredWhitening(times,spec,formal_blocks=formal,
                                 transforms=transforms)
    base=operator.apply(residual,jacobian)
    step=1e-5
    plus=operator.apply(residual+step*jacobian[:,0],jacobian)
    minus=operator.apply(residual-step*jacobian[:,0],jacobian)
    numerical=(plus['negative_log_likelihood']-
               minus['negative_log_likelihood'])/(2*step)
    wanted=base['jacobian'][:,0]@base['residual']
    assert numerical==pytest.approx(wanted,rel=1e-8,abs=1e-6)


@pytest.mark.parametrize('tau',[0.,10.])
@pytest.mark.parametrize('axes',[(0,1,2),(0,1),(2,)])
def test_legacy_observed_law_translation_matches_dense_whitening(tau,axes):
    from lll.ilvis0_gps_sensitivity import Assumption,coordinate_covariance
    from lll.ilvis0_structured_receiver_likelihood import from_legacy_assumption
    times=np.array([2.,3.1,5.8,6.2,9.])
    lat=np.deg2rad(np.array([-61.,-61.001,-61.003,-61.004,-61.006]))
    height=np.array([900.,901.,904.,903.,905.])
    formal=np.array([[[.1+.01*i,.02,0.],[.02,.2+.01*i,.01],
                      [0.,.01,.3+.01*i]] for i in range(len(times))])
    law=Assumption('matched',(1.,2.,3.),tau,(.4,.5,.6),(.2,.3,.4))
    rng=np.random.default_rng(710)
    residual=rng.normal(size=3*len(times))
    jacobian=rng.normal(size=(3*len(times),4))
    actual=from_legacy_assumption(times,lat,height,formal,law,
                                  axes=axes).apply(residual,jacobian)
    dense=coordinate_covariance(times,lat,height,formal,law)
    indices=[3*i+j for i in range(len(times)) for j in axes]
    lower=np.linalg.cholesky(dense[np.ix_(indices,indices)])
    np.testing.assert_allclose(actual['residual'],
                               np.linalg.solve(lower,residual[indices]),
                               rtol=2e-8,atol=2e-8)
    np.testing.assert_allclose(actual['jacobian'],
                               np.linalg.solve(lower,jacobian[indices]),
                               rtol=2e-8,atol=2e-8)
