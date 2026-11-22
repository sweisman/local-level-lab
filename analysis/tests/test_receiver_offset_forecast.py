# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer checks for time-dependent receiver offsets."""

import numpy as np
import pytest

from lll.receiver_offset_forecast import forecast, fit_candidate, predictability


def test_random_walk_variance_scales_with_elapsed_window_count():
    model = dict(law='walk', memory=None, mean=[0.]*6, covariance=np.eye(6).tolist())
    previous = np.arange(6)
    mean, covariance = forecast(model, previous, 4.)
    np.testing.assert_array_equal(mean, previous)
    np.testing.assert_allclose(covariance, 4*np.eye(6))


def test_reverting_mean_and_variance_have_stationary_limit():
    donor = [3.]*6
    model = dict(law='reverting', memory=2., mean=donor, covariance=np.eye(6).tolist())
    first = np.zeros(6)
    mean, covariance = forecast(model, first, 2.)
    np.testing.assert_allclose(mean, np.array(donor)*(1-np.exp(-1.)))
    np.testing.assert_allclose(covariance, (1-np.exp(-2.))*np.eye(6))
    np.testing.assert_allclose(forecast(model, first, 5000.)[0], donor)


def test_walk_fit_uses_elapsed_cadence_and_only_the_named_donors():
    slope = np.array([2., 0., 0., 0., 0., 0.])
    samples = np.arange(8)[:, None]*slope
    result = fit_candidate(np.arange(0, 16, 2), samples, 'walk', None)
    np.testing.assert_allclose(np.asarray(result['covariance'])[0, 0], 2.+2.e-6/6)
    h, rho = predictability('reverting', 5., np.ones(2))
    np.testing.assert_allclose(h+rho**2, np.ones(2))
    with pytest.raises(ValueError, match='positive'):
        predictability('walk', None, 0)
