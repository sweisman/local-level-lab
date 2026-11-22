# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_native_rolling_transfer import matched_window


def test_only_returns_the_exact_declared_later_epochs():
    rows = [dict(time_s=float(i+100), latitude_deg=55.) for i in range(6)]
    assert matched_window(rows, rows[:2], [0.,1.,2.,3.], origin=100.) == rows[2:4]


def test_rejects_changed_training_prefix_and_reordered_scoring():
    rows = [dict(time_s=float(i+100), latitude_deg=55.) for i in range(4)]
    with pytest.raises(ValueError, match='prefix'):
        matched_window(rows, rows[1:3], [0.,1.,2.,3.], origin=100.)
    with pytest.raises(ValueError, match='query'):
        matched_window(rows, rows[:2], [0.,1.,3.,2.], origin=100.)
