"""Receiver-only gap splitting retains original row provenance."""

import pytest


def test_gap_split_preserves_every_row_and_original_indices():
    from lll.ilvis0_receiver_support import split_gga_blocks
    rows = [dict(utc_week_s=float(t)) for t in (0, 1, 2, 10, 11, 12, 13)]
    result = split_gga_blocks(rows, maximum_gap_s=2., minimum_samples=4)
    assert [(block['first_index'], block['last_index'], block['accepted'])
            for block in result['blocks']] == [(0, 2, False), (3, 6, True)]
    assert result['blocks'][0]['reason'] == 'sample_count'
    assert result['blocks'][1]['reason'] == 'supported'
    assert result['gaps'] == [dict(left_index=2, right_index=3,
                                   duration_s=8.)]
    assert sum(block['sample_count'] for block in result['blocks']) == len(rows)
    assert result['interpolated_measurements'] is False


def test_enhanced_receiver_positions_keep_their_own_provenance():
    from lll.ilvis0_receiver_support import split_receiver_blocks
    result = split_receiver_blocks(
        [100., 101., 108., 109.],
        source_kind='primary_receiver_enhanced_position',
        maximum_gap_s=2., minimum_samples=3)
    assert result['source'] == 'primary_receiver_enhanced_position'
    assert [(row['first_index'], row['last_index']) for row in result['blocks']] == [
        (0, 1), (2, 3)]
    assert all(row['accepted'] is False for row in result['blocks'])


@pytest.mark.parametrize('times', [(0., 1., 1.), (0., 2., 1.),
                                    (0., float('nan'), 2.)])
def test_gap_split_rejects_invalid_receiver_times(times):
    from lll.ilvis0_receiver_support import split_gga_blocks
    with pytest.raises(ValueError, match='ordered'):
        split_gga_blocks([dict(utc_week_s=t) for t in times],
                         maximum_gap_s=2., minimum_samples=3)
