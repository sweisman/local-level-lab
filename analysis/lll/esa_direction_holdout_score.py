# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate sealed ESA direction predictions against newly released inertial angles."""

from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import sys

from . import esa_direction_holdout_forecast as forecast
from .airquantumgrav_geographic_controls import construct
from .airquantumgrav_inventory import IMU_NAME, METADATA
from .airquantumgrav_packet_slice import held_measurements
from .esa_component_preflight import RECORDS, WIDTH
from .esa_direction_exact_gradient import support_windows
from .esa_direction_lever_arm import OFFSET_M
from .esa_direction_receiver_derivative import angle_scores
from .esa_force_direction_transfer import CENTERS, FIELDS, TRAINING, WIDTHS, midpoint_attitudes
from .esa_repeat_turn_inputs import MAX_GAP, PAD
from .force_direction_alignment import direction_pair_angles_deg
from .lever_arm_acceleration import lever_arm_acceleration
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-direction-holdout-score-v1'
SCOPE = 'score eight sealed ESA 187 angle-pair forecasts against original iMAR measurements'
PLAN = forecast.selection.FOLDER+'ESA_DIRECTION_HOLDOUT_SCORE_PLAN.md'
RESULT = forecast.selection.FOLDER+'esa-direction-holdout-score.json'
FORECAST_SHA = '11a7e455490dff5b980d382edd035ea70c3adec71da2d5efe6c13a726734f5f9'
FORECAST_MANIFEST = '0a2b634635e4b13b87795e126135797ab193c3dcd13c0981838c5de9fd689caf'
MAX_SAMPLES = 121000
SOURCE_BYTES = WIDTH*(RECORDS+1)
TASK = dict(identity='opened-recording-angle-measurement', input_key='forecasts', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+forecast.WINDOWS,
                bound_steps=SOURCE_BYTES+forecast.WINDOWS*MAX_SAMPLES))


def score_setting(observed, predicted, reference):
    if not math.isfinite(reference) or reference < 0:
        raise ValueError('finite earlier error reference required')
    result = angle_scores(observed, predicted)
    return dict(result, earlier_reference_rms_deg=reference,
                within_reference={shape: error <= reference for shape, error in result['rms_deg'].items()})


def measured_angles(times, edges, rates, force):
    """Use the same trapezoidal intervals and support weights as the prior directions."""
    import numpy as np

    time, edges, rates, force = (np.asarray(x, float) for x in (times, edges, rates, force))
    if (time.shape != (forecast.selection.QUERIES,) or edges.ndim != 1 or len(edges) < 4
            or rates.shape != (len(edges)-1, 3) or force.shape != rates.shape
            or not all(np.isfinite(x).all() for x in (time, edges, rates, force))
            or np.any(abs(np.diff(time)-1.) > .02) or np.any((np.diff(edges) <= 0.) | (np.diff(edges) > MAX_GAP))
            or not edges[0] < time[0] < time[-1] < edges[-2]):
        raise ValueError('complete receiver and inertial clocks must bracket all direction supports')

    def reserve(*, constructed_intervals):
        if not 0 < constructed_intervals <= MAX_SAMPLES:
            raise ValueError('inertial construction exceeds the prepaid interval allowance')

    increments = construct(dict(times=edges[:-1], angular_rate_rads=rates, specific_force_mps2=force),
                           method='linear_points', rate_hz=300, reserve=reserve)
    dt, theta, dv = (increments[key] for key in ('dt', 'theta', 'dv'))
    attitudes = midpoint_attitudes(theta)
    nominal = attitudes.apply(dv/dt[:, None])
    corrected = nominal+lever_arm_acceleration(dt, theta, attitudes, OFFSET_M)
    clock = np.r_[0., np.cumsum(dt)]
    result = {}
    for width in WIDTHS:
        windows = support_windows(time-edges[0], clock, width, CENTERS[TRAINING:])
        result[str(width)] = {label: direction_pair_angles_deg([weights@value[sl] for sl, weights in windows]).tolist()
                              for label, value in (('uncorrected', nominal), ('antenna_corrected', corrected))}
    return result


def evaluate_window(window, stream, header, references):
    import numpy as np

    times = window['receiver_times_s']
    edges, force, rates = held_measurements(stream, header, row_bytes=WIDTH, row_count=RECORDS,
        maximum_samples=MAX_SAMPLES, lower=times[0]-PAD, upper=times[-1]+PAD)
    observed = measured_angles(times, edges, rates, force)
    predicted = window['predicted_angles_deg']
    scores = {width: {method: {field: {label: score_setting(values, predicted[width][method][field],
        references[width][method][field][label]) for label, values in angles.items()} for field in FIELDS}
        for method in forecast.METHODS} for width, angles in observed.items()}
    return dict(observed_deg=observed, scores=scores, raw_interval_count=len(edges)-1,
                inertial_clock_span_s=edges[[0, -1]].tolist(), maximum_gap_s=float(np.diff(edges).max()))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing holdout score study must stay sealed')
    raw = (root/forecast.RESULT).read_bytes()
    if digest(raw) != FORECAST_SHA:
        raise ValueError('exact receiver forecast receipt required')
    with closing(ClosedStudy(root, 'data/'+forecast.ID)) as study:
        if study.completion['manifest_sha256'] != FORECAST_MANIFEST or not study.summary['passed']:
            raise ValueError('receiver forecasts must be sealed before IMU release')
        expected = study.artifact(forecast.TASK['identity'], 'forecasts.json')
        if encoded(dict(expected, manifest_sha256=FORECAST_MANIFEST)) != raw:
            raise ValueError('receiver forecast receipt differs from sealed artifact')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=dict(forecasts=forecast.RESULT),
        tasks=[TASK], sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_direction_holdout_score.py']),
        workers=1, threads=1, maximum_wall_s=150.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact holdout score task required')
    design = forecast.frozen_input(context, 'forecasts', FORECAST_SHA)
    windows = design['windows']
    if (len(windows) != forecast.WINDOWS or design['source']['group_id'] != 'esa-99f1530c3eda4318'
            or design['manifest_sha256'] != FORECAST_MANIFEST):
        raise ValueError('fixed recording 187 forecast required')
    original = Path(METADATA['inspection']).with_name(IMU_NAME).as_posix()
    rows = []
    with safe_path(context.root.parents[1], original).open('rb') as stream:
        context.charge(bound_calls=1, bound_steps=SOURCE_BYTES)
        start = os.fstat(stream.fileno())
        if start.st_size != SOURCE_BYTES or hashlib.file_digest(stream, 'sha256').hexdigest() != design['source']['imu_source_sha256']:
            raise ValueError('original IMU source hash or byte count differs')
        stream.seek(0)
        header = stream.read(WIDTH)
        for window in windows:
            context.charge(bound_calls=1, bound_steps=MAX_SAMPLES)
            indices = {key: window[key] for key in ('leg', 'course', 'query_first_index', 'query_last_index')}
            try:
                row = dict(indices, status='scored', **evaluate_window(window, stream, header, design['reference_error_deg']))
            except ValueError as error:
                row = dict(indices, status='rejected', reason=str(error))
            context.save_bytes(f"window-{window['query_first_index']}.json", encoded(row))
            rows.append(row)
        end = os.fstat(stream.fileno())
        keys = ('st_size', 'st_mtime_ns', 'st_ctime_ns')
        if any(getattr(start, key) != getattr(end, key) for key in keys):
            raise ValueError('original recording changed during scoring')
    passed = sum(row['status'] == 'scored' for row in rows)
    context.save_bytes('scores.json', encoded(dict(windows=rows, forecast_sha256=FORECAST_SHA,
        forecast_manifest_sha256=FORECAST_MANIFEST, imu_source_sha256=design['source']['imu_source_sha256'],
        antenna_offset_m=OFFSET_M, original_receiver_reads=0, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=passed == len(windows), scored_windows=passed, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        if study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('the full charge ledger is required to report the eight window attempts')
        result = study.artifact(identity, 'scores.json')
        if len(result['windows']) != forecast.WINDOWS:
            raise ValueError('every window result must be present')
        for row in result['windows']:
            if study.artifact(identity, f"window-{row['query_first_index']}.json") != row:
                raise ValueError('individual window artifact differs from the score summary')
        result['manifest_sha256'] = study.completion['manifest_sha256']
        result['charged'] = study.summary['charged']
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('published score receipt differs from sealed evidence')
    return dict(sha256=digest(raw), windows=len(result['windows']))


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
