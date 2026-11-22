# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.state_space_covariance import LinearInnovations


def operator(n):
    return LinearInnovations((dict(transition=[[1.]], process_loading=[[.3]],
        observation=[[1.]], white_loading=[[.4]]) for _ in range(n)),
        epoch_count=n, state_dimension=1, observation_dimension=1,
        initial_loading=[[.2]], maximum_bytes=8000, design_is_fixed=True,
        error_distribution='gaussian')


def test_smooth_decomposition_matches_independent_dense_conditioning():
    from lll.forecast_smooth_error import decompose

    cut, future = 4, 9
    t = np.arange(1., cut + future + 1)
    error = np.cos(t[cut:]) + .22 * t[cut:]**2
    covariance = .2**2 + .3**2 * np.minimum.outer(t, t) + .4**2 * np.eye(len(t))
    cross = covariance[cut:, :cut]
    conditional = covariance[cut:, cut:] - cross @ np.linalg.solve(covariance[:cut, :cut], cross.T)
    precision = np.linalg.inv(conditional)
    result = decompose(operator(len(t)), t, error[:, None], training_epochs=cut)
    assert result['total_squared_error'] == pytest.approx(error @ precision @ error)
    for degree, partition in enumerate(result['through_degree']):
        x = np.vander(t[cut:] / t[-1], N=degree + 1, increasing=True)
        beta = np.linalg.solve(x.T @ precision @ x, x.T @ precision @ error)
        remainder = error - x @ beta
        assert partition['remaining_squared_error'] == pytest.approx(remainder @ precision @ remainder)
        expected = result['total_squared_error'] - partition['remaining_squared_error']
        assert partition['smooth_squared_error'] == pytest.approx(expected)
        assert partition['smooth_dimension'] == degree + 1


def test_quadratic_physical_error_needs_no_remaining_noise():
    from lll.forecast_smooth_error import decompose

    t = np.arange(12.)
    values = t[4:, None] ** 2
    result = decompose(operator(len(t)), t, values, training_epochs=4)
    assert result['through_degree'][1]['remaining_squared_error'] > 1.
    assert result['through_degree'][2]['remaining_squared_error'] == pytest.approx(0., abs=1e-20)


def test_requires_complete_aligned_detectable_later_trajectory():
    from lll.forecast_smooth_error import decompose

    with pytest.raises(ValueError):
        decompose(operator(10), np.arange(10.), np.zeros((5, 1)), training_epochs=3)
    with pytest.raises(ValueError):
        decompose(operator(10), np.arange(10.), np.zeros((4, 1)), training_epochs=6)
