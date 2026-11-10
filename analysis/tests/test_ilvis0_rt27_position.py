# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded receiver-boundary accounting never repairs interior corruption."""
import hashlib
import gzip
import struct

import pytest

from lll import ilvis0_rt27_position as audit
from test_trimble_enhanced_position import position_packet
from test_ilvis0_processing import group, nmea


def test_complete_checked_position_and_explicit_partial_boundaries():
    packet = position_packet()
    prefix, tail = packet[-7:], packet[:9]
    result = audit.audit_receiver_bytes(prefix+packet+tail)
    assert result['prefix_bytes'] == len(prefix)
    assert result['prefix_sha256'] == hashlib.sha256(prefix).hexdigest()
    assert result['tail_bytes'] == len(tail)
    assert result['tail_sha256'] == hashlib.sha256(tail).hexdigest()
    assert result['packet_counts'] == {'57':1}
    assert len(result['positions']) == 1
    assert result['positions'][0]['gps_week'] == 1865
    assert not result['whole_stream_complete']
    assert result['interior_valid']


def test_invalid_interior_packet_is_not_resynchronized():
    good = position_packet()
    bad = bytearray(good)
    bad[-2] ^= 1
    with pytest.raises(ValueError, match='checksum/end failure'):
        audit.audit_receiver_bytes(good+bad+good)


def test_unbounded_initial_gap_and_missing_position_are_rejected():
    with pytest.raises(ValueError, match='initial receiver boundary'):
        audit.audit_receiver_bytes(b'X'*513+position_packet())
    with pytest.raises(ValueError, match='no enhanced-position'):
        audit.audit_receiver_bytes(b'\x02\x00\x55\x00\x55\x03')


def test_original_extraction_reads_only_checked_group10001(tmp_path):
    receiver = position_packet()
    raw = group(4, b'not decoded')+group(10001,
        struct.pack('<HIH', 16, 0, len(receiver))+receiver)
    source = tmp_path/'source.013.gz'
    source.write_bytes(gzip.compress(raw, mtime=0))
    result = audit.extract_primary_receiver(source, hashlib.sha256(raw).hexdigest())
    assert result['receiver_bytes'] == receiver
    assert result['original_bytes'] == len(raw)
    assert result['original_frames'] == 2
    assert result['receiver_packets'] == 1
    with pytest.raises(ValueError, match='original source hash'):
        audit.extract_primary_receiver(source, '0'*64)


def test_receiver_position_matches_its_own_gga_without_fitting():
    binary = position_packet(milliseconds=132356000)
    text = nmea('GPGGA,124539.0,5830.000000,S,07415.000000,W,1,11,0.9,11990.125,M,10.000,M,,')
    result = audit.audit_receiver_bytes(binary+text)
    check = audit.compare_receiver_positions(result['positions'], result['gga_fixes'],
                                             leap_seconds=17)
    assert check['matched_epochs'] == 1
    assert check['maximum_abs_north_m'] < 0.001
    assert check['maximum_abs_east_m'] < 0.001
    assert check['maximum_abs_up_m'] < 0.001
    assert not check['independent_accuracy_established']


def test_gga_matching_rejects_a_wrong_leap_second():
    result = audit.audit_receiver_bytes(position_packet(milliseconds=132356000)
        +nmea('GPGGA,124539.0,5830.000000,S,07415.000000,W,1,11,0.9,11990.125,M,10.000,M,,'))
    with pytest.raises(ValueError, match='no time-matched'):
        audit.compare_receiver_positions(result['positions'], result['gga_fixes'],
                                         leap_seconds=16)
