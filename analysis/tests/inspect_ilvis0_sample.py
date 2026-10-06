# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inventory one Applanix log, preserving opaque IMU data without guessed physical units."""
import argparse
import collections
import contextlib
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct

ICD = 'https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf'
GGA_DOC = 'https://receiverhelp.trimble.com/oem-gnss/nmea0183-messages-gga.html'
ZDA_DOC = 'https://receiverhelp.trimble.com/oem-gnss/nmea0183-messages-zda.html'


def frames(data):
    """Fail on malformed framing/checksum; never repair or resynchronize science input."""
    offset = 0
    while offset < len(data):
        if offset + 8 > len(data) or data[offset:offset+4] not in (b'$GRP', b'$MSG'):
            raise ValueError(f'invalid or truncated header at {offset}')
        mid, count = struct.unpack_from('<HH', data, offset + 4)
        size = count + 8
        if size < 12 or size % 4 or offset + size > len(data):
            raise ValueError(f'invalid or truncated packet length at {offset}')
        packet = data[offset:offset+size]
        if packet[-2:] != b'$#':
            raise ValueError(f'invalid packet end at {offset}')
        if sum(struct.unpack('<' + str(size//2) + 'H', packet)) % 65536:
            raise ValueError(f'checksum failure at {offset}')
        yield offset, packet[:4].decode('ascii'), mid, packet
        offset += size


def nmea_sentences(stream):
    """Extract complete sentences after reassembling GPS payloads across packet boundaries."""
    valid, invalid = [], []
    for match in re.finditer(rb'\$([A-Z]{5}),([^\r\n$]*?)\*([0-9A-Fa-f]{2})', stream):
        sentence = match.group()
        body, checksum = sentence[1:].split(b'*')
        residue = 0
        for value in body:
            residue ^= value
        if residue != int(checksum, 16):
            invalid.append(dict(stream_offset=match.start(), sentence=sentence.decode('ascii')))
        else:
            valid.append((match.start(), body.decode('ascii').split(','), sentence))
    return valid, invalid


def coordinate(value, hemisphere, positive, negative):
    if hemisphere not in (positive, negative):
        raise ValueError('invalid coordinate hemisphere')
    number = float(value)
    degrees = int(number // 100)
    minutes = number - 100 * degrees
    if not 0 <= minutes < 60:
        raise ValueError('invalid coordinate minutes')
    return (degrees + minutes / 60) * (1 if hemisphere == positive else -1)


def utc_day_seconds(value):
    hours, minutes, seconds = int(value[:2]), int(value[2:4]), float(value[4:])
    if not (0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 61):
        raise ValueError('invalid UTC time')
    return hours * 3600 + minutes * 60 + seconds


def write_csv(path, rows, compressed=False):
    with contextlib.ExitStack() as stack:
        if compressed:
            raw = stack.enter_context(path.open('xb'))
            binary = stack.enter_context(gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0))
            out = stack.enter_context(io.TextIOWrapper(binary, newline=''))
        else:
            out = stack.enter_context(path.open('x', newline=''))
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def inspect(path, output):
    data = path.read_bytes()
    counts = collections.Counter()
    imu, nav, gps_parts, versions = [], [], [], collections.Counter()
    receiver_types = collections.Counter()
    frame_count = 0
    nav_fields = ('latitude_deg', 'longitude_deg', 'altitude_m', 'velocity_north_mps',
                  'velocity_east_mps', 'velocity_down_mps', 'roll_deg', 'pitch_deg', 'heading_deg')
    for offset, tag, mid, packet in frames(data):
        counts[f'{tag}:{mid}'] += 1
        frame_count += 1
        if tag != '$GRP':
            continue
        if mid == 4:
            if len(packet) != 68:
                raise ValueError('unsupported Group4 layout')
            time1, time2, distance = struct.unpack_from('<3d', packet, 8)
            imu.append(dict(packet_offset=offset, time1_s=time1, time2_s=time2,
                            time_types=packet[32], distance_type=packet[33], distance_tag_m=distance,
                            imu_payload_hex=packet[34:58].hex(), data_status=packet[58],
                            imu_type=packet[59], rate_code=packet[60],
                            imu_status=struct.unpack_from('<H', packet, 61)[0], pad=packet[63]))
        elif mid == 1:
            if len(packet) != 140:
                raise ValueError('unsupported navigation layout')
            values = struct.unpack_from('<3d3f3d', packet, 34)
            nav.append(dict(packet_offset=offset, time1_s=struct.unpack_from('<d', packet, 8)[0],
                            time_types=packet[32], **dict(zip(nav_fields, values)),
                            alignment_status=packet[134]))
        elif mid == 99:
            versions[packet[34:134].split(b'\x00')[0].decode('ascii')] += 1
        elif mid == 10001:
            receiver_types[struct.unpack_from('<H', packet, 34)[0]] += 1
            length = struct.unpack_from('<H', packet, 40)[0]
            if 42 + length > len(packet) - 4:
                raise ValueError('unsupported primary GPS payload length')
            gps_parts.append(packet[42:42+length])
    if not imu or not nav:
        raise ValueError('required IMU/navigation groups absent')
    if not all(math.isfinite(row['time1_s']) and math.isfinite(row['time2_s']) for row in imu):
        raise ValueError('nonfinite IMU time')
    times = [row['time1_s'] for row in imu]
    steps = [b - a for a, b in zip(times, times[1:])]
    if not steps or min(steps) <= 0:
        raise ValueError('nonmonotonic or insufficient IMU time')
    stream = b''.join(gps_parts)
    sentences, invalid = nmea_sentences(stream)
    fixes, dates = [], collections.Counter()
    for offset, fields, _ in sentences:
        if fields[0] == 'GPZDA':
            dates[dt.date(int(fields[4]), int(fields[3]), int(fields[2])).isoformat()] += 1
        elif fields[0] == 'GPGGA':
            if fields[10] != 'M' or fields[12] != 'M':
                raise ValueError('unexpected GGA height units')
            fixes.append(dict(gps_stream_offset=offset, utc_seconds_of_day=utc_day_seconds(fields[1]),
                              latitude_deg=coordinate(fields[2], fields[3], 'N', 'S'),
                              longitude_deg=coordinate(fields[4], fields[5], 'E', 'W'),
                              fix_quality=int(fields[6]), satellites=int(fields[7]), hdop=float(fields[8]),
                              orthometric_height_m=float(fields[9]), geoid_separation_m=float(fields[11])))
    result = dict(dataset='ILVIS0', doi='10.5067/E6JPQ3QNW77R',
                  state='timed_imu_payload_preserved_type8_physical_decoding_pending',
                  original_filename=path.name, original_bytes=len(data),
                  original_sha256=hashlib.sha256(data).hexdigest(),
                  helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  frame_count=frame_count, frame_counts=dict(counts), checksum_failures=0,
                  unframed_bytes=0, version_strings=dict(versions),
                  imu=dict(packets=len(imu), first_time1_s=times[0], last_time1_s=times[-1],
                           span_s=times[-1]-times[0], step_min_s=min(steps), step_max_s=max(steps),
                           step_median_s=sorted(steps)[len(steps)//2],
                           gaps_over_7_5ms=sum(step > 0.0075 for step in steps),
                           time_types=dict(collections.Counter(row['time_types'] for row in imu)),
                           types=dict(collections.Counter(row['imu_type'] for row in imu)),
                           rate_codes=dict(collections.Counter(row['rate_code'] for row in imu)),
                           data_status=dict(collections.Counter(row['data_status'] for row in imu)),
                           imu_status=dict(collections.Counter(row['imu_status'] for row in imu)),
                           physical_payload_decoded=False, scaling_verified=False, axes_verified=False),
                  navigation=dict(packets=len(nav),
                                  ranges={field: dict(min=min(row[field] for row in nav), max=max(row[field] for row in nav))
                                          for field in nav_fields},
                                  alignment_status=dict(collections.Counter(row['alignment_status'] for row in nav))),
                  gps=dict(receiver_types=dict(receiver_types), reconstructed_stream_bytes=len(stream),
                           valid_sentence_counts=dict(collections.Counter(fields[0] for _, fields, _ in sentences)),
                           checksum_failed_sentences=invalid, dates=dict(dates), position_fixes=len(fixes),
                           fix_quality=dict(collections.Counter(row['fix_quality'] for row in fixes))),
                  documentation_urls=[ICD, GGA_DOC, ZDA_DOC],
                  empirical_discrimination_tested=False, main_pipeline_imported=False,
                  limitations=[
                      'Observed AV510 VER5 firmware04.60 ICD15.00; public2014 V6 ICD is a compatible container lead, not the exact firmware specification.',
                      '24byte Group4 payload remains opaque: no guessed axis order, scales, rate/increment convention or corrections.',
                      'Group1 is a fused navigation solution: orientation/angular rates are not independent gyro evidence.',
                      'Time-types byte2 denotes UTC time1/POS time2 in public ICD; date from independent receiver ZDA; detailed sensor/antenna timing and lever arms unverified.',
                      'GGA fixes are receiver navigation outputs, not raw pseudoranges; ellipsoid height has not been substituted for orthometric height.',
                      'IMU8 status0 is recorded without an undocumented sensor-status interpretation.',
                      'Short fixed-mount segment; no identification, power, calibration or WT901 performance claim.'])
    output.mkdir(parents=True, exist_ok=False)
    (output / (path.name + '.gz')).write_bytes(gzip.compress(data, compresslevel=6, mtime=0))
    write_csv(output / 'imu-packets.csv.gz', imu, compressed=True)
    write_csv(output / 'navigation.csv', nav)
    (output / 'primary-gps-stream.bin.gz').write_bytes(gzip.compress(stream, compresslevel=6, mtime=0))
    (output / 'gps-sentences.txt').write_bytes(b'\n'.join(sentence for _, _, sentence in sentences) + b'\n')
    if fixes:
        write_csv(output / 'gps-fixes.csv', fixes)
    (output / 'inspection.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.input, args.output_dir)
    print(json.dumps(dict(frames=result['frame_count'], imu=result['imu'], gps=result['gps'])))
