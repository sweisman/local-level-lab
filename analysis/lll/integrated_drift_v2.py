# SPDX-License-Identifier: AGPL-3.0-or-later
"""Candidate position-error law with a changing jerk-error state.

All scales are caller supplied. This operator does not estimate or validate
an error law for a recorded aircraft.
"""

import math


def integrated_drift_v2_operator(
        times_s, *, origin_s, acceleration_psd, jerk_psd, snap_psd,
        initial_position_std_m, initial_velocity_std_mps,
        initial_acceleration_std_mps2, initial_jerk_std_mps3,
        receiver_random_walk_psd, initial_receiver_offset_std_m,
        receiver_loading, maximum_bytes):
    """Build a 15-state integrated Gaussian law with receiver drift.

    The first three independent white drivers enter velocity, acceleration
    and jerk respectively. Their position kernels are t, t²/2 and t³/6.
    A separate random walk drives receiver position. Zero process scales
    mean absent drivers; no positive floor is silently introduced.
    """
    import numpy as np
    from .state_space_covariance import LinearInnovations

    times = np.asarray(times_s, dtype=float)
    white = np.asarray(receiver_loading, dtype=float)
    scales = (origin_s, acceleration_psd, jerk_psd, snap_psd,
              initial_position_std_m, initial_velocity_std_mps,
              initial_acceleration_std_mps2, initial_jerk_std_mps3,
              receiver_random_walk_psd, initial_receiver_offset_std_m)
    if (times.ndim != 1 or not 2 <= len(times) <= 100000 or
            not np.all(np.isfinite(times)) or
            white.shape != (len(times), 3, 3) or
            not np.all(np.isfinite(white)) or
            any(isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0 for value in scales) or
            type(maximum_bytes) is not int or maximum_bytes < 1):
        raise ValueError('finite declared times, receiver factors and process scales required')
    intervals = np.diff(np.concatenate(([float(origin_s)], times)))
    if (np.any(intervals < 0) or np.any(intervals[1:] <= 0) or
            np.any(intervals > 10)):
        raise ValueError('ordered receiver epochs without gaps above 10 seconds required')
    identity = np.eye(3)
    observation = np.zeros((3, 15))
    observation[:, :3] = identity
    observation[:, 12:] = identity
    initial = np.diag(np.repeat((
        initial_position_std_m, initial_velocity_std_mps,
        initial_acceleration_std_mps2, initial_jerk_std_mps3,
        initial_receiver_offset_std_m), 3))

    def steps():
        for interval, receiver in zip(intervals, white, strict=True):
            t = float(interval)
            transition = np.eye(15)
            transition[:12, :12] = np.kron(np.array((
                (1., t, t*t/2, t**3/6),
                (0., 1., t, t*t/2),
                (0., 0., 1., t),
                (0., 0., 0., 1.))), identity)
            loading = np.zeros((15, 30))
            if t:
                local = np.zeros((4, 9))
                for order, offset, intensity in (
                        (1, 0, acceleration_psd),
                        (2, 2, jerk_psd),
                        (3, 5, snap_psd)):
                    if not intensity:
                        continue
                    powers = list(range(order, -1, -1))
                    covariance = np.array([
                        [intensity*t**(i+j+1)/(
                            math.factorial(i)*math.factorial(j)*(i+j+1))
                         for j in powers] for i in powers])
                    local[:order+1, offset:offset+order+1] = (
                        np.linalg.cholesky(covariance))
                loading[:12, :27] = np.kron(local, identity)
                loading[12:, 27:] = (
                    math.sqrt(receiver_random_walk_psd*t)*identity)
            yield dict(transition=transition, process_loading=loading,
                       observation=observation, white_loading=receiver)

    return LinearInnovations(
        steps(), epoch_count=len(times), state_dimension=15,
        observation_dimension=3, initial_loading=initial,
        maximum_bytes=maximum_bytes, design_is_fixed=True,
        error_distribution='gaussian')
