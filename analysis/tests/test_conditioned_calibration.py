# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.conditioned_calibration import conditioned_tangent
from lll.state_space_covariance import LinearInnovations


def test_earlier_forecast_minus_observation_sign_and_sensitivity_match_dense():
    operator = LinearInnovations(
        [dict(transition=[[.9]], process_loading=[[.2]], observation=[[1.]], white_loading=[[.4]])
         for _ in range(4)], epoch_count=4, state_dimension=1, observation_dimension=1,
        initial_loading=[[.6]], maximum_bytes=1000, design_is_fixed=True, error_distribution='gaussian')
    nominal = np.arange(4.)
    residual = np.array([.7, -.4])
    design = np.array([[.5, 1.], [.2, 0.], [.4, 2.], [.8, 3.]])
    cov_root = operator.unwhiten(np.eye(4))
    covariance = cov_root@cov_root.T
    bridge = np.linalg.solve(covariance[:2,:2], covariance[:2,2:]).T
    result = conditioned_tangent(operator, nominal, design, residual, training_epochs=2)
    np.testing.assert_allclose(result['mean'], nominal[2:]-bridge@residual, atol=1e-14)
    np.testing.assert_allclose(result['design'], design[2:]-bridge@design[:2], atol=1e-14)


def test_requires_earlier_residual_only():
    operator = LinearInnovations(
        [dict(transition=[[1.]], process_loading=[[.2]], observation=[[1.]], white_loading=[[.4]])
         for _ in range(4)], epoch_count=4, state_dimension=1, observation_dimension=1,
        initial_loading=None, maximum_bytes=1000, design_is_fixed=True, error_distribution='gaussian')
    with pytest.raises(ValueError, match='earlier'):
        conditioned_tangent(operator, np.zeros(4), np.zeros((4, 1)), np.zeros(4), training_epochs=2)
