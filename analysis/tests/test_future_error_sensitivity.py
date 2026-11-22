# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.future_error_sensitivity import added_error_roots, resolve, spectrum


def test_spectral_score_matches_dense_covariance_and_logdet():
    cov = np.array([[2., .4], [.4, 1.]])
    y = np.array([2., 3.])
    root = np.array([[.3, 0.], [1., 2.]])
    model = spectrum(np.linalg.cholesky(cov), y, root)
    check = model.score(.75)
    enlarged = cov + .75**2 * root@root.T
    assert check['quadratic'] == pytest.approx(y@np.linalg.solve(enlarged,y))
    assert check['logdet_change'] == pytest.approx(
        np.linalg.slogdet(enlarged)[1]-np.linalg.slogdet(cov)[1])


def test_limit_without_support_is_explicit():
    model = spectrum(np.eye(2), [3., 4.], [[1.], [0.]])
    result = resolve(model, target=2., maximum_std=100.)
    assert result['status'] == 'outside_range'
    assert result['infinite_error_floor'] == pytest.approx(16.)


def test_find_smallest_reachable_common_error_scale():
    model = spectrum(np.eye(2), [3., 4.], np.eye(2))
    result = resolve(model, target=5., maximum_std=100.)
    assert result['status'] == 'reached'
    assert result['standard_deviation_m'] == pytest.approx(2.)


def test_physical_walk_starts_after_cut_and_has_unit_variance_at_last_epoch():
    roots = added_error_roots([10., 11., 14.], previous_time=9.)
    walk = roots['walk_endpoint']
    covariance = walk@walk.T
    np.testing.assert_allclose(covariance[0, [0, 3, 6]], [.2, .2, .2])
    np.testing.assert_allclose(np.diag(covariance)[-3:], np.ones(3))
