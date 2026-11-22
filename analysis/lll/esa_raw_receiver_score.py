# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure fixed-score sensitivity to matched raw receiver differences."""

from contextlib import closing
import json
from pathlib import Path
import sys

from .esa_carrier_satellite_influence import COUNT, CUT, END, FOLDER, ID as GEOMETRY, START, TASKS
from .esa_parallel_raw_receiver import FIRST_SHARED, INTERVALS, ID as MATCHED, PAIRS, TASK as MATCHED_TASK
from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


ID = 'esa-raw-receiver-score-v1'
PLAN = FOLDER + 'ESA_RAW_RECEIVER_SCORE_PLAN.md'
RESULT = FOLDER + 'esa-raw-receiver-score-result.json'
SCOPE = 'ESA 187 frozen shape score under linearized relative raw receiver shifts'
GEOMETRY_MANIFEST = '6365d30f77cdba58de8e0afb95d7410c6b4ab8fb74edc94bdaa460141a3de274'
MATCHED_MANIFEST = '97a9eacde0586dad1d9975cd6c92490fdde9a184907cf9d27ecfd160781913c4'
TASK = dict(identity='matched-relative-receiver-score', input_key='matched', payload=dict(intervals=INTERVALS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=INTERVALS, bound_steps=4*INTERVALS))


def centered_geometry(saved):
    import numpy as np

    correction = np.asarray(saved['correction_ecef_m'])
    residual = np.asarray(saved['withheld_range_error_m'])
    if (correction.shape != (len(saved['satellites']), 3) or residual.shape != (len(correction),)
            or np.any(residual == 0.) or not np.isfinite(residual).all() or not np.isfinite(correction).all()):
        raise ValueError('one saved displacement and nonzero residual per satellite required')
    gain = (-correction/residual[:, None]).T
    geometry = np.linalg.pinv(gain)
    if (np.max(np.abs(geometry.mean(axis=0))) > 1e-12
            or not np.allclose(np.linalg.pinv(geometry), gain, rtol=1e-12, atol=1e-12)):
        raise ValueError('the archived position-and-clock design did not reproduce')
    return geometry


def fit_displacements(geometry, ranges):
    import numpy as np

    from .gnss_carrier_phase import MAX_CONDITION

    design = np.c_[geometry-geometry.mean(axis=0), np.ones(len(geometry))]
    condition = float(np.linalg.cond(design))
    if len(design) < 5 or not condition < MAX_CONDITION:
        raise ValueError('insufficient common satellite geometry')
    fit = np.linalg.lstsq(design, ranges, rcond=None)[0]
    return fit[:3].T, condition


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('the existing score comparison must be preserved')
    with closing(ClosedStudy(root, 'data/'+GEOMETRY)) as geometry, closing(
            ClosedStudy(root, 'data/'+MATCHED, store=geometry.store)) as matched:
        if (geometry.completion['manifest_sha256'] != GEOMETRY_MANIFEST
                or matched.completion['manifest_sha256'] != MATCHED_MANIFEST
                or not geometry.summary['passed'] or not matched.summary['passed']):
            raise ValueError('exact checked raw pair and satellite geometry evidence required')
        staged = {key: geometry.input(key, raw=True) for key in ('track', 'shape', 'operator', 'baseline')}
        archived = [row for task in TASKS for row in geometry.artifact(task['identity'], 'satellite-influence.json')]
        staged['geometry'] = encoded(archived)
        staged['matched'] = matched.artifact(MATCHED_TASK['identity'], 'carrier-differences.json', raw=True)
    inputs = dict(plan=PLAN)
    for key, raw in staged.items():
        path = 'data/'+ID+'-inputs/'+key
        atomic(root/path, raw)
        inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_raw_receiver_score.py']),
        workers=1, threads=1, maximum_wall_s=60.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def intervals(context, geometry, matched):
    import numpy as np

    keys = ['-'.join(pair) for pair in PAIRS]
    correction = np.zeros((INTERVALS+1, 2, len(keys), 3))
    records = []
    for index, row in enumerate(matched):
        context.charge(bound_calls=1, bound_steps=4)
        if row['first_gps_seconds'] != FIRST_SHARED+index or row['last_gps_seconds'] != FIRST_SHARED+index+1:
            raise ValueError('original ordered one-second receiver intervals required')
        base = dict(first_gps_seconds=row['first_gps_seconds'], portion=row['portion'])
        if 'skipped' in row:
            records.append(dict(base, skipped=row['skipped']))
            continue
        phases = [row['pairs'][key] for key in keys]
        names = phases[0]['satellites']
        if any(item['satellites'] != names for item in phases):
            raise ValueError('identical pair supports required')
        half_steps = [geometry[START+2*index+side] for side in range(2)]
        support = sorted(set(names).intersection(*(step['satellites'] for step in half_steps)))
        if len(support) < 5 or any('signed_differences_m' not in item for item in phases):
            records.append(dict(base, skipped='insufficient shared receiver and geometry support', satellites=support))
            continue
        ranges = np.asarray([item['signed_differences_m'] for item in phases]).T
        ranges = ranges[[names.index(prn) for prn in support]]
        condition = []
        try:
            for side, step in enumerate(half_steps):
                selected = [step['satellites'].index(prn) for prn in support]
                steps, cond = fit_displacements(centered_geometry(step)[selected], ranges)
                if np.max(np.abs(steps[0]+steps[2]-steps[1])) > 1e-12:
                    raise ValueError('the relative displacement triangle did not close')
                correction[index+1, side] = steps
                condition.append(cond)
        except ValueError as error:
            if str(error) != 'insufficient common satellite geometry':
                raise
            correction[index+1] = 0
            records.append(dict(base, skipped=str(error), satellites=support))
            continue
        records.append(dict(base, satellites=support, condition=condition, differences_ecef_m=correction[index+1].tolist()))
    return correction.cumsum(axis=0), records


def evaluate(task, context):
    import numpy as np

    from .esa_carrier_satellite_influence import ecef_track
    from .esa_changing_drift_transfer import _chart
    from .esa_phase_error_score import ecef_gradients
    from .gnss_position import geodetic
    from .innovations_snapshot import restore
    from .state_space_directional_bound import adjoint_intervals

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the exact frozen receiver score task is required')
    def load(key):
        return json.loads(context.input_path(key).read_bytes())

    matched, track, shape, baseline = load('matched'), load('track')['positions'], load('shape'), load('baseline')
    geometry = {row['index']: row for row in load('geometry')}
    if len(matched) != INTERVALS or sorted(geometry) != list(range(START, END)) or len(track) != COUNT+1:
        raise ValueError('the entire saved forecast trajectory and all evidence are required')
    correction, records = intervals(context, geometry, matched)
    operator = restore(context.input_path('operator').read_bytes(), expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    direction = np.r_[np.zeros(3*CUT), shape['direction']]
    origin = np.asarray(track[0]['position'])
    base = _chart([r['position'] for r in track[::2]], origin)
    positions = ecef_track(track)[::2]
    clock_skips = [index for index, row in enumerate(records) if row.get('skipped') == 'archived AIR1 receiver clock step']
    if len(clock_skips) != 1 or len(positions) != len(correction):
        raise ValueError('the known clock gap and matching score grid required')
    lo, hi = adjoint_intervals(operator, direction)
    gradient = ecef_gradients(track, ((lo+hi)/2).reshape(-1, 3))[::2]
    gap_gain = float(np.linalg.norm(gradient[clock_skips[0]+1:].sum(axis=0)))
    results = []
    original = baseline['carrier_signed_midpoint']
    for side, geometry_name in enumerate(('opening', 'closing')):
        for index, (first, last) in enumerate(PAIRS):
            # Saved differences are first minus last. Report last relative to first.
            shifted = positions - correction[:, side, index]
            delta = _chart([geodetic(p) for p in shifted], origin) - base
            change = float(direction @ operator.whiten(delta.ravel()))
            results.append(dict(first=first, last=last, geometry=geometry_name, score_shift=change,
                later_rms_m=float(np.sqrt(np.mean(np.sum(delta[CUT:]**2, axis=1)))),
                shifted_air1_score=original+change if first == 'air1' else None))
    passed = [r for r in records if 'skipped' not in r]
    context.save_bytes('receiver-shifts.json', encoded(records))
    result = dict(passed=True, baseline_score=original, results=results, intervals=len(records),
        retained_intervals=len(passed), skipped=[r for r in records if 'skipped' in r],
        minimum_satellites=min(len(r['satellites']) for r in passed),
        clock_gap_score_gain_per_m=gap_gain, scientific_decision='abstain')
    context.save_bytes('receiver-score.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != INTERVALS:
            raise ValueError('the complete sealed receiver score evidence is required')
        result = study.artifact(TASK['identity'], 'receiver-score.json')
        raw = encoded(result | dict(manifest_sha256=study.completion['manifest_sha256']))
    destination = root/RESULT
    if not destination.exists():
        atomic(destination, raw)
    if destination.read_bytes() != raw:
        raise ValueError('the saved receiver score report differs')
    print(raw.decode(), end='')


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_raw_receiver_score {prepare,report}')
