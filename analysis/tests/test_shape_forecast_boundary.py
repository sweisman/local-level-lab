# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.shape_forecast_boundary import conditional_factor, marginal_factor
from lll.state_space_covariance import LinearInnovations


def test_omitted_reports_stay_unknown_in_the_forecast_covariance():
    # Each report observes a shared unit-variance offset plus independent noise.
    noise = 0.2
    count, training = 9, 2
    operator = LinearInnovations((dict(transition=[[1.]], process_loading=[[0.]],
        observation=[[1.]], white_loading=[[noise]]) for _ in range(count)),
        epoch_count=count, state_dimension=1, observation_dimension=1,
        initial_loading=[[1.]], maximum_bytes=16000, design_is_fixed=True,
        error_distribution='gaussian')
    future = conditional_factor(operator, training)
    retained = marginal_factor(future, 3)
    variance = 1. / (1. + training / noise**2)
    expected = variance * np.ones((4, 4)) + noise**2 * np.eye(4)
    np.testing.assert_allclose(retained @ retained.T, expected, atol=1e-13)
    assert not np.allclose(future[3:, 3:] @ future[3:, 3:].T, expected)
