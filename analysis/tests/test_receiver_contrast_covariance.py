# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer checks for estimating covariance from receiver differences."""

import numpy as np
import pytest
from scipy.stats import multivariate_normal

from lll.receiver_contrast_covariance import contrast_covariances, gaussian_loss, split_bands


def test_separate_receiver_matrices_recover_exact_independent_components():
    air1 = np.diag([1., 2., 3.])
    mosaic = np.array([[3., 1., 0.], [1., 3., .3], [0., .3, 3.]])
    pwrpak = np.diag([2., 4., 7.])
    original = np.block([[air1+mosaic, air1], [air1, air1+pwrpak]])
    estimate = contrast_covariances(original)
    np.testing.assert_allclose(estimate['independent'], estimate['unrestricted'], rtol=0., atol=5e-15)
    np.testing.assert_allclose(estimate['raw_components'], [air1, mosaic, pwrpak])


def test_invalid_components_are_recorded_and_structured_score_stays_finite():
    symmetric = np.eye(3)
    cross = np.diag([-.65, .1, .3])
    covariance = np.block([[symmetric, cross], [cross, symmetric]])
    estimate = contrast_covariances(covariance)
    assert estimate['raw_eigenvalues'][0, 0] == pytest.approx(-.65)
    assert estimate['independent'][0, 3] == pytest.approx(0.)
    samples = np.arange(18).reshape(3, 6)/5
    for law in ('independent', 'unrestricted', 'isotropic'):
        model = estimate[law]
        expected = -multivariate_normal.logpdf(samples, cov=model).sum()
        assert gaussian_loss(samples, model) == pytest.approx(expected)


def test_cosine_band_partition_preserves_dc_free_energy():
    n = 120
    samples = np.cos(np.pi*(np.arange(n)+.5)*8/n)[:, None]*np.arange(1., 7.)
    bands, constant = split_bands(samples, np.arange(n))
    assert [len(part) for part in bands] == [12, 48, 59]
    np.testing.assert_allclose(constant, np.zeros(6), atol=1e-12)
    assert np.linalg.norm(bands[0]) == pytest.approx(np.linalg.norm(samples))
    assert np.linalg.norm(np.vstack(bands[1:])) < 1e-12
    with pytest.raises(ValueError, match='cadence'):
        split_bands(samples, np.arange(n)*.5)
