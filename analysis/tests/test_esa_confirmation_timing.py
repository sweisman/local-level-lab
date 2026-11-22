# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise fixed-width byte alignment and strict timestamp support."""

import io

import pytest


def raw_row(value):
    # The continuation of the record is intentionally opaque to this audit.
    return (f'{value} value fields'.ljust(119)+'\n').encode('ascii')


def test_timing_records_require_framing_and_keep_printed_precision():
    from lll.esa_confirmation_timing import timestamp

    assert timestamp(raw_row('384897.45354201')) == 38489745354201
    with pytest.raises(ValueError):
        timestamp(raw_row('384897.45354201')[:-1])
    with pytest.raises(ValueError):
        timestamp(raw_row('604800.00000000'))


def test_timing_gap_at_the_requested_start_is_counted():
    from lll.esa_confirmation_timing import audit_stream

    values = ['2.00000000', '2.00333333', '2.01000000', '2.01333333']
    output = audit_stream(io.BytesIO(b''.join(map(raw_row, values))), 480, (200500000, 201100000))
    assert output['brackets_slice'] is True
    assert output['slice_gap_count'] == 1
    assert not output['timing_supported']
    output = audit_stream(io.BytesIO(b''.join(map(raw_row, values))), 480, (201000001, 201300000))
    assert output['slice_gap_count'] == 0
    assert output['timing_supported']


def test_timing_rejects_missing_bytes_and_reversed_time():
    from lll.esa_confirmation_timing import audit_stream

    with pytest.raises(ValueError, match='byte count'):
        audit_stream(io.BytesIO(raw_row('9.00100000')), 240, (1, 2))
    with pytest.raises(ValueError, match='strictly increasing'):
        sequence = raw_row('9.00100000')+raw_row('9.00000000')
        audit_stream(io.BytesIO(sequence), 240, (1, 2))


def test_bounded_range_is_record_aligned_and_excludes_the_header():
    from lll.esa_confirmation_timing import range_spec

    assert range_spec(120*10000, 1000000000, (1000000000, 1000400000)) == (120, 180479)
    with pytest.raises(ValueError, match='fixed-width'):
        range_spec(120*10000+1, 1000000000, (1000000000, 1000400000))
