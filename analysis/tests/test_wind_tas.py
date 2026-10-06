# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic physical wind-triangle fixtures; no flight campaign."""
import numpy as np
import pytest

from lll.wind_tas import WindTAS,WIND_TAS_POLICY


def fixture():
    t=np.arange(0.,1801.,60.)
    psi=.4+np.arange(len(t))*.01
    speed=245.+5.*np.sin(t/1800.)
    return dict(t=t,v_n=speed*np.cos(psi),v_e=speed*np.sin(psi),psi_dot=np.full(len(t),.01/60.))


def test_exact_wind_triangle_and_airspeed_constraint():
    bins=fixture(); bins['v_n'][:]=250.; bins['v_e'][:]=0.; bins['psi_dot'][:]=0.
    model=WindTAS(bins,WIND_TAS_POLICY)
    q=np.tile([0.,25.,np.log(np.hypot(250.,25.)/250.)],len(model.knots))
    angle,rate=model.angles(q)
    np.testing.assert_allclose(angle,-np.arctan2(25.,250.),atol=1e-15)
    np.testing.assert_allclose(rate,0.,atol=1e-15)
    np.testing.assert_allclose(model.speed_constraint(q),0.,atol=1e-12)
    np.testing.assert_array_equal(model.ground,np.column_stack([bins['v_n'],bins['v_e']]))


def test_zero_wind_has_no_extra_heading_rate_on_a_turning_route():
    model=WindTAS(fixture(),WIND_TAS_POLICY)
    angle,rate=model.angles(np.zeros(model.npar))
    np.testing.assert_allclose(angle,0.,atol=1e-15)
    np.testing.assert_allclose(rate,0.,atol=1e-15)


def test_independent_wind_simulator_agrees_with_triangle():
    from lll.synth import wind_velocity
    bins=fixture(); t=bins['t']; course=np.full(len(t),.4)
    _,ground,heading=wind_velocity(course,t,250.,[15.,-25.],[4.,-2.])
    bins.update(v_n=ground[:,0],v_e=ground[:,1],psi_dot=np.zeros(len(t)))
    model=WindTAS(bins,WIND_TAS_POLICY)
    q=np.zeros((len(model.knots),3))
    q[:,:2]=[15.,-25.]+model.knots[:,None]/3600.*np.array([4.,-2.])
    angle,rate=model.angles(q.ravel())
    np.testing.assert_allclose(angle,heading-course,atol=1e-14)
    np.testing.assert_allclose(model.speed_constraint(q.ravel()),0.,atol=1e-12)
    np.testing.assert_allclose(rate[1:-1],np.gradient(heading,t)[1:-1],rtol=1e-5,atol=1e-10)


def test_nonlinear_wind_angle_rate_and_speed_jacobians():
    model=WindTAS(fixture(),WIND_TAS_POLICY)
    q=np.tile([12.,-8.,-.01],len(model.knots))
    q.reshape(-1,3)[:,0]+=model.knots/3600.*3.
    _,_,angle_j,rate_j=model.angles(q,True)
    _,speed_j=model.speed_constraint(q,True)
    for j in range(model.npar):
        step=1e-5 if j%3!=2 else 1e-6
        plus=q.copy(); minus=q.copy(); plus[j]+=step; minus[j]-=step
        a,r=model.angles(plus); b,s=model.angles(minus)
        np.testing.assert_allclose(angle_j[:,j],(a-b)/(2*step),rtol=1e-5,atol=1e-9)
        np.testing.assert_allclose(rate_j[:,j],(r-s)/(2*step),rtol=1e-5,atol=1e-10)
        np.testing.assert_allclose(speed_j[:,j],(model.speed_constraint(plus)-model.speed_constraint(minus))/(2*step),rtol=1e-5,atol=1e-8)


def test_physical_bounds_priors_and_unobserved_wind_are_explicit():
    model=WindTAS(fixture(),WIND_TAS_POLICY)
    lo,hi=model.bounds()
    assert np.all(lo<0.) and np.all(hi>0.)
    assert np.linalg.matrix_rank(model.penalty())==model.npar
    assert not model.boundary(np.zeros(model.npar))['near_boundary']
    assert model.boundary(hi)['near_boundary']
    assert 'latent' in model.report(np.zeros(model.npar))['policy']['evidence']
    bins=fixture(); bins['v_n'][:]=0.; bins['v_e'][:]=0.
    with pytest.raises(ValueError,match='cruise ground vectors'): WindTAS(bins,WIND_TAS_POLICY)


def candidate():
    from lll.inference import CandidateProblem
    from test_release060 import crab_fixture
    from test_research_candidates import settings
    bins,fwd=crab_fixture()
    return CandidateProblem(bins,fwd,lambda _:0.,np.full(3,1e-5),settings(crab_model='wind_tas',
        crab_knot_seconds=900.,wind_tas_policy=dict(WIND_TAS_POLICY),design_mode='envelope'))


def test_candidate_gyro_and_auxiliary_jacobians_match_finite_differences():
    problem=candidate(); z=np.zeros(problem.npar); z[:3]=[1.,1.,0.]
    z[problem.p:problem.p+problem.nc]=np.tile([12.,-8.,0.],len(problem.knots))
    _,J=problem.prediction(z,True); _,aux=problem.auxiliary(z,True)
    for i in range(problem.npar):
        step=1e-5; plus=z.copy(); minus=z.copy(); plus[i]+=step; minus[i]-=step
        np.testing.assert_allclose(J[:,i],(problem.prediction(plus)-problem.prediction(minus))/(2*step),rtol=1e-4,atol=1e-10)
        np.testing.assert_allclose(aux[:,i],(problem.auxiliary(plus)-problem.auxiliary(minus))/(2*step),rtol=1e-5,atol=1e-7)
    augmented,w=problem.observation_information(z,J,problem.w)
    assert len(augmented)==len(problem.y)+len(problem.bins['t']) and len(w)==len(augmented)
    assert not augmented[len(problem.y):,:3].any()


def test_bounded_free_fixed_global_and_pair_profiles_are_nested():
    from lll import models
    from lll.profile_pairs import solve_pair
    from lll.policy import MODEL_PAIRS
    p=candidate(); free=p.solve()
    lo,hi=p.bounds()
    assert free['success'] and np.all(free['z']>=lo) and np.all(free['z']<=hi)
    a=p.solve(fixed=models.EXPECTED_K['sphere_still'])
    assert free['objective']<=a['objective']+1e-6
    global_profile=p.profile(models.EXPECTED_K['sphere_still'],np.eye(3),reference=free)
    assert global_profile['success'] and free['objective']<=global_profile['objective']+1e-6
    name=next(iter(MODEL_PAIRS)); pair=solve_pair(p,name)
    endpoint=solve_pair(p,name,endpoint=0.,start=pair)
    assert pair['success'] and endpoint['success'] and pair['objective']<=endpoint['objective']+1e-6
    with pytest.raises(ValueError,match='nonlinear'): p.local(p.y,free)


def test_physical_envelope_evaluates_both_noise_levels_without_gyro_dependence():
    from lll.design_envelope import envelope_information,envelope_size
    p=candidate()
    # Retain one mount epoch/short fixture to keep the finite-grid component test small.
    p.bins['epoch']=np.zeros(len(p.bins['t']),int)
    first=envelope_information(p)
    p.bins['gyro'][:]=99.; p.w[:]=1.e-30
    second=envelope_information(p)
    assert first==second
    assert first['svd_evaluations']==envelope_size(p)
    assert first['envelope_configuration']['evaluated_noise_dph']==[3.,6.]
    assert first['envelope_configuration']['information_at_3dph_multiplier'] is None


def test_fit_options_and_boundary_gate_are_explicit():
    from lll import fit
    from lll.policy import eligibility_provenance,scientific_exclusions
    from lll.design_envelope import PHYSICAL_ENVELOPE_ASSUMPTIONS
    from test_candidate_eligibility import candidate_fit
    p=candidate()
    with pytest.raises(ValueError,match='envelope'): fit.fit(p.bins,p.fwd,p.bias_fn,np.full(3,1e-5),crab_model='wind_tas',n_boot=0)
    with pytest.raises(ValueError,match='nonlinear'): fit.fit(p.bins,p.fwd,p.bias_fn,np.full(3,1e-5),crab_model='wind_tas',design_mode='envelope',n_boot=20)
    result=candidate_fit(); config=result['inference_policy']['settings']
    config.update(crab_model='wind_tas',design_mode='envelope',wind_tas_policy=WIND_TAS_POLICY)
    result['eligibility_policy']=eligibility_provenance(True,config)
    result['design_identifiability']['assumptions']=PHYSICAL_ENVELOPE_ASSUMPTIONS
    result['wind_tas_test_near_boundary']=True
    assert any('parameter boundary' in v for v in scientific_exclusions({'fit':result}))
    from lll.policy import MODEL_PAIRS
    assert any('parameter boundary' in v for v in scientific_exclusions({'fit':result},next(iter(MODEL_PAIRS))))
    result['wind_tas_test_near_boundary']=False
    assert not scientific_exclusions({'fit':result})


def test_public_fit_integrates_physical_profiles_and_conditional_bootstrap():
    from lll import fit
    from lll.policy import MODEL_PAIRS
    p=candidate()
    result=fit.fit(p.bins,p.fwd,p.bias_fn,np.full(3,1e-5),crab_model='wind_tas',
                   design_mode='envelope',pairwise_method='profile',bootstrap_refit='nonlinear',n_boot=1,seed=7)
    assert result['inference_policy']['settings']['wind_tas_policy']==WIND_TAS_POLICY
    assert result['wind_tas']['policy']==WIND_TAS_POLICY
    assert isinstance(result['wind_tas_test_near_boundary'],bool)
    assert result['crab']['prior_sigma_deg'] is None
    assert result['bootstrap']['requested']==1 and not result['bootstrap']['bootstrap_valid']
    assert {'airspeed','airspeed_rate'} <= result['prior_sensitivity']['k_shift_sigma_by_prior'].keys()
    assert result['pairwise_profile'].keys()==MODEL_PAIRS.keys()
    for pair in result['pairwise_profile'].values():
        assert pair['bootstrap']['requested']==1
        assert not pair['bootstrap']['bootstrap_valid']
