# SPDX-License-Identifier: AGPL-3.0-or-later
import io
import struct
import numpy as np
import pytest
from lll import applanix as ap
from lll.ilvis0 import validate_arrays


def packet(group, body, tag=b'$GRP'):
    raw = tag + struct.pack('<HH', group, len(body) + 4) + body + b'\0\0$#'
    checksum = -sum(v[0] for v in struct.iter_unpack('<H', raw)) & 65535
    return raw[:-4] + struct.pack('<H', checksum) + raw[-2:]


def imu(time=1, values=(-2**31, -1, 2**31 - 1, 2, -3, 4), rate=2):
    body = bytearray(56)
    struct.pack_into('<3d', body, 0, time, time - 0.2, 0)
    body[24] = 2
    struct.pack_into('<6i', body, 26, *values)
    body[51], body[52] = 8, rate
    return ap.group4(next(ap.frames(io.BytesIO(packet(4, body)))))


def test_streaming_length_checksum_and_short_reads():
    class Short(io.BytesIO):
        def read(self, n=-1):
            return super().read(min(n, 3))
    raw = packet(7, bytes(4), b'$MSG') + packet(4, bytes(56))
    rows = list(ap.frames(Short(raw)))
    assert [(r.offset, r.tag, r.group, len(r.packet)) for r in rows] == [(0, '$MSG', 7, 16), (16, '$GRP', 4, 68)]
    for bad in (raw[:-1], raw + b'x', b'x' + raw):
        with pytest.raises(ValueError):
            list(ap.frames(io.BytesIO(bad)))
    corrupt = bytearray(raw)
    corrupt[12] ^= 1
    with pytest.raises(ValueError, match='checksum'):
        list(ap.frames(io.BytesIO(corrupt)))
    with pytest.raises(ValueError, match='length'):
        list(ap.frames(io.BytesIO(b'$GRP' + struct.pack('<HH', 4, 3))))


def test_signed_increment_scales_dt_and_flags():
    a, b = imu(1), imu(1.005)
    row = ap.increments(b, a, True)
    assert row['raw_dv_x'] == -2**31
    assert row['dv_y_mps'] == -2**-14
    assert row['dtheta_y_rad'] == -3 * 2**-18
    assert row['angular_rate_y_rads'] == pytest.approx(-3 * 2**-18 / 0.005)
    assert row['dt_s'] == pytest.approx(0.005)
    assert not row['flags']
    assert ap.increments(a, None, True)['angular_rate_x_rads'] is None
    for time in (0.9, 1, 1.02):
        assert ap.increments(imu(time), a, True)['angular_rate_x_rads'] is None
    assert 'configuration_change' in ap.increments(imu(1.0025, rate=3), a, True)['flags']
    assert ap.increments(b, a, False)['dv_x_mps'] is None
    assert ap.RATE_HZ[2] == 200


def test_group1_fields_include_wander_and_status():
    body = bytearray(128)
    struct.pack_into('<3d', body, 0, 10, 9, 3)
    values = list(range(1, 19))
    struct.pack_into('<3d3f4d8f', body, 26, *values)
    body[126] = 0
    nav = ap.group1(next(ap.frames(io.BytesIO(packet(1, body)))))
    assert nav['wander_deg'] == 10
    assert nav['track_deg'] == 11
    assert nav['angular_rate_x_deg_s'] == 13
    assert nav['acceleration_z_mps2'] == 18
    assert nav['source_kind'] == 'fused_navigation'


def test_receiver_packets_split_sentences_and_bad_checksum():
    sentence = b'$GPGGA,122931.00,7943.09215409,N,04101.22898956,W,1,13,0.7,6904.540,M,30.920,M,,*4F'
    parser = ap.NMEA()
    rows = []
    for part in (b'\0' + sentence[:17], sentence[17:79], sentence[79:] + b'\r\n'):
        body = bytearray(34 + len(part))
        while (len(body) + 12) % 4:
            body.append(0)
        struct.pack_into('<H', body, 26, 1)
        struct.pack_into('<H', body, 32, len(part))
        body[34:34 + len(part)] = part
        frame = next(ap.frames(io.BytesIO(packet(10001, body))))
        receiver, decoded = ap.group10001(frame)
        assert receiver == 1
        rows.extend(parser.feed(decoded))
    assert len(rows) == 1 and rows[0]['valid'] and rows[0]['stream_offset'] == 1
    assert not parser.feed(sentence[:-2] + b'00')[0]['valid']
    assert parser.finish()['invalid_checksums'] == 1
    assert ap.coordinate('04101.22898956', 'W') == pytest.approx(-41.02048315933333)
    with pytest.raises(ValueError):
        ap.coordinate('04161', 'W')


def test_binary_receiver_bytes_cannot_swallow_a_split_nmea_start():
    sentence = b'$GPZDA,000000.00,14,04,2009,00,00'
    checksum = 0
    for value in sentence[1:]:
        checksum ^= value
    sentence += ('*%02X' % checksum).encode()
    parser = ap.NMEA()
    # The binary '*' is immediately followed by the real NMEA start.
    assert not parser.feed(b'$\x00binary*' + sentence[:1])
    result = parser.feed(sentence[1:10]) + parser.feed(sentence[10:])
    assert len(result) == 1 and result[0]['valid']


def test_independent_scales_gravity_and_wrong_axis_sign():
    rng = np.random.default_rng(5)
    raw = rng.normal(size=(100, 3)) * 10000
    gravity = rng.normal(size=(100, 3))
    scale = ap.DELTA_V_SCALE
    target = raw * scale + gravity * 9.81 + np.array([.01, -.02, .03])
    result = validate_arrays(raw, target, scale, gravity)
    assert result['accepted']
    assert result['shared_gravity_mps2'] == pytest.approx(9.81)
    assert all(row['scale_ratio'] == pytest.approx(1) for row in result['axes'])
    wrong = raw[:, [1, 0, 2]] * np.array([-1, 1, 1])
    result = validate_arrays(wrong, target, scale, gravity)
    assert not result['accepted']
    assert result['plausible_mapping_scores'][0]['permutation'] == [1, 0, 2]
    assert result['plausible_mapping_scores'][0]['signs'] == [1, -1, 1]


def test_wrong_scale_cannot_pass_high_correlation():
    raw = np.random.default_rng(7).normal(size=(120, 3))
    result = validate_arrays(raw, raw * ap.DELTA_ANGLE_SCALE * 2, ap.DELTA_ANGLE_SCALE)
    assert not result['accepted']
