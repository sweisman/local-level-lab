# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import pytest

from lll.esa_motion_axis_support import axis_replay
from lll.shared_motion_gap import minimum_acceleration


def test_closed_axis_replay_preserves_gap_and_exact_anchors():
    times = list(map(F, range(5)))
    taps = [(2, 0, 1), (0, 0, 0), (1, 0, 2), (0, 0, 0)]
    motion = minimum_acceleration(times, taps, 1, position_anchors=[2])
    result = axis_replay(times, taps, F(1), [F(2)], motion['acceleration'])
    assert result['energy_fraction']['east'] == 0
    assert result['cases']['east_only']['possible'] is False
    assert result['cases']['north_only']['score_shift_exact'] == '1'
    assert result['cases']['north_only']['peak_position_m'][1:] == [0., 0.]
    assert result['cases']['horizontal'] == result['cases']['north_only']
    assert result['cases']['unrestricted']['acceleration_rms_mps2'] < result['cases']['north_only']['acceleration_rms_mps2']


def test_axis_replay_rejects_a_different_score_gap():
    times = list(map(F, range(5)))
    taps = [(2, 1, 1), (0, 0, 0), (1, 0, 2), (0, 0, 0)]
    motion = minimum_acceleration(times, taps, 1, position_anchors=[2])
    with pytest.raises(ValueError, match='fixed score'):
        axis_replay(times, taps, F(2), [F(2)], motion['acceleration'])
