# SPDX-License-Identifier: AGPL-3.0-or-later
"""Candidate position-error law with changing acceleration and receiver drift.

All process and initial-state scales are supplied by the caller. This module
propagates those assumptions; it does not estimate or validate them for any
recorded aircraft.
"""

import math


def integrated_drift_operator(
        times_s, *, origin_s, acceleration_psd, jerk_psd,
        initial_position_std_m, initial_velocity_std_mps,
        initial_acceleration_std_mps2, receiver_random_walk_psd,
        initial_receiver_offset_std_m, receiver_loading, maximum_bytes):
    """Build a 12-state Gaussian position/velocity/acceleration/receiver law.

    White acceleration has spectral intensity ``acceleration_psd``; white
    jerk drives changing acceleration with intensity ``jerk_psd``. Both are
    independent and isotropic. Receiver error has an independent random-walk
    component and per-epoch white loading; the white loading may be correlated
    across north/east/up within an epoch.
    The operator conditions on earlier residuals without reading later ones.
    """
    import numpy as np
    from .state_space_covariance import LinearInnovations

    times = np.asarray(times_s, dtype=float)
    white = np.asarray(receiver_loading, dtype=float)
    scalars = (origin_s, acceleration_psd, jerk_psd,
               initial_position_std_m, initial_velocity_std_mps,
               initial_acceleration_std_mps2,
               receiver_random_walk_psd, initial_receiver_offset_std_m)
    if (times.ndim != 1 or not 2 <= len(times) <= 100000 or
            not np.all(np.isfinite(times)) or
            white.shape != (len(times), 3, 3) or
            not np.all(np.isfinite(white)) or
            any(isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0 for value in scalars) or
            jerk_psd <= 0 or type(maximum_bytes) is not int or
            maximum_bytes < 1):
        raise ValueError('finite declared times, receiver factors and process scales required')
    steps_s = np.diff(np.concatenate(([float(origin_s)], times)))
    if np.any(steps_s < 0) or np.any(steps_s[1:] <= 0) or np.any(steps_s > 10):
        raise ValueError('ordered receiver epochs without gaps above 10 seconds required')
    identity = np.eye(3)
    observation = np.zeros((3, 12))
    observation[:, :3] = identity
    observation[:, 9:] = identity
    initial = np.diag(np.repeat([
        initial_position_std_m, initial_velocity_std_mps,
        initial_acceleration_std_mps2,
        initial_receiver_offset_std_m], 3))

    def steps():
        for interval, receiver in zip(steps_s, white, strict=True):
            t = float(interval)
            transition = np.eye(12)
            transition[:9, :9] = np.kron(np.array([
                [1., t, .5*t*t], [0., 1., t], [0., 0., 1.]]), identity)
            if t:
                jerk = np.array([
                    [t**5/20, t**4/8, t**3/6],
                    [t**4/8, t**3/3, t*t/2],
                    [t**3/6, t*t/2, t]])
                acceleration = np.array([
                    [t**3/3, t*t/2, 0.],
                    [t*t/2, t, 0.],
                    [0., 0., 0.]])
                covariance = np.kron(jerk_psd*jerk +
                                     acceleration_psd*acceleration, identity)
                loading = np.zeros((12, 12))
                loading[:9, :9] = np.linalg.cholesky(covariance)
                loading[9:, 9:] = math.sqrt(receiver_random_walk_psd*t)*identity
            else:
                loading = np.zeros((12, 12))
            yield dict(transition=transition,
                       process_loading=loading,
                       observation=observation,
                       white_loading=receiver)

    return LinearInnovations(
        steps(), epoch_count=len(times), state_dimension=12,
        observation_dimension=3, initial_loading=initial,
        maximum_bytes=maximum_bytes, design_is_fixed=True,
        error_distribution='gaussian')
