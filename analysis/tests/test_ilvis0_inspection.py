# SPDX-License-Identifier: AGPL-3.0-or-later
import struct

import pytest

from inspect_ilvis0_sample import coordinate, frames, nmea_sentences, utc_day_seconds


def packet(tag=b'$GRP', mid=4, body=bytes(56)):
    raw = tag + struct.pack('<HH', mid, len(body) + 4) + body + bytes(2) + b'$#'
    checksum = -sum(struct.unpack('<' + str(len(raw)//2) + 'H', raw)) % 65536
    return raw[:-4] + struct.pack('<H', checksum) + raw[-2:]


def test_whole_frame_checksum_includes_terminator_and_rejects_damage():
    group = packet()
    message = packet(tag=b'$MSG', mid=7, body=bytes(4))
    parsed = list(frames(group + message))
    assert [(offset, tag, mid) for offset, tag, mid, _ in parsed] == [(0, '$GRP', 4), (68, '$MSG', 7)]
    corrupted = group[:34] + bytes([1]) + group[35:]
    with pytest.raises(ValueError, match='checksum'):
        list(frames(corrupted))
    with pytest.raises(ValueError, match='truncated'):
        list(frames(group[:-1]))


def test_receiver_sentence_reassembly_checksum_and_signed_position():
    sentence = b'$GPGGA,122931.00,7943.09215409,N,04101.22898956,W,1,13,0.7,6904.540,M,30.920,M,,*4F'
    stream = b'\x00\x01' + b''.join([sentence[:20], sentence[20:]]) + b'\r\n'
    valid, invalid = nmea_sentences(stream)
    assert len(valid) == 1 and not invalid
    assert valid[0][0] == 2
    assert coordinate('04101.22898956', 'W', 'E', 'W') == pytest.approx(-41.02048315933333)
    assert utc_day_seconds('122931.00') == 44971
    valid, invalid = nmea_sentences(sentence[:-2] + b'00')
    assert not valid and len(invalid) == 1
    with pytest.raises(ValueError):
        coordinate('04161.0', 'W', 'E', 'W')
