# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent linearized IMU/receiver error truth for covariance controls.

The generator advances scalar errors directly from random draws. The candidate
operator constructs state matrices separately. This checks error propagation;
it is not a full aircraft or Earth-model simulation.
"""
from dataclasses import dataclass
import math


VERSION = 'independent-linear-imu-receiver-error-v1'


@dataclass(frozen=True)
class Law:
    gyro_white_rad_sqrt_s: float = 1e-6
    accel_white_mps_sqrt_s: float = .001
    gyro_bias_rad_s: float = 1e-7
    accel_bias_mps2: float = .0002
    gyro_bias_tau_s: float = 300.
    accel_bias_tau_s: float = 200.
    receiver_white_m: float = .5
    receiver_offset_m: float = .3
    receiver_drift_mps: float = .001
    receiver_ar_m: float = .3
    receiver_ar_tau_s: float = 30.


def _inputs(law, times, speed_mps):
    import numpy as np
    if not isinstance(law, Law):
        raise ValueError('explicit known-answer error law required')
    values = vars(law)
    if (any(type(value) not in (int, float) or not math.isfinite(value) or
            value < 0 for value in values.values()) or
            any(values[name] <= 0 for name in
                ('gyro_bias_tau_s', 'accel_bias_tau_s', 'receiver_ar_tau_s',
                 'receiver_white_m')) or
            type(speed_mps) not in (int, float) or not math.isfinite(speed_mps) or
            not 0 < speed_mps <= 400):
        raise ValueError('finite nonnegative scales and positive time constants required')
    t = np.asarray(times, dtype=float)
    if (t.ndim != 1 or not 2 <= len(t) <= 2048 or not np.all(np.isfinite(t)) or
            t[0] <= 0 or np.any(np.diff(t) <= 0) or
            np.any(np.diff(np.r_[0., t]) > 60)):
        raise ValueError('bounded positive ordered sample times required')
    return t, np.diff(np.r_[0., t])


def generate(seed, law, times, *, speed_mps):
    """Draw gyro, accelerometer and receiver errors from separate streams."""
    import numpy as np
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError('explicit unsigned 64-bit truth seed required')
    t, intervals = _inputs(law, times, speed_mps)
    gyro_rng, accel_rng, receiver_rng = [np.random.default_rng(child)
                                         for child in np.random.SeedSequence(seed).spawn(3)]
    bg = law.gyro_bias_rad_s*gyro_rng.normal()
    ba = law.accel_bias_mps2*accel_rng.normal()
    offset = law.receiver_offset_m*receiver_rng.normal()
    drift = law.receiver_drift_mps*receiver_rng.normal()
    ar = law.receiver_ar_m*receiver_rng.normal()
    angle = velocity = position = 0.
    gyro = np.empty(len(t)); accel = np.empty(len(t))
    receiver = np.empty(len(t)); propagated = np.empty(len(t))
    for i, (time, dt) in enumerate(zip(t, intervals, strict=True)):
        gyro[i] = bg*dt + law.gyro_white_rad_sqrt_s*math.sqrt(dt)*gyro_rng.normal()
        accel[i] = ba*dt + law.accel_white_mps_sqrt_s*math.sqrt(dt)*accel_rng.normal()
        position += velocity*dt + .5*speed_mps*angle*dt*dt + .5*accel[i]*dt
        velocity += speed_mps*angle*dt + accel[i]
        angle += gyro[i]
        rho_g = math.exp(-dt/law.gyro_bias_tau_s)
        rho_a = math.exp(-dt/law.accel_bias_tau_s)
        rho_r = math.exp(-dt/law.receiver_ar_tau_s)
        bg = rho_g*bg + law.gyro_bias_rad_s*math.sqrt(1-rho_g*rho_g)*gyro_rng.normal()
        ba = rho_a*ba + law.accel_bias_mps2*math.sqrt(1-rho_a*rho_a)*accel_rng.normal()
        ar = rho_r*ar + law.receiver_ar_m*math.sqrt(1-rho_r*rho_r)*receiver_rng.normal()
        receiver[i] = offset + drift*time + ar + law.receiver_white_m*receiver_rng.normal()
        propagated[i] = position
    return dict(version=VERSION, times_s=t, gyro_increment_error_rad=gyro,
                accel_increment_error_mps=accel, imu_position_error_m=propagated,
                receiver_error_m=receiver, residual_m=receiver-propagated,
                receiver_and_imu_streams_separate=True,
                later_observations_used_for_law_selection=False,
                physical_model_compared=False, calibrated_coverage=False)


def operator(law, times, *, speed_mps):
    """Construct the fixed Gaussian law without calling the truth generator."""
    import numpy as np
    from .state_space_covariance import LinearInnovations
    t, intervals = _inputs(law, times, speed_mps)
    initial = np.zeros((8, 5))
    initial[3, 0] = law.gyro_bias_rad_s
    initial[4, 1] = law.accel_bias_mps2
    initial[5, 2] = law.receiver_offset_m
    initial[6, 3] = law.receiver_drift_mps
    initial[7, 4] = law.receiver_ar_m
    steps = []
    for time, dt in zip(t, intervals, strict=True):
        f = np.eye(8)
        f[0, 1] = dt
        f[0, 2] = .5*speed_mps*dt*dt
        f[0, 4] = .5*dt*dt
        f[1, 2] = speed_mps*dt
        f[1, 4] = dt
        f[2, 3] = dt
        b = np.zeros((8, 5))
        b[2, 0] = law.gyro_white_rad_sqrt_s*math.sqrt(dt)
        b[0, 1] = .5*law.accel_white_mps_sqrt_s*dt*math.sqrt(dt)
        b[1, 1] = law.accel_white_mps_sqrt_s*math.sqrt(dt)
        for index, scale, tau in (
                (3, law.gyro_bias_rad_s, law.gyro_bias_tau_s),
                (4, law.accel_bias_mps2, law.accel_bias_tau_s),
                (7, law.receiver_ar_m, law.receiver_ar_tau_s)):
            rho = math.exp(-dt/tau)
            f[index, index] = rho
            b[index, {3:2, 4:3, 7:4}[index]] = scale*math.sqrt(1-rho*rho)
        h = np.zeros((1, 8))
        h[0, (0, 5, 6, 7)] = (-1., 1., time, 1.)
        steps.append(dict(transition=f, process_loading=b,
                          observation=h,
                          white_loading=np.array([[law.receiver_white_m]])))
    return LinearInnovations(
        steps, epoch_count=len(t), state_dimension=8,
        observation_dimension=1, initial_loading=initial,
        maximum_bytes=2*1024**2, design_is_fixed=True,
        error_distribution='gaussian')
