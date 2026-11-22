# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent local-aircraft truth for prediction-error law controls.

This analytic Cartesian generator does not call the inverse-navigation model.
It supplies known motion, each error component, and sampled observations. It
is a software control, not a representation of an ESA flight or its IMU.
"""

import math

import numpy as np


def analytic_path(time_s, *, vibration=True):
    """Return position, derivatives and attitude for a small moving aircraft.

World coordinates are north, east, up. Body coordinates are forward, right,
down. Heading follows the analytic horizontal velocity; independent low-rate
pitch and optional high-rate pitch/forward vibration vary the body attitude.
"""
    t = np.asarray(time_s, dtype=float)
    if t.ndim != 1 or not np.all(np.isfinite(t)) or np.any(t < -1e-3):
        raise ValueError('finite one-dimensional nonnegative times required')
    wc = 2*math.pi/45.
    wh = 2*math.pi/31.
    wp = 2*math.pi/37.
    wv = 2*math.pi*10.
    forward_vibration = .0002 if vibration else 0.
    pitch_vibration = .0005 if vibration else 0.
    n = 80*t + forward_vibration*np.cos(wv*t)
    vn = 80 - forward_vibration*wv*np.sin(wv*t)
    an = -forward_vibration*wv*wv*np.cos(wv*t)
    e = 3*np.sin(wc*t)
    ve = 3*wc*np.cos(wc*t)
    ae = -3*wc*wc*np.sin(wc*t)
    u = 950 + .2*np.sin(wh*t)
    vu = .2*wh*np.cos(wh*t)
    au = -.2*wh*wh*np.sin(wh*t)
    yaw = np.arctan2(ve, vn)
    yaw_rate = (vn*ae-ve*an)/(vn*vn+ve*ve)
    pitch = .005*np.sin(wp*t) + pitch_vibration*np.sin(wv*t)
    pitch_rate = .005*wp*np.cos(wp*t) + pitch_vibration*wv*np.cos(wv*t)
    return dict(position_neu_m=np.column_stack((n, e, u)),
                velocity_neu_mps=np.column_stack((vn, ve, vu)),
                acceleration_neu_mps2=np.column_stack((an, ae, au)),
                yaw_rad=yaw, yaw_rate_rads=yaw_rate,
                pitch_rad=pitch, pitch_rate_rads=pitch_rate)


def _body_observations(path):
    yaw = path['yaw_rad']
    pitch = path['pitch_rad']
    yaw_rate = path['yaw_rate_rads']
    pitch_rate = path['pitch_rate_rads']
    acceleration = path['acceleration_neu_mps2']
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    # ZYX yaw/pitch rotation; gyro is the body-frame angular velocity.
    gyro = np.column_stack((-yaw_rate*sp, pitch_rate, yaw_rate*cp))
    # Specific force is inertial acceleration minus gravity, expressed in body
    # axes. World up is positive, whereas body z is down.
    forward = cy*acceleration[:, 0] + sy*acceleration[:, 1]
    right = -sy*acceleration[:, 0] + cy*acceleration[:, 1]
    down = -acceleration[:, 2] - 9.80665
    force = np.column_stack((cp*forward-sp*down, right,
                             sp*forward+cp*down))
    return gyro, force


def _random_walk(rng, count, dt, diffusion):
    return np.cumsum(rng.normal(0, diffusion*math.sqrt(dt),
                                   size=(count, 3)), axis=0)


def make_control(*, duration_s=30, rate_hz=300, seed=20261115,
                 vibration=True, errors=True):
    """Generate one known-truth six-channel IMU and one-Hz receiver history.

    Independent RNG streams cover gyro white error, force white error, two
    changing biases, shared sensor coupling and receiver error. The same seed
    gives the same error draws with or without physical vibration.
    """
    if (type(duration_s) is not int or not 1 <= duration_s <= 1200 or
            type(rate_hz) is not int or not 1 <= rate_hz <= 1000 or
            type(seed) is not int or not 0 <= seed < 2**63 or
            type(vibration) is not bool or type(errors) is not bool):
        raise ValueError('bounded duration, rate, seed and boolean controls required')
    dt = 1/rate_hz
    t = (np.arange(duration_s*rate_hz, dtype=float)+.5)*dt
    q = np.arange(duration_s+1, dtype=float)
    path = analytic_path(t, vibration=vibration)
    receiver_path = analytic_path(q, vibration=vibration)
    gyro, force = _body_observations(path)
    seeds = np.random.SeedSequence(seed).spawn(6)
    rng = [np.random.default_rng(item) for item in seeds]
    count = len(t)
    if errors:
        gyro_white = rng[0].normal(0, 1e-4, size=(count, 3))
        force_white = rng[1].normal(0, .01, size=(count, 3))
        gyro_bias = _random_walk(rng[2], count, dt, 2e-6)
        force_bias = _random_walk(rng[3], count, dt, 3e-4)
        shared = rng[4].normal(size=count)
        coupled_gyro = np.column_stack((np.zeros(count),
                                         2e-4*shared, np.zeros(count)))
        coupled_force = np.column_stack((.02*shared, np.zeros(count),
                                         np.zeros(count)))
        receiver_white = rng[5].normal(0, .03, size=(len(q), 3))
        receiver_persistent = _random_walk(rng[5], len(q), 1, .01)
        receiver_error = receiver_white + receiver_persistent
    else:
        gyro_white = gyro_bias = coupled_gyro = np.zeros_like(gyro)
        force_white = force_bias = coupled_force = np.zeros_like(force)
        receiver_error = np.zeros_like(receiver_path['position_neu_m'])
    return dict(version='esa-motion-error-control-v1',
                imu_time_s=t, receiver_time_s=q, imu_dt_s=dt,
                truth_position_neu_m=path['position_neu_m'],
                truth_velocity_neu_mps=path['velocity_neu_mps'],
                truth_acceleration_neu_mps2=path['acceleration_neu_mps2'],
                truth_gyro_body_rads=gyro,
                truth_force_body_mps2=force,
                truth_receiver_position_neu_m=receiver_path['position_neu_m'],
                gyro_white_rads=gyro_white,
                force_white_mps2=force_white,
                gyro_bias_rads=gyro_bias,
                force_bias_mps2=force_bias,
                coupled_gyro_rads=coupled_gyro,
                coupled_force_mps2=coupled_force,
                receiver_error_neu_m=receiver_error,
                measured_dtheta_rad=(gyro+gyro_white+gyro_bias+coupled_gyro)*dt,
                measured_dv_mps=(force+force_white+force_bias+coupled_force)*dt,
                receiver_position_neu_m=(receiver_path['position_neu_m']+
                                         receiver_error))
