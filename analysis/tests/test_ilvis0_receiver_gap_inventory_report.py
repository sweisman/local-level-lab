"""Saved-only publication of the receiver-gap inventory."""

import pytest

from lll.ilvis0_receiver_gap_inventory_report import build_rows


def test_build_rows_preserves_blocks_and_decoder_abstention():
    tasks = [
        dict(identity='a', index=0, filename='a.013', start_utc='start',
             end_utc='end', source_sha256='source-a'),
        dict(identity='b', index=1, filename='b.013', start_utc='start-b',
             end_utc='end-b', source_sha256='source-b'),
    ]
    results = {
        'a': dict(passed=True, selected_rows=7, accepted_rows=5,
                  accepted_blocks=1, receiver_table_sha256='table-a',
                  block_inventory=dict(gaps=[dict(gap_s=2.0)], blocks=[
                      dict(accepted=True, first_table_row=4, last_table_row=8,
                           sample_count=5, start_s=100.0, end_s=104.0,
                           reason='supported'),
                      dict(accepted=False, first_table_row=9, last_table_row=10,
                           sample_count=2, start_s=106.0, end_s=107.0,
                           reason='too_few_samples'),
                  ])),
        'b': dict(passed=False, reason='prior_receiver_decoder_failure'),
    }
    stretches, blocks = build_rows(tasks, results)
    assert len(stretches) == 2
    assert stretches[0]['accepted_blocks'] == 1
    assert stretches[0]['gap_count'] == 1
    assert stretches[0]['accepted_duration_s'] == 4.0
    assert stretches[1]['disposition'] == 'abstain'
    assert stretches[1]['reason'] == 'prior_receiver_decoder_failure'
    assert [(row['accepted'], row['first_table_row'], row['last_table_row'])
            for row in blocks] == [(True, 4, 8), (False, 9, 10)]


def test_build_rows_rejects_missing_or_mismatched_result():
    tasks = [dict(identity='a', index=0)]
    with pytest.raises(ValueError):
        build_rows(tasks, {})
