# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check phase accumulation using fixed windows and exact common satellite IDs."""

import pytest

from lll.esa_raw_phase_timescale import blocks, stacked_contrast


def row(second, satellites, observed, predicted):
    return dict(first_gps_seconds=second, last_gps_seconds=second+1,
                satellites=satellites, pairs={'test': dict(measured_range_m=observed, predicted_range_m=predicted)})


def test_accumulation_uses_common_satellites_and_removes_shared_clock():
    rows = [
        row(10, [1, 2, 3, 4, 5, 6], [32., 33., 34., 35., 36., 200.], [8., 9., 10., 11., 12., 205.]),
        row(11, [5, 4, 3, 2, 1, 7], [8., 7., 6., 5., 4., 150.], [4., 3., 2., 1., 0., 150.]),
    ]
    out = stacked_contrast(rows)
    assert out['satellites'] == [1, 2, 3, 4, 5]
    assert out['pairs']['test']['measured_m'] == [-4., -2., 0., 2., 4.]
    assert out['pairs']['test']['predicted_m'] == [-4., -2., 0., 2., 4.]


def test_blocks_preserve_clock_exclusions_and_do_not_count_partial_tails():
    rows = [row(index, list(range(1, 7)), [0.]*6, [1.]*6) for index in range(9)]
    del rows[2]['satellites']
    rows[2]['skipped'] = 'original clock step'
    chunks, tail = blocks(rows, 4)
    assert [chunk[0]['first_gps_seconds'] for chunk in chunks] == [0, 4]
    assert tail == 1
    assert stacked_contrast(chunks[0]) == {'skipped': 'archived interval excluded'}
    assert len(stacked_contrast(chunks[1])['satellites']) == 6
    with pytest.raises(ValueError, match='consecutive'):
        stacked_contrast([rows[0], rows[3]])
