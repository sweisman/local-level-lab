# SPDX-License-Identifier: AGPL-3.0-or-later
"""Screen dual-frequency GPS carrier differences on the sealed AIR1 excerpt."""

from collections import Counter
import gzip
import math
from pathlib import Path
import sys

from .esa_rinex_code import _real, observation_epochs
from .esa_rinex_code_study import _INPUTS, _OBS
from .esa_rinex_window import FIRST, FOLDER, LAST, WEEK, epoch_offsets, read_header
from .studies.artifacts import atomic, digest, encoded


PLAN = FOLDER + 'ESA_CARRIER_PHASE_SUPPORT_PLAN.md'
FREEZE = FOLDER + 'esa-carrier-phase-support-freeze.json'
RESULT = FOLDER + 'esa-carrier-phase-support-result.json'
C = 299792458.
F1, F2 = 1_575_420_000., 1_227_600_000.
L1_WAVELENGTH, L2_WAVELENGTH = C / F1, C / F2
GAMMA = (F1 / F2)**2
L1_DOPPLER_LIMIT_CYCLES = .35
DUAL_DIFFERENCE_LIMIT_M = .075
L2_ORDER = ('2W', '2X')
MINIMUM_SATELLITES = 5


def _fields(line, gps):
    def field(code):
        if code not in gps:
            return None
        offset = 3 + 16 * gps.index(code)
        value = line[offset:offset + 14].strip()
        return _real(value) if value else None

    def phase(code):
        value = field(code)
        if value is None:
            return None
        offset = 3 + 16 * gps.index(code)
        mark = line[offset + 14:offset + 15].strip()
        if mark and mark not in '01234567':
            raise ValueError('invalid RINEX phase loss-of-lock flag')
        return value, int(mark) if mark else 0

    return dict(code_m=field('C1C'), l1=phase('L1C'), doppler=field('D1C'),
                l2={band: value for band in L2_ORDER if (value := phase('L' + band)) is not None})


def phase_epochs(raw, *, first=FIRST, last=LAST, week=WEEK):
    """Reuse the code reader's framing checks on a declared half-second window."""
    header, metadata = read_header(raw)
    definitions = metadata['observation_types']
    body = raw[len(header):]
    markers = epoch_offsets(body, offset=0)
    expected = [first + .5 * i for i in range(round((last - first) * 2) + 1)]
    if [row[2] for row in markers] != expected or any(row[1] != week for row in markers):
        raise ValueError('complete sealed half-second GPS window required')
    ends = [row[0] for row in markers[1:]] + [len(body)]
    decoded = observation_epochs(body.decode('ascii'), definitions)
    for code, (start, week, seconds, _, _), end in zip(decoded, markers, ends, strict=True):
        if (week, seconds) != (code['gps_week'], code['gps_week_seconds']):
            raise ValueError('inconsistent GPS epoch framing')
        lines = body[start:end].decode('ascii').splitlines()[1:]
        yield dict(week=week, seconds=seconds,
            satellites={int(line[1:3]): _fields(line, definitions['G'])
                        for line in lines if line.startswith('G')})


def pair_observation(first, second, dt):
    """Match one unchanged dual-phase channel and apply both continuity screens."""
    if dt != .5:
        raise ValueError('only adjacent half-second pairs are qualified')
    if any(row[key] is None for row in (first, second) for key in ('l1', 'doppler', 'code_m')):
        return None, 'missing_l1_fields'
    if not all(1e6 < row['code_m'] < 6e7 for row in (first, second)):
        return None, 'invalid_code'
    band = next((band for band in L2_ORDER if band in first['l2'] and band in second['l2']), None)
    if band is None:
        return None, 'no_common_l2_code'
    l1_a, l1_b = first['l1'], second['l1']
    l2_a, l2_b = first['l2'][band], second['l2'][band]
    if any(flag for _, flag in (l1_a, l1_b, l2_a, l2_b)):
        return None, 'loss_of_lock'
    l1_cycles = l1_b[0] - l1_a[0]
    doppler_gap = l1_cycles + dt * (first['doppler'] + second['doppler']) / 2
    if abs(doppler_gap) > L1_DOPPLER_LIMIT_CYCLES:
        return None, 'l1_doppler'
    l1_range = L1_WAVELENGTH * l1_cycles
    l2_range = L2_WAVELENGTH * (l2_b[0] - l2_a[0])
    if abs(l1_range - l2_range) > DUAL_DIFFERENCE_LIMIT_M:
        return None, 'dual_phase'
    return dict(ionosphere_free_displacement_m=(GAMMA * l1_range - l2_range) / (GAMMA - 1),
        broadcast_input_code_m=(first['code_m'], second['code_m']), l2_code=band,
        doppler_gap_cycles=doppler_gap, dual_phase_gap_m=l1_range - l2_range), None


def pair_satellites(first, second):
    a, b = first['satellites'], second['satellites']
    selected, reasons = {}, {}
    for prn in sorted(a.keys() | b.keys()):
        if prn not in a or prn not in b:
            reasons[prn] = 'one_endpoint_only'
            continue
        row, reason = pair_observation(a[prn], b[prn], second['seconds'] - first['seconds'])
        if reason is None:
            selected[prn] = row
        else:
            reasons[prn] = reason
    return selected, reasons


def scan(raw):
    epochs = list(phase_epochs(raw))
    counts, bands, span = Counter(), Counter(), []
    largest_l1 = largest_dual = 0.
    for first, second in zip(epochs, epochs[1:]):
        selected, reasons = pair_satellites(first, second)
        counts.update(reasons.values())
        bands.update(row['l2_code'] for row in selected.values())
        for row in selected.values():
            largest_l1 = max(largest_l1, abs(row['doppler_gap_cycles']))
            largest_dual = max(largest_dual, abs(row['dual_phase_gap_m']))
        span.append(dict(first_gps_seconds=first['seconds'], second_gps_seconds=second['seconds'],
            accepted_prns=list(selected), rejected_prns=reasons))
    sizes = [len(row['accepted_prns']) for row in span]
    return dict(epochs=len(epochs), pairs=len(span), min_satellites=min(sizes), max_satellites=max(sizes),
        supported_pairs=sum(n >= MINIMUM_SATELLITES for n in sizes),
        accepted_signals_by_l2=bands, rejections=counts, accepted_max_l1_gap_cycles=largest_l1,
        accepted_max_dual_gap_m=largest_dual, per_pair=span, new_positions=0,
        new_inertial_fits=0, protected_reads=0, scientific_decision='abstain')


def run(root, action):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure

    raw = gzip.decompress((root / _OBS).read_bytes())
    if digest(raw) != _INPUTS[_OBS]:
        raise ValueError('exact original RINEX excerpt required')
    sources = source_closure(root, [Path(__file__).relative_to(root).as_posix(), PLAN,
                                   'analysis/tests/test_esa_carrier_phase_support.py'])
    freeze = encoded(dict(
        exact_rinex_sha256=digest(raw), source_sha256={p: digest((root / p).read_bytes()) for p in sources},
        environment=runtime_environment(), threads=1, maximum_pairs=1040, receiver_reads=1,
        l1_limit_cycles=L1_DOPPLER_LIMIT_CYCLES, dual_limit_m=DUAL_DIFFERENCE_LIMIT_M,
        minimum_satellites=MINIMUM_SATELLITES, fit_starts=0, receiver_solves=0, protected_reads=0,
    ))
    control = root / FREEZE
    if action == 'freeze':
        if not control.exists():
            atomic(control, freeze)
        if control.read_bytes() != freeze:
            raise ValueError('existing carrier support freeze differs')
        print(digest(freeze))
        return
    if control.read_bytes() != freeze:
        raise ValueError('unchanged carrier support freeze required')
    result = scan(raw)
    output = encoded(dict(freeze_sha256=digest(freeze), result=result))
    target = root / RESULT
    if not target.exists():
        atomic(target, output)
    if target.read_bytes() != output:
        raise ValueError('saved carrier support result differs')
    print(encoded({key: result[key] for key in ('epochs', 'pairs', 'supported_pairs',
        'min_satellites', 'max_satellites', 'accepted_signals_by_l2', 'rejections')}
        | dict(result_sha256=digest(output))).decode(), end='')


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('freeze', 'calculate'):
        raise SystemExit('usage: python -m lll.esa_carrier_phase_support {freeze,calculate}')
    run(Path.cwd(), sys.argv[1])
