# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay a fixed platform rate convention on the first ESA ground stop."""

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path

from . import esa_girafe_platform_imar_force as pair
from . import esa_girafe_platform_rate as rate
from .esa_direction_holdout_forecast import frozen_input
from .esa_direction_holdout_score import RECORDS, SOURCE_BYTES, WIDTH, held_measurements
from .esa_ftps_bounded_read import GIRAFE_REMOTE, GIRAFE_SOURCE_BYTES
from .esa_ground_rate_scale import FIRST, SOURCE
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-girafe-ground-rate-v1'
SCOPE = 'same-instrument rate closure and separate iMAR timing at three first-stop targets'
PLAN = rate.holdout.FOLDER+'ESA_GIRAFE_GROUND_RATE_PLAN.md'
RESULT = rate.holdout.FOLDER+'esa-girafe-ground-rate-result.json'
DIRECTORY = rate.holdout.DIRECTORY.with_name('girafe-platform-ground-rate-v1')
TRANSFER = (DIRECTORY/'transfer-receipt.json').as_posix()
FIRST_SHA = 'e587348ea92fd3918183bd2b7986e959b4038e77134fc1ded72396fd4e8a12e3'
RATE_SHA = 'a8d097ac419e44d66736c78e8e5a7b1d6fb45884ea736fcc02dd4937a0ce93e4'
TARGETS = ((385574, 61889151), (386250, 115190399), (386927, 168570495))
CONVENTION = ('radian_per_second', (0, 1, 2), (1, 1, 1))
OFFSET_S = rate.holdout.PROVISIONAL_OFFSET_S
DELTA_GPS_S = OFFSET_S+rate.timing.girafe.GPS_AT_UTC_MIDNIGHT
OVERLAP = rate.holdout.OVERLAP_BYTES
RANGE_BYTES = rate.timing.RANGE_BYTES
SHIFTS = 2*pair.LAG_STEPS+1
TASK = dict(identity='ground-direction-and-independent-clock', input_key='transfer', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+4*len(TARGETS),
        bound_steps=SOURCE_BYTES+len(TARGETS)*(RANGE_BYTES+2*OVERLAP+rate.MAX_ROWS+pair.MAX_INTERVALS+SHIFTS)))


def overlap_digest(raw, probe):
    if len(raw) < OVERLAP or len(probe) != 2*OVERLAP or raw[:OVERLAP] != probe[OVERLAP:]:
        raise ValueError('independent byte overlap differs')
    return digest(raw[:OVERLAP])


def support_flags(direction, clock):
    clock_pass = clock['passes'] is True
    direction_pass = len(direction) == len(rate.SPANS) and all(
        row['gyro_prediction_rms_arcsec'] < row['no_motion_rms_arcsec'] for row in direction)
    return clock_pass, direction_pass, clock_pass and direction_pass


def _source_ranges(root, offset):
    raw = safe_path(root, (DIRECTORY/f'range-{offset}.asc').as_posix())
    probe = safe_path(root, (DIRECTORY/f'check-{offset}.asc').as_posix())
    if raw.stat().st_size != RANGE_BYTES or probe.stat().st_size != 2*OVERLAP:
        raise ValueError('exact stated byte counts required for both transfers')
    return raw.read_bytes(), probe.read_bytes()


def _checked_rows(raw, entry, prefix):
    rows, layout = rate.holdout.new_samples(raw, entry, prefix, include_candidate_rates=True)
    if len(rows) > rate.MAX_ROWS or abs(layout['first_tag_s']+DELTA_GPS_S-entry['target_gps_s']) > 30.:
        raise ValueError('platform support exceeds the declared GPS target or sample tolerance')
    return rows, layout


def _public_input(root, relative, sha):
    raw = (root/relative).read_bytes()
    if digest(raw) != sha:
        raise ValueError('required earlier ground or rate screen differs')
    return json.loads(raw)


def seal(root, *, source_size, short_exits, long_exits):
    if (source_size != GIRAFE_SOURCE_BYTES or len(short_exits) != len(TARGETS)
            or len(long_exits) != len(TARGETS) or any(v not in (0, 28) for v in (*short_exits, *long_exits))):
        raise ValueError('original archive size and exact completed range outcomes required')
    stop = _public_input(root, FIRST, FIRST_SHA)
    prefix = _public_input(root, rate.timing.probe.RESULT, rate.timing.probe.PROBE_SHA)['prefix']
    earlier = _public_input(root, rate.RESULT, RATE_SHA)
    if (rate.CONVENTIONS[earlier['selected_index']] != CONVENTION
            or earlier['absolute_timing_qualified'] is not False):
        raise ValueError('the frozen rate convention must precede this separate timing check')
    lower, upper = stop['imu_overlap_time_s']
    declared = tuple((gps, round((gps-DELTA_GPS_S-prefix['first_tag_s'])*77*1024))
                     for gps in (round(lower+(upper-lower)*f) for f in (.25, .5, .75)))
    if declared != TARGETS:
        raise ValueError('quarter-point targets derived from the original selection differ')
    entries = []
    for (gps, offset), short, long in zip(TARGETS, short_exits, long_exits, strict=True):
        raw, probe = _source_ranges(root, offset)
        entry = dict(target_gps_s=gps, offset=offset, bytes=len(raw), sha256=digest(raw),
                     short_offset=offset-OVERLAP, short_bytes=len(probe), short_sha256=digest(probe),
                     expected_overlap_sha256=overlap_digest(raw, probe), short_curl_exit=short, long_curl_exit=long)
        _, entry['layout'] = _checked_rows(raw, entry, prefix)
        entries.append(entry)
    result = dict(remote_path=GIRAFE_REMOTE, remote_size=source_size, fixed_offset_s=OFFSET_S,
                  range_receipts=entries, ground_stop_sha256=FIRST_SHA, rate_screen_sha256=RATE_SHA)
    raw = encoded(result)
    path = root/TRANSFER
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('transfer already sealed under different evidence')
    return dict(sha256=digest(raw), ranges=len(entries))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('keep the existing ground rate comparison sealed')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter,
        inputs=dict(transfer=TRANSFER, ground=FIRST, rate=rate.RESULT, probes=rate.timing.probe.RESULT),
        tasks=[TASK], sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_ground_rate.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if declared != TASK or context.manifest['scope'] != SCOPE:
        raise ValueError('exact frozen ground and rate check required')
    transfer = frozen_input(context, 'transfer', context.manifest['inputs']['transfer']['sha256'])
    stop = frozen_input(context, 'ground', FIRST_SHA)
    earlier = frozen_input(context, 'rate', RATE_SHA)
    prefix = frozen_input(context, 'probes', rate.timing.probe.PROBE_SHA)['prefix']
    if (transfer['fixed_offset_s'] != OFFSET_S or transfer['remote_path'] != GIRAFE_REMOTE
            or transfer['remote_size'] != GIRAFE_SOURCE_BYTES or transfer['ground_stop_sha256'] != FIRST_SHA
            or transfer['rate_screen_sha256'] != RATE_SHA or rate.CONVENTIONS[earlier['selected_index']] != CONVENTION
            or tuple((row['target_gps_s'], row['offset']) for row in transfer['range_receipts']) != TARGETS):
        raise ValueError('unchanged transfer and prospective convention required')
    root = context.root.parents[1]
    original = safe_path(root, SOURCE)
    output = []
    with original.open('rb') as stream:
        context.charge(bound_calls=1, bound_steps=SOURCE_BYTES)
        before = os.fstat(stream.fileno())
        if before.st_size != SOURCE_BYTES or hashlib.file_digest(stream, 'sha256').hexdigest() != stop['source_sha256']:
            raise ValueError('original iMAR file differs from the ground selection')
        stream.seek(0)
        header = stream.read(WIDTH)
        for entry in transfer['range_receipts']:
            context.charge(bound_calls=1, bound_steps=RANGE_BYTES+2*OVERLAP)
            raw, probe = _source_ranges(root, entry['offset'])
            if digest(probe) != entry['short_sha256'] or overlap_digest(raw, probe) != entry['expected_overlap_sha256']:
                raise ValueError('frozen platform range overlap differs')
            rows, layout = _checked_rows(raw, entry, prefix)
            if layout != entry['layout']:
                raise ValueError('frozen platform clock layout differs')

            context.charge(bound_calls=1, bound_steps=rate.MAX_ROWS)
            vectors = rows[:, 1:4]
            magnitudes = np.linalg.norm(vectors, axis=1)
            centers, support = rate.timing.tenth_second_values(rows[:, 0], np.column_stack((vectors, magnitudes)))
            directions = rate.case_score(rows, centers, support[:, :3], CONVENTION)
            leading_edge = centers[0]-.05+DELTA_GPS_S
            edges = leading_edge+np.arange(-pair.LAG_STEPS, len(centers)+pair.LAG_STEPS+1)/10.
            lower, upper = stop['imu_overlap_time_s']
            if not lower <= edges[0] < edges[-1] <= upper:
                raise ValueError('independent iMAR support must stay inside the selected stop')

            context.charge(bound_calls=1, bound_steps=pair.MAX_INTERVALS)
            times, force, _ = held_measurements(stream, header, row_bytes=WIDTH, row_count=RECORDS,
                                               maximum_samples=pair.MAX_INTERVALS, lower=edges[0], upper=edges[-1])
            reference = rate.timing.held_cell_means(times, np.linalg.norm(force, axis=1)[:, None], edges)[:, 0]
            context.charge(bound_calls=1, bound_steps=SHIFTS)
            match = pair.lag_scores(support[:, 3], reference)
            clock_pass, direction_pass, supported = support_flags(directions, match)
            record = dict(offset=entry['offset'], platform_sha256=entry['sha256'], platform_rows=len(rows),
                          imar_intervals=len(force), imar_gps_span_s=[float(edges[0]), float(edges[-1])],
                          direction=directions, force_clock=match, ground_clock_pass=clock_pass,
                          both_rate_separations_improve=direction_pass, rate_supported_here=supported)
            output.append(record)
            context.save_bytes(f"range-{entry['offset']}.json", encoded(record))
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('iMAR original changed during the local verification')
    supported = sum(row['rate_supported_here'] for row in output)
    context.save_bytes('ground-rate.json', encoded(dict(excerpts=output, supported_excerpts=supported,
        convention=CONVENTION, fixed_offset_s=OFFSET_S, imar_sha256=stop['source_sha256'],
        protected_reads=0, model_fits=0, scientific_decision='abstain')))
    return dict(passed=supported == len(TARGETS), supported_excerpts=supported, scientific_decision='abstain')


def report(root):
    identity = TASK['identity']
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('all frozen ground operations must be charged')
        result = study.artifact(identity, 'ground-rate.json')
        if tuple(row['offset'] for row in result['excerpts']) != tuple(offset for _, offset in TARGETS):
            raise ValueError('report must retain all three ground comparisons')
        for row in result['excerpts']:
            if study.artifact(identity, f"range-{row['offset']}.json") != row:
                raise ValueError('saved ground comparison differs from the closure')
        result.update(manifest_sha256=study.completion['manifest_sha256'], charged=TASK['limits'],
                      transfer_sha256=study.manifest['inputs']['transfer']['sha256'])
    raw = encoded(result)
    path = root/RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('sealed ground result differs')
    return dict(sha256=digest(raw), supported=result['supported_excerpts'], all_excerpts=len(TARGETS))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('seal', 'prepare', 'report'))
    parser.add_argument('--source-size', type=int)
    parser.add_argument('--short-exits', type=int, nargs=3)
    parser.add_argument('--long-exits', type=int, nargs=3)
    args = parser.parse_args()
    root = Path.cwd()
    if args.operation == 'seal':
        result = seal(root, source_size=args.source_size, short_exits=args.short_exits, long_exits=args.long_exits)
    else:
        result = {'prepare': prepare, 'report': report}[args.operation](root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
