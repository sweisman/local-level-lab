# SPDX-License-Identifier: AGPL-3.0-or-later
"""Strict, bounded-memory Applanix framing and structural decoding.

The public POS V6 ICD describes the container. Group-4 integer interpretation
is an empirical hypothesis, validated separately by :mod:`lll.ilvis0`.
"""
from dataclasses import dataclass
import math
import struct

ICD_URL = 'https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf'
DELTA_V_SCALE = 2.0 ** -14
DELTA_ANGLE_SCALE = 2.0 ** -18
RATE_HZ = {0: 50, 1: 100, 2: 200, 3: 400, 4: 125, 5: 500}
NAV_FIELDS = ('latitude_deg', 'longitude_deg', 'altitude_m',
              'velocity_north_mps', 'velocity_east_mps', 'velocity_down_mps',
              'roll_deg', 'pitch_deg', 'heading_deg', 'wander_deg',
              'track_deg', 'speed_mps', 'angular_rate_x_deg_s',
              'angular_rate_y_deg_s', 'angular_rate_z_deg_s',
              'acceleration_x_mps2', 'acceleration_y_mps2', 'acceleration_z_mps2')
RAW_FIELDS = tuple(f'raw_{kind}_{axis}' for kind in ('dv', 'dtheta') for axis in 'xyz')


@dataclass(frozen=True)
class Frame:
    offset: int
    tag: str
    group: int
    packet: bytes


def _read(stream, length):
    """Also support streams that return fewer bytes than requested."""
    parts = bytearray()
    while len(parts) < length:
        part = stream.read(length - len(parts))
        if not part:
            break
        parts.extend(part)
    return bytes(parts)


def frames(stream):
    offset = 0
    while True:
        header = _read(stream, 8)
        if not header:
            return
        if len(header) != 8 or header[:4] not in (b'$GRP', b'$MSG'):
            raise ValueError(f'invalid or truncated header at {offset}')
        group, count = struct.unpack_from('<HH', header, 4)
        size = count + 8
        if size < 12 or size % 4:
            raise ValueError(f'invalid packet length at {offset}')
        packet = header + _read(stream, count)
        if len(packet) != size:
            raise ValueError(f'truncated packet at {offset}')
        if packet[-2:] != b'$#':
            raise ValueError(f'invalid packet end at {offset}')
        if sum(value[0] for value in struct.iter_unpack('<H', packet)) & 65535:
            raise ValueError(f'checksum failure at {offset}')
        yield Frame(offset, header[:4].decode('ascii'), group, packet)
        offset += size


def time_header(frame):
    if len(frame.packet) < 38:
        raise ValueError(f'truncated group header at {frame.offset}')
    t1, t2, distance = struct.unpack_from('<3d', frame.packet, 8)
    if not all(map(math.isfinite, (t1, t2, distance))):
        raise ValueError(f'nonfinite time/distance at {frame.offset}')
    return dict(packet_offset=frame.offset, time1_s=t1, time2_s=t2,
                distance_tag_m=distance, time_types=frame.packet[32],
                distance_type=frame.packet[33])


def group4(frame):
    if len(frame.packet) != 68:
        raise ValueError(f'unsupported Group-4 size {len(frame.packet)} at {frame.offset}')
    row = time_header(frame)
    row.update(zip(RAW_FIELDS, struct.unpack_from('<6i', frame.packet, 34)))
    row.update(imu_payload_hex=frame.packet[34:58].hex(), data_status=frame.packet[58],
               imu_type=frame.packet[59], rate_code=frame.packet[60],
               imu_status=struct.unpack_from('<H', frame.packet, 61)[0])
    return row


def group1(frame):
    if len(frame.packet) != 140:
        raise ValueError(f'unsupported Group-1 size {len(frame.packet)} at {frame.offset}')
    row = time_header(frame)
    row.update(zip(NAV_FIELDS, struct.unpack_from('<3d3f4d8f', frame.packet, 34)))
    if not all(math.isfinite(row[field]) for field in NAV_FIELDS):
        raise ValueError(f'nonfinite navigation at {frame.offset}')
    row.update(alignment_status=frame.packet[134], source_kind='fused_navigation')
    return row


def group99(frame):
    if len(frame.packet) < 138:
        raise ValueError(f'unsupported Group-99 size at {frame.offset}')
    return frame.packet[34:134].split(b'\0')[0].decode('ascii')


def group10001(frame):
    if len(frame.packet) < 48:
        raise ValueError(f'truncated Group-10001 at {frame.offset}')
    length = struct.unpack_from('<H', frame.packet, 40)[0]
    if 42 + length > len(frame.packet) - 4:
        raise ValueError(f'invalid receiver payload length at {frame.offset}')
    return struct.unpack_from('<H', frame.packet, 34)[0], frame.packet[42:42 + length]


def increments(row, previous=None, supported=False):
    """Preserve measurements; never assign a gap's elapsed time to one increment."""
    out = dict(row)
    flags = []
    dt = None if previous is None else row['time1_s'] - previous['time1_s']
    expected = 1 / RATE_HZ[row['rate_code']] if row['rate_code'] in RATE_HZ else None
    if previous is None:
        flags.append('first_sample')
    else:
        if dt <= 0:
            flags.append('nonpositive_dt')
        if any(row[k] != previous[k] for k in ('imu_type', 'rate_code', 'time_types')):
            flags.append('configuration_change')
        if dt > 0 and abs((row['time2_s'] - previous['time2_s']) - dt) > 1e-4:
            flags.append('time_discontinuity')
        if expected is None or not 0.8 * expected <= dt <= 1.2 * expected:
            flags.append('unexpected_interval')
    if row['data_status']:
        flags.append('bad_raw_frame_status')
    if row['imu_status']:
        flags.append('uninterpreted_imu_status')
    if not supported:
        flags.append('physical_interpretation_not_validated')
    out.update(dt_s=dt, flags=';'.join(flags))
    valid_rate = supported and not flags
    for kind, scale, units, rate in (
            ('dv', DELTA_V_SCALE, 'mps', 'specific_force'),
            ('dtheta', DELTA_ANGLE_SCALE, 'rad', 'angular_rate')):
        for axis in 'xyz':
            value = row[f'raw_{kind}_{axis}'] * scale if supported else None
            out[f'{kind}_{axis}_{units}'] = value
            out[f'{rate}_{axis}_{"mps2" if kind == "dv" else "rads"}'] = value / dt if valid_rate else None
    return out


class NMEA:
    """Incremental receiver-stream sentences, including provenance and discarded fragments."""
    def __init__(self):
        self.buffer = bytearray()
        self.offset = 0
        self.received = 0
        self.invalid = 0
        self.fragment_bytes = 0

    def feed(self, chunk):
        self.received += len(chunk)
        self.buffer.extend(chunk)
        result = []
        while self.buffer:
            start = self.buffer.find(b'$')
            if start < 0:
                self.fragment_bytes += len(self.buffer)
                self.offset += len(self.buffer)
                self.buffer.clear()
                break
            if start:
                self.fragment_bytes += start
                self.offset += start
                del self.buffer[:start]
            # Receiver bytes also contain binary messages with incidental '$'/'*'.
            # Require a complete standard NMEA header before consuming a checksum;
            # otherwise a binary '*' can swallow the start of the next real sentence.
            if len(self.buffer) < 7:
                break
            if self.buffer[6] != ord(',') or any(not 65 <= byte <= 90 for byte in self.buffer[1:6]):
                self.fragment_bytes += 1
                self.offset += 1
                del self.buffer[:1]
                continue
            star = self.buffer.find(b'*')
            next_start = self.buffer.find(b'$', 1)
            if next_start >= 0 and (star < 0 or next_start < star):
                self.fragment_bytes += next_start
                self.offset += next_start
                del self.buffer[:next_start]
                continue
            if star < 0 or len(self.buffer) < star + 3:
                if len(self.buffer) > 4096:
                    raise ValueError('oversized receiver sentence fragment')
                break
            sentence = bytes(self.buffer[:star + 3])
            try:
                checksum = int(sentence[-2:], 16)
                body = sentence[1:star]
                residue = 0
                for value in body:
                    residue ^= value
                fields = body.decode('ascii').split(',')
                valid = residue == checksum and len(fields[0]) == 5
            except (ValueError, UnicodeDecodeError):
                fields, valid = [], False
            result.append(dict(stream_offset=self.offset, sentence=sentence.decode('ascii', 'replace'),
                               fields=fields, valid=valid))
            self.invalid += not valid
            del self.buffer[:star + 3]
            self.offset += star + 3
        return result

    def finish(self):
        return dict(bytes=self.received, invalid_checksums=self.invalid,
                    discarded_fragment_bytes=self.fragment_bytes,
                    trailing_fragment_hex=bytes(self.buffer).hex())


def coordinate(value, hemisphere):
    if hemisphere not in ('N', 'S', 'E', 'W'):
        raise ValueError('invalid coordinate hemisphere')
    number = float(value)
    degrees = int(number // 100)
    minutes = number - degrees * 100
    limit = 90 if hemisphere in ('N', 'S') else 180
    if not 0 <= minutes < 60 or not 0 <= degrees + minutes / 60 <= limit:
        raise ValueError('invalid coordinate')
    return (degrees + minutes / 60) * (-1 if hemisphere in ('S', 'W') else 1)
