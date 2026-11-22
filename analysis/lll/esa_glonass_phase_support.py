# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check paired GLONASS carrier observables on the opened AIR1 window."""

from collections import Counter
import gzip
from pathlib import Path
import sys

from .esa_carrier_phase_continuous import CLOCK_STEP, CLOCK_STEP_SHA
from .esa_carrier_phase_support import C, DUAL_DIFFERENCE_LIMIT_M, L1_DOPPLER_LIMIT_CYCLES, MINIMUM_SATELLITES
from .esa_final_orbit_score import _load
from .esa_rinex_code import _real
from .esa_rinex_code_study import _INPUTS, _OBS
from .esa_rinex_window import FIRST, FOLDER, LAST, WEEK, epoch_offsets, read_header
from .glonass_code import GAMMA, observation_epochs
from .studies.artifacts import atomic, digest, encoded


PLAN = FOLDER + 'ESA_GLONASS_PHASE_SUPPORT_PLAN.md'
FREEZE = FOLDER + 'esa-glonass-phase-support-freeze.json'
RESULT = FOLDER + 'esa-glonass-phase-support-result.json'


def frequencies(channel):
    if type(channel) is not int or not -7 <= channel <= 12:
        raise ValueError('valid GLONASS FDMA channel required')
    return 1_602e6 + 562_500. * channel, 1_246e6 + 437_500. * channel


def _slots(header):
    rows = [line[:60].split() for line in header.decode('ascii').splitlines()
            if line[60:].strip() == 'GLONASS SLOT / FRQ #']
    if not rows:
        raise ValueError('GLONASS channel metadata required')
    count = int(rows[0][0])
    values = rows[0][1:] + [item for row in rows[1:] for item in row]
    if len(values) != 2 * count:
        raise ValueError('incomplete GLONASS slot table')
    slots = {}
    for label, raw in zip(values[::2], values[1::2], strict=True):
        if len(label) != 3 or label[0] != 'R' or not label[1:].isdigit() or int(label[1:]) in slots:
            raise ValueError('unique GLONASS slot identifiers required')
        channel = int(raw)
        frequencies(channel)
        slots[int(label[1:])] = channel
    return slots


def _fields(line, names, code):
    offsets = {name: 3 + 16 * names.index(name) for name in ('L1C', 'L2C', 'D1C', 'D2C')}
    values = {}
    for name, offset in offsets.items():
        field = line[offset:offset + 14].strip()
        values[name] = _real(field) if field else None
    flags = []
    for name in ('L1C', 'L2C'):
        offset = offsets[name]
        flag = line[offset + 14:offset + 15].strip()
        if flag and flag not in '01234567':
            raise ValueError('invalid GLONASS loss-of-lock flag')
        flags.append(int(flag) if flag else 0)
    return dict(code_m=code, phase=(values['L1C'], values['L2C']),
                doppler=(values['D1C'], values['D2C']), lli=tuple(flags))


def observations(raw):
    header, info = read_header(raw)
    slots = _slots(header)
    body = raw[len(header):]
    starts = epoch_offsets(body, offset=0)
    expected = [FIRST + .5 * i for i in range(round((LAST - FIRST) * 2) + 1)]
    if [row[2] for row in starts] != expected or any(row[1] != WEEK for row in starts):
        raise ValueError('unaltered half-second receiver epochs required')
    ends = [row[0] for row in starts[1:]] + [len(body)]
    definitions = info['observation_types']
    code_rows = observation_epochs(body.decode('ascii'), definitions)
    rows = []
    for (offset, week, seconds, _, _), end, (time, codes) in zip(starts, ends, code_rows, strict=True):
        if (week, seconds) != time:
            raise ValueError('GLONASS framing and code time disagree')
        signals = {}
        for line in body[offset:end].decode('ascii').splitlines()[1:]:
            if not line.startswith('R'):
                continue
            prn = int(line[1:3])
            if prn not in slots or len(line) > 3 + 16 * len(definitions['R']):
                raise ValueError('declared GLONASS slot and observation fields required')
            signals[prn] = _fields(line, definitions['R'], codes[prn][0])
        rows.append(dict(week=week, seconds=seconds, satellites=signals))
    return slots, rows


def phase_change(first, second, channel, *, elapsed, jump):
    if (abs(jump) != .001 and jump != 0) or not .498 <= elapsed <= .502:
        raise ValueError('declared half-second phase interval required')
    if any(row['code_m'] is None or None in row['phase'] or None in row['doppler']
           for row in (first, second)):
        return None, 'missing_signal'
    if not all(1e6 < row['code_m'] < 6e7 for row in (first, second)):
        return None, 'invalid_code'
    if any((*first['lli'], *second['lli'])):
        return None, 'loss_of_lock'
    travelled, discrepancies = [], []
    for i, frequency in enumerate(frequencies(channel)):
        cycles = second['phase'][i] - first['phase'][i] - frequency * jump
        error = cycles + elapsed * (first['doppler'][i] + second['doppler'][i]) / 2
        if abs(error) > L1_DOPPLER_LIMIT_CYCLES:
            return None, f'band{i + 1}_doppler'
        travelled.append(cycles * C / frequency)
        discrepancies.append(error)
    geometry_free = travelled[0] - travelled[1]
    if abs(geometry_free) > DUAL_DIFFERENCE_LIMIT_M:
        return None, 'dual_phase'
    return dict(range_difference_m=(GAMMA * travelled[0] - travelled[1]) / (GAMMA - 1),
                code_endpoints_m=(first['code_m'], second['code_m']), channel=channel,
                doppler_errors_cycles=discrepancies, geometry_free_m=geometry_free), None


def accepted(first, second, slots, *, jump=0., elapsed=.5):
    a, b = first['satellites'], second['satellites']
    rows, exclusions = {}, {}
    for prn in sorted(a.keys() | b.keys()):
        if prn not in a or prn not in b:
            exclusions[prn] = 'one_endpoint_only'
            continue
        result, reason = phase_change(a[prn], b[prn], slots[prn], elapsed=elapsed, jump=jump)
        if reason is None:
            rows[prn] = result
        else:
            exclusions[prn] = reason
    return rows, exclusions


def scan(raw, clock):
    slots, epochs = observations(raw)
    rows, counts = [], Counter()
    for index, (a, b) in enumerate(zip(epochs, epochs[1:])):
        if index == clock['pair_index']:
            passed, failed = accepted(a, b, slots, jump=clock['integer_clock_step_s'],
                                      elapsed=clock['corrected_elapsed_s'])
        else:
            passed, failed = accepted(a, b, slots)
        counts.update(failed.values())
        rows.append(dict(index=index, accepted=list(passed), rejected=failed))
    return dict(epochs=len(epochs), pairs=len(rows), per_pair=rows, rejection_counts=counts,
        supported_pairs=sum(len(row['accepted']) >= MINIMUM_SATELLITES for row in rows),
        minimum_satellites=min(len(row['accepted']) for row in rows),
        maximum_satellites=max(len(row['accepted']) for row in rows),
        clock_step_pair=rows[clock['pair_index']], input_clock_sha256=CLOCK_STEP_SHA,
        new_position_solves=0, new_inertial_fits=0, protected_reads=0, scientific_decision='abstain')


def run(root, action):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure

    raw = gzip.decompress((root / _OBS).read_bytes())
    if digest(raw) != _INPUTS[_OBS]:
        raise ValueError('same sealed AIR1 receiver data required')
    clock = _load(root, CLOCK_STEP, CLOCK_STEP_SHA)['result']
    if not clock['passed']:
        raise ValueError('prequalified receiver clock step required')
    source = source_closure(root, [Path(__file__).relative_to(root).as_posix(), PLAN,
                                   'analysis/tests/test_esa_glonass_phase_support.py'])
    freeze = encoded(dict(source_sha256={name: digest((root / name).read_bytes()) for name in source},
        environment=runtime_environment(), threads=1, raw_sha256=digest(raw), clock_sha256=CLOCK_STEP_SHA,
        maximum_pairs=1040, position_solves=0, fit_starts=0, protected_reads=0))
    path = root / FREEZE
    if action == 'freeze':
        if not path.exists():
            atomic(path, freeze)
        if path.read_bytes() != freeze:
            raise ValueError('existing GLONASS support freeze differs')
        print(digest(freeze))
        return
    if path.read_bytes() != freeze:
        raise ValueError('unchanged approved GLONASS support check required')
    result = scan(raw, clock)
    output = encoded(dict(freeze_sha256=digest(freeze), result=result))
    path = root / RESULT
    if not path.exists():
        atomic(path, output)
    if path.read_bytes() != output:
        raise ValueError('saved GLONASS support result differs')
    print(encoded({key: result[key] for key in (
        'pairs', 'supported_pairs', 'minimum_satellites', 'maximum_satellites', 'clock_step_pair', 'rejection_counts')}
        | dict(result_sha256=digest(output))).decode(), end='')


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('freeze', 'calculate'):
        raise SystemExit('usage: python -m lll.esa_glonass_phase_support {freeze,calculate}')
    run(Path.cwd(), sys.argv[1])
