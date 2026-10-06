# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inspect the five explicitly supplied IPUTI0 files; navigation only, no gyro inference."""
import argparse
import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import struct

NAMES = (
    'ASB_JKB0a_GL0017a_AVNcp1.bxds',
    'ASB_JKB0a_GL0017a_AVNcp1.ct',
    'AN09.IPUTI0.AVNcp1.bxds.format',
    'AN09.IPUTI0.AVNcp2.bxds.format',
    'AN09.IPUTI0.ct.format',
)
NAV_FIELDS = ('latitude_deg', 'longitude_deg', 'altitude_m', 'velocity_north_mps',
              'velocity_east_mps', 'velocity_up_mps', 'pitch_deg', 'roll_deg', 'heading_deg')
SIZES = {3500: 44, 3501: 56}


def scan(data):
    """Recover only known frames with zero additive header and payload checksum residues.

    Byte order and additive checksum convention are inferred from this sample, not
    established by a manufacturer interface specification. An invalid candidate advances
    one byte so a valid frame inside its apparent extent is not silently discarded.
    """
    accepted, rejected, gaps = [], [], []
    cursor = accounted = 0
    while cursor < len(data):
        offset = data.find(b'\xff\x81', cursor)
        if offset < 0:
            break
        cursor = offset + 1
        if offset + 10 > len(data):
            continue
        header = struct.unpack_from('<5H', data, offset)
        _, mid, wc, _, _ = header
        size = SIZES.get(mid)
        if size is None or 12 + 2 * wc != size or sum(header) % 65536:
            continue
        if offset + size > len(data):
            rejected.append(dict(offset=offset, message_id=mid, reason='truncated_packet'))
            continue
        packet = data[offset:offset + size]
        residue = sum(struct.unpack('<' + str((size - 10) // 2) + 'H', packet[10:])) % 65536
        if residue:
            rejected.append(dict(offset=offset, message_id=mid, reason='data_checksum', residue=residue))
            continue
        if offset > accounted:
            gaps.append(dict(offset=accounted, bytes=offset - accounted))
        accepted.append((offset, mid, packet))
        cursor = accounted = offset + size
    if accounted < len(data):
        gaps.append(dict(offset=accounted, bytes=len(data) - accounted))
    return accepted, rejected, gaps


def navigation(packet):
    """Signed fixed-point navigation fields with the supplied format's divisors."""
    if len(packet) != 56 or struct.unpack_from('<H', packet, 2)[0] != 3501:
        raise ValueError('expected navigation message 3501')
    values = struct.unpack_from('<9i', packet, 18)
    divisors = (2**31 / 180, 2**31 / 180, 2**16, 2**21, 2**21, 2**21,
                2**31 / 180, 2**31 / 180, 2**31 / 180)
    return dict(zip(NAV_FIELDS, (v / d for v, d in zip(values, divisors))))


def clock_summary(text):
    rows = [line.split() for line in text.splitlines() if line.strip()]
    if not rows or any(len(row) != 12 for row in rows):
        raise ValueError('expected twelve clock fields')
    if any(row[:3] != ['ASB', 'JKB0a', 'GL0017a'] for row in rows):
        raise ValueError('unexpected clock source')
    ticks = [int(row[11]) for row in rows]
    sequences = [int(row[3]) for row in rows]
    deltas = [b - a for a, b in zip(ticks, ticks[1:])]
    if any(v <= 0 for v in deltas) or any(b <= a for a, b in zip(sequences, sequences[1:])):
        raise ValueError('nonmonotonic clock or sequence')
    return dict(rows=len(rows), first_fields=rows[0], last_fields=rows[-1],
                relative_time_span_s=(ticks[-1] - ticks[0]) * 1e-5,
                relative_step_s_min=min(deltas) * 1e-5,
                relative_step_s_max=max(deltas) * 1e-5,
                sequence_steps=dict(collections.Counter(b - a for a, b in zip(sequences, sequences[1:]))),
                clock_time_approximate=True, clock_timezone_verified=False,
                packet_alignment_verified=False, inferred_clock_cadence_hz=1e5 / sorted(deltas)[len(deltas)//2])


def inspect(input_dir, output_dir):
    sources = {name: (input_dir / name).read_bytes() for name in NAMES}
    for name, mid, size in ((NAMES[2], 3500, 44), (NAMES[3], 3501, 56)):
        text = sources[name].decode('utf-8')
        if str(mid) not in text or str(size) not in text or '2^43' not in text:
            raise ValueError('supplied packet description differs from supported layout')
    frames, rejected, gaps = scan(sources[NAMES[0]])
    rows = [dict(packet_offset=offset, time_tag_hex=packet[10:18].hex(), **navigation(packet))
            for offset, mid, packet in frames if mid == 3501]
    if not rows:
        raise ValueError('no verified navigation packets')
    counts = collections.Counter(mid for _, mid, _ in frames)
    statuses = collections.Counter(struct.unpack_from('<6H', packet, 18)
                                   for _, mid, packet in frames if mid == 3500)
    ranges = {field: dict(min=min(row[field] for row in rows), max=max(row[field] for row in rows))
              for field in NAV_FIELDS}
    speeds = [math.hypot(row['velocity_north_mps'], row['velocity_east_mps']) for row in rows]
    result = dict(dataset='IPUTI0', doi='10.5067/7K31MCH5XXZA',
                  state='navigation_sample_decoded_independent_gyro_unavailable',
                  input_provenance={name: dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                                    for name, raw in sources.items()},
                  helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  checksum_convention='inferred little-endian uint16 additive sums modulo65536 equal zero',
                  packet_counts=dict(counts), rejected_packet_candidates=rejected,
                  unframed_ranges=gaps, unframed_bytes=sum(gap['bytes'] for gap in gaps),
                  status_field_order=['mode', 'ssv', 'nsv', 'npmp', 'nvmp', 'fom'],
                  status_values=[dict(raw_words=list(words), count=count) for words, count in sorted(statuses.items())],
                  status_bit_meanings_verified=False,
                  clock=clock_summary(sources[NAMES[1]].decode('utf-8')),
                  navigation_ranges=ranges,
                  horizontal_speed_mps=dict(min=min(speeds), max=max(speeds), mean=sum(speeds)/len(speeds)),
                  raw_gyro_fields_present=False, empirical_discrimination_tested=False,
                  valid_navigation_csv='navigation.csv',
                  limitations=[
                      '3500 is system status;3501 is a navigation solution, not raw gyro measurements.',
                      'Do not differentiate orientation and treat it as independent gyro evidence.',
                      'Signed fixed-point fields follow supplied scaling; byte order/checksum rule inferred from sample.',
                      '64bit time-tag representation/word order and epoch unresolved; exact bytes preserved, no guessed times.',
                      'Clock relative time is documented in10microsecond units; approximate wall clock/timezone and binary alignment unresolved.',
                      'Status tokens/validity flags have not been interpreted; navigation values are exploratory only.',
                      'Reported corruption retained; no repair or missing-data interpolation.',
                      'No source corrections, mount axes, raw rates, gyro calibration or WT901 validation established.'])
    output_dir.mkdir(parents=True, exist_ok=False)
    originals = output_dir / 'inputs'
    originals.mkdir()
    for name in NAMES:
        (originals / name).write_bytes(sources[name])
    with (output_dir / 'navigation.csv').open('x', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=['packet_offset', 'time_tag_hex', *NAV_FIELDS])
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / 'inspection.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.input_dir, args.output_dir)
    print(json.dumps({key: result[key] for key in ('state', 'packet_counts', 'unframed_bytes',
                                                 'horizontal_speed_mps')}))
    print(json.dumps(dict(clock_span_s=result['clock']['relative_time_span_s'],
                         rejected_candidates=len(result['rejected_packet_candidates']))))
