# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
from scipy.stats import f

from lll.calibrated_joint_path import prepare, score
from lll.state_space_covariance import LinearInnovations


def _operator(n):
    identity = np.eye(1)
    return LinearInnovations((dict(transition=identity, process_loading=.3*identity,
        observation=identity, white_loading=.4*identity) for _ in range(n)),
        epoch_count=n, state_dimension=1, observation_dimension=1, initial_loading=.2*identity,
        maximum_bytes=10000, design_is_fixed=True, error_distribution='gaussian')


def test_joint_gls_and_training_scale_match_independent_dense_forecast():
    n, cut = 9, 5
    times = np.arange(1., n+1)
    design = np.column_stack((np.ones(n), times/3.))
    y = np.array([1., 2.2, 1.3, 3.5, 2., 4.6, 6.1, 3.1, 5.])
    covariance = .2**2+.3**2*np.minimum.outer(times,times)+.4**2*np.eye(n)
    earlier = covariance[:cut,:cut]
    k = np.linalg.solve(earlier, covariance[:cut,cut:]).T
    x, z = design[:cut], design[cut:]-k@design[:cut]
    coefficient_covariance = np.linalg.inv(x.T @ np.linalg.solve(earlier,x))
    beta = coefficient_covariance @ x.T @ np.linalg.solve(earlier,y[:cut])
    expected = k@y[:cut]+z@beta
    joint = covariance[cut:,cut:]-k@covariance[:cut,cut:]+z@coefficient_covariance@z.T
    residual = y[:cut]-x@beta
    scale = residual@np.linalg.solve(earlier,residual)/(cut-2)
    delta = y[cut:]-expected
    square = delta@np.linalg.solve(joint,delta)
    operator = _operator(n)
    forecast = prepare(operator, design, y[:cut], training_epochs=cut, parameter_scales=[1.,1.])
    np.testing.assert_allclose(forecast['mean'].ravel(),expected)
    answer = score(operator, forecast, y[cut:])
    np.testing.assert_allclose(answer['conditional_log_determinant'],np.linalg.slogdet(joint)[1])
    np.testing.assert_allclose(answer['squared_standardized_error'],square)
    np.testing.assert_allclose(answer['training_variance_scale_estimate'],scale)
    np.testing.assert_allclose(answer['estimated_scale_f_statistic'],square/((n-cut)*scale))
    np.testing.assert_allclose(answer['estimated_scale_reference_band'],f.ppf([.025,.975],n-cut,cut-2))


def test_future_sensitive_training_null_direction_remains_unidentifiable():
    operator = _operator(6)
    design = np.column_stack((np.ones(6),[0.,0.,0.,0.,1.,2.]))
    forecast = prepare(operator, design, [3.,4.,3.,1.],training_epochs=4,parameter_scales=[1.,1.])
    assert forecast['status'] == 'unidentifiable'
    assert score(operator,forecast,[1.,2.])['status'] == 'unidentifiable'
