# SPDX-License-Identifier: AGPL-3.0-or-later
"""Strict mixed Trimble/NMEA receiver framing, never byte-search resynchronization.

Binary envelope and RT17/RT27 paging follow Trimble's public receiver interface.
Survey payloads stay opaque here: no pseudoranges, positions or covariance invented.
ASCII diagnostic lines have no checksum and are never accepted timing observations.
"""
import hashlib
import math
import struct

from . import applanix as ap

PACKET_REFERENCE = 'https://receiverhelp.trimble.com/oem-gnss/api-data-collector-format-packet-structure.html'
SURVEY_REFERENCE = 'https://receiverhelp.trimble.com/oem-gnss/icd-pkt-response57h-rawdata.html'


class ReceiverStream:
    def __init__(self):
        self.buffer = bytearray()
        self.offset = 0
        self.received = 0

    def feed(self, data):
        self.buffer.extend(data)
        self.received += len(data)
        result = []
        while self.buffer:
            if self.buffer[0] in (6, 21):
                # Documented single-byte command responses, not discarded noise.
                size = 1
                record = dict(kind='protocol_response', stream_offset=self.offset,
                    response='ACK' if self.buffer[0]==6 else 'NAK', byte=self.buffer[0],
                    scientific_measurement=False)
            elif self.buffer[0] == 2:
                if len(self.buffer) < 4:
                    break
                size = self.buffer[3]+6
                if len(self.buffer) < size:
                    break
                packet = bytes(self.buffer[:size])
                if packet[-1] != 3 or sum(packet[1:-2]) % 256 != packet[-2]:
                    raise ValueError(f'receiver checksum/end failure at {self.offset}; no repair')
                record = dict(kind='binary', stream_offset=self.offset, packet_type=packet[2],
                              status=packet[1], payload=packet[4:-2], packet=packet)
            else:
                end = self.buffer.find(b'\n')
                if end < 0:
                    if len(self.buffer) > 512:
                        raise ValueError(f'unsupported receiver prefix at {self.offset}; no resynchronization')
                    break
                size = end+1
                line = bytes(self.buffer[:size]).rstrip(b'\r\n')
                if not line or any(not 32 <= b <= 126 for b in line):
                    raise ValueError(f'unsupported receiver bytes at {self.offset}; no resynchronization')
                record = dict(kind='ascii_unchecksummed', stream_offset=self.offset, line=line.decode('ascii'))
                if line.startswith(b'$'):
                    rows = ap.NMEA().feed(line)
                    if len(rows) != 1 or not rows[0]['valid'] or rows[0]['sentence'].encode() != line:
                        raise ValueError(f'invalid NMEA sentence at {self.offset}; no repair')
                    record.update(kind='nmea', sentence=rows[0]['sentence'], fields=rows[0]['fields'])
            result.append(record)
            del self.buffer[:size]
            self.offset += size
        return result

    def finish(self):
        if self.buffer:
            raise ValueError(f'truncated receiver item at {self.offset}; {len(self.buffer)} bytes retained')
        return dict(bytes=self.received, accounted_bytes=self.offset, complete=True)


class SurveyPages:
    """One-based pages, subtype/reply/flags invariant; >15-page sets unsupported.

    Failure clears no state and does not silently repair the record. A caller doing
    diagnostic inventory may stop assembly and report the failure, retaining originals.
    """
    def __init__(self):
        self.pending = {}

    def feed(self, packet):
        if packet['kind'] != 'binary' or packet['packet_type'] != 0x57:
            raise ValueError('expected verified 57h receiver packet')
        payload = packet['payload']
        if len(payload) < 4:
            raise ValueError('truncated survey header')
        subtype, page, reply, flags = payload[:4]
        index, total = page >> 4, page & 15
        if flags & 12:
            raise ValueError('extended >15-page survey layout unsupported')
        if total == 0 or not 1 <= index <= total:
            raise ValueError('invalid survey page numbering')
        if index == 1:
            if subtype in self.pending:
                raise ValueError('unfinished survey record before next first page')
            self.pending[subtype] = dict(reply=reply, flags=flags, total=total, next=1,
                first_stream_offset=packet['stream_offset'], data=bytearray())
        current = self.pending.get(subtype)
        if current is None or (reply, flags, total, index) != (
                current['reply'], current['flags'], current['total'], current['next']):
            raise ValueError('missing, duplicate or mismatched survey page')
        current['data'].extend(payload[4:])
        current['next'] += 1
        if index != total:
            return None
        data = bytes(current['data'])
        del self.pending[subtype]
        return dict(subtype=subtype, reply=reply, flags=flags, pages=total,
            first_stream_offset=current['first_stream_offset'], last_stream_offset=packet['stream_offset'],
            payload=data, payload_sha256=hashlib.sha256(data).hexdigest(),
            interpretation='complete checksummed survey envelope; measurement payload not decoded')

    def finish(self):
        if self.pending:
            raise ValueError('incomplete survey record at end of stream')


class GSOFPages:
    """Zero-based GSOF pages with records allowed to cross packet boundaries."""
    def __init__(self):
        self.pending = None

    def feed(self, packet):
        if packet['kind'] != 'binary' or packet['packet_type'] != 0x40 or len(packet['payload']) < 3:
            raise ValueError('verified GSOF packet and page header required')
        transmission, page, maximum = packet['payload'][:3]
        if page > maximum:
            raise ValueError('invalid GSOF page number')
        if page == 0:
            if self.pending is not None:
                raise ValueError('unfinished GSOF before next first page')
            self.pending = dict(transmission=transmission, maximum=maximum, next=0,
                first_stream_offset=packet['stream_offset'], data=bytearray())
        current = self.pending
        if current is None or (transmission, maximum, page) != (
                current['transmission'], current['maximum'], current['next']):
            raise ValueError('missing, duplicate or mismatched GSOF page')
        current['data'].extend(packet['payload'][3:])
        current['next'] += 1
        if page != maximum:
            return None
        data = bytes(current['data'])
        records = []
        offset = 0
        while offset < len(data):
            if offset+2 > len(data) or offset+2+data[offset+1] > len(data):
                raise ValueError('truncated GSOF record; no repair')
            kind, size = data[offset:offset+2]
            records.append(dict(record_type=kind, payload=data[offset+2:offset+2+size]))
            offset += size+2
        self.pending = None
        return dict(transmission=transmission, pages=maximum+1,
            first_stream_offset=current['first_stream_offset'], last_stream_offset=packet['stream_offset'],
            records=records, payload_sha256=hashlib.sha256(data).hexdigest())

    def finish(self):
        if self.pending is not None:
            raise ValueError('incomplete GSOF pages at end of stream')


def decode_gsof(group):
    """Receiver engineering units. EN covariance meaning/temporal covariance stay open."""
    out = {k:v for k,v in group.items() if k!='records'}
    out.update(record_types=[r['record_type'] for r in group['records']],
               source_kind='primary GNSS receiver GSOF, not Applanix fused navigation')
    seen = set()
    for record in group['records']:
        kind, payload = record['record_type'], record['payload']
        if kind not in (1, 2, 12):
            continue
        if kind in seen:
            raise ValueError('duplicate required GSOF record; ambiguous epoch')
        seen.add(kind)
        if kind==1:
            if len(payload)!=10:
                raise ValueError('unsupported GSOF time record length')
            ms,week,satellites,flag1,flag2,initialization = struct.unpack('>IH4B',payload)
            if ms>=604800000:
                raise ValueError('GPS epoch outside week')
            out.update(gps_week=week,gps_week_seconds=ms/1000, satellites=satellites,
                       position_flags1=flag1,position_flags2=flag2,initialization_counter=initialization)
        elif kind==2:
            if len(payload)!=24:
                raise ValueError('unsupported GSOF position record length')
            latitude,longitude,height = struct.unpack('>3d',payload)
            if not all(math.isfinite(v) for v in (latitude,longitude,height)) or abs(latitude)>math.pi/2 or abs(longitude)>math.pi:
                raise ValueError('invalid GSOF coordinates')
            out.update(latitude_rad=latitude,longitude_rad=longitude,ellipsoid_height_m=height)
        elif kind==12:
            if len(payload)!=38:
                raise ValueError('unsupported GSOF sigma record length')
            values = struct.unpack('>9fH',payload)
            if not all(math.isfinite(v) for v in values):
                raise ValueError('nonfinite GSOF uncertainty')
            names=('position_rms_m','sigma_east_m','sigma_north_m','covariance_east_north_reported',
                   'sigma_up_m','ellipse_major_m','ellipse_minor_m','ellipse_orientation_deg','unit_variance','epochs')
            sigma = dict(zip(names,values))
            if any(sigma[k]<0 for k in ('position_rms_m','sigma_east_m','sigma_north_m','sigma_up_m')):
                raise ValueError('negative GSOF uncertainty')
            out.update(reported_uncertainty=sigma,
                covariance_semantics='receiver reports; EN field documented as dimensionless, not assumed m²; no cross-epoch covariance')
    return out
