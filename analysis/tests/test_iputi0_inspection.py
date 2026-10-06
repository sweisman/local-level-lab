# SPDX-License-Identifier: AGPL-3.0-or-later
import struct

import pytest

from inspect_iputi0_sample import clock_summary, navigation, scan


def packet(mid, payload):
    header = [0x81ff, mid, len(payload)//2, 0x8000]
    header.append(-sum(header) % 65536)
    words = struct.unpack('<' + str(len(payload)//2) + 'H', payload)
    return struct.pack('<5H', *header) + payload + struct.pack('<H', -sum(words) % 65536)


def test_recover_valid_frames_inside_failed_candidate_without_repair():
    status = packet(3500, bytes(32))
    nav = packet(3501, bytes(44))
    damaged = nav[:11] + status + nav
    frames, rejected, gaps = scan(damaged)
    assert [(offset, mid) for offset, mid, _ in frames] == [(11, 3500), (55, 3501)]
    assert len(rejected) == 1
    assert rejected[0]['offset'] == 0
    assert rejected[0]['reason'] == 'data_checksum'
    assert rejected[0]['residue'] != 0
    assert gaps == [dict(offset=0, bytes=11)]


def test_signed_navigation_units_and_truncated_tail():
    values = (-2**30, 2**29, 640 * 2**16, 45 * 2**21, -80 * 2**21,
              -2 * 2**21, 2**26, -2**25, -2**29)
    nav = packet(3501, bytes(8) + struct.pack('<9i', *values))
    decoded = navigation(nav)
    assert decoded['latitude_deg'] == -90
    assert decoded['longitude_deg'] == 45
    assert decoded['altitude_m'] == 640
    assert decoded['velocity_east_mps'] == -80
    assert decoded['heading_deg'] == -45
    frames, rejected, gaps = scan(nav + nav[:20])
    assert len(frames) == 1
    assert rejected[0]['reason'] == 'truncated_packet'
    assert gaps == [dict(offset=56, bytes=20)]


def test_clock_relative_units_and_nonmonotonic_rejection():
    text = ('ASB JKB0a GL0017a 2 2010 01 01 07 31 49 09 29721\n'
            'ASB JKB0a GL0017a 12 2010 01 01 07 31 50 09 129715\n')
    result = clock_summary(text)
    assert result['relative_time_span_s'] == pytest.approx(0.99994)
    assert result['packet_alignment_verified'] is False
    with pytest.raises(ValueError, match='nonmonotonic'):
        clock_summary('\n'.join(reversed(text.splitlines())))
