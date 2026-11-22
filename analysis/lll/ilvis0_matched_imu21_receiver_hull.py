# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the four sealed IMU21 forecasts over a shared GPS receiver hull."""

from contextlib import closing
import json
from pathlib import Path
import sys

from .ilvis0_matched_forecast_receiver import HORIZONS, _local, paired_range
from .ilvis0_matched_observed_inputs import FOLDER, TRACKS
from .ilvis0_matched_unstarted_report import (
    ARCHIVE, IDENTITY, MANIFEST, MODELS, RESULT as PREVIOUS, STAGE, STAGE_MANIFEST, STAGE_SUMMARY, SUMMARY,
)
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-imu21-receiver-hull-v1'
PLAN = FOLDER+'MATCHED_IMU21_RECEIVER_HULL_PLAN.md'
RESULT = FOLDER+'matched-imu21-receiver-hull-result.json'
PREVIOUS_SHA = 'd0fff4c047d0efacff044e761680f3fee698ff94f09a2c95ec24f6f143649627'
SCOPE = 'shared receiver sensitivity for the four completed IMU21 forecasts'
PAIRS = (
    ('shape_zero_field', 'sphere_still', 'flat_still'),
    ('shape_specified_field', 'sphere_rotating', 'flat_geographic_field'),
    ('field_globe', 'sphere_rotating', 'sphere_still'),
    ('field_disc', 'flat_geographic_field', 'flat_still'),
)
AXES = {'horizontal': slice(0, 2), 'height': slice(2, 3), '3d': slice(None)}
COMPARISONS = len(HORIZONS)*len(PAIRS)*len(AXES)
TASK = dict(identity='shared-receiver-hull', input_key='scoring', payload=dict(later_reports=148),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=COMPARISONS, bound_steps=COMPARISONS))


def compare(times, predictions, vertices, *, reserve=lambda: None):
    import numpy as np

    seconds, hull = np.asarray(times, float), np.asarray(vertices, float)
    paths = {name: np.asarray(value, float) for name, value in predictions.items()}
    if (seconds.ndim != 1 or not len(seconds) or seconds[0] <= 0. or np.any(np.diff(seconds) <= 0.)
            or not np.isfinite(seconds).all() or seconds[-1] < 120.
            or hull.shape != (len(seconds), 3, 3) or not np.isfinite(hull).all()
            or set(paths) != set(MODELS)
            or any(path.shape != (len(seconds), 3) or not np.isfinite(path).all() for path in paths.values())):
        raise ValueError('the full ordered four-forecast support is required')
    rows = []
    for horizon in HORIZONS:
        n = len(seconds) if horizon is None else int(np.searchsorted(seconds, horizon, side='right'))
        if n < 2:
            raise ValueError('insufficient earlier horizon support')
        contrasts = {}
        for label, first, second in PAIRS:
            scores = {}
            for axis, use in AXES.items():
                reserve()
                scores[axis] = paired_range(paths[first][:n, use], paths[second][:n, use], hull[:n, :, use])
            contrasts[label] = scores
        rows.append(dict(horizon_s=horizon, last_time_s=float(seconds[n-1]), epochs=n, contrasts=contrasts))
    return rows


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing shared reference study')
    if digest((root/PREVIOUS).read_bytes()) != PREVIOUS_SHA:
        raise ValueError('the verified four-way forecast report is required')
    segment = IDENTITY.removesuffix('-flat_still')
    with closing(ClosedStudy(root, ARCHIVE)) as parent, closing(ClosedStudy(root, STAGE, store=parent.store)) as stage:
        if ((parent.completion['manifest_sha256'], parent.completion['summary_sha256']) != (MANIFEST, SUMMARY)
                or (stage.completion['manifest_sha256'], stage.completion['summary_sha256']) != (STAGE_MANIFEST, STAGE_SUMMARY)
                or set(stage.rows) != {IDENTITY} or IDENTITY in parent.rows):
            raise ValueError('exact archived forecasts required')
        materials = {name: parent.input(segment+'-'+name, raw=True) for name in ('queries', 'scoring')}
        for model in MODELS:
            study = stage if model == 'flat_still' else parent
            identity = segment+'-'+model
            result = study.envelope(identity)['result']
            if not result['passed'] or not result['converged'] or not result['forecast_saved_before_scoring']:
                raise ValueError('each forecast must have passed its original numerical checks')
            materials['forecast-'+model] = study.artifact(identity, 'forecast.json', raw=True)
    inputs = dict(plan=PLAN, verified_forecast_report=PREVIOUS)
    for key, raw in materials.items():
        name = 'data/'+ID+'-inputs/'+key
        atomic(root/name, raw)
        inputs[key] = name
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter,
        tasks=[TASK], workers=1, threads=1, maximum_wall_s=60.,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_ilvis0_matched_imu21_receiver_hull.py']))
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    from .ilvis0_solver_position import physical_metric

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('only the sealed IMU21 receiver comparison is allowed')

    def load(key):
        return json.loads(context.input_path(key).read_bytes())

    scoring, queries = load('scoring'), load('queries')
    times = queries['query_times_s']
    cut = queries['training_epochs']
    later = scoring['query_times_s']
    if (cut != 295 or len(later) != 148 or times[cut:] != later
            or set(scoring['coordinates']) != set(TRACKS)):
        raise ValueError('original withheld GPS times and streams required')
    reference = np.asarray(scoring['coordinates']['onboard'], float)
    metric = physical_metric(reference)
    hull = np.stack([_local(scoring['coordinates'][name], reference, metric) for name in TRACKS], axis=1)
    paths = {}
    for name in MODELS:
        forecast = load('forecast-'+name)
        if forecast['training_epochs'] != cut or forecast['later_positions_used'] or forecast['query_times_s'] != times:
            raise ValueError('the sealed forecast provenance or time grid differs')
        paths[name] = _local(forecast['coordinates'][cut:], reference, metric)
    rows = compare(np.asarray(later)-times[cut-1], paths, hull,
                   reserve=lambda: context.charge(bound_calls=1, bound_steps=1))
    result = dict(horizons=rows, paired_work=COMPARISONS, later_reports=len(later),
                  passed=True, scientific_decision='abstain')
    context.save_bytes('hull.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != COMPARISONS:
            raise ValueError('every frozen GPS comparison must have completed')
        raw = encoded(study.artifact(TASK['identity'], 'hull.json') |
                      dict(manifest_sha256=study.completion['manifest_sha256']))
    out = root/RESULT
    if not out.exists():
        atomic(out, raw)
    if out.read_bytes() != raw:
        raise ValueError('shared receiver report differs from saved evidence')
    print(digest(raw))


if __name__ == '__main__':
    command = {'prepare': prepare, 'report': report}.get(sys.argv[1] if len(sys.argv) == 2 else '')
    if command is None:
        raise SystemExit('usage: python -m lll.ilvis0_matched_imu21_receiver_hull {prepare,report}')
    command(Path.cwd())
