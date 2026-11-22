import numpy as np
import pytest

from lll.ilvis0_gyro_free_packet_fit import PacketForceProblem, continuous_gap_upper
from lll.ilvis0_packet_force_calibration import PacketMeans


def test_quadrature_fit_jacobian_includes_gravity_and_retains_off_diagonal_covariance():
    means = PacketMeans([[.01, .02, .04], [.02, .01, .04], [.01, -.02, .04]],
                       [.004, .006, .005], [[0, 2], [1, 3]])
    target = np.array([[[.3, .2, -9.8], [.1, .2, -10.]], [[.2, .3, -9.7], [.2, .1, -10.1]]])
    law = np.array([[.4, .2], [.2, .5]])
    limits = [.1, .1, .1, .2, .2, .2, .2]
    problem = PacketForceProblem(means, target, [.4, .6], limits, law)
    point = np.array([.1, -.1, .2, -.1, .2, .1, -.1])
    residual = problem.residual(point)
    assert residual @ residual == pytest.approx(problem.raw_residual(point) @ np.linalg.solve(law, problem.raw_residual(point)))
    shifts = np.eye(7)*1e-6
    direct = np.array([(problem.residual(point+s)-problem.residual(point-s))/2e-6 for s in shifts]).T
    np.testing.assert_allclose(problem.jacobian(point), direct, rtol=1e-6, atol=1e-8)


def test_continuous_gap_bound_encloses_a_rotating_force_with_exact_packet_average():
    duration = np.array([.005, .0075, .005])
    angular_speed = np.array([.02, .5, 10.])
    norm = 9.81
    # Evaluate 1-sinc directly so subtracting near-equal force magnitudes does not round away the gap.
    squared_angle = (angular_speed*duration/2.)**2
    gap = norm*squared_angle*(1./6.+squared_angle*(-1./120.+squared_angle*(1./5040.-squared_angle/362880.)))
    packet_norm = np.nextafter(norm-gap, 0.)
    upper = continuous_gap_upper(duration, norm*angular_speed, packet_norm)
    assert np.all(upper >= gap)
    assert np.all(upper <= 1.001*gap)
    assert continuous_gap_upper(.005, 0., 0.) == 0.
    assert continuous_gap_upper(.005, 1., 0.) == pytest.approx(.005/np.sqrt(12.))
    with pytest.raises(ValueError, match='nonnegative'):
        continuous_gap_upper(.005, 1., -1.)
