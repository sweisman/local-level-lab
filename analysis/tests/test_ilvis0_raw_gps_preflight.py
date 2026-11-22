"""Checks for decoding independently preserved raw receiver spans."""

import hashlib

import pytest

from lll import ilvis0_raw_gps_preflight as preflight
from test_trimble_observations import rt17, rt27


def packet(payload):
    body = bytes([0, 0x57, len(payload)])+payload
    return b'\x02'+body+bytes([sum(body)%256, 3])


def survey(record, n=0x11, reply=1, payload=None):
    return packet(bytes([record['subtype'], n, reply, record['flags']])
                  +(record['payload'] if payload is None else payload))


def bounds(prefix=b'', tail=b''):
    return {name+'_bytes': len(data) for name, data in (('prefix', prefix), ('tail', tail))} | {
        name+'_sha256': hashlib.sha256(data).hexdigest() for name, data in
        (('prefix', prefix), ('tail', tail))}


def test_survey_records_keep_offsets_and_do_not_complete_a_partial_tail():
    one, two = rt17(), rt27()
    prefix, tail = b'end of earlier frame\r\n', b'\x02\x00'
    raw = prefix+survey(one)+survey(two)+survey(two, n=0x12, reply=2, payload=b'\x00')+tail
    result = preflight.decode(raw, bounds(prefix, tail), 1527)
    assert [r['format'] for r in result['records']] == ['RT17', 'RT27']
    assert result['records'][0]['first_stream_offset'] == len(prefix)
    assert result['tail_incomplete_survey_records'] == 1
    assert result['binary_packets'] == 3
    assert result['records'][0]['gps_week_seconds'] == 216130.


def test_midstream_orphan_and_changed_boundary_are_rejected():
    r = rt27()
    with pytest.raises(ValueError, match='missing, duplicate'):
        preflight.decode(survey(r)+survey(r, n=0x22, reply=9), bounds(), 1527)
    with pytest.raises(ValueError, match='boundary hash'):
        preflight.decode(b'x'+survey(r), bounds(b'y'), 1527)


def test_initial_orphan_is_retained_as_a_count_never_a_measurement():
    r = rt27()
    raw = survey(r, n=0x23, reply=4, payload=b'xx')+survey(r, n=0x33, reply=4, payload=b'yy')+survey(r)
    result = preflight.decode(raw, bounds(), 1527)
    assert len(result['records']) == 1
    assert result['initial_unassembled_survey_pages'] == 2


def test_duplicate_survey_epochs_remain_ambiguous():
    r = dict(gps_week=1527, gps_week_seconds=216130.)
    tag = preflight.tag(r)
    result = preflight.associate([r, r | dict(format='RT27')], {tag})
    assert result == ({}, {tag})
