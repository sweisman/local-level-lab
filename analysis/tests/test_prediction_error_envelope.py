"""Known-answer checks for a declared, conditional forecast-error bound."""

import math

import pytest
import numpy as np
from scipy.spatial.transform import Rotation

from lll.esa_motion_error_controls import make_control
from lll.airquantumgrav_noisy_inputs import noise_settings
from lll.prediction_error_envelope import position_error_bound


ZERO = dict(initial_position_error_m=0., initial_velocity_error_mps=0.,
            initial_attitude_error_rad=0., gyro_rate_error_rads=0.,
            gyro_rate_drift_rads2=0., force_error_mps2=0.,
            force_error_drift_mps3=0., unmodeled_acceleration_mps2=0.,
            force_norm_bound_mps2=10., receiver_error_m=0.)


def check(**changes):
    return position_error_bound(12., **dict(ZERO, **changes))


def test_exact_initial_and_constant_acceleration_terms():
    result = check(initial_position_error_m=.2,
                   initial_velocity_error_mps=.03,
                   force_error_mps2=.004,
                   unmodeled_acceleration_mps2=.005,
                   receiver_error_m=.1)
    expected = .2 + .03*12 + .5*(.004+.005)*12**2 + .1
    assert result['total_m'] == pytest.approx(expected)
    assert result['observed_coverage_qualified'] is False
    assert result['assumptions_empirically_verified'] is False


def test_drift_and_attitude_coefficients():
    result = check(initial_attitude_error_rad=.01,
                   gyro_rate_error_rads=.002,
                   gyro_rate_drift_rads2=.0003,
                   force_error_drift_mps3=.004)
    expected = (10*.01*12**2/2 + 10*.002*12**3/6 +
                10*.0003*12**4/24 + .004*12**3/6)
    assert result['total_m'] == pytest.approx(expected)
    assert sum(result['terms_m'].values()) == pytest.approx(expected)


def test_independently_integrated_rotating_force_stays_inside_bound():
    # Direct midpoint integration uses an actual rotated force, not the
    # polynomial used by the bound. Its angular discrepancy grows with time.
    step = .001
    horizon = 12.
    samples = int(horizon/step)
    actual = 0.
    for index in range(samples):
        t = (index+.5)*step
        angle = .01+.002*t+.5*.0003*t*t
        acceleration_error = 10*math.sin(angle)+.004*t
        actual += (horizon-t)*acceleration_error*step
    bound = check(initial_attitude_error_rad=.01,
                  gyro_rate_error_rads=.002,
                  gyro_rate_drift_rads2=.0003,
                  force_error_drift_mps3=.004)
    assert actual > 0
    assert actual < bound['total_m']
    assert bound['total_m']-actual < .1


def test_generated_aircraft_sensor_error_stays_inside_declared_bound():
    case = make_control(duration_s=8, rate_hz=100, seed=728,
                        vibration=True, errors=True)
    dt = case['imu_dt_s']
    truth_rate = case['truth_gyro_body_rads']
    measured_rate = case['measured_dtheta_rad']/dt
    truth_force = case['truth_force_body_mps2']
    measured_force = case['measured_dv_mps']/dt
    angular_error = float(np.max(np.linalg.norm(measured_rate-truth_rate,
                                               axis=1)))
    force_error = float(np.max(np.linalg.norm(measured_force-truth_force,
                                             axis=1)))
    force_bound = float(np.max(np.linalg.norm(truth_force, axis=1)))
    states = []
    for rate, force in ((truth_rate, truth_force),
                        (measured_rate, measured_force)):
        attitude = Rotation.identity()
        velocity = np.zeros(3)
        position = np.zeros(3)
        for angular_rate, body_force in zip(rate, force):
            acceleration = attitude.apply(body_force)
            position += velocity*dt + .5*acceleration*dt**2
            velocity += acceleration*dt
            attitude = attitude*Rotation.from_rotvec(angular_rate*dt)
        states.append(position)
    realized = float(np.linalg.norm(states[1]-states[0]))
    bound = position_error_bound(8., **dict(ZERO,
        gyro_rate_error_rads=angular_error,
        force_error_mps2=force_error,
        force_norm_bound_mps2=force_bound))
    assert realized > 0
    assert realized < bound['total_m']


def test_fails_closed_on_missing_or_invalid_assumptions():
    with pytest.raises(TypeError):
        position_error_bound(12., force_norm_bound_mps2=10.)
    with pytest.raises(ValueError):
        check(force_error_mps2=-.1)
    with pytest.raises(ValueError):
        position_error_bound(float('nan'), **ZERO)
    with pytest.raises(ValueError):
        position_error_bound(12., **dict(ZERO, gyro_rate_drift_rads2=float('inf')))


def test_samplewise_synthetic_noise_limit_is_too_broad_for_short_forecast():
    # Four Gaussian component families, three axes, 300 Hz over 120 s.
    # The union bound is valid despite correlation of the sampled bias.
    settings = noise_settings()
    horizon = 120.
    rate = 300.
    factor = math.sqrt(2*math.log(2*3*int(horizon*rate)/(.05/4)))
    gyro_limit = math.sqrt(3)*factor*(
        settings['gyro_white_rads_per_sqrt_s']*math.sqrt(rate) +
        settings['gyro_bias_stationary_rads'])
    force_limit = math.sqrt(3)*factor*(
        settings['accel_white_mps_per_sqrt_s']*math.sqrt(rate) +
        settings['accel_bias_stationary_mps2'])
    result = position_error_bound(horizon, **dict(ZERO,
        gyro_rate_error_rads=gyro_limit,
        force_error_mps2=force_limit))
    assert result['total_m'] == pytest.approx(3161.92323083917)
    assert result['total_m'] > 3000.
