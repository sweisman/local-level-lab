"""Known-component checks for multi-scale rate contrasts."""

import pytest

from lll.esa_motion_error_contrast import analyze


def test_contrast_components_reconstruct_observation_and_expose_motion():
    result = analyze(duration_s=30, rate_hz=300, seed=23)
    assert result['max_reconstruction_error'] < 1e-12
    assert result['scientific_decision'] == 'abstain'
    assert result['observed_error_law_qualified'] is False
    assert result['original_reads'] == 0
    assert result['protected_reads'] == 0
    by_stride = {row['stride']: row for row in result['rows']}
    assert set(by_stride) == {1, 3, 30, 300}
    row = by_stride[3]
    assert row['rms']['physical_vibration'][1] > row['rms']['gyro_white'][1]
    assert row['rms']['physical_vibration'][3] > row['rms']['force_white'][3]
    assert row['naive_gyro_y_white_inflation'] > 10
    assert row['gyro_y_force_x_correlation']['physical_vibration'] < -.5
    assert row['gyro_y_force_x_correlation']['coupled_error'] > .99
    assert by_stride[30]['gyro_y_force_x_correlation']['physical_vibration'] is None


def test_invalid_control_scope_is_rejected():
    with pytest.raises(ValueError):
        analyze(duration_s=1, rate_hz=300)
