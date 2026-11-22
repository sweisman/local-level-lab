# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test the fixed error comparisons and the inertial clock contract."""

import numpy as np
import pytest

from lll import esa_direction_holdout_score as score


def test_lower_error_does_not_imply_passing_the_saved_error_reference():
    observed = [1.] * 28
    predicted = {'globe': [1.25] * 28, 'disc': [1.75] * 28}
    result = score.score_setting(observed, predicted, .2)
    assert result['rms_deg'] == {'globe': .25, 'disc': .75}
    assert result['disc_minus_globe_deg'] == .5
    assert result['minimum_change_to_tie_rms_deg'] == .5
    assert result['within_reference'] == {'globe': False, 'disc': False}
    assert score.score_setting(observed, predicted, .25)['within_reference'] == {'globe': True, 'disc': False}


def test_stationary_constant_force_has_zero_measured_angles_in_both_frames():
    times = 400000. + np.arange(400., dtype=float)
    clock = np.linspace(times[0]-.05, times[-1]+.05, 119_731)
    rates = np.zeros((len(clock)-1, 3))
    forces = np.column_stack((rates[:, :2], np.full(len(rates), -9.8)))
    result = score.measured_angles(times, clock, rates, forces)
    for values in result.values():
        assert values == {'uncorrected': [0.] * 28, 'antenna_corrected': [0.] * 28}


def test_clock_gap_fails_before_increment_construction(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail('bad clock entered increment construction')

    monkeypatch.setattr(score, 'construct', unexpected)
    times = 400000. + np.arange(400., dtype=float)
    clock = np.linspace(times[0]-.05, times[-1]+.05, 119_731)
    clock[101] = clock[100]
    rates = np.zeros((len(clock)-1, 3))
    with pytest.raises(ValueError, match='inertial clock'):
        score.measured_angles(times, clock, rates, rates)
