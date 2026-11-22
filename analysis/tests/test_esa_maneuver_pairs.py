# SPDX-License-Identifier: AGPL-3.0-or-later
from lll.esa_maneuver_pairs import select_pairs


def test_turn_comparison_uses_adjacent_quiet_blocks_and_nonoverlapping_control():
    values = [.1, .2, .1, .3, 7., .2, .3, .2, .1, .5]
    result = select_pairs(values)
    assert result['turn_centres'] == [4]
    assert result['matches'] == [dict(turn=4, straight=1)]


def test_no_quiet_control_retains_unmatched_turn():
    result = select_pairs([.1, 7., .2, 7., .1])
    assert result['turn_centres'] == [1, 3]
    assert result['unmatched_turns'] == [1, 3]
    assert not result['matches']
