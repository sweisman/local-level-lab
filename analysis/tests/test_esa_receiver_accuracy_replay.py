# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_receiver_accuracy_replay import score_setting


def test_relative_preference_and_absolute_accuracy_remain_separate():
    later = [[.5, 1., 0.], [.5, 1., 0.]]
    forecasts = {model: [[.5, 1., height]]*2 for model, height in
                 [('sphere_rotating', 35.), ('sphere_still', 38.), ('flat_still', 60.)]}
    result = score_setting(forecasts, later)
    assert result['ranking']['shape_lower_error_family'] == 'globe'
    assert result['ranking']['field_lower_error_model'] == 'specified_field'
    assert result['ranking']['preferred_accuracy'] is False
    assert result['headroom_m']['vertical_rms_m'] == pytest.approx(-5.)
    assert result['minimum_breaking_shift_rms_m']['vertical_rms_m'] == 0.
