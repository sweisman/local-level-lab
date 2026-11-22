# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer tests for carrying receiver terms into a fixed forecast."""

import numpy as np
import pytest
from scipy.fft import dct
from scipy.stats import multivariate_normal

from lll.esa_motion_innovation_scale import InnovationScore
from lll.receiver_covariance_compatibility import (
    ForecastWhitener, gaussian_score, receiver_root, replacement_capacity, replace_receiver,
)


def test_receiver_root_recovers_band_covariances_and_excludes_constant_mode():
    n = 40
    components = [np.ones((3, 3)), np.diag([1., 4., 9.]), 2*np.eye(3)]
    receiver = receiver_root(n, components)
    converted = dct(receiver.reshape(n, 3, -1), norm='ortho', axis=0).reshape(3*n, -1)
    covariance = converted @ converted.T
    expected = [np.zeros((3, 3))]+[components[0]]*4+[components[1]]*16+[components[2]]*19
    diagonal = np.zeros((3*n, 3*n))
    for index, block in enumerate(expected):
        diagonal[3*index:3*index+3, 3*index:3*index+3] = block
    np.testing.assert_allclose(covariance, diagonal, atol=2e-14)


def test_working_whitener_matches_independent_dense_covariance():
    times = [0., 1., 3.]
    weights = np.array([0., .3, .8])
    native = .2*np.eye(9)
    native[8, 0] = .025
    raw = np.arange(9.)*.01
    roots = np.arange(18.).reshape(9, 2)*.0005
    baseline = InnovationScore(np.linalg.solve(native, raw), np.linalg.solve(native, roots),
                               np.repeat(weights, 3), np.log(native.diagonal()).sum())
    parameters = np.log([1., 2., 3., .3, 1.5, 5.])
    forecast = ForecastWhitener(baseline, native, times, parameters)
    phi = (1-weights[1:])*np.exp(-np.diff(times)/1.5)+weights[1:]*np.exp(-np.diff(times)/5.)
    a, b = phi
    relationship = np.kron([[1., a, a*b], [a, 1., b], [a*b, b, 1.]], np.eye(3))
    scale = np.sqrt(np.array([1., 2., 3.])+.3*weights[:, None]).ravel()
    inner = native*scale[None, :]
    dense = inner @ relationship @ inner.T + roots @ roots.T
    transform = forecast.apply(np.eye(9))
    np.testing.assert_allclose(transform @ dense @ transform.T, np.eye(9), atol=2e-14)
    result = gaussian_score(forecast.residual, forecast.logdet)
    assert result['negative_log_score'] == pytest.approx(-multivariate_normal.logpdf(raw, cov=dense))
    assert result['quadratic'] == pytest.approx(raw @ np.linalg.solve(dense, raw))


def test_exact_receiver_capacity_and_replacement_are_not_clipped():
    root = np.diag([2., .1, .2])
    assert replacement_capacity(root) == pytest.approx((.25, -3.))
    assert replacement_capacity(np.zeros_like(root)) == (None, 1.)
    old, new = root/4., root/6.
    residual = np.array([.2, .3, -.4])
    reference = np.eye(3)-old@old.T+new@new.T
    scored = replace_receiver(residual, old, new, logdet=0.)
    assert scored['negative_log_score'] == pytest.approx(-multivariate_normal.logpdf(residual, cov=reference))
