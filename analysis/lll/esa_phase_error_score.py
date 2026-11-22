# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propagate changes in GPS carrier phase to the frozen shape score."""

from contextlib import closing
import json
from pathlib import Path
import sys

from .esa_carrier_satellite_influence import COUNT, CUT, END, FOLDER, LATER, START
from .esa_carrier_satellite_influence import ID as PARENT, RESULT as PARENT_REPORT, TASKS
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-phase-error-score-v1'
SCOPE = 'linearized propagation of archived ESA 187 GPS phase errors into the fixed shape score'
PLAN = FOLDER + 'ESA_PHASE_ERROR_SCORE_PLAN.md'
RESULT = FOLDER + 'esa-phase-error-score-result.json'
PARENT_MANIFEST = '6365d30f77cdba58de8e0afb95d7410c6b4ab8fb74edc94bdaa460141a3de274'
PARENT_SHA = 'ee0a7a82e416c1a6e04f4af1d52a6d7f7e0a08d9150e077f11643a28ca77aa8e'
TOLERANCE = .00002
TASK = dict(identity='phase-error-score', input_key='rows', payload=dict(pairs=COUNT),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=COUNT, bound_steps=COUNT*32))


def endpoint_weights(steps):
    """Map weights on phase differences to weights on the original observations."""
    import numpy as np

    steps = np.asarray(steps, dtype=float)
    if steps.ndim != 2 or not len(steps) or not np.isfinite(steps).all():
        raise ValueError('expected a finite chronological step-by-satellite array')
    rows = np.zeros((1+len(steps), steps.shape[1]))
    rows[:-1] -= steps
    rows[1:] += steps
    return rows


def ecef_gradients(track, coordinates):
    import numpy as np

    from .gnss_position import local_rotation
    from .models import radii

    latitude, _, height = track[0]['position']
    meridian, prime = radii(latitude)
    north_scale, east_scale = meridian+height, (prime+height)*np.cos(latitude)
    gradient = np.zeros((len(track), 3))
    for index, (row, weights) in enumerate(zip(track[::2], coordinates, strict=True)):
        lat, lon, h = row['position']
        m, n = radii(lat)
        scale = [north_scale/(m+h), east_scale/((n+h)*np.cos(lat)), 1.]
        gradient[index*2] = (weights * scale) @ local_rotation(lat, lon)
    return gradient


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing phase sensitivity freeze must be preserved')
    report = (root/PARENT_REPORT).read_bytes()
    if digest(report) != PARENT_SHA:
        raise ValueError('the exact archived satellite report is required')
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_MANIFEST or not parent.summary['passed']:
            raise ValueError('a verified satellite-influence completion is required')
        staged = {name: parent.input(name, raw=True) for name in ('track', 'shape', 'operator')}
        rows = [row for task in TASKS for row in parent.artifact(task['identity'], 'satellite-influence.json')]
    if [row['index'] for row in rows] != list(range(START, END)) or any('error' in row for row in rows):
        raise ValueError('all original carrier steps must be present and passing')
    staged['rows'] = encoded(rows)
    inputs = dict(plan=PLAN, baseline=PARENT_REPORT)
    for name, raw in staged.items():
        path = 'data/'+ID+'-inputs/'+name
        atomic(root/path, raw)
        inputs[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_phase_error_score.py']),
        workers=1, threads=1, maximum_wall_s=45.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def calculate(context, rows, track, expected, tail):
    import numpy as np

    prns = sorted(expected)
    step_weights = np.zeros((COUNT, len(prns)))
    omission = np.zeros_like(step_weights)
    for index, (row, gradient) in enumerate(zip(rows, tail, strict=True)):
        context.charge(bound_calls=1, bound_steps=32)
        columns = [prns.index(prn) for prn in row['satellites']]
        residual = np.asarray(row['withheld_range_error_m'])
        correction = np.asarray(row['correction_ecef_m'])
        if (not 5 <= len(columns) <= 32 or len(set(columns)) != len(columns)
                or residual.shape != (len(columns),) or correction.shape != (len(columns), 3)
                or np.any(residual == 0) or not np.isfinite(residual).all()
                or not np.isfinite(correction).all()):
            raise ValueError('one finite sensitivity per supported satellite required')
        omission[index, columns] = correction @ gradient
        step_weights[index, columns] = -omission[index, columns] / residual
    offsets = endpoint_weights(step_weights)
    seconds = np.asarray([row['seconds'] for row in track])
    minutes = (seconds-seconds[0])/60
    if not np.all(np.diff(seconds) > 0):
        raise ValueError('strictly increasing saved carrier times required')
    drift = minutes @ offsets
    effects = omission.sum(axis=0)
    omission_error = float(max(abs(effect-expected[prn]) for effect, prn in zip(effects, prns, strict=True)))
    if omission_error > TOLERANCE:
        raise ValueError('the 12 checked satellite omission scores did not reproduce')
    clock_error = float(np.max(np.abs(offsets.sum(axis=1))))
    fixed_phase_error = float(np.max(np.abs(offsets.sum(axis=0))))
    clock_limit = 1e-10 * max(1., float(np.max(np.abs(offsets))))
    if max(clock_error, fixed_phase_error) > clock_limit:
        raise ValueError('constant satellite phase or per-epoch receiver-clock cancellation failed')
    context.save_bytes('phase-score-weights.json', encoded(dict(prns=prns, times=seconds.tolist(),
        step_weights=step_weights.tolist(), epoch_weights=offsets.tolist(), drift_gains=drift.tolist())))
    return dict(omission_replay_max_error=omission_error, clock_gain_max=clock_error,
                constant_satellite_phase_gain_max=fixed_phase_error,
                endpoint_independent_score_sd_per_m=float(np.linalg.norm(offsets)),
                independent_steps_score_sd_per_m_endpoint_equivalent=float(np.sqrt(2)*np.linalg.norm(step_weights)),
                endpoint_bounded_gain=float(np.sum(np.abs(offsets))),
                bounded_drift_gain=float(np.sum(np.abs(drift))))


def evaluate(task, context):
    import numpy as np

    from .innovations_snapshot import restore
    from .state_space_directional_bound import adjoint_intervals

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('unexpected carrier-phase score task')
    track = json.loads(context.input_path('track').read_bytes())['positions']
    rows = json.loads(context.input_path('rows').read_bytes())
    original = json.loads(context.input_path('baseline').read_bytes())
    shape = json.loads(context.input_path('shape').read_bytes())
    if (len(track) != COUNT+1 or len(track[::2]) != CUT+LATER
            or [row['index'] for row in rows] != list(range(START, END))
            or original['manifest_sha256'] != PARENT_MANIFEST or len(original['satellites']) != 12):
        raise ValueError('unchanged archived trajectory, score and support required')
    operator = restore(context.input_path('operator').read_bytes(), expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    lo, hi = adjoint_intervals(operator, np.r_[np.zeros(3*CUT), shape['direction']])
    gradients = ecef_gradients(track, ((lo+hi)/2).reshape(-1, 3))
    tail = np.cumsum(gradients[::-1], axis=0)[::-1][1:]
    expected = {row['prn']: row['score_effect'] for row in original['satellites']}
    result = calculate(context, rows, track, expected, tail)
    margin = -original['baseline']
    if margin <= 0 or any(result[key] <= 0 for key in (
        'endpoint_independent_score_sd_per_m', 'endpoint_bounded_gain', 'bounded_drift_gain')):
        raise ValueError('the saved score must have a positive margin and positive sensitivity')
    result.update(passed=True, baseline_score=-margin, pairs=COUNT,
        endpoint_noise_sd_for_margin_m=margin/result['endpoint_independent_score_sd_per_m'],
        endpoint_peak_for_tie_m=margin/result['endpoint_bounded_gain'],
        per_satellite_drift_for_tie_m_per_min=margin/result['bounded_drift_gain'],
        adjoint_enclosure_max_width=float(np.max(hi-lo)), scientific_decision='abstain')
    context.save_bytes('phase-score-result.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != COUNT:
            raise ValueError('complete phase sensitivity result required')
        result = study.artifact(TASK['identity'], 'phase-score-result.json')
        result.update(manifest_sha256=study.completion['manifest_sha256'])
    raw = encoded(result)
    out = root/RESULT
    if not out.exists():
        atomic(out, raw)
    if out.read_bytes() != raw:
        raise ValueError('saved phase sensitivity result differs')
    print(raw.decode(), end='')


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_phase_error_score {prepare,report}')
