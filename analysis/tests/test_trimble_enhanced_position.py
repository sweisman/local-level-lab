# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer checks for receiver-reported RT27 position precision."""
import struct

import pytest

from lll import trimble_receiver as trimble
from lll.trimble_enhanced_position import decode_enhanced_position


def position_packet(*, latitude=-58.5, longitude=-74.25, height=12000.125,
                    sigmas=(0.5, 0.75, 1.25), week=1865, milliseconds=132356400,
                    first_size=15, second_size=53, flags=0, extra=b''):
    first = bytes([first_size])+struct.pack('>HI8B', week, milliseconds,
        0, 13, 11, 0, 1, 2, 0, 0)
    signed = lambda value, size: int(value).to_bytes(size, 'big', signed=True)
    second = (bytes([second_size])
        + signed(round(latitude*2**40), 6)
        + signed(round(longitude*2**39), 6)
        + signed(round(height*2**12), 4)
        + b''.join(signed(round(value*2**21), 4) for value in (100., -200., 1.))
        + signed(0, 4)+signed(0, 4)
        + struct.pack('>3H', 24, 32, 40)
        + struct.pack('>3H', *(round(s*2**11) for s in sigmas))
        + struct.pack('>2H', 8192, 2048))
    body = bytes([7, 0x11, 42, flags])+first+second+extra
    packet = bytes([2, 0x28, 0x57, len(body)])+body
    packet += bytes([sum(packet[1:]) % 256, 3])
    return packet


def position_record(**kwargs):
    packet = position_packet(**kwargs)
    rows = trimble.ReceiverStream().feed(packet)
    assert len(rows) == 1
    return trimble.SurveyPages().feed(rows[0])


def test_enhanced_position_preserves_raw_and_scaled_receiver_fields():
    row = decode_enhanced_position(position_record())
    assert row['gps_week'] == 1865
    assert row['gps_week_seconds'] == pytest.approx(132356.4)
    assert row['latitude_deg'] == pytest.approx(-58.5, abs=1e-9)
    assert row['longitude_deg'] == pytest.approx(-74.25, abs=1e-9)
    assert row['ellipsoid_height_m'] == pytest.approx(12000.125)
    assert row['velocity_north_mps'] == pytest.approx(100.)
    assert row['velocity_east_mps'] == pytest.approx(-200.)
    assert row['reported_sigma_north_m'] == pytest.approx(0.5)
    assert row['reported_sigma_east_m'] == pytest.approx(0.75)
    assert row['reported_sigma_up_m'] == pytest.approx(1.25)
    assert row['raw']['sigma_north_counts'] == 1024
    assert row['raw']['latitude_counts'] < 0
    assert row['source_kind'].startswith('primary GNSS receiver')
    assert row['receiver_covariance_established'] is False


@pytest.mark.parametrize('change', [
    {'first_size':14}, {'second_size':52}, {'flags':1},
    {'milliseconds':604800000}, {'latitude':91.},
    {'extra':b'\x05\x01'},
])
def test_enhanced_position_rejects_unsupported_or_invalid_layout(change):
    with pytest.raises(ValueError):
        decode_enhanced_position(position_record(**change))


def test_enhanced_position_keeps_unknown_complete_optional_blocks():
    row = decode_enhanced_position(position_record(extra=b'\x03\x12\x34'))
    assert row['optional_blocks'][0]['size'] == 3
    assert row['optional_blocks'][0]['sha256']
