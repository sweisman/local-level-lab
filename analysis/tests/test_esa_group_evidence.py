# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_group_evidence import receiver_split, summarize_windows


def test_receiver_split_uses_exact_stride_and_never_overlaps():
    earlier, later = receiver_split(200, 206, 2, 2)
    assert list(earlier) == [200, 202]
    assert list(later) == [204, 206]
    with pytest.raises(ValueError, match='receiver'):
        receiver_split(200, 205, 2, 2)


def test_summary_counts_shared_epochs_and_leaves_planned_rows_out():
    original_train, original_test = receiver_split(20, 38, 6, 4)
    rolling_train, rolling_test = receiver_split(20, 30, 3, 3)
    alternate_train, alternate_test = receiver_split(20, 34, 6, 2)
    planned_train, planned_test = receiver_split(40, 48, 3, 2)
    rows = [dict(id=name, state=state, train=train, later=test)
            for name, state, train, test in (
                ('long', 'scored', original_train, original_test),
                ('earlier', 'scored', rolling_train, rolling_test),
                ('shorter', 'scored', alternate_train, alternate_test),
                ('candidate', 'selected_only', planned_train, planned_test))]
    totals = summarize_windows(rows)
    assert totals == dict(scored_cuts=3, selected_only_cuts=1, later_report_slots=9,
                          distinct_later_reports=7, later_reports_used_for_training=3,
                          distinct_training_reports=6)
    assert [row['later_in_other_scoring'] for row in rows] == [2, 0, 2, None]
    assert [row['later_in_other_training'] for row in rows] == [0, 3, 0, None]


def test_reject_same_cut_or_overlap_within_a_cut():
    train, later = receiver_split(20, 30, 3, 3)
    row = dict(id='test', state='scored', train=train, later=later)
    with pytest.raises(ValueError):
        summarize_windows([row, row.copy()])
    with pytest.raises(ValueError):
        summarize_windows([dict(row, later=train)])
