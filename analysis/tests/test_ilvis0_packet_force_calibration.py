import numpy as np
import pytest

from lll.ilvis0_packet_force_calibration import PacketMeans


def test_packet_calibration_recovers_force_even_when_directions_cancel():
    force = np.array([[10., 0., 0.], [-10., 0., 0.], [0., 10., 0.], [0., -10., 0.]])
    durations = np.array([.004, .004, .006, .006])
    gain = np.array([.03, .05, -.02])
    offset = np.array([.1, -.3, .2])
    increments = durations[:, None] * (force * (1. + gain) + offset)
    means = PacketMeans(increments, durations, [[0, 4], [1, 3]])
    values, _ = means.value_jacobian(np.r_[gain, offset])
    np.testing.assert_allclose(values, [10., 10.], rtol=1e-14)
    assert np.linalg.norm((durations[:, None] * force).sum(axis=0)) == 0.


def test_overlapping_packet_windows_match_direct_sums_and_finite_differences():
    rng = np.random.default_rng(195)
    dt = rng.uniform(.004, .006, 1600)
    increments = (rng.normal(size=(len(dt), 3)) + [1., -.2, -9.]) * dt[:, None]
    windows = np.array([[0, 100], [100, 400], [100, 505], [300, 1560], [1599, 1600]])
    means = PacketMeans(increments, dt, windows)
    point = np.array([.01, -.02, .03, .1, -.1, -.05])
    values, jac = means.value_jacobian(point)
    corrected = (increments - point[3:] * dt[:, None]) / (1. + point[:3])
    direct = [np.linalg.norm(corrected[a:b], axis=1).sum() / dt[a:b].sum() for a, b in windows]
    np.testing.assert_allclose(values, direct, rtol=1e-12)
    shifts = np.eye(6) * 1e-6
    numeric = np.array([(means.value_jacobian(point+s)[0] - means.value_jacobian(point-s)[0]) / 2e-6
                        for s in shifts]).T
    np.testing.assert_allclose(jac, numeric, rtol=1e-6, atol=1e-8)


def test_packet_calibration_rejects_fractional_windows_and_singular_parameters():
    with pytest.raises(ValueError, match='integer'):
        PacketMeans([[0., 0., .04]], [.005], [[0., 1.]])
    means = PacketMeans([[0., 0., .04]], [.005], [[0, 1]])
    with pytest.raises(ValueError, match='gain'):
        means.value_jacobian([-1., 0., 0., 0., 0., 0.])
    with pytest.raises(ValueError, match='nonzero'):
        means.value_jacobian([0., 0., 0., 0., 0., 8.])
