"""Known-answer joint receiver-error propagation for the gyro-free scalar."""

import numpy as np
import pytest


def _stationary_case():
    jets = np.array([[.3, .5, 1000., 0., 0., 0., 0., 0., 0.],
                     [.3, .5, 1000., 0., 0., 0., 0., 0., 0.]])
    weights = np.zeros((2, 9, 12))
    for row, indices in enumerate(((0, 1, 2), (1, 2, 3))):
        for index, coefficient in zip(indices, (1., -2., 1.)):
            weights[row, 8, 3*index+2] = coefficient
    covariance = np.eye(12)*.04
    return jets, weights, covariance


@pytest.mark.parametrize('model', ['sphere_rotating', 'sphere_still', 'flat_still'])
def test_stationary_force_covariance_keeps_shared_receiver_error(model):
    from lll.ilvis0_force_magnitude_covariance import propagate
    jets, weights, covariance = _stationary_case()
    result = propagate(jets, weights, covariance, model=model,
                       background_rate_rads=7.292115e-5 if model == 'sphere_rotating' else 0.,
                       gravity_mps2=9.8, disc_radius_m=6371000.)
    np.testing.assert_allclose(result['gradient'][:, 8], [1., 1.], atol=1e-8)
    np.testing.assert_allclose(result['conditional_covariance_mps4'],
                               .04*np.array([[6., -4.], [-4., 6.]]), atol=1e-8)
    assert result['receiver_covariance_calibrated'] is False
    assert result['gyro_observations_used'] is False
    assert result['scientific_decision'] == 'abstain'


def test_force_covariance_rejects_changed_joint_support_and_invalid_covariance():
    from lll.ilvis0_force_magnitude_covariance import propagate
    jets, weights, covariance = _stationary_case()
    with pytest.raises(ValueError, match='joint'):
        propagate(jets, weights[:, :, :-1], covariance, model='sphere_still',
                  background_rate_rads=0., gravity_mps2=9.8,
                  disc_radius_m=6371000.)
    covariance[0, 0] = -1.
    with pytest.raises(ValueError, match='positive definite'):
        propagate(jets, weights, covariance, model='sphere_still',
                  background_rate_rads=0., gravity_mps2=9.8,
                  disc_radius_m=6371000.)


def test_force_covariance_accepts_overlapping_local_polynomial_operators():
    from lll.ilvis0_force_magnitude_covariance import propagate
    from lll.ilvis0_receiver_derivatives import LocalPolynomial
    times = np.arange(5., dtype=float)
    covariance = np.eye(15)*.04
    weights = np.zeros((2, 9, 15))
    for index, first in enumerate((0, 1)):
        operator = LocalPolynomial(times[first:first+4], times[first+2],
                                   covariance[3*first:3*(first+4),
                                              3*first:3*(first+4)],
                                   degree=2, maximum_gap_s=1.)
        weights[index, :, 3*first:3*(first+4)] = operator.weights
    jets = np.repeat([[.3, .5, 1000., 0., 0., 0., 0., 0., 0.]], 2, axis=0)
    result = propagate(jets, weights, covariance, model='sphere_still',
                       background_rate_rads=0., gravity_mps2=9.8,
                       disc_radius_m=6371000.)
    expected = .04*(weights[:, 8, :]@weights[:, 8, :].T)
    np.testing.assert_allclose(result['conditional_covariance_mps4'],
                               expected, atol=1e-8)
    assert abs(result['conditional_covariance_mps4'][0, 1]) > 0.


def test_moving_northward_force_gradient_distinguishes_sphere_and_disc():
    from lll.ilvis0_force_magnitude_covariance import propagate
    from lll.models import WGS84_A, WGS84_E2
    p = 1e-5
    jet = np.array([[0., 0., 0., p, 0., 0., 0., 0., 0.]])
    weights = np.zeros((1, 9, 3))
    kwargs = dict(background_rate_rads=0., gravity_mps2=9.8,
                  disc_radius_m=6371000.)
    sphere = propagate(jet, weights, np.eye(3), model='sphere_still', **kwargs)
    disc = propagate(jet, weights, np.eye(3), model='flat_still', **kwargs)
    meridian_at_equator = WGS84_A*(1.-WGS84_E2)
    np.testing.assert_allclose(sphere['gradient'][0, 3],
                               -2.*meridian_at_equator*p, atol=1e-5)
    np.testing.assert_allclose(disc['gradient'][0, 3], 0., atol=1e-6)


def test_zero_required_force_abstains_from_magnitude_linearization():
    from lll.ilvis0_force_magnitude_covariance import propagate
    jet = np.array([[0., 0., 0., 0., 0., 0., 0., 0., -9.8]])
    with pytest.raises(ValueError, match='near-zero'):
        propagate(jet, np.zeros((1, 9, 3)), np.eye(3),
                  model='sphere_still', background_rate_rads=0.,
                  gravity_mps2=9.8, disc_radius_m=6371000.)


def test_joint_linearization_matches_small_correlated_receiver_perturbations():
    """An independent nonlinear replay checks both variances and shared error."""
    from lll.ilvis0_force_magnitude_covariance import propagate
    from lll.ilvis0_receiver_force import evaluate
    jets = np.array([
        [.4, .1, 1000., 1.2e-5, 8e-6, .02, 2e-8, -1e-8, .15],
        [.4, .1, 1000., 1.1e-5, 9e-6, .01, -1e-8, 2e-8, -.12]])
    scale = np.array([1e-7, 1e-7, .1, 1e-8, 1e-8, .005,
                      1e-9, 1e-9, .01])
    within = np.diag(scale**2)
    covariance = np.block([[within, .4*within], [.4*within, within]])
    weights = np.zeros((2, 9, 18))
    weights[0, :, :9] = np.eye(9)
    weights[1, :, 9:] = np.eye(9)
    result = propagate(jets, weights, covariance, model='sphere_rotating',
                       background_rate_rads=7.292115e-5,
                       gravity_mps2=9.8, disc_radius_m=6371000.)
    rng = np.random.default_rng(2187)
    perturbations = rng.multivariate_normal(np.zeros(18), covariance, size=2048)
    actual = np.empty((len(perturbations), 2))
    for index, perturbation in enumerate(perturbations):
        for row in range(2):
            shifted = jets[row] + perturbation[9*row:9*(row+1)]
            predicted = evaluate(shifted[:3], shifted[3:6], shifted[6:9],
                                 model='sphere_rotating',
                                 background_rate_rads=7.292115e-5,
                                 gravity_mps2=9.8,
                                 disc_radius_m=6371000.)
            actual[index, row] = np.linalg.norm(predicted['specific_force_ned_mps2'])
    empirical = np.cov(actual.T)
    np.testing.assert_allclose(empirical, result['conditional_covariance_mps4'],
                               rtol=.12, atol=1e-6)
