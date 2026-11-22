"""Two physical causes can yield the same sampled IMU/GNSS observations."""

import math

import numpy as np
import pytest


def test_motion_and_sensor_coupling_have_identical_sampled_observations():
    from lll.esa_error_attribution_adversary import paired_explanations

    paired = paired_explanations(duration_s=6, rate_hz=300,
        vibration_hz=10, seed=31415)
    motion, coupling = paired['motion'], paired['sensor_coupling']
    for key in ('measured_gyro_rads', 'measured_force_mps2',
                'reported_position_m'):
        np.testing.assert_array_equal(motion[key], coupling[key])
    assert np.any(motion['true_gyro_rads'] != coupling['true_gyro_rads'])
    assert np.any(motion['true_force_mps2'] != coupling['true_force_mps2'])
    np.testing.assert_allclose(
        motion['true_position_m'][:, 0] -
        coupling['true_position_m'][:, 0], 0.0002, atol=1e-12)
    assert paired['observationally_distinguishable'] is False


def test_motion_world_uses_analytic_pitch_and_translation_derivatives():
    from lll.esa_error_attribution_adversary import paired_explanations

    paired = paired_explanations(duration_s=6, rate_hz=300,
        vibration_hz=10, seed=1)
    t = paired['imu_time_s']
    motion = paired['motion']
    omega = 2*math.pi*10
    theta = 0.0005*np.sin(omega*t)
    acceleration_x = -0.0002*omega**2*np.cos(omega*t)
    np.testing.assert_allclose(motion['true_gyro_rads'][:, 1],
        0.0005*omega*np.cos(omega*t), rtol=0, atol=1e-14)
    np.testing.assert_allclose(motion['true_force_mps2'][:, 0],
        acceleration_x*np.cos(theta)-9.80665*np.sin(theta),
        rtol=0, atol=1e-14)
    np.testing.assert_allclose(motion['true_force_mps2'][:, 2],
        acceleration_x*np.sin(theta)+9.80665*np.cos(theta),
        rtol=0, atol=1e-14)


def test_input_validation_and_independent_seed_replay():
    from lll.esa_error_attribution_adversary import paired_explanations

    first = paired_explanations(duration_s=6, rate_hz=300,
        vibration_hz=10, seed=27)
    second = paired_explanations(duration_s=6, rate_hz=300,
        vibration_hz=10, seed=27)
    different = paired_explanations(duration_s=6, rate_hz=300,
        vibration_hz=10, seed=28)
    np.testing.assert_array_equal(first['motion']['measured_gyro_rads'],
                                  second['motion']['measured_gyro_rads'])
    assert not np.array_equal(first['motion']['measured_gyro_rads'],
                              different['motion']['measured_gyro_rads'])
    for kwargs in (dict(duration_s=0), dict(rate_hz=100),
                   dict(vibration_hz=10.5), dict(vibration_hz=150),
                   dict(seed=-1)):
        with pytest.raises(ValueError):
            paired_explanations(**kwargs)


def test_saved_control_summary_preserves_ambiguity_and_scope():
    from lll.esa_error_attribution_adversary import summarize_control

    report = summarize_control(duration_s=6, seed=3)
    assert report['all_sampled_observations_identical'] is True
    assert report['maximum_sample_difference'] == 0.
    assert report['maximum_true_gyro_difference_rads'] > 0.
    assert report['maximum_true_force_difference_mps2'] > 0.
    assert report['gyro_y_force_x_contrast_correlation'] < 0.
    assert report['original_reads'] == report['protected_reads'] == 0
    assert report['scientific_decision'] == 'abstain'
