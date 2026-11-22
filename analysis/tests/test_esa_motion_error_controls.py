"""Known-truth controls for ESA prediction-error development."""

import numpy as np
import pytest

from lll.esa_motion_error_controls import make_control


def test_analytic_motion_and_increments_without_errors():
    case = make_control(duration_s=8, rate_hz=100, seed=17, errors=False)
    t = case['imu_time_s']
    h = 1e-4
    from lll.esa_motion_error_controls import analytic_path

    before = analytic_path(t-h)
    after = analytic_path(t+h)
    np.testing.assert_allclose((after['velocity_neu_mps']-
                                before['velocity_neu_mps'])/(2*h),
                               case['truth_acceleration_neu_mps2'], atol=2e-5)
    np.testing.assert_allclose(case['measured_dtheta_rad'],
                               case['truth_gyro_body_rads']/100, atol=0)
    np.testing.assert_allclose(case['measured_dv_mps'],
                               case['truth_force_body_mps2']/100, atol=0)
    assert np.max(np.abs(case['truth_gyro_body_rads'][:, 2])) > 0
    assert np.max(np.abs(case['truth_gyro_body_rads'][:, 1])) > 0

    def orientation(at):
        state = analytic_path(np.array([at]))
        yaw = state['yaw_rad'][0]
        pitch = state['pitch_rad'][0]
        cy, sy = np.cos(yaw), np.sin(yaw)
        cp, sp = np.cos(pitch), np.sin(pitch)
        return (np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]) @
                np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]]))

    for index in (0, 172, 491, 799):
        center = orientation(t[index])
        derivative = (orientation(t[index]+h)-orientation(t[index]-h))/(2*h)
        skew = center.T @ derivative
        independent_gyro = np.array([skew[2, 1], skew[0, 2], skew[1, 0]])
        np.testing.assert_allclose(independent_gyro,
                                   case['truth_gyro_body_rads'][index], atol=2e-7)
        acceleration = case['truth_acceleration_neu_mps2'][index]
        expected_specific_force = acceleration.copy()
        expected_specific_force[2] += 9.80665
        np.testing.assert_allclose(center @ case['truth_force_body_mps2'][index],
                                   np.array([expected_specific_force[0],
                                             expected_specific_force[1],
                                             -expected_specific_force[2]]), atol=2e-5)


def test_noise_is_deterministic_and_separate_from_motion():
    first = make_control(duration_s=5, rate_hz=100, seed=18)
    repeat = make_control(duration_s=5, rate_hz=100, seed=18)
    smooth = make_control(duration_s=5, rate_hz=100, seed=18,
                          vibration=False)
    for key in ('measured_dtheta_rad', 'measured_dv_mps',
                'receiver_position_neu_m'):
        np.testing.assert_array_equal(first[key], repeat[key])
    for key in ('gyro_white_rads', 'force_white_mps2',
                'gyro_bias_rads', 'force_bias_mps2',
                'coupled_gyro_rads', 'coupled_force_mps2',
                'receiver_error_neu_m'):
        np.testing.assert_array_equal(first[key], smooth[key])
    assert not np.array_equal(first['truth_gyro_body_rads'],
                              smooth['truth_gyro_body_rads'])
    assert not np.array_equal(first['truth_force_body_mps2'],
                              smooth['truth_force_body_mps2'])
    assert not np.array_equal(first['measured_dtheta_rad'],
                              smooth['measured_dtheta_rad'])


def test_truth_error_decomposition_and_input_bounds():
    case = make_control(duration_s=6, rate_hz=100, seed=19)
    np.testing.assert_allclose(case['measured_dtheta_rad']*100,
        case['truth_gyro_body_rads'] + case['gyro_white_rads'] +
        case['gyro_bias_rads'] + case['coupled_gyro_rads'])
    np.testing.assert_allclose(case['measured_dv_mps']*100,
        case['truth_force_body_mps2'] + case['force_white_mps2'] +
        case['force_bias_mps2'] + case['coupled_force_mps2'])
    np.testing.assert_allclose(case['receiver_position_neu_m'],
        case['truth_receiver_position_neu_m'] +
        case['receiver_error_neu_m'])
    assert case['receiver_time_s'][-1] == 6
    with pytest.raises(ValueError):
        make_control(duration_s=0)
    with pytest.raises(ValueError):
        make_control(duration_s=5, rate_hz=0)
    with pytest.raises(ValueError):
        make_control(duration_s=5, seed=-1)
