"""A five-hertz receiver cannot resolve all airborne IMU motion."""

import numpy as np

from lll.esa_gnss_alias_control import build_control


def test_5hz_position_and_velocity_can_alias_real_motion():
    paired = build_control(duration_s=30)
    motion = paired['motion']
    coupling = paired['sensor_coupling']
    assert len(paired['receiver_time_s']) == 151
    assert len(paired['imu_time_s']) == 9000
    for name in ('measured_gyro_rads', 'measured_force_mps2',
                 'reported_position_m', 'reported_velocity_mps'):
        np.testing.assert_array_equal(motion[name], coupling[name])
    assert paired['receiver_rate_hz'] == 5
    assert paired['vibration_hz'] == 10
    assert paired['maximum_true_gyro_difference_rads'] > .03
    np.testing.assert_allclose(
        motion['true_receiver_position_m'][:, 0]
        -coupling['true_receiver_position_m'][:, 0], .0002, atol=1e-11)
    np.testing.assert_array_equal(
        motion['true_receiver_velocity_mps'],
        coupling['true_receiver_velocity_mps'])
    assert paired['earth_model_test'] is False
