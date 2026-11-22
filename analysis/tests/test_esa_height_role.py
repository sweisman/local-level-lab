# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_height_role import Z95, band_diagnostic, partition_scores


def test_horizontal_marginal_uses_cross_time_covariance_and_excludes_height():
    lower = np.array([[2., 0., 0., 0., 0., 0.],
                      [.4, 1., 0., 0., 0., 0.],
                      [.5, .3, 2., 0., 0., 0.],
                      [.1, .3, .6, 1.8, 0., 0.],
                      [.2, .1, .4, .5, 1., 0.],
                      [.6, .4, .3, .2, .3, 1.]])
    errors = np.tile([2., 1.5, 3., 3.5, 2., 1.], (2, 1)).T
    errors[[2, 5], 1] += 8.
    horizontal = [0, 1, 3, 4]
    observed = partition_scores(lower, errors)
    covariance = lower @ lower.T
    h = errors[horizontal]
    total = np.sum(errors * np.linalg.solve(covariance, errors), axis=0)
    marginal = np.sum(h * np.linalg.solve(covariance[np.ix_(horizontal, horizontal)], h), axis=0)
    np.testing.assert_allclose(observed['full'], total)
    np.testing.assert_allclose(observed['horizontal'], marginal)
    np.testing.assert_allclose(observed['horizontal'][0], observed['horizontal'][1])
    np.testing.assert_allclose(observed['height_given_horizontal'], total-marginal)


def test_mean_comparison_reuses_same_width_without_moving_forecasts():
    result = band_diagnostic([0., 3., 0., 4.], [1., 0., 2., 3.], [0.]*4, [1.1/Z95]*4)
    assert result['raw_inside'] == 2
    assert result['adjusted_inside'] == 2
    assert result['entered'] == result['left'] == 1
    assert result['squared_error_change_m2'] == pytest.approx(-11.)


def test_invalid_band_scale_fails_closed():
    with pytest.raises(ValueError, match='positive'):
        band_diagnostic([0.], [0.], [0.], [0.])
