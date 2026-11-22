import numpy as np
import pytest

from lll import esa_matched_force as force


def test_cubic_derivative_kernel_reproduces_constant_and_linear_acceleration():
    t = np.array([-3., -2., -.9, 0., 1.01, 2., 3.])
    _, kernel, primitive = force.acceleration_kernel(t, center=3)
    nodes, weights = np.polynomial.legendre.leggauss(2)
    u = (t[:-1, None]+t[1:, None])/2 + np.diff(t)[:, None]*nodes/2
    k = np.interp(u, t, kernel)
    assert np.sum(k*np.diff(t)[:, None]*weights/2) == pytest.approx(1.)
    assert np.sum(u*k*np.diff(t)[:, None]*weights/2) == pytest.approx(0., abs=1e-12)
    assert primitive[-1] == pytest.approx(1.)


def test_partial_packet_weights_conserve_support_and_average_magnitudes():
    gps = np.arange(5.)
    _, kernel, primitive = force.acceleration_kernel(gps, center=2)
    times = np.array([-.25, .25, 1.75, 2.25, 3.75, 4.25])
    weights = force.sample_weights(times, gps, kernel, primitive)
    assert weights.sum() == pytest.approx(1.)
    assert weights == pytest.approx(weights[::-1])
    assert np.all(weights > 0.)
    vectors = np.array([[0., 0., 9.8], [0., 0., -9.8], [9.8, 0., 0.], [0., 9.8, 0.], [0., -9.8, 0.]])
    assert weights @ np.linalg.norm(vectors, axis=1) == pytest.approx(9.8)


def test_offset_transfer_uses_only_other_windows():
    results = {'quiet': [2., 2.], 'maneuver': [2., 4.], 'later': [9., 10.]}
    transfers = force.transfer_offsets(results)
    assert transfers['later']['offset_m_s2'] == pytest.approx(2.)
    assert transfers['later']['residual_rms_m_s2'] == pytest.approx(np.sqrt((7.**2+8.**2)/2))
