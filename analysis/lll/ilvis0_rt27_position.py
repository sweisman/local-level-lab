# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checked receiver-position inventory with explicit stream-boundary fragments."""
from collections import Counter
import hashlib
import math

from . import trimble_receiver as trimble
from .trimble_enhanced_position import decode_enhanced_position


def extract_primary_receiver(path, expected_source_sha256, *,
                             max_original_bytes=300000000, max_receiver_bytes=64000000):
    """Copy Group 10001 bytes from one checksum-valid original; ignore IMU bodies."""
    from . import applanix as ap, ilvis0 as il
    from .ilvis0_followup import HashedReader

    content = bytearray()
    frames = receiver_packets = 0
    with il.open_source(path) as original:
        source = HashedReader(original)
        for frame in ap.frames(source):
            frames += 1
            if source.size > max_original_bytes:
                raise ValueError('original source exceeds finite byte limit')
            if frame.tag == '$GRP' and frame.group == 10001:
                _, payload = ap.group10001(frame)
                content.extend(payload)
                receiver_packets += 1
                if len(content) > max_receiver_bytes:
                    raise ValueError('receiver stream exceeds finite byte limit')
    if source.digest.hexdigest() != expected_source_sha256:
        raise ValueError('original source hash differs from selected recording')
    if not receiver_packets:
        raise ValueError('no Group 10001 receiver packets')
    return dict(receiver_bytes=bytes(content), original_bytes=source.size,
        original_sha256=source.digest.hexdigest(), original_frames=frames,
        receiver_packets=receiver_packets,
        receiver_sha256=hashlib.sha256(content).hexdigest())


def audit_receiver_bytes(data, *, max_boundary_bytes=512, max_stream_bytes=64000000):
    """Decode the complete interior; never search past a corrupt interior item.

    Applanix Group 10001 capture can start/end inside a receiver packet. Only
    bounded leading and trailing fragments may be omitted, and their exact
    hashes and byte counts are retained. This is a receiver inventory, not a
    whole-stream integrity certificate or GNSS-accuracy calibration.
    """
    if not isinstance(data, bytes) or not 0 < len(data) <= max_stream_bytes:
        raise ValueError('bounded receiver bytes required')
    first = None
    for offset in range(min(max_boundary_bytes+1, len(data)-5)):
        if data[offset] != 2:
            continue
        end = offset+data[offset+3]+6
        if (end <= len(data) and data[end-1] == 3
                and sum(data[offset+1:end-2]) % 256 == data[end-2]):
            first = offset
            break
    if first is None:
        raise ValueError('no checked TSIP packet within initial receiver boundary')
    stream = trimble.ReceiverStream()
    items = stream.feed(data[first:])
    tail = bytes(stream.buffer)
    if len(tail) > max_boundary_bytes:
        raise ValueError('terminal receiver boundary exceeds limit')
    packet_counts = Counter()
    positions = []
    gga_fixes = []
    pages = trimble.SurveyPages()
    for item in items:
        if item['kind'] == 'nmea' and item['fields'][0].endswith('GGA'):
            from . import applanix as ap
            from .ilvis0_followup import utc_sod
            fields = item['fields']
            if (len(fields) < 13 or int(fields[6]) <= 0 or fields[10] != 'M'
                    or fields[12] != 'M'):
                raise ValueError('unsupported receiver GGA quality or height fields')
            gga_fixes.append(dict(utc_sod=utc_sod(fields[1]),
                latitude_deg=ap.coordinate(fields[2], fields[3]),
                longitude_deg=ap.coordinate(fields[4], fields[5]),
                ellipsoid_height_m=float(fields[9])+float(fields[11])))
        if item['kind'] != 'binary':
            continue
        packet_counts[f'{item["packet_type"]:02x}'] += 1
        if item['packet_type'] != 0x57 or len(item['payload']) < 4:
            continue
        if item['payload'][0] != 7:
            continue
        absolute = dict(item, stream_offset=item['stream_offset']+first)
        record = pages.feed(absolute)
        if record is not None:
            positions.append(decode_enhanced_position(record))
    pages.finish()
    if not positions:
        raise ValueError('no enhanced-position record in checked receiver span')
    return dict(byte_size=len(data), stream_sha256=hashlib.sha256(data).hexdigest(),
        prefix_bytes=first, prefix_sha256=hashlib.sha256(data[:first]).hexdigest(),
        tail_bytes=len(tail), tail_sha256=hashlib.sha256(tail).hexdigest(),
        whole_stream_complete=first == 0 and not tail, interior_valid=True,
        checked_packet_count=sum(packet_counts.values()),
        packet_counts=dict(sorted(packet_counts.items())), position_count=len(positions),
        positions=positions, gga_fixes=gga_fixes,
        receiver_covariance_established=False)


def compare_receiver_positions(positions, gga_fixes, *, leap_seconds,
                               time_tolerance_ms=20):
    """Check RT27 decoding against NMEA from the same receiver, not truth."""
    if type(leap_seconds) is not int or not 0 <= leap_seconds <= 30:
        raise ValueError('predeclared GPS-to-UTC leap seconds required')
    if type(time_tolerance_ms) is not int or not 0 <= time_tolerance_ms <= 100:
        raise ValueError('fixed millisecond tolerance required')
    by_time = {}
    for row in positions:
        key = (row['gps_milliseconds']-leap_seconds*1000) % 86400000
        if key in by_time:
            raise ValueError('duplicate receiver position time')
        by_time[key] = row
    differences = []
    for fix in gga_fixes:
        target = round(fix['utc_sod']*1000) % 86400000
        candidates = [by_time[key] for key in range(target-time_tolerance_ms,
                       target+time_tolerance_ms+1) if key in by_time]
        if len(candidates) > 1:
            raise ValueError('ambiguous time-matched receiver position')
        if not candidates:
            continue
        row = candidates[0]
        differences.append((111000*(row['latitude_deg']-fix['latitude_deg']),
            111000*math.cos(math.radians(row['latitude_deg']))
                *(row['longitude_deg']-fix['longitude_deg']),
            row['ellipsoid_height_m']-fix['ellipsoid_height_m']))
    if not differences:
        raise ValueError('no time-matched enhanced position and GGA fixes')
    return dict(matched_epochs=len(differences), gga_epochs=len(gga_fixes),
        maximum_abs_north_m=max(abs(row[0]) for row in differences),
        maximum_abs_east_m=max(abs(row[1]) for row in differences),
        maximum_abs_up_m=max(abs(row[2]) for row in differences),
        independent_accuracy_established=False,
        interpretation='same primary receiver: decoder consistency only')
