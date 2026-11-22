# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decode and verify the two published GIRAFE acceleration files for ESA 187."""

from bisect import bisect_right
from dataclasses import dataclass
from hashlib import file_digest, sha256
from itertools import pairwise
import json
import math
from pathlib import Path
import sys

from .studies.artifacts import atomic, encoded

BASE = Path('data/external-imu-survey-20261018/esa-sample')
REPORT = Path('docs/external-imu-data/esa-girafe-187-acceleration-inventory.json')
WINDOWS = Path('docs/prediction-observed-development/esa-direction-window-transfer-result.json')
WINDOWS_SHA256 = 'ebbef12c33cb84824ab289886fa41d81c40d77aeae6f628e7bfa49fe32840b0c'
HEADER = (
    b'UTCl time (s) (ref: 00:00 day of flight)\tacc  z  (m/s\xb2) from atom accelerometer'
    b'\tacc x (m/s\xb2) from QA accelerometer\tacc y (m/s\xb2) from QA accelerometer'
    b'\tT (s) atom half interrogation time\tTemperature (deg C) from QA acclerometer'
)
TARGETS = {
    'GIRAFE_raw_acc_187a-Nuuk-Rey.txt':
        (16_883_030, '59af2c6c8e20752f6a222fbf577915715c92da70504a42a15ee66dea2358d45b'),
    'GIRAFE_raw_acc_187b-Rey-Aku.txt':
        (6_277_733, '5ee7f09bcb1c29ffd48cd1414ce4371a3d108b5fe2b32083dd295dd2ae56fea8'),
}
# Flight date 2023-07-06, Thursday of GPS week 2269, at GPS-UTC = 18 s.
GPS_WEEK = 2269
GPS_AT_UTC_MIDNIGHT = 4*86_400+18


@dataclass(frozen=True)
class ForceSample:
    utc_seconds: float
    xyz_mps2: tuple[float, float, float]
    half_interrogation_s: float
    quartz_deg_c: float


def utc_seconds_to_gps(seconds):
    if not 0. <= seconds < 86_400.:
        raise ValueError('UTC seconds on the known flight day required')
    return GPS_AT_UTC_MIDNIGHT+seconds


def read_rows(stream):
    """Yield finite ordered force rows, preserving the original clock and unit signs."""
    if stream.readline().rstrip(b'\r\n') != HEADER:
        raise ValueError('unexpected GIRAFE acceleration header')
    previous = -1.
    for number, line in enumerate(stream, start=2):
        try:
            seconds, z, x, y, half_interrogation, quartz_temperature = map(float, line.split(b'\t'))
        except ValueError as exc:
            raise ValueError(f'invalid GIRAFE acceleration row {number}') from exc
        values = (seconds, z, x, y, half_interrogation, quartz_temperature)
        if (not all(map(math.isfinite, values)) or not previous < seconds < 86_400.
                or seconds < 0. or half_interrogation < 0.):
            raise ValueError(f'invalid GIRAFE acceleration row {number}')
        yield ForceSample(seconds, (x, y, z), half_interrogation, quartz_temperature)
        previous = seconds


def verify_file(path, filename):
    size, expected = TARGETS[filename]
    if path.stat().st_size != size:
        raise ValueError('GIRAFE source size differs from the catalog')
    with path.open('rb') as stream:
        if file_digest(stream, 'sha256').hexdigest() != expected:
            raise ValueError('GIRAFE source SHA-256 differs from the verified acquisition')


def _coverage(path, windows):
    """Collect only clock coverage and interrogation ranges, without comparing accelerations."""
    starts = [start for _, start, _ in windows]
    gaps = dict(minimum_s=float('inf'), maximum_s=0.)
    earlier = first = None
    count = 0
    overlaps = {name: dict(rows=0, first_utc_s=None, last_utc_s=None,
                           minimum_half_interrogation_s=None, maximum_half_interrogation_s=None)
                for name, _, _ in windows}
    with path.open('rb') as stream:
        for sample in read_rows(stream):
            seconds = sample.utc_seconds
            if earlier is not None:
                gap = seconds-earlier
                gaps['minimum_s'] = min(gaps['minimum_s'], gap)
                gaps['maximum_s'] = max(gaps['maximum_s'], gap)
            else:
                first = seconds
            earlier = seconds
            count += 1
            index = bisect_right(starts, seconds)-1
            if index < 0 or seconds > windows[index][2]:
                continue
            stats = overlaps[windows[index][0]]
            half = sample.half_interrogation_s
            if stats['rows'] == 0:
                stats['first_utc_s'] = seconds
                stats['minimum_half_interrogation_s'] = stats['maximum_half_interrogation_s'] = half
            stats['rows'] += 1
            stats['last_utc_s'] = seconds
            stats['minimum_half_interrogation_s'] = min(stats['minimum_half_interrogation_s'], half)
            stats['maximum_half_interrogation_s'] = max(stats['maximum_half_interrogation_s'], half)
    if count < 2:
        raise ValueError('at least two GIRAFE acceleration rows required')
    return dict(samples=count, first_utc_s=first, last_utc_s=earlier,
                sample_interval_s=gaps, saved_window_overlaps=overlaps)


def _window_ranges(root):
    raw = (root / WINDOWS).read_bytes()
    if sha256(raw).hexdigest() != WINDOWS_SHA256:
        raise ValueError('saved ESA 187 development windows changed')
    windows = sorted(((f"{w['kind']}-{w['window']}", w['range_s'][0]-GPS_AT_UTC_MIDNIGHT,
                       w['range_s'][1]-GPS_AT_UTC_MIDNIGHT) for w in json.loads(raw)['windows']),
                     key=lambda item: item[1])
    if len(windows) != 8 or any(a[2] >= b[1] for a, b in pairwise(windows)):
        raise ValueError('eight disjoint development windows required')
    return windows


def inventory(root, *, finalize=False):
    windows = _window_ranges(root)
    base = root / BASE
    files, pending = {}, []
    for name, (size, expected) in TARGETS.items():
        target = base / name
        path = target
        if finalize and not target.exists():
            path = target.with_name(name+'.part')
            pending.append((path, target))
        verify_file(path, name)
        files[name] = dict(bytes=size, sha256=expected, **_coverage(path, windows))
    for path, target in pending:
        path.rename(target)
    result = dict(flight='187', date='2023-07-06', gps_week=GPS_WEEK,
                  gps_week_seconds_at_utc_midnight=GPS_AT_UTC_MIDNIGHT,
                  window_source_sha256=WINDOWS_SHA256, windows_utc_seconds=windows, files=files,
                  protected_reads=0, model_fits=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / REPORT
    if finalize and not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('GIRAFE inventory differs from the saved report')
    print(sha256(raw).hexdigest())


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('finalize', 'check'):
        raise SystemExit('usage: python -m lll.esa_girafe {finalize,check}')
    inventory(Path.cwd(), finalize=sys.argv[1] == 'finalize')
