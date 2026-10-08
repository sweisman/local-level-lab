# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import struct

import pytest

from lll import applanix as ap, ilvis0_processing as processing, trimble_receiver as trimble


def packet(kind, payload, status=0x28):
    data = bytes([2, status, kind, len(payload)])+payload
    return data+bytes([sum(data[1:])%256, 3])


def nmea(body):
    checksum = 0
    for b in body.encode():
        checksum ^= b
    return f'${body}*{checksum:02X}\r\n'.encode()


def survey(subtype=6, page=0x11, reply=12, flags=0, data=b'raw'):
    return packet(0x57, bytes([subtype, page, reply, flags])+data)


def verified(p, offset=0):
    return trimble.ReceiverStream().feed(p)[0] | dict(stream_offset=offset)


def test_receiver_packets_nmea_and_ascii_split_at_every_byte():
    data = packet(0x57, b'\x06\x11\x00\x00\x02\x03$\x0a') + b'UTC 09.04.14 12:01:55 59\r\n' + nmea('GPZDA,120155.0,14,04,2009,00,00')
    stream = trimble.ReceiverStream()
    rows = []
    for byte in data:
        rows += stream.feed(bytes([byte]))
    assert [r['kind'] for r in rows] == ['binary', 'ascii_unchecksummed', 'nmea']
    assert rows[0]['payload'].endswith(b'\x02\x03$\x0a')
    assert rows[2]['fields'][0] == 'GPZDA'
    assert stream.finish()['accounted_bytes'] == len(data)


def test_checksum_and_end_corruption_not_repaired():
    good = packet(0x57, b'\x06\x11\x00\x00raw')
    for index in (-2, -1, 4):
        bad = bytearray(good)
        bad[index] ^= 1
        with pytest.raises(ValueError, match='no repair'):
            trimble.ReceiverStream().feed(bad+good)


def test_no_search_through_unrecognized_binary_or_bad_nmea():
    with pytest.raises(ValueError, match='no resynchronization'):
        trimble.ReceiverStream().feed(b'\x01garbage\n'+packet(0x57,b'raw'))
    with pytest.raises(ValueError, match='invalid NMEA'):
        trimble.ReceiverStream().feed(b'$GPGGA,1*00\r\n')


def test_receiver_truncation_retains_fragment():
    stream = trimble.ReceiverStream()
    stream.feed(survey()[:-1])
    with pytest.raises(ValueError, match='truncated'):
        stream.finish()
    assert stream.buffer


def test_survey_reassembly_preserves_exact_bytes_and_reply_rollover():
    pages = trimble.SurveyPages()
    assert pages.feed(verified(survey(page=0x12, reply=255, data=b'abc'), 100)) is None
    record = pages.feed(verified(survey(page=0x22, reply=255, data=b'def'), 130))
    assert record['payload'] == b'abcdef'
    assert record['payload_sha256'] == hashlib.sha256(b'abcdef').hexdigest()
    assert record['first_stream_offset'] == 100 and record['last_stream_offset'] == 130
    assert pages.feed(verified(survey(reply=0)))['reply'] == 0
    pages.finish()


@pytest.mark.parametrize('change', [{'page':0x32}, {'page':0x22,'reply':11}, {'page':0x22,'flags':1}, {'page':0x12}])
def test_missing_duplicate_or_mismatched_survey_pages(change):
    pages = trimble.SurveyPages()
    pages.feed(verified(survey(page=0x12)))
    with pytest.raises(ValueError):
        pages.feed(verified(survey(**change)))


def test_survey_unsupported_extended_pages_and_truncation():
    pages = trimble.SurveyPages()
    with pytest.raises(ValueError, match='unsupported'):
        pages.feed(verified(survey(flags=4)))
    pages.feed(verified(survey(page=0x12)))
    with pytest.raises(ValueError, match='incomplete'):
        pages.finish()


def group(number, body, time=100., pos=50.):
    header = struct.pack('<3dBB', time, pos, 0., 2, 1)
    padding = b'\0'*((-38-len(body))%4)
    size = 34+len(body)+len(padding)+4
    data = bytearray(struct.pack('<4sHH', b'$GRP', number, size-8)+header+body+padding+b'\0\0$#')
    checksum = -sum(x[0] for x in struct.iter_unpack('<H', data))%65536
    struct.pack_into('<H', data, len(data)-4, checksum)
    return bytes(data)


def test_strict_original_audit_and_independent_uncertainty_distinction(tmp_path):
    raw = struct.pack('<6iBBBH', -1,2,-3,4,-5,6,0,6,2,0)
    receiver = survey(subtype=0)+nmea('GPGGA,001640.0,4500.00,N,12000.00,W,1,8,0.9,100.0,M,20.0,M,,')
    receiver += nmea('GPGST,001640.0,1,1,1,0,0.4,0.5,0.8')
    data = group(4,raw)+group(4,raw,time=100.005,pos=50.005)
    data += group(10001,struct.pack('<HIH',13,0,len(receiver))+receiver)
    data += group(2,struct.pack('<9f',*range(1,10)))
    path = tmp_path/'sample.013'
    path.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    counts = {'$GRP:4':2,'$GRP:10001':1,'$GRP:2':1}
    result = processing.scan(path,digest,counts,0)
    assert result['receiver']['survey_record_counts'] == {'0':1}
    assert result['receiver']['raw_satellite_record_envelopes_present']
    assert result['receiver']['gst'][0]['sigma_latitude_longitude_height_m'] == [.4,.5,.8]
    assert result['receiver']['hdop']['median'] == .9
    assert result['fused_uncertainty']['samples'] == 1
    assert not result['receiver']['receiver_covariance_established']
    assert not result['independence']['processing_independence_established']
    assert result['empirical_earth_fit_attempts'] == 0
    with pytest.raises(ValueError,match='correspondence'):
        processing.scan(path,'0'*64,counts,0)
    with pytest.raises(ValueError,match='correspondence'):
        processing.scan(path,digest,{},0)


def test_receiver_corruption_is_recorded_not_promoted(tmp_path):
    bad = bytearray(survey())
    bad[-2] ^= 1
    data = group(10001,struct.pack('<HIH',16,0,len(bad))+bad)
    path = tmp_path/'bad-receiver.013'
    path.write_bytes(data)
    report = processing.scan(path,hashlib.sha256(data).hexdigest(),{'$GRP:10001':1},0)
    assert report['receiver']['stream_errors']
    assert not report['receiver']['raw_satellite_record_envelopes_present']
    assert not report['receiver']['receiver_covariance_established']
