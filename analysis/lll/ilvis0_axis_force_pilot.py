# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded shared axis-calibration proposals on the two frozen recordings."""

import argparse
from collections import defaultdict
import gzip
import io
import json
from pathlib import Path

import numpy as np

from . import ilvis0_force_direction_gap as direction
from .ilvis0_force_interval_calibration import ROUNDING_MPS2
from .ilvis0_packet_calibration import linear_terms, packet_intervals, propose
from .studies.artifacts import digest, encoded


IDENTITY = 'ilvis0-axis-force-pilot-v1-20261118'
SCOPE = 'one bounded linear axis calibration proposal per task, with exact packet verification'
ADAPTER = 'analysis/lll/ilvis0_axis_force_pilot.py'
SUPPORT, AVERAGE, CARRIER, ORDER = direction.SUPPORT, direction.AVERAGE, direction.CARRIER, direction.order
PLAN = SUPPORT.FOLDER+'AXIS_FORCE_PILOT_PLAN.md'
LIMITS = {'narrow': [.01]*3+[.05]*3, 'wide': [.15]*3+[.25]*3}
TASKS = 2*len(AVERAGE.MATCHED_MODELS)*len(ORDER.ORDERS)*len(LIMITS)
MAX_WINDOW_CLOCK_TRACK_ROWS = 3964


def _targets(raw):
    measured = {(r['segment_id'], int(r['gps_millisecond_tag'])): r for r in
                AVERAGE._table(raw[SUPPORT.OUTPUT]) if r['state']=='supported'}
    onboard = {(r['segment_id'], int(r['gps_millisecond_tag']), r['clock']): r for r in
               AVERAGE._table(raw[AVERAGE.OUTPUT]) if r['gps_stream']=='onboard'}
    phased = {(r['segment_id'], r['gps_millisecond_tag'], r['clock']): r for r in
              json.loads(gzip.decompress(raw[CARRIER.OUTPUT]))}
    rows = json.loads(gzip.decompress(raw[ORDER.OUTPUT]))
    if (len(rows) != MAX_WINDOW_CLOCK_TRACK_ROWS or len(measured) != AVERAGE.WINDOW_COUNT
            or set(phased) != set(onboard)):
        raise ValueError('unchanged joint 991-window path inputs required')
    seen = set()
    cases = defaultdict(list)
    for row in rows:
        segment, tag, clock, track, side = (row[k] for k in
            ('segment_id', 'gps_millisecond_tag', 'clock', 'track', 'side'))
        key = segment, tag, clock
        ref, original = measured[segment, tag], onboard[key]
        if ((*key, track) in seen or track not in ORDER.TRACKS or clock not in SUPPORT.CLOCKS
                or side not in ('training', 'later') or side != ref['side'] or side != original['side']
                or row['imu_type'] != ref['imu_type']):
            raise ValueError('changed matched calibration support')
        seen.add((*key, track))
        idx = [int(ref['packet_first']), int(ref['packet_stop'])]
        measurements = [float(ref[clock+'_'+bound+'_mps2']) for bound in ('lower', 'upper')]
        base = dict(tag=tag, clock=clock, track=track, support=idx, measured=measurements)
        for model in AVERAGE.MATCHED_MODELS:
            quad = ([float(original[model+'_'+bound+'_mps2']) for bound in ('lower', 'upper')]
                    if track=='onboard' else phased[key]['bounds_mps2'][model])
            cases[segment, 2, model, side].append(dict(base, predicted=quad))
            quart = row['models'][model]['quartic_bounds_mps2']
            cases[segment, 4, model, side].append(dict(base, predicted=quart))
    return cases


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/IDENTITY).exists():
        raise ValueError('inspect existing pilot instead of preparing a duplicate')
    manifest_raw = direction._inputs(root)
    earlier, raw = SUPPORT._inputs(root)
    manifest_raw.update(raw)
    cases = _targets(manifest_raw)
    inputs = {'plan': PLAN}
    tasks = []

    def stage(key, raw_bytes):
        name = f'data/{IDENTITY}-inputs/{key}'
        SUPPORT._write_equal(root/name, raw_bytes)
        inputs[key] = name

    stage('provenance.json', encoded({key: digest(value) for key, value in manifest_raw.items()}))
    for case in earlier['recordings']:
        record = SUPPORT._record(case, raw)
        segment = case['segment_id']
        buffer = io.BytesIO()
        np.savez(buffer, counts=record['counts'], elapsed=record['periods'][1], scale=record['scale'])
        packet_key = segment+'-accelerometer.npz.gz'
        stage(packet_key, gzip.compress(buffer.getvalue(), mtime=0))
        for degree in ORDER.ORDERS:
            for model in AVERAGE.MATCHED_MODELS:
                identity = f'{segment}-{degree}-{model}'
                size = {}
                for side in ('training', 'later'):
                    rows = cases[segment, degree, model, side]
                    size[side] = len(rows)
                    stage(identity+'-'+side+'.json.gz', gzip.compress(encoded(rows), mtime=0))
                for box_name, bounds in LIMITS.items():
                    tasks.append(dict(identity=identity+'-'+box_name, input_key=packet_key,
                        training_key=identity+'-training.json.gz', later_key=identity+'-later.json.gz',
                        case_count=size, imu_type=record['imu_type'], segment_id=segment,
                        model=model, degree=degree, box=box_name, coordinate_limits=bounds,
                        limits=dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0)))
    if len(tasks) != TASKS:
        raise ValueError('changed finite calibration allowance')
    definition = dict(id=IDENTITY, scope=SCOPE, adapter=ADAPTER, inputs=inputs, tasks=tasks,
        workers=2, threads=1, maximum_wall_s=180.,
        sources=source_closure(root, (ADAPTER, PLAN, 'analysis/tests/test_ilvis0_packet_calibration.py')))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study=IDENTITY, tasks=TASKS, maximum_proposals=TASKS, allocation=manifest['allocation'])


def _side(raw, periods):
    rows = json.loads(gzip.decompress(raw))
    prepared = []
    for clock, dt in zip(SUPPORT.CLOCKS, periods, strict=True):
        group = [row for row in rows if row['clock']==clock]
        prepared.append((dt, np.array([r['support'] for r in group]),
            np.array([r['measured'] for r in group]), np.array([r['predicted'] for r in group])))
    if sum(len(group[1]) for group in prepared) != len(rows):
        raise ValueError('unknown prepared clock')
    return prepared


def _score(counts, scale, side, correction):
    gaps = []
    for periods, slices, _, prediction in side:
        corrected = packet_intervals(counts, periods, scale, slices, correction, count_error=SUPPORT.COUNT_ERROR)
        gaps.extend(np.maximum(0., np.maximum(corrected[:, 0]-prediction[:, 1],
                                               prediction[:, 0]-corrected[:, 1])))
    values = np.asarray(gaps)
    return dict(cases=len(values), maximum_gap_mps2=float(np.max(values)),
                nonoverlap=int(np.count_nonzero(values > ROUNDING_MPS2)))


def evaluate(task, context):
    if context.manifest['scope'] != SCOPE or task['coordinate_limits'] != LIMITS[task['box']]:
        raise ValueError('unchanged bounded calibration task required')
    with np.load(io.BytesIO(gzip.decompress(context.input_path().read_bytes())), allow_pickle=False) as arrays:
        counts, elapsed, scale = arrays['counts'], arrays['elapsed'], float(arrays['scale'])
    if not 0 < len(counts) <= SUPPORT.MAX_PACKETS:
        raise ValueError('packet allowance exceeded')
    periods = (np.full(len(counts), .005), elapsed)
    earlier = _side(context.input_path(task['training_key']).read_bytes(), periods)
    if sum(len(group[1]) for group in earlier) != task['case_count']['training']:
        raise ValueError('changed training case count')
    design = np.vstack([linear_terms(counts, dt, scale, slices)[1] for dt, slices, _, _ in earlier])
    context.save('charge.json', dict(proposals=1, max_iterations=1000, max_seconds=2, navigation_fits=0))
    result = propose(np.vstack([x[2] for x in earlier]), np.vstack([x[3] for x in earlier]),
                     design, task['coordinate_limits'])
    context.save('training-proposal.json', result)
    if not result['passed']:
        return dict(result, scientific_decision='abstain')
    correction = result['correction']
    training = _score(counts, scale, earlier, correction)
    later = _score(counts, scale, _side(context.input_path(task['later_key']).read_bytes(), periods), correction)
    if later['cases'] != task['case_count']['later']:
        raise ValueError('changed held-out force case count')
    return dict(passed=True, training=training, later=later, navigation_fits=0,
                parameters_at_bound=sum(abs(value) >= cap-1e-10 for value, cap in
                    zip(correction, task['coordinate_limits'], strict=True)), scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare',))
    parser.parse_args()
    print(json.dumps(prepare(Path.cwd()), sort_keys=True))
