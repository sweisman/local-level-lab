# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_group_companion_receiver import _matched, _score
from lll.ilvis0_receiver_overlap import WEEK_MS


def test_match_uses_exact_epoch_tags_across_week_boundary():
    tags = [8*WEEK_MS+17_000, 8*WEEK_MS+18_001, 8*WEEK_MS+19_000]
    assert _matched([604799., 0., 1.], dict.fromkeys(tags), 18) == [(0, tags[0]), (2, tags[2])]
    with pytest.raises(ValueError, match='ambiguous'):
        _matched([0., 604800.], dict.fromkeys(tags), 18)


def test_score_applies_the_earlier_receiver_offset_to_later_positions():
    delta = np.array([[3., 4., 2.], [3., 4., 2.]])
    earlier = np.array([[8., 0., 2.], [10., 0., 4.]])
    later = np.array([[12., 4., 5.], [12., 4., 5.]])
    result = _score(delta, earlier, later)
    assert result['training_offset_neu_m'] == [9., 0., 3.]
    assert result['errors'] == {
        'onboard': {'horizontal_m': 5., 'height_m': 2.},
        'companion_raw': {'horizontal_m': 9., 'height_m': 3.},
        'companion_training_offset': {'horizontal_m': 0., 'height_m': 0.}}
