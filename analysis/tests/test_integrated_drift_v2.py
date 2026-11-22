"""Independent continuous-noise checks for the changing-gyro-bias law."""

import numpy as np
import pytest
from scipy.integrate import quad

from lll.integrated_drift_v2 import integrated_drift_v2_operator
from lll.integrated_drift_law import integrated_drift_operator


def build(times, *, snap_psd=.002, maximum_bytes=1_000_000):
    return integrated_drift_v2_operator(
        times, origin_s=0., acceleration_psd=.004, jerk_psd=.003,
        snap_psd=snap_psd, initial_position_std_m=.2,
        initial_velocity_std_mps=.03, initial_acceleration_std_mps2=.002,
        initial_jerk_std_mps3=.001, receiver_random_walk_psd=.0001,
        initial_receiver_offset_std_m=.01,
        receiver_loading=np.broadcast_to(np.eye(3)*.1,
                                         (len(times), 3, 3)),
        maximum_bytes=maximum_bytes)


def dense_covariance(times):
    covariance = np.zeros((3*len(times), 3*len(times)))
    for i, t in enumerate(times):
        for j, s in enumerate(times):
            limit = min(t, s)
            q_acc = .004*quad(lambda u: (t-u)*(s-u), 0., limit)[0]
            q_jerk = .003*quad(lambda u: (t-u)**2*(s-u)**2/4,
                               0., limit)[0]
            q_snap = .002*quad(lambda u: (t-u)**3*(s-u)**3/36,
                               0., limit)[0]
            initial = (.2**2 + .03**2*t*s + .002**2*t*t*s*s/4 +
                       .001**2*t**3*s**3/36)
            receiver = .01**2 + .0001*limit
            block = (q_acc+q_jerk+q_snap+initial+receiver)*np.eye(3)
            if i == j:
                block += .01*np.eye(3)
            covariance[3*i:3*i+3, 3*j:3*j+3] = block
    return covariance


def test_dense_covariance_matches_independent_quadrature():
    times = np.array([0., 1., 2.])
    operator = build(times)
    loading, _ = operator.apply_block(np.eye(9), first_epoch=0,
                                      inverse=True)
    np.testing.assert_allclose(loading @ loading.T,
                               dense_covariance(times),
                               rtol=1e-10, atol=1e-11)


def test_conditional_future_matches_dense_schur_complement():
    times = np.arange(5., dtype=float)
    operator = build(times)
    earlier = np.array([.1, -.2, .3, .2, .1, -.1])
    _, state = operator.apply_block(earlier, first_epoch=0)
    later = operator.conditional_marginals(state=state)
    full = dense_covariance(times)
    expected_mean = full[6:, :6] @ np.linalg.solve(full[:6, :6], earlier)
    expected_covariance = (full[6:, 6:] - full[6:, :6] @
                           np.linalg.solve(full[:6, :6], full[:6, 6:]))
    np.testing.assert_allclose(later['mean'], expected_mean.reshape(3, 3),
                               rtol=1e-10, atol=1e-10)
    for i in range(3):
        np.testing.assert_allclose(later['covariance'][i],
            expected_covariance[3*i:3*i+3, 3*i:3*i+3],
            rtol=1e-10, atol=1e-10)


def test_zero_snap_and_zero_initial_jerk_reduce_to_first_candidate():
    times = np.arange(4., dtype=float)
    second = integrated_drift_v2_operator(
        times, origin_s=0., acceleration_psd=.004, jerk_psd=.003,
        snap_psd=0., initial_position_std_m=.2,
        initial_velocity_std_mps=.03, initial_acceleration_std_mps2=.002,
        initial_jerk_std_mps3=0., receiver_random_walk_psd=.0001,
        initial_receiver_offset_std_m=.01,
        receiver_loading=np.broadcast_to(np.eye(3)*.1, (4, 3, 3)),
        maximum_bytes=1_000_000)
    first = integrated_drift_operator(
        times, origin_s=0., acceleration_psd=.004, jerk_psd=.003,
        initial_position_std_m=.2, initial_velocity_std_mps=.03,
        initial_acceleration_std_mps2=.002,
        receiver_random_walk_psd=.0001,
        initial_receiver_offset_std_m=.01,
        receiver_loading=np.broadcast_to(np.eye(3)*.1, (4, 3, 3)),
        maximum_bytes=1_000_000)
    one, _ = first.apply_block(np.eye(12), first_epoch=0, inverse=True)
    two, _ = second.apply_block(np.eye(12), first_epoch=0, inverse=True)
    np.testing.assert_allclose(two @ two.T, one @ one.T,
                               rtol=1e-10, atol=1e-11)


def test_invalid_scales_and_storage_fail_closed():
    with pytest.raises(ValueError):
        build([0., 1.], snap_psd=-1.)
    with pytest.raises(ValueError):
        build([0., 1.], maximum_bytes=1)
    with pytest.raises(ValueError):
        build([0., 1., 1.])
