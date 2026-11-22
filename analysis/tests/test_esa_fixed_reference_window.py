# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from lll.esa_fixed_reference_window import match_ground_epochs


def test_fixed_reference_keeps_only_complete_epochs_in_the_stop():
    rows = [(100+i, 2269, t, 0, 10) for i, t in enumerate([0, 30, 60, 90, 120])]
    matches = match_ground_epochs(rows, week=2269, first=7., last=109.)
    assert [row[2] for row, _ in matches] == [30, 60, 90]
    with pytest.raises(ValueError, match='complete normal'):
        match_ground_epochs(rows[:2]+rows[3:], week=2269, first=7., last=109.)


def test_fixed_reference_refuses_a_non_observation_marker():
    rows = [(100, 2269, 30., 1, 2), (200, 2269, 60., 0, 10)]
    with pytest.raises(ValueError, match='complete normal'):
        match_ground_epochs(rows, week=2269, first=7., last=58.)
