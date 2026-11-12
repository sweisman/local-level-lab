# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched generated gyro calibration cases for future finite studies."""
import math

import numpy as np
import pytest
from test_airquantumgrav_prediction import kernels


def fixture(sensor_case):
    from lll.airquantumgrav_noisy_inputs import construct, noise_settings
    from lll.airquantumgrav_training_controls import recipe
    r = dict(recipe(), rate_hz=200, duration_s=2., queries=9,
             query_start_s=.1, query_step_s=.2, noise=noise_settings(seed=71),
             sensor_case=sensor_case)
    spec = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                start=0, policy_id='reported-short-v1')
    return construct(spec, r, reserve=lambda **work: None)


def test_boundary_case_changes_only_z_gyro_calibration_not_receiver_or_noise():
    from lll.airquantumgrav_observation_truth import sensor_parameters
    from lll.airquantumgrav_training_controls import parameter_limits
    interior = fixture('interior')
    boundary = fixture('z_gyro_boundary')
    p = sensor_parameters(1, 'z_gyro_boundary')
    limits = parameter_limits()
    assert p['gyro_gain_z'] == limits['gyro_gain_z']
    assert p['gyro_bias_z'] == limits['gyro_bias_z']
    assert sensor_parameters(-1, 'z_gyro_boundary')['gyro_gain_z'] == -limits['gyro_gain_z']
    assert sensor_parameters(-1, 'z_gyro_boundary')['gyro_bias_z'] == -limits['gyro_bias_z']
    assert p['gyro_gain_z'] != sensor_parameters(1, 'interior')['gyro_gain_z']
    assert p['gyro_bias_z'] != sensor_parameters(1, 'interior')['gyro_bias_z']
    assert math.isfinite(p['gyro_bias_z'])
    assert interior['training_rows'] == boundary['training_rows']
    np.testing.assert_array_equal(interior['dt'], boundary['dt'])
    np.testing.assert_array_equal(interior['dv'], boundary['dv'])
    np.testing.assert_array_equal(interior['theta'][:, :2], boundary['theta'][:, :2])
    assert np.any(interior['theta'][:, 2] != boundary['theta'][:, 2])
    assert interior['binding']['noise_increment_sha256'] == boundary['binding']['noise_increment_sha256']
    assert boundary['binding']['sensor_case'] == 'z_gyro_boundary'


def test_unknown_calibration_case_fails_before_input_construction():
    from lll.airquantumgrav_observation_truth import sensor_parameters
    with pytest.raises(ValueError, match='sensor case'):
        sensor_parameters(1, 'not-a-case')


def test_boundary_case_reaches_native_fit_with_truth_still_withheld(kernels):
    from lll.airquantumgrav_noisy_inputs import construct, noise_settings
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.airquantumgrav_training_controls import _spec, recipe
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.generated_prediction import calculate

    spec = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                start=0, policy_id='reported-short-v1')
    r = dict(recipe(), rate_hz=200, duration_s=2., queries=9,
             query_start_s=.1, query_step_s=.2, maximum_evaluations=8,
             noise=noise_settings(seed=71), sensor_case='z_gyro_boundary')
    material = construct(spec, r, reserve=lambda **work: None)
    arguments, sign = _spec({key: value for key, value in spec.items()
                             if key != 'policy_id'})
    saved = {}

    def truth(times):
        assert 'forecast.json' in saved
        return receiver_samples(times=times, sign=sign, **arguments,
                                height_profile='climb',
                                gravity_model='inverse_square_height')

    result = calculate(
        spec, r, material=material,
        train_and_forecast=train_and_forecast,
        kernel_factory=lambda anchor: (*kernels, {'anchor': anchor}),
        reserve=lambda **work: None,
        reserve_construction=lambda **work: None,
        save=lambda name, value: saved.__setitem__(name, value),
        truth=truth, check_continue=lambda: None)
    assert result['evaluations'] <= 8
    assert saved['input-binding.json']['noise']['sensor_case'] == 'z_gyro_boundary'
    assert len(saved['fit.json']['active_parameters']) == 26
    assert result['scientific_decision'] == 'abstain'
