# SPDX-License-Identifier: AGPL-3.0-or-later
"""Match the saved GIRAFE level 1 prefix to the original vertical samples."""

from bisect import bisect_left
from decimal import Decimal
from itertools import islice, pairwise
from math import fsum, isfinite, sqrt
from pathlib import Path

from . import esa_girafe as girafe
from .studies.artifacts import digest, encoded


ID = 'esa-girafe-level1-prefix-clock-v2'
SCOPE = 'GIRAFE 187a recording-start vertical correspondence only'
PLAN = 'docs/prediction-observed-development/ESA_GIRAFE_LEVEL1_PREFIX_PLAN.md'
SIGN_ID = 'esa-girafe-level1-prefix-sign-v1'
SIGN_SCOPE = 'GIRAFE 187a recording-start vertical correspondence with reversed export sign'
SIGN_PLAN = 'docs/prediction-observed-development/ESA_GIRAFE_LEVEL1_PREFIX_SIGN_PLAN.md'
TICKS = 100_000_000
STEP = TICKS//10
SHIFTS = range(-20, 21)
BLOCK = 660
MAX_ROWS = 240_000
FIRST = 38_489_851_739_992
ROW_BYTES = 249
SOURCE = 'GIRAFE_raw_acc_187a-Nuuk-Rey.txt'
PREFIX = '187a_girafe_accelerations-prefix.txt'
RESPONSE = '187a-girafe-level1-score.txt'
PREFIX_HASH = '0b26c5ad28effe883eeb3d8dc9e200bfee939f735f185393dd1033ab99e9cc9d'
RESPONSE_HASH = 'eaef0e070807bad3e37f6ba2b7c02e0da4aa596b6437de05a734fc2e2eb5494e'
TASK = dict(identity='prefix-clock', input_key='original', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=83,
                bound_steps=MAX_ROWS+2*BLOCK*len(SHIFTS)))


def compare(processed, original, charge):
    """Compare all fixed shifts with unique nearest matches on the timestamp grid."""
    times, values = zip(*original, strict=True)
    if any(a >= b for a, b in pairwise(times)):
        raise ValueError('original timestamps must strictly increase')
    scores = []
    for shift in SHIFTS:
        charge(len(processed))
        force_errors, offsets, used = [], [], set()
        for time, force in processed:
            target = time+shift*STEP
            right = bisect_left(times, target)
            index = min(range(max(0, right-1), min(len(times), right+1)),
                        key=lambda i: abs(times[i]-target))
            if abs(times[index]-target) >= STEP//2 or index in used:
                raise ValueError('one-to-one time match within half a sample required')
            used.add(index)
            offsets.append((times[index]-time)/TICKS)
            force_errors.append(values[index]-force)
        count = len(processed)
        scores.append(dict(shift_s=shift/10, matches=count,
            mean_time_offset_s=fsum(offsets)/count, min_time_offset_s=min(offsets),
            max_time_offset_s=max(offsets), mean_mps2=fsum(force_errors)/count,
            rms_mps2=sqrt(fsum(x*x for x in force_errors)/count),
            max_abs_mps2=max(map(abs, force_errors))))
    return scores


def read_export(raw, prefix):
    if (digest(raw) != RESPONSE_HASH or digest(prefix) != PREFIX_HASH
            or not raw.startswith(prefix)):
        raise ValueError('the two exact saved processed captures are required')
    return read_export_rows(raw, 2*BLOCK)


def read_export_rows(raw, expected_rows):
    """Decode an export prefix whose record framing and 10 Hz grid are complete."""
    header, *rows = raw.splitlines(keepends=True)
    if (len(header) != ROW_BYTES or b'z-acc [m/s^2]' not in header
            or b'GPS Week' not in header or len(rows) != expected_rows):
        raise ValueError('expected processed GIRAFE header and row count')
    result = []
    for index, row in enumerate(rows):
        fields = row.split()
        if len(row) != ROW_BYTES or len(fields) != 15:
            raise ValueError('expected complete fixed-width GIRAFE row')
        ticks = Decimal(fields[0].decode('ascii'))*TICKS
        force = float(fields[11])
        if ticks != FIRST+index*STEP or Decimal(fields[13].decode('ascii')) != girafe.GPS_WEEK or not isfinite(force):
            raise ValueError('expected exact 10 Hz recording-start timestamps and GPS week')
        result.append((int(ticks), force))
    return result


def prepare(root, *, reverse_export_sign=False):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    identity, scope, plan = (SIGN_ID, SIGN_SCOPE, SIGN_PLAN) if reverse_export_sign else (ID, SCOPE, PLAN)
    if (root/'data'/identity).exists():
        raise ValueError('preserve the existing study')
    adapter = Path(__file__).relative_to(root).as_posix()
    inputs = {key: (girafe.BASE/name).as_posix() for key, name in
              [('original', SOURCE), ('prefix', PREFIX), ('export', RESPONSE)]}
    sources = source_closure(root, [adapter, plan, 'analysis/tests/test_esa_girafe_level1_prefix.py'])
    definition = dict(id=identity, scope=scope, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=30.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def original_window(path, lower, upper):
    girafe.verify_file(path, SOURCE)
    original = []
    with path.open('rb') as stream:
        for sample in islice(girafe.read_rows(stream), MAX_ROWS):
            time = girafe.GPS_AT_UTC_MIDNIGHT*TICKS+round(sample.utc_seconds*TICKS)
            if time >= lower:
                original.append((time, sample.xyz_mps2[2]))
            if time >= upper:
                break
        else:
            raise ValueError('original acceleration does not cover the frozen time grid')
    return original


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    scope = context.manifest['scope']
    if scope not in (SCOPE, SIGN_SCOPE) or declared != TASK:
        raise ValueError('exact recording-start comparison required')
    context.charge(bound_calls=1, bound_steps=MAX_ROWS)
    processed = read_export(context.input_path('export').read_bytes(), context.input_path('prefix').read_bytes())
    export_sign = -1 if scope == SIGN_SCOPE else 1
    if export_sign == -1:
        processed = [(time, -force) for time, force in processed]
    original = original_window(context.input_path('original'), processed[0][0]-21*STEP, processed[-1][0]+21*STEP)
    def charge(samples):
        context.charge(bound_calls=1, bound_steps=samples)

    blocks = [compare(block, original, charge) for block in (processed[:BLOCK], processed[BLOCK:])]
    within = [[row['shift_s'] for row in block if row['rms_mps2'] <= 1e-6] for block in blocks]
    copied = len(within[0]) == 1 and within[0] == within[1]
    context.save_bytes('clock-scores.json', encoded(dict(blocks=blocks, within_tolerance=within,
        copied_samples_supported=copied, export_sign=export_sign,
        processed_gps_range_s=[processed[0][0]/TICKS, processed[-1][0]/TICKS],
        in_flight_timing_verified=False, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=True, copied_samples_supported=copied, checks=82, scientific_decision='abstain')
