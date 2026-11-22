# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit the AIR1 receiver-time discontinuity without a position fit."""

import gzip
import math
from pathlib import Path
import sys

from .esa_carrier_phase_later import SUPPORT_SHA
from .esa_carrier_phase_support import F1, F2, MINIMUM_SATELLITES, pair_observation, pair_satellites, phase_epochs
from .esa_carrier_phase_support import RESULT as CONTINUITY
from .esa_final_orbit_score import _load
from .esa_rinex_code_study import _INPUTS, _OBS, _approximation
from .esa_rinex_window import FOLDER, read_header
from .studies.artifacts import atomic, digest, encoded


PLAN = FOLDER + 'ESA_CARRIER_CLOCK_STEP_PLAN.md'
FREEZE = FOLDER + 'esa-carrier-clock-step-freeze.json'
RESULT = FOLDER + 'esa-carrier-clock-step-result.json'


def _normalized_row(row, jump, elapsed):
    l1 = row['l1']
    # The old continuity screen takes a half-second Doppler integral.
    # Supply the integral for the corrected elapsed time through its argument.
    # These temporary fields never replace the recorded observables.
    return row | dict(
        l1=None if l1 is None else (l1[0] - F1 * jump, l1[1]),
        l2={band: (phase - F2 * jump, flag) for band, (phase, flag) in row['l2'].items()},
        doppler=None if row['doppler'] is None else row['doppler'] * (elapsed / .5),
    )


def normalized_pair(first, second, jump, elapsed):
    return pair_observation(_normalized_row(first, 0, elapsed),
                            _normalized_row(second, jump, elapsed), .5)


def normalized_epochs(first, second, jump, elapsed):
    return tuple(row | dict(satellites={
        prn: _normalized_row(signal, shift, elapsed) for prn, signal in row['satellites'].items()
    }) for row, shift in ((first, 0), (second, jump)))


def metadata(raw, index):
    header, _ = read_header(raw)
    if _approximation(header)[1]:
        raise ValueError('unapplied receiver clock offset required')
    markers = [line.split() for line in raw[len(header):].splitlines() if line.startswith(b'> ')]
    a, b = markers[index:index + 2]
    if len(a) != 10 or len(b) != 10:
        raise ValueError('both original receiver clock offsets required')
    earlier, later = float(a[-1]), float(b[-1])
    change = later - earlier
    jump = round(change * 1000) / 1000
    if abs(jump) != .001 or not math.isfinite(change) or abs(change - jump) > 1e-5:
        raise ValueError('one millisecond receiver clock step required')
    return dict(first_clock_s=earlier, second_clock_s=later, offset_change_s=change,
                integer_clock_step_s=jump, corrected_elapsed_s=.5 - change)


def calculate(raw, continuity):
    failures = [i for i, pair in enumerate(continuity['per_pair'])
                if len(pair['accepted_prns']) < MINIMUM_SATELLITES]
    if len(failures) != 1:
        raise ValueError('one preserved unsupported pair required')
    index = failures[0]
    details = metadata(raw, index)
    epochs = list(phase_epochs(raw))
    a, b = normalized_epochs(*epochs[index:index + 2], details['integer_clock_step_s'],
                             details['corrected_elapsed_s'])
    supported, rejected = pair_satellites(a, b)
    diagnostics = {prn: {key: row[key] for key in ('l2_code', 'doppler_gap_cycles', 'dual_phase_gap_m')}
                   for prn, row in supported.items()}
    return dict(pair_index=index, first_gps_seconds=a['seconds'], second_gps_seconds=b['seconds'],
                **details, supported_prns=list(supported), rejected_prns=rejected, diagnostics=diagnostics,
                passed=len(supported) >= MINIMUM_SATELLITES, new_receiver_solves=0,
                new_fits=0, protected_reads=0, scientific_decision='abstain')


def run(root, action):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure

    raw = gzip.decompress((root / _OBS).read_bytes())
    if digest(raw) != _INPUTS[_OBS]:
        raise ValueError('exact original RINEX excerpt required')
    frozen = _load(root, CONTINUITY, SUPPORT_SHA)['result']
    sources = source_closure(root, [Path(__file__).relative_to(root).as_posix(), PLAN,
                                   'analysis/tests/test_esa_carrier_clock_step.py'])
    freeze = encoded(dict(source_sha256={p: digest((root / p).read_bytes()) for p in sources},
        environment=runtime_environment(), threads=1, maximum_pairs=1, fit_starts=0, receiver_solves=0,
        raw_sha256=digest(raw), continuity_sha256=SUPPORT_SHA))
    target = root / FREEZE
    if action == 'freeze':
        if not target.exists():
            atomic(target, freeze)
        if target.read_bytes() != freeze:
            raise ValueError('existing clock normalization freeze differs')
        print(digest(freeze))
        return
    if target.read_bytes() != freeze:
        raise ValueError('unchanged clock normalization required')
    result = calculate(raw, frozen)
    output = encoded(dict(freeze_sha256=digest(freeze), result=result))
    target = root / RESULT
    if not target.exists():
        atomic(target, output)
    if target.read_bytes() != output:
        raise ValueError('saved clock normalization differs')
    print(encoded(dict(result_sha256=digest(output), passed=result['passed'],
                       accepted=len(result['supported_prns']))).decode(), end='')


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('freeze', 'calculate'):
        raise SystemExit('usage: python -m lll.esa_carrier_clock_step {freeze,calculate}')
    run(Path.cwd(), sys.argv[1])
