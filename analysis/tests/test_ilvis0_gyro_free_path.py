"""Constructive controls for a missing gyro stream over a force history."""

import numpy as np
import pytest

from lll.ilvis0_gyro_free_path import attitude_histories


def test_two_distinct_attitude_histories_fit_the_same_force_history():
    body = np.array([[0., 0., -9.8], [.1, 0., -9.8],
                     [.1, .2, -9.8], [0., .2, -9.8]])
    required = np.array([[0., 0., -9.8], [0., .1, -9.8],
                         [-.2, .1, -9.8], [-.2, 0., -9.8]])
    required *= np.linalg.norm(body, axis=1)[:, None]/np.linalg.norm(
        required, axis=1)[:, None]
    base = attitude_histories(body, required, np.zeros(4))
    twisted = attitude_histories(body, required, [.0, .2, .4, .6])
    for path in (base, twisted):
        np.testing.assert_allclose(np.einsum('nij,nj->ni', path, body),
                                   required, atol=1e-12)
        np.testing.assert_allclose(path @ path.transpose(0, 2, 1),
                                   np.broadcast_to(np.eye(3), (4, 3, 3)),
                                   atol=1e-12)
        np.testing.assert_allclose(np.linalg.det(path), 1., atol=1e-12)
    assert np.linalg.norm(base[3]-twisted[3]) > .1
    assert np.linalg.norm((base[3]@base[2].T)-
                          (twisted[3]@twisted[2].T)) > .1


def test_antiparallel_force_is_supported_without_gyro():
    body = np.array([[0., 0., -1.], [0., 0., -1.]])
    required = np.array([[0., 0., -1.], [0., 0., 1.]])
    path = attitude_histories(body, required, [0., 0.])
    np.testing.assert_allclose(np.einsum('nij,nj->ni', path, body),
                               required, atol=1e-12)


def test_magnitude_mismatch_and_bad_twist_fail_closed():
    body = np.array([[0., 0., -9.8], [0., 0., -9.8]])
    required = np.array([[0., 0., -9.8], [0., 0., -9.7]])
    with pytest.raises(ValueError):
        attitude_histories(body, required, [0., 0.])
    with pytest.raises(ValueError):
        attitude_histories(body, body, [0., float('nan')])
