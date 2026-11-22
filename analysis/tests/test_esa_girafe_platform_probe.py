# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check exact printed-clock arithmetic and strict byte record boundaries."""

import pytest

from lll.esa_girafe_platform_probe import ROW_BYTES, inspect_block, inspect_range_fragments


def sample(index, *, time_shift=0.):
    time = f'{696.8154+index/1024+time_shift:011.4f}'
    rest = '   -0.162986 -0.394864 -9.761379   -01.20857 +00.02136 -00.01741\r\n'
    raw = (time+rest).encode()
    assert len(raw) == ROW_BYTES
    return raw


def test_lattice_binds_printed_timestamps_to_the_original_row_index():
    first = 100_000
    raw = b''.join(sample(first+i) for i in range(128))
    row = inspect_block(raw, first, expected_rows=128)
    assert row['first_row'] == first and row['last_row'] == first+127
    assert row['local_rounding_compatible']
    assert set(row['step_counts_0p1ms']) == {'9', '10'}
    assert row['phase_min_64ths_tick'] <= 6968154*64 <= row['phase_max_64ths_tick']+32


def test_valid_rows_can_have_an_incompatible_uniform_clock():
    raw = sample(0)+sample(1, time_shift=.01)+sample(2, time_shift=.01)
    assert not inspect_block(raw, 0, expected_rows=3)['local_rounding_compatible']


def test_broken_width_delimiters_or_chronology_fail():
    for data in (sample(0)+sample(1)[:-1], sample(0).replace(b'   ', b' \n ', 1)+sample(1),
                 sample(1)+sample(0)):
        with pytest.raises(ValueError):
            inspect_block(data, 0, expected_rows=2)


def test_range_edges_preserve_variable_width_complete_rows():
    raw = b' -02.00000\r\n'+sample(100)+sample(101).replace(b'-9.761379', b'-10.761379')+b'000697'
    result = inspect_range_fragments(raw, 6968154)
    assert result['rows'] == 2 and result['local_rounding_compatible']
    assert result['first_clock_index'] == 100 and result['last_clock_index'] == 101
    assert result['record_width_counts'] == {'77': 1, '78': 1}


def test_vertical_holdout_preserves_overlap_and_uses_only_post_guard_rows(monkeypatch):
    from lll import esa_girafe_platform_vertical_holdout as holdout
    from lll.studies.artifacts import digest

    prefix = inspect_block(sample(0)+sample(1), 0, expected_rows=2)
    raw = b' -02.00000\r\n'+b''.join(sample(i) for i in range(4000, 6500))+b'000702'
    monkeypatch.setattr(holdout.timing, 'RANGE_BYTES', len(raw))
    receipt = dict(sha256=digest(raw), expected_overlap_sha256=digest(raw[:512]))
    rows, layout = holdout.new_samples(raw, receipt, prefix)
    assert layout['guard_end_s']-layout['first_after_overlap_s'] == 2.
    assert rows[0, 0] >= layout['guard_end_s']
    assert rows[0, 0]-layout['guard_end_s'] <= .0011
    assert rows[0, 1] == -9.761379
    with pytest.raises(ValueError, match='overlap'):
        holdout.new_samples(raw, dict(receipt, expected_overlap_sha256='wrong'), prefix)
