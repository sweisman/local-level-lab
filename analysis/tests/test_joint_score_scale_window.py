# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import pytest

from lll.joint_score_abstention import ARMS, assess


def scores(rotating, still, disc):
    return {model: dict.fromkeys(ARMS, value) for model, value in zip(
        ('sphere_rotating', 'sphere_still', 'flat_still'), (rotating, still, disc), strict=True)}


def test_reference_window_is_closed_at_adequacy_and_open_at_competitor():
    from lll.joint_score_scale_window import windows

    inputs = scores(12.0, 13.0, 900.0)
    result = windows(inputs, epochs=40)
    lower, upper = assess(inputs, epochs=40)['reference_band']
    assert result['windows']['globe'] == [[12 / upper, 13 / lower, True]]
    assert result['windows']['specified'] == [[12 / upper, 13 / upper, False]]
    assert result['windows']['zero'] == []


def test_all_arms_can_keep_competitor_plausible_despite_physical_veto():
    from lll.joint_score_scale_window import windows

    inputs = scores(120.0, 550.0, 550.0)
    inputs['flat_still'][ARMS[0]] = 20.0
    physical = {key: dict.fromkeys(ARMS, key != 'flat_still') for key in inputs}
    result = windows(inputs, epochs=40, physical=physical)
    assert not any(result['windows'].values())
    assert result['compatible_from']['flat_still'] == 20 / result['reference_band'][1]


def test_windows_agree_with_original_rule_across_scale():
    from lll.joint_score_scale_window import windows

    inputs = scores(120.0, 550.0, 3500.0)
    inputs['sphere_rotating'][ARMS[0]] = 4.0
    inputs['sphere_rotating'][ARMS[-1]] = 11.0
    inputs['sphere_still'][ARMS[0]] = 40.0
    inputs['flat_still'][ARMS[0]] = 90.0
    physical = {key: dict.fromkeys(ARMS, True) for key in inputs}
    physical['sphere_rotating'][ARMS[-1]] = False
    intervals = windows(inputs, epochs=40, physical=physical)['windows']
    for exponent in range(-80, 30):
        scale = math.exp(exponent / 10)
        scaled = {model: {arm: v / scale for arm, v in values.items()}
                  for model, values in inputs.items()}
        direct = assess(scaled, epochs=40, physical=physical)
        for label, cases in intervals.items():
            covered = any(a <= scale < b or (closed and scale == b)
                          for a, b, closed in cases)
            assert covered == (label in (direct['shape'], direct['field']))


def test_zero_cost_does_not_supply_adequacy_and_incomplete_stays_incomplete():
    from lll.joint_score_scale_window import windows

    assert windows({}, epochs=40)['status'] == 'incomplete'
    assert windows(scores(0.0, 550.0, 550.0), epochs=40)['windows']['specified'] == []
    with pytest.raises(ValueError, match='nonnegative'):
        windows(scores(-1.0, 0.0, 0.0), epochs=40)
