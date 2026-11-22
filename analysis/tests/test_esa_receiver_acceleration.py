import numpy as np
import pytest

from lll import esa_receiver_acceleration as accel


def test_quadratic_derivative_uses_actual_uneven_times():
    times = np.array([100., 101.01, 102., 103., 103.99, 105., 106.])
    t = times-times[3]
    velocity = np.column_stack((3.+5.*t-2.*t**2, 2.-4.*t**2, -2.+t))
    value, derivative = accel.velocity_weights(times, times[3])
    assert value@velocity == pytest.approx([3., 2., -2.], abs=1e-12)
    assert derivative@velocity == pytest.approx([5., 0., 1.], abs=1e-12)


def test_arbitrary_cross_time_sd_bound_is_attainable():
    # Perfectly anti-correlated errors have opposite signs and add in this contrast.
    weights = np.array([[1., 0., .5], [-1., 0., -.5]])
    one_covariance = np.array([[4., 0., 1.], [0., 1., 0.], [1., 0., 2.]])
    independently, any_correlation = accel.scalar_sd(weights, np.stack([one_covariance]*2))
    assert independently == pytest.approx(np.sqrt(11.))
    assert any_correlation == pytest.approx(2.*np.sqrt(5.5))


def test_corrected_force_jacobian_matches_finite_differences():
    velocity = np.array([80., 40., -.12])
    derivative = np.array([-.2, .5, .05])
    fixed = dict(latitude_rad=1.11, height_m=350., gravity_mps2=9.81)
    _, _, gradient = accel.force_and_gradient(velocity, derivative, **fixed)
    finite = [(accel.force_and_gradient(velocity+d, derivative, **fixed)[0]
               - accel.force_and_gradient(velocity-d, derivative, **fixed)[0])/(2e-3)
              for d in 1e-3*np.eye(3)]
    assert gradient == pytest.approx(finite, abs=2e-12)
