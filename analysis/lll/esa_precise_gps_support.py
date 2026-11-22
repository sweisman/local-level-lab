# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check precise-product support for the sealed ESA 187 GPS code solution."""

from collections import Counter, defaultdict
import gzip
import json
import math
from pathlib import Path

from .esa_rinex_window import FOLDER, LOCAL, WEEK, gps_seconds
from .studies.artifacts import digest, encoded


LATEST_RECEIVE_TIME = 388734.5
EARLIEST_RECEIVE_TIME = 388214.5
MAXIMUM_LOOKBACK_S = .2
ORBIT_STEP_S = 900
CLOCK_STEP_S = 30
EXTRA_ORBIT_KNOTS_PER_SIDE = 3
SAVED_POSITIONS_SHA256 = '02b904918d6bd835d94ef8d0987d1d1180312cbf486870d37293a24756cadc63'


def _record_support(table, prn, epoch):
    if not 1 <= prn <= 32 or epoch in table[prn]:
        raise ValueError('invalid or duplicate GPS satellite support')
    table[prn].add(epoch)


def _product_epoch(fields, step):
    week, seconds = gps_seconds(fields)
    if week != WEEK or seconds % step:
        raise ValueError('unexpected GPS week or product cadence')
    return int(seconds)


def read_orbit_positions(text):
    """Read validated GPS SP3-c positions in metres at their GPS-time knots."""
    lines = text.splitlines()
    if (not lines or not lines[0].startswith('#cP') or not any(
            line.startswith('%c') and line.split()[3:4] == ['GPS'] for line in lines)
            or lines[-1].strip() != 'EOF'):
        raise ValueError('expected complete SP3-c GPS-time orbit product')
    table = defaultdict(dict)
    epoch = None
    for line in lines:
        if line.startswith('* '):
            epoch = _product_epoch(line[1:].split(), ORBIT_STEP_S)
        elif line.startswith('PG'):
            if epoch is None:
                raise ValueError('missing SP3 epoch marker')
            position = [float(line[i:i + 14]) for i in (4, 18, 32)]
            if 20_000 < math.hypot(*position) < 35_000:
                prn = int(line[2:4])
                if not 1 <= prn <= 32 or epoch in table[prn]:
                    raise ValueError('invalid or duplicate GPS satellite orbit')
                table[prn][epoch] = tuple(1000 * value for value in position)
    return table


def _orbit_support(text):
    return {prn: set(knots) for prn, knots in read_orbit_positions(text).items()}


def _clock_support(text):
    header, found, body = text.partition('END OF HEADER')
    if not found or 'CLOCKS ARE ALIGNED TO GPS TIME' not in header:
        raise ValueError('expected IGS clock product aligned to GPS time')
    table = defaultdict(set)
    for line in body.splitlines():
        if not line.startswith('AS G'):
            continue
        fields = line.split()
        epoch = _product_epoch(fields[2:8], CLOCK_STEP_S)
        correction = float(fields[9])
        if math.isfinite(correction) and abs(correction) < .1:
            _record_support(table, int(fields[1][1:]), epoch)
    return table


def missing_support(prn, receive, orbits, clocks):
    """Identify products with missing knots in the time-of-flight envelope."""
    earlier = receive - MAXIMUM_LOOKBACK_S
    missing = []
    for name, step, extra, support in (
        ('orbit', ORBIT_STEP_S, EXTRA_ORBIT_KNOTS_PER_SIDE, orbits),
        ('clock', CLOCK_STEP_S, 0, clocks),
    ):
        first = (math.floor(earlier / step) - extra) * step
        last = (math.ceil(receive / step) + extra) * step
        if not set(range(first, last + 1, step)) <= support.get(prn, set()):
            missing.append(name)
    return missing


def scan(root):
    """Bind the saved aircraft sample and the exact IGS orbit and clock products."""
    base = root / LOCAL / 'rinex-400-120-stream'
    roles = ('precise orbit', 'precise clock')
    manifest = json.loads((root / FOLDER / 'esa-rinex-products.json').read_bytes())
    products = {item['role']: item for item in manifest['products'] if item['role'] in roles}
    support = {}
    for role, parser in zip(roles, (_orbit_support, _clock_support), strict=True):
        item = products[role]
        raw = (base / 'products' / item['filename']).read_bytes()
        if digest(raw) != item['sha256'] or len(raw) != item['bytes']:
            raise ValueError('precise product differs from the acquisition receipt')
        support[role] = parser(gzip.decompress(raw).decode('ascii'))

    receipt = json.loads(gzip.decompress((base / 'code-position/positions.json.gz').read_bytes()))
    rows = receipt['positions']
    if digest(encoded(rows)) != SAVED_POSITIONS_SHA256 or len(rows) != 1041:
        raise ValueError('expected unchanged 1041 saved GPS position records')
    satellites = set()
    count = 0
    missing = {'orbit': Counter(), 'clock': Counter()}
    fully_supported_counts = []
    for index, row in enumerate(rows):
        time = EARLIEST_RECEIVE_TIME + index * .5
        solution = row['dual_frequency']
        if (row['gps_week'] != WEEK or row['gps_week_seconds'] != time
                or time > LATEST_RECEIVE_TIME or solution['status'] != 'converged'):
            raise ValueError('discontinuous saved GPS positions')
        covered = 0
        for prn in solution['used_satellites']:
            absent = missing_support(prn, time, support['precise orbit'], support['precise clock'])
            for product in absent:
                missing[product][prn] += 1
            if not absent:
                covered += 1
            satellites.add(prn)
            count += 1
        fully_supported_counts.append(covered)
    return dict(
        recording='187', epochs=len(rows), used_gps_satellites=sorted(satellites),
        dual_frequency_epoch_satellite_count=count,
        earliest_receive_gps_week_seconds=EARLIEST_RECEIVE_TIME,
        latest_receive_gps_week_seconds=LATEST_RECEIVE_TIME,
        maximum_lookback_s=MAXIMUM_LOOKBACK_S, orbit_knot_spacing_s=ORBIT_STEP_S,
        clock_knot_spacing_s=CLOCK_STEP_S, extra_orbit_knots_per_side=EXTRA_ORBIT_KNOTS_PER_SIDE,
        position_rows_sha256=SAVED_POSITIONS_SHA256,
        product_sha256={role: item['sha256'] for role, item in products.items()},
        missing_support_epoch_satellites=missing,
        minimum_gps_satellites_supported_by_both=min(fully_supported_counts),
        maximum_gps_satellites_supported_by_both=max(fully_supported_counts),
        can_preserve_satellites_with_both_products=not any(missing.values()),
        new_receiver_solutions=0, new_trajectory_fits=0, protected_reads=0,
    )


if __name__ == '__main__':
    print(encoded(scan(Path.cwd())).decode(), end='')
