"""Independent local integration of a generated airborne IMU stream."""

import numpy as np
import pytest

from lll.esa_motion_error_controls import make_control
from lll.esa_generated_imu_propagation import propagate_generated


def test_clean_increments_reconstruct_analytic_positions():
    case = make_control(duration_s=8, rate_hz=100, seed=51,
                        vibration=True, errors=False)
    result = propagate_generated(case)
    np.testing.assert_allclose(result['measured_position_neu_m'],
                               result['truth_integrated_position_neu_m'], atol=0)
    assert np.max(np.abs(result['truth_integrated_position_neu_m']-
                         case['truth_receiver_position_neu_m'])) < .05
    assert result['receiver_epochs'] == 9
    assert result['original_reads'] == 0


def test_noisy_increment_and_receiver_errors_are_kept_distinct():
    case = make_control(duration_s=8, rate_hz=100, seed=52,
                        vibration=True, errors=True)
    result = propagate_generated(case)
    np.testing.assert_allclose(result['receiver_position_neu_m'],
                               case['receiver_position_neu_m'], atol=0)
    np.testing.assert_allclose(result['sensor_only_position_error_neu_m'],
        result['measured_position_neu_m']-
        result['truth_integrated_position_neu_m'], atol=0)
    assert np.max(np.abs(result['sensor_only_position_error_neu_m'][-1])) > 0
    assert not np.array_equal(result['receiver_error_neu_m'],
                              result['sensor_only_position_error_neu_m'])


def test_corrupt_alignment_fails_closed():
    case = make_control(duration_s=5, rate_hz=100, seed=53)
    case['measured_dtheta_rad'] = case['measured_dtheta_rad'][:-1]
    with pytest.raises(ValueError):
        propagate_generated(case)
