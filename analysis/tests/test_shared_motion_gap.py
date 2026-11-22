# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import pytest

from lll.shared_motion_gap import integrate_path, minimum_acceleration


def test_closed_motion_recovers_exact_midpoint_displacement():
    times = [0, 1, 2]
    result = minimum_acceleration(times, [(1, 0, 0), (300, -200, 100)], 1)
    assert result['acceleration'] == [[6, 0, 0], [-6, 0, 0], [6, 0, 0]]
    assert result['acceleration_rms_squared'] == 12
    pos, velocity = integrate_path(times, result['acceleration'])
    assert pos == [[0, 0, 0], [1, 0, 0], [0, 0, 0]]
    assert velocity == [[0, 0, 0]]*3


def test_closed_motion_uses_all_axes_and_keeps_irregular_end_conditions():
    times = [F(1, 3), F(3, 4), 2, F(10, 3)]
    taps = [(F(-1, 7), 1, 2), (2, 1, -1), (0, 0, 5)]
    target = F(-3, 10)
    result = minimum_acceleration(times, taps, target)
    pos, velocity = integrate_path(times, result['acceleration'])
    assert any(value for row in result['acceleration'] for value in row[:2])
    assert pos[-1] == velocity[-1] == [0]*3
    assert sum(t*x for row, sample in zip(taps, pos[1:], strict=True)
               for t, x in zip(row, sample, strict=True)) == target
    swapped = minimum_acceleration(times, [tuple(reversed(row)) for row in taps], target)
    assert swapped['acceleration_rms_squared'] == result['acceleration_rms_squared']
    assert swapped['acceleration'] == [list(reversed(row)) for row in result['acceleration']]


def test_closed_motion_rejects_terminal_only_score():
    with pytest.raises(ValueError, match='cannot change this score'):
        minimum_acceleration([0, 1, 2], [(0, 0, 0), (3, -1, 8)], 1)


def test_closed_motion_anchors_raise_minimum_and_leave_exact_gap():
    times = [0, 1, F(3, 2), 2, 3, 4]
    taps = [(3, 0, -1), (0, 0, 0), (1, 2, 0), (0, 0, 0), (0, 0, 0)]
    anchors = [times[2], times[4]]
    target = F(2, 3)
    unanchored = minimum_acceleration(times, taps, target)
    motion = minimum_acceleration(times, taps, target, position_anchors=anchors)
    pos, speed = integrate_path(times, motion['acceleration'])
    assert motion['acceleration_rms_squared'] > unanchored['acceleration_rms_squared']
    assert all(pos[times.index(t)] == [0]*3 for t in anchors)
    assert pos[-1] == speed[-1] == [0]*3
    assert sum(x*w for point, row in zip(pos[1:], taps, strict=True)
               for x, w in zip(point, row, strict=True)) == target


def test_closed_motion_rejects_score_supported_only_at_fixed_positions():
    with pytest.raises(ValueError, match='cannot change this score'):
        minimum_acceleration([0, 1, 2], [(1, 2, 3), (4, 5, 6)], 1, position_anchors=[1])
