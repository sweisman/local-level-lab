# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the sampled gyro-free motion check after a sealed GPS correction."""

import argparse
from collections import defaultdict
from contextlib import closing
import json
from pathlib import Path

import numpy as np

from . import ilvis0_recorded_motion_rate as previous
from .ilvis0_shared_force_forecast import FORCE_RECEIPT_SHA
from .ilvis0_shared_force_witness_report import RESULT as FORCE_RECEIPT
from .ilvis0_shared_force_witness_study import ID as FORCE_STUDY
from .ilvis0_solver_position import physical_metric
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-shared-gps-motion-rate-v1-20261121'
PLAN = previous.FOLDER+'SHARED_GPS_MOTION_RATE_PLAN.md'
RESULT = previous.FOLDER+'shared-gps-motion-rate.json'
FREEZE_SHA = 'af3bf4864f9ca9f54da89e24a159a316ca48a842371962c21fcdc147b5a2233e'
PRIOR_SHA = 'af3eff4157b9c70431c3ac409e93f208999ff96ae0c5fdaf4d0ec948da860072'
SCOPE = 'Apply one sealed receiver correction to the two sampled gyro-free IMU8 histories'
WINDOWS = {'training': 415, 'later': 193}
PATHS = previous.paths
CLOCKS = PATHS.SUPPORT.CLOCKS
MODELS = PATHS.average.MATCHED_MODELS
CASES = len(CLOCKS)*len(MODELS)


def tasks():
    return [dict(identity=side, input_key=side, payload={},
                 limits=dict(native_calls=0, packet_visits=0,
                             bound_calls=count+CASES, bound_steps=count*CASES+CASES))
            for side, count in WINDOWS.items()]


def corrected_window(tags, onboard, archived_tags, archived_onboard, correction_m):
    indices = np.searchsorted(archived_tags, tags)
    if np.any(indices >= len(archived_tags)) or not np.array_equal(archived_tags[indices], tags):
        raise ValueError('exact archived GPS epochs required')
    positions = archived_onboard[indices].copy()
    positions[:, 1] = np.unwrap(positions[:, 1])
    if not np.array_equal(positions, onboard):
        raise ValueError('exact archived GPS positions required')
    return onboard + (correction_m/physical_metric(archived_onboard))[indices]


def _read_checked(root, path, sha):
    raw = (root/path).read_bytes()
    if digest(raw) != sha:
        raise ValueError('changed archived evidence: '+path)
    return json.loads(raw)


def _material(root, prior, freeze, force_receipt):
    raw, source, _, pairs = PATHS.carrier._checked_inputs(root)
    earlier, prepared = PATHS.SUPPORT._inputs(root)
    raw.update(prepared)
    if freeze['inputs'] != {name: digest(data) for name, data in raw.items()}:
        raise ValueError('exact original motion-rate inputs required')
    with closing(ClosedStudy(root, 'data/'+FORCE_STUDY)) as study:
        manifest = study.completion['manifest_sha256']
        if manifest != force_receipt['manifests']['imu8'] or not study.rows['imu8']['passed']:
            raise ValueError('exact sealed IMU8 correction required')
        saved = study.input('imu8')
        correction = study.artifact('imu8', 'receiver-error.json')
    segment = saved['segment_id']
    archived_tags = np.asarray(saved['tags'], np.int64)
    archived_onboard = np.asarray(saved['coordinates'], float)
    delta = np.asarray(correction['correction_m'], float)
    if (saved['imu_type'] != '8' or correction['axes'] != ['north', 'east', 'up']
            or correction['times_s'] != saved['times'] or np.any(np.diff(archived_tags) <= 0)
            or archived_onboard.shape != (len(archived_tags), 3) or delta.shape != archived_onboard.shape
            or not np.isfinite(delta).all()):
        raise ValueError('invalid shared IMU8 receiver correction')
    records = {}
    for case in earlier['recordings']:
        record = PATHS.SUPPORT._record(case, raw)
        record['midpoints'] = tuple(np.cumsum(p)-p/2 for p in record['periods'])
        records[case['segment_id']] = record
    recorded = records[segment]
    if (not np.array_equal(recorded['tags'], archived_tags)
            or not np.array_equal(recorded['times'], saved['times']) or recorded['cut'] != saved['cut']):
        raise ValueError('changed recording identity or split')
    selected = []
    grouped = {side: [] for side in WINDOWS}
    for window, offsets, (onboard, _), _ in PATHS._paths(root, raw, source, pairs):
        identity, side, tag = window['segment_id'], window['side'], int(window['gps_millisecond_tag'])
        record = records[identity]
        index = int(np.searchsorted(record['tags'], tag))
        if index >= len(record['tags']) or record['tags'][index] != tag:
            raise ValueError('changed packet selection epoch')
        target = record['times'][index]
        start, stop = int(window['packet_first']), int(window['packet_stop'])
        nominal = record['midpoints'][0][start:stop]
        packet = start+int(np.argmin(abs(nominal-target)))
        selected.append((identity, tag, side, packet))
        if identity != segment:
            continue
        tags = tag+np.rint(offsets*1000).astype(np.int64)
        if not np.array_equal((tags-tag)/1000., offsets):
            raise ValueError('window epochs must reproduce archived integer tags')
        adjusted = corrected_window(tags, onboard, archived_tags, archived_onboard, delta)
        grouped[side].append(dict(offsets=offsets.tolist(), corrected=adjusted.tolist(),
                                  target=float(target), tag=tag, packet=packet,
                                  elapsed=[float(p[packet]) for p in record['midpoints']],
                                  counts=record['counts'][packet].tolist()))
    selection_sha = digest(encoded(selected))
    if len(selected) != prior['windows'] or selection_sha != prior['packet_selection_sha256']:
        raise ValueError('packet selection differs from the original rate check')
    material = {}
    for side, rows in grouped.items():
        original = [r for r in prior['rows'] if r['side'] == side and r['segment_id'] == segment
                    and r['track'] == 'onboard']
        if len(rows) != WINDOWS[side] or len(original) != CASES:
            raise ValueError('changed sampled history inventory')
        material[side] = dict(side=side, segment_id=segment, force_manifest_sha256=manifest,
                             packet_selection_sha256=selection_sha, rows=rows, original=original)
    return material


def evaluate(task, context):
    declared = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact frozen motion-rate tasks required')
    material = json.loads(context.input_path().read_bytes())
    side = task['identity']
    rows = material['rows']
    original = {(r['clock'], r['model']): r for r in material['original']}
    if material['side'] != side or len(rows) != WINDOWS[side] or len(original) != CASES:
        raise ValueError('changed sampled history inventory')
    cases = defaultdict(list)
    for row in rows:
        context.charge(bound_calls=1, bound_steps=CASES)
        polynomial = PATHS.fit_path(row['offsets'], row['corrected'], degree=previous.DEGREE)
        for clock, elapsed in zip(CLOCKS, row['elapsed'], strict=True):
            offset = elapsed-row['target']
            if not row['offsets'][0] <= offset <= row['offsets'][-1]:
                raise ValueError('packet midpoint lies outside its original GPS window')
            jet = PATHS.point_jet(polynomial, offset)
            for model in MODELS:
                force = PATHS.evaluate(*jet, **PATHS._settings(model))['specific_force_ned_mps2']
                cases[clock, model].append((elapsed, row['counts'], force, jet[0]))
    results = []
    for key, history in sorted(cases.items()):
        context.charge(bound_calls=1, bound_steps=1)
        clock, model = key
        times, counts, force, position = zip(*history, strict=True)
        required = previous.force_in_fixed_frame(force, position, model=model)
        adjusted = previous.rate_bracket(counts, required, times, twists=previous.TWISTS)
        results.append(dict(clock=clock, model=model, original=original[key], corrected=adjusted))
    overlap = {}
    for clock in CLOCKS:
        ranges = [row['corrected'] for row in results if row['clock'] == clock]
        low = max(row['lower_rads'] for row in ranges)
        high = min(row['upper_rads'] for row in ranges)
        overlap[clock] = dict(lower_rads=low, upper_rads=high, overlap=low <= high)
    result = dict(side=side, windows=len(rows), rows=results, common_brackets=overlap,
                  packet_selection_sha256=material['packet_selection_sha256'],
                  force_point_evaluations=len(rows)*CASES, probes=len(results),
                  fit_starts=0, scientific_decision='abstain')
    context.save('motions.json', result)
    return dict(result, passed=True)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing motion-rate freeze')
    prior = _read_checked(root, previous.RESULT, PRIOR_SHA)
    freeze = _read_checked(root, previous.FREEZE, FREEZE_SHA)
    if prior['freeze_sha256'] != FREEZE_SHA:
        raise ValueError('prior brackets do not match their original freeze')
    force = _read_checked(root, FORCE_RECEIPT, FORCE_RECEIPT_SHA)
    material = _material(root, prior, freeze, force)
    inputs = dict(prior=previous.RESULT, prior_freeze=previous.FREEZE, force_receipt=FORCE_RECEIPT)
    base.mkdir()
    for key, content in material.items():
        path = base/(key+'.json')
        atomic(path, encoded(content))
        inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    test = 'analysis/tests/test_ilvis0_shared_gps_motion_rate.py'
    manifest = Definition.from_dict(dict(id=ID, adapter=adapter, scope=SCOPE, tasks=tasks(),
        inputs=inputs, workers=1, threads=1, maximum_wall_s=120.,
        sources=source_closure(root, [adapter, test, PLAN])), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or set(study.rows) != set(WINDOWS):
            raise ValueError('both sealed motion-rate histories required')
        results = []
        for side, count in WINDOWS.items():
            row = study.artifact(side, 'motions.json')
            if (dict(row, passed=True) != study.envelope(side)['result'] or row['windows'] != count
                    or row['force_point_evaluations'] != CASES*count or row['probes'] != CASES):
                raise ValueError('sealed motion-rate comparison changed')
            results.append(row)
        output = encoded(dict(records=results, prior_sha256=PRIOR_SHA,
            manifest_sha256=study.completion['manifest_sha256'], scientific_decision='abstain'))
    _write_equal(root/RESULT, output)
    print(digest(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    args = parser.parse_args()
    {'prepare': prepare, 'collect': collect}[args.action](Path.cwd())
