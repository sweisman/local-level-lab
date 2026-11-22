# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer replay projection and time-cut checks."""

from fractions import Fraction as F

import pytest

from lll.contrast_replay import summarize_error


def test_replay_preserves_subtraction_and_projects_signed_error_enclosure():
    delta = [[1e16, 0], [0, .5], [3, 2]]
    baseline = [[1, 0], [0, 0], [0, 0]]
    affine = [[1e16, 0], [0, 0], [0, 0]]
    taps = [(1, 1), (0, 0), (0, 0), (-2, -1), (-1, 1), (1, 1)]
    result = summarize_error(delta, baseline, affine, [1, 4], [0, 2, 3], taps, cut=2)
    assert result['score_bounds'] == (0, 8)
    assert result['earlier_velocity_max'] == [F(1, 2), 1]
    assert result['later_velocity_max'] == [3, 6]
    assert result['later_position_max'] == [3, 8]


def test_replay_requires_all_epochs_and_complete_cut():
    args = [[0]], [[0]], [[0]], [1], [0, 1, 2], [(0, 0)]*3
    with pytest.raises(ValueError, match='one coordinate vector per epoch'):
        summarize_error(*args, cut=2)
    with pytest.raises(ValueError, match='strictly ordered'):
        summarize_error(*args[:4], [1, 1, 2], args[-1], cut=2)
