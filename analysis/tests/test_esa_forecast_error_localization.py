# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_component_scale_transfer import make_case
from lll.esa_forecast_error_localization import contrast, marginal
from lll.esa_whitened_scale_transfer import whiten


def test_marginal_factors_retain_the_principal_covariance():
    native = np.array([[1., 0., 0.], [1., 1., 0.], [2., 1., 1.]])
    case = make_case(1, dict(native=native, persistent=np.ones((3, 1)),
                             maneuver=np.zeros((3, 1))), [1., 2., 3.])
    extracted = marginal(case, np.array([0, 2]))
    np.testing.assert_allclose(extracted.component_covariance[0], [[1., 2.], [2., 6.]])
    np.testing.assert_array_equal(extracted.error, [1., 3.])


@pytest.mark.parametrize('error, expected', [([3., 0., 0.], 0.), ([0., 3., 0.], 9.)])
def test_bound_distinguishes_removable_from_unexplained_error(error, expected):
    case = make_case(1, dict(native=np.eye(3), persistent=np.array([[2.], [0.], [0.]]),
                             maneuver=np.zeros((3, 1))), error)
    result = contrast(case, maximum_ratio=100.)
    assert 0. <= result['lower_bound'] <= expected
    assert result['lower_bound'] == pytest.approx(expected, abs=1e-9)


def test_marginal_lower_bound_cannot_exceed_direct_joint_score():
    rng = np.random.default_rng(44)
    native = np.tril(rng.normal(size=(12, 12))) + 3. * np.eye(12)
    added = rng.normal(size=(12, 2))
    case = make_case(1, dict(native=native, persistent=added, maneuver=added[:, ::-1]),
                     rng.normal(size=12))
    selected = marginal(case, np.array([1, 2, 4, 6, 7, 11]))
    bound = contrast(whiten(selected)[0], maximum_ratio=50.)['lower_bound']
    for a, b in [(0., 0.), (.2, 3.), (50., 50.)]:
        matrix = case.component_covariance[0] + a*case.component_covariance[1] + b*case.component_covariance[2]
        actual = case.error @ np.linalg.solve(matrix, case.error)
        assert 0. < bound <= actual
