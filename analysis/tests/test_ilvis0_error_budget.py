# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

import ilvis0_error_budget_controls as controls


def test_nonpolynomial_motion_derivatives_have_independent_finite_difference_agreement():
    t=7.;step=.01
    center=controls.motion(t);left=controls.motion(t-step);right=controls.motion(t+step)
    for position,rate,second in (('phi','p','pp'),('longitude','l','ll'),('height','h','hh')):
        assert center[rate]==pytest.approx((right[position]-left[position])/(2*step),rel=1e-6,abs=1e-10)
        assert center[second]==pytest.approx((right[position]-2*center[position]+left[position])/step**2,rel=1e-5,abs=1e-8)


@pytest.mark.parametrize('angle', (0.,.1,1.,5.,20.,90.))
def test_rotating_force_packet_integrals_match_the_closed_form(angle):
    result=controls.rotation_control(angle)
    half=math.radians(angle)/2
    expected=9.81 if half==0. else 9.81*math.sin(half)/half
    assert result['summed_vector_magnitude_mps2']==pytest.approx(expected,abs=1e-12)
    assert result['mean_packet_magnitude_mps2']>=result['summed_vector_magnitude_mps2']-1e-12
    assert result['passed'] is True


def test_gaussian_force_magnitude_has_positive_bias_without_changing_true_force():
    report=controls.noise_control(.1)
    assert report['bias_order9_mps2']>0.
    assert report['bias_order9_mps2']==pytest.approx(.1**2/9.81,rel=.01)
    assert report['passed'] is True


def test_local_screen_rejects_nonlinear_shift_and_trajectory_bias_separately():
    base=dict(linear_sigma=1.,cubature_sigma=1.,mean_shift=0.,relative_gradient_disagreement=0.)
    assert controls.approximation_screen(base,0.)['screen_passed'] is True
    assert controls.approximation_screen(dict(base,mean_shift=.2),0.)['linear_screen_passed'] is False
    assert controls.approximation_screen(base,.3)['truncation_screen_passed'] is False


def test_exact_fixture_covariance_is_positive_and_common_to_candidates():
    times=np.arange(3.)
    covariance=controls.receiver_covariance(times,1.)
    assert covariance.shape==(9,9)
    assert np.all(np.linalg.eigvalsh(covariance)>0.)
    np.testing.assert_allclose(controls.receiver_covariance(times,50.),2500*covariance,atol=1e-12)


def test_nonpolynomial_trajectory_control_preserves_every_candidate_and_call_count():
    result=controls.trajectory_control(dict(model='sphere_rotating',degree=4,half_window_s=4,noise_multiplier=1.))
    assert result['passed'] is True
    assert result['force_evaluations']==168
    assert set(result['candidates'])=={'sphere_rotating','sphere_still','flat_still'}
    assert np.linalg.norm(result['polynomial_residuals'])>0.
    assert all(r['scientific_eligible'] is False for r in result['candidates'].values())
