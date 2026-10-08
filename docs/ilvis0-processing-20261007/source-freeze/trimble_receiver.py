# SPDX-License-Identifier: AGPL-3.0-or-later
"""Strict mixed Trimble/NMEA receiver framing, never byte-search resynchronization.

Binary envelope and RT17/RT27 paging follow Trimble's public receiver interface.
Survey payloads stay opaque here: no pseudoranges, positions or covariance invented.
ASCII diagnostic lines have no checksum and are never accepted timing observations.
"""
import hashlib

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
            if self.buffer[0] == 2:
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
