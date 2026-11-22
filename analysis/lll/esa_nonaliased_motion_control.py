# SPDX-License-Identifier: AGPL-3.0-or-later
"""Analytic aircraft-motion control visible at one-second receiver reports."""

import math

import numpy as np

from .esa_motion_error_controls import (
    analytic_path, make_control, _body_observations)


FREQUENCY_HZ = .37
NORTH_AMPLITUDE_M = .1
PITCH_AMPLITUDE_RAD = .001


def nonaliased_path(time_s, *, motion=True):
    """Add analytic north and pitch motion while retaining the base trajectory."""
    if type(motion) is not bool:
        raise ValueError('boolean motion switch required')
    base = analytic_path(time_s, vibration=True)
    if not motion:
        return base
    t = np.asarray(time_s, dtype=float)
    omega = 2*math.pi*FREQUENCY_HZ
    cosine = np.cos(omega*t)
    sine = np.sin(omega*t)
    position = base['position_neu_m'].copy()
    velocity = base['velocity_neu_mps'].copy()
    acceleration = base['acceleration_neu_mps2'].copy()
    position[:, 0] += NORTH_AMPLITUDE_M*(1-cosine)
    velocity[:, 0] += NORTH_AMPLITUDE_M*omega*sine
    acceleration[:, 0] += NORTH_AMPLITUDE_M*omega*omega*cosine
    vn, ve = velocity[:, 0], velocity[:, 1]
    an, ae = acceleration[:, 0], acceleration[:, 1]
    return dict(position_neu_m=position, velocity_neu_mps=velocity,
                acceleration_neu_mps2=acceleration,
                yaw_rad=np.arctan2(ve, vn),
                yaw_rate_rads=(vn*ae-ve*an)/(vn*vn+ve*ve),
                pitch_rad=base['pitch_rad']+
                    PITCH_AMPLITUDE_RAD*(1-cosine),
                pitch_rate_rads=base['pitch_rate_rads']+
                    PITCH_AMPLITUDE_RAD*omega*sine)


def make_nonaliased_control(*, duration_s=120, rate_hz=100,
                            seed=2026112200, motion=True, errors=True):
    """Keep the original independent error draws under both motion settings."""
    if type(motion) is not bool:
        raise ValueError('boolean motion switch required')
    case = make_control(duration_s=duration_s, rate_hz=rate_hz,
                        seed=seed, vibration=True, errors=errors)
    case['nonaliased_motion'] = motion
    if not motion:
        return case
    path = nonaliased_path(case['imu_time_s'], motion=True)
    receiver_path = nonaliased_path(case['receiver_time_s'], motion=True)
    gyro, force = _body_observations(path)
    dt = case['imu_dt_s']
    case.update(truth_position_neu_m=path['position_neu_m'],
                truth_velocity_neu_mps=path['velocity_neu_mps'],
                truth_acceleration_neu_mps2=path['acceleration_neu_mps2'],
                truth_gyro_body_rads=gyro,
                truth_force_body_mps2=force,
                truth_receiver_position_neu_m=
                    receiver_path['position_neu_m'],
                measured_dtheta_rad=(gyro+case['gyro_white_rads']+
                    case['gyro_bias_rads']+case['coupled_gyro_rads'])*dt,
                measured_dv_mps=(force+case['force_white_mps2']+
                    case['force_bias_mps2']+case['coupled_force_mps2'])*dt,
                receiver_position_neu_m=(
                    receiver_path['position_neu_m']+
                    case['receiver_error_neu_m']))
    return case
