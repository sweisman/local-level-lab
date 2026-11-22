"""Dense independent checks for a candidate time-correlated forecast law."""

import numpy as np
import pytest
from scipy.integrate import quad

from lll.integrated_drift_law import integrated_drift_operator


def make(times):
    return integrated_drift_operator(
        times, origin_s=0., acceleration_psd=.004, jerk_psd=.003,
        initial_position_std_m=.2, initial_velocity_std_mps=.03,
        initial_acceleration_std_mps2=.002,
        receiver_random_walk_psd=.0001,
        initial_receiver_offset_std_m=.01,
        receiver_loading=np.broadcast_to(np.eye(3)*.1,
                                         (len(times), 3, 3)),
        maximum_bytes=1_000_000)


def dense_covariance(times):
    expected = np.zeros((3*len(times), 3*len(times)))
    for i, t in enumerate(times):
        for j, s in enumerate(times):
            limit = min(t, s)
            acceleration = .004*quad(lambda u: (t-u)*(s-u),
                                     0., limit)[0]
            changing = .003*quad(lambda u: .25*(t-u)**2*(s-u)**2,
                                 0., limit)[0]
            initial = .2**2 + .03**2*t*s + .25*.002**2*t*t*s*s
            receiver_drift = .01**2 + .0001*limit
            block = (initial+acceleration+changing+receiver_drift)*np.eye(3)
            if i == j:
                block += .01*np.eye(3)
            expected[3*i:3*i+3, 3*j:3*j+3] = block
    return expected


def test_independent_dense_covariance_matches_streamed_operator():
    times = np.array([0., 1., 2.])
    operator = make(times)
    loading, _ = operator.apply_block(np.eye(9), first_epoch=0,
                                      inverse=True)
    actual = loading @ loading.T
    expected = dense_covariance(times)
    np.testing.assert_allclose(actual, expected, rtol=1e-10, atol=1e-11)
    assert operator.error_law_calibrated is False


def test_future_range_grows_and_uses_only_earlier_residuals():
    operator = make(np.arange(5., dtype=float))
    _, state = operator.apply_block(np.zeros(6), first_epoch=0)
    future = operator.conditional_marginals(state=state)
    assert future['forecast_epochs'] == 3
    variance = future['covariance'][:, 0, 0]
    assert np.all(np.diff(variance) > 0)
    assert future['later_observations_used'] is False
    assert future['error_law_calibrated'] is False


def test_conditioned_mean_and_variance_match_independent_dense_formula():
    times = np.arange(5., dtype=float)
    operator = make(times)
    earlier = np.array([.1, -.2, .3, .2, .1, -.1])
    _, state = operator.apply_block(earlier, first_epoch=0)
    future = operator.conditional_marginals(state=state)
    covariance = dense_covariance(times)
    trained = covariance[:6, :6]
    cross = covariance[6:, :6]
    mean = cross @ np.linalg.solve(trained, earlier)
    conditional = covariance[6:, 6:] - cross @ np.linalg.solve(
        trained, cross.T)
    np.testing.assert_allclose(future['mean'], mean.reshape(3, 3),
                               rtol=1e-10, atol=1e-10)
    for index in range(3):
        np.testing.assert_allclose(future['covariance'][index],
            conditional[3*index:3*index+3, 3*index:3*index+3],
            rtol=1e-10, atol=1e-10)


def test_rejects_unordered_times_and_unstated_process_scale():
    with pytest.raises(ValueError):
        make([0., 1., 1.])
    with pytest.raises(ValueError):
        integrated_drift_operator(
            [0., 1.], origin_s=0., acceleration_psd=.004,
            jerk_psd=-.003, initial_position_std_m=.2,
            initial_velocity_std_mps=.03,
            initial_acceleration_std_mps2=.002,
            receiver_random_walk_psd=.0001,
            initial_receiver_offset_std_m=.01,
            receiver_loading=np.broadcast_to(np.eye(3)*.1, (2, 3, 3)),
            maximum_bytes=1_000_000)
    with pytest.raises(ValueError):
        integrated_drift_operator(
            [0., 1.], origin_s=0., acceleration_psd=.004,
            jerk_psd=.003, initial_position_std_m=.2,
            initial_velocity_std_mps=.03,
            initial_acceleration_std_mps2=.002,
            receiver_random_walk_psd=-.0001,
            initial_receiver_offset_std_m=.01,
            receiver_loading=np.broadcast_to(np.eye(3)*.1, (2, 3, 3)),
            maximum_bytes=1_000_000)
