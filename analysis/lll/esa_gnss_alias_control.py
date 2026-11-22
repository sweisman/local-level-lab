# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-motion aliasing control for a 300-Hz IMU and 5-Hz GNSS receiver.

This is an exact sampled-data counterexample, not an ESA instrument model.
It extends the earlier one-hertz control without changing its frozen source.
"""

import numpy as np

from .esa_error_attribution_adversary import paired_explanations


def build_control(*, duration_s=30, seed=20261115):
    """Return two different latent worlds with identical sampled channels.

    A 10-Hz forward displacement is at the same phase at every 5-Hz receiver
    epoch. Its sampled velocity is also identical to steady flight. A fixed
    receiver position offset absorbs the 0.2-mm sampled displacement in the
    steady world; correlated IMU error absorbs the true pitch/force motion.
    """
    old = paired_explanations(duration_s=duration_s, rate_hz=300,
                              vibration_hz=10, seed=seed)
    q = np.arange(duration_s*5+1, dtype=float)/5.
    steady_position = np.zeros((len(q), 3), dtype=float)
    steady_position[:, 0] = 80*q
    moving_position = steady_position.copy()
    moving_position[:, 0] += old['displacement_amplitude_m']
    # The analytic derivative of 0.2 mm*cos(2*pi*10*t) vanishes exactly at
    # every t=n/5. Do not evaluate sin(4*pi*n) in floating point and mistake
    # roundoff for observed motion.
    sampled_velocity = np.zeros_like(steady_position)
    sampled_velocity[:, 0] = 80.
    common_position = moving_position.copy()
    common_velocity = sampled_velocity.copy()
    worlds = {}
    for name, true_position in (('motion', moving_position),
                                ('sensor_coupling', steady_position)):
        original = old[name]
        worlds[name] = dict(
            measured_gyro_rads=original['measured_gyro_rads'].copy(),
            measured_force_mps2=original['measured_force_mps2'].copy(),
            true_gyro_rads=original['true_gyro_rads'].copy(),
            true_force_mps2=original['true_force_mps2'].copy(),
            true_receiver_position_m=true_position,
            true_receiver_velocity_mps=sampled_velocity.copy(),
            reported_position_m=common_position.copy(),
            reported_velocity_mps=common_velocity.copy(),
            receiver_position_error_m=common_position-true_position)
    difference = np.max(np.abs(worlds['motion']['true_gyro_rads']
                               -worlds['sensor_coupling']['true_gyro_rads']))
    return dict(version='esa-gnss-alias-control-v1',
                duration_s=duration_s, seed=seed, imu_rate_hz=300,
                receiver_rate_hz=5, vibration_hz=10,
                imu_time_s=old['imu_time_s'], receiver_time_s=q,
                maximum_true_gyro_difference_rads=float(difference),
                motion=worlds['motion'],
                sensor_coupling=worlds['sensor_coupling'],
                observationally_distinguishable=False,
                earth_model_test=False, protected_reads=0)
