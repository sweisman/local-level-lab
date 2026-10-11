# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_coupled_controls as controls


@pytest.mark.parametrize('near_boundary',[False,True])
def test_coupled_clock_calibration_control_has_known_recovered_answer(near_boundary):
    row=controls.run_control(near_boundary)
    assert row['passed']
    assert row['correct_clock']['maximum_position_error_m']<5e-4
    assert row['wrong_clock']['maximum_position_error_m']>.01
    assert row['coupled_compensation']['maximum_position_error_m']<5e-4
    assert row['coupled_compensation']['maximum_attitude_error_rad']<1e-9
    assert row['external_time_max_position_error_m']>.01
    assert row['production_primitive_max_difference']<1e-9
    assert row['calibration_recovery']['maximum_gain_error']<1e-8
    assert row['calibration_recovery']['maximum_bias_error']<1e-9
    assert row['observed_fit_starts']==row['native_predictions']==0
    assert row['full_archival_solver_qualified'] is False


def test_true_increment_generator_includes_exact_specific_force_integral():
    fixture=controls.fixture(False)
    # The generated integral is independently checked by numerical quadrature.
    period=fixture['period_s']; w=fixture['rates'][0]; c=fixture['initial_attitude']
    force=fixture['acceleration'][0]-fixture['gravity']
    x=np.linspace(0,period,1001)
    rates=np.array([(c@controls.rotation(w*t)).T@force for t in x])
    quadrature=np.trapezoid(rates,x,axis=0)
    assert np.allclose(fixture['true_dv'][0],quadrature,rtol=0,atol=1e-11)


def test_known_calibration_respects_mount_and_all_three_axes():
    f=controls.fixture(False)
    theta,dv=controls.correct(f,f['calibration'],f['period_s'])
    assert np.allclose(theta,f['true_theta'],atol=1e-14,rtol=0)
    assert np.allclose(dv,f['true_dv'],atol=1e-14,rtol=0)


def test_invalid_gain_or_clock_is_rejected():
    f=controls.fixture(False)
    with pytest.raises(ValueError): controls.correct(f,dict(f['calibration'],gyro_gain=np.array([-1.,0.,0.])),f['period_s'])
    with pytest.raises(ValueError): controls.correct(f,f['calibration'],-.005)
