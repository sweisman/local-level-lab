"""Receiver-visible analytic motion and matched-noise controls."""

import numpy as np

from lll.esa_nonaliased_motion_control import (
    nonaliased_path, make_nonaliased_control)
from lll.esa_generated_imu_propagation import propagate_generated


def test_receiver_truth_varies_at_one_hz_and_error_draws_match():
    off = make_nonaliased_control(duration_s=12, rate_hz=100,
                                  seed=2026112200, motion=False)
    on = make_nonaliased_control(duration_s=12, rate_hz=100,
                                 seed=2026112200, motion=True)
    delta = (on['truth_receiver_position_neu_m']-
             off['truth_receiver_position_neu_m'])
    np.testing.assert_allclose(delta[0], 0., atol=1e-12)
    assert np.ptp(delta[:, 0]) > .15
    np.testing.assert_allclose(delta[:, 1:], 0., atol=1e-12)
    for key in ('gyro_white_rads', 'force_white_mps2', 'gyro_bias_rads',
                'force_bias_mps2', 'coupled_gyro_rads',
                'coupled_force_mps2', 'receiver_error_neu_m'):
        np.testing.assert_array_equal(off[key], on[key])


def test_motion_derivatives_and_measured_increment_decomposition():
    case = make_nonaliased_control(duration_s=8, rate_hz=100,
                                  seed=2026112201, motion=True)
    t = case['imu_time_s']
    h = 1e-4
    before = nonaliased_path(t-h, motion=True)
    after = nonaliased_path(t+h, motion=True)
    np.testing.assert_allclose(
        (after['position_neu_m']-before['position_neu_m'])/(2*h),
        case['truth_velocity_neu_mps'], atol=2e-6)
    np.testing.assert_allclose(
        (after['velocity_neu_mps']-before['velocity_neu_mps'])/(2*h),
        case['truth_acceleration_neu_mps2'], atol=2e-5)
    np.testing.assert_allclose(
        case['measured_dtheta_rad']*100,
        case['truth_gyro_body_rads']+case['gyro_white_rads']+
        case['gyro_bias_rads']+case['coupled_gyro_rads'])
    np.testing.assert_allclose(
        case['measured_dv_mps']*100,
        case['truth_force_body_mps2']+case['force_white_mps2']+
        case['force_bias_mps2']+case['coupled_force_mps2'])


def test_clean_imu_reconstructs_receiver_visible_motion():
    case = make_nonaliased_control(duration_s=120, rate_hz=100,
                                  seed=2026112202, motion=True,
                                  errors=False)
    result = propagate_generated(case)
    assert np.max(np.abs(result['truth_integrated_position_neu_m']-
                             case['truth_receiver_position_neu_m'])) < .01
    np.testing.assert_allclose(result['measured_position_neu_m'],
                               result['truth_integrated_position_neu_m'],
                               rtol=0., atol=1e-12)
