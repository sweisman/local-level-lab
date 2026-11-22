# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound paired ranks and descriptive accuracy across the measured GPS spread."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import ilvis0_matched_extension_forecast as parent, ilvis0_matched_imu21_receiver_hull as shared
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_prediction_observed import accuracy_screen
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-extension-receiver-hull-v1'
PLAN = shared.FOLDER+'MATCHED_EXTENSION_RECEIVER_HULL_PLAN.md'
RESULT = shared.FOLDER+'matched-extension-receiver-hull-result.json'
SCOPE = 'paired and absolute GPS spread sensitivity on two complete NASA four-model groups'
TEST = 'analysis/tests/test_ilvis0_matched_extension_receiver_hull.py'
FORECAST_HASH = '8531eaaff881b6a14db2a3299a3048e5d65b4f143e9fc8ce81d418b5036a1918'
WORK = shared.COMPARISONS+len(shared.MODELS)
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=WORK, bound_steps=WORK)


def worst_accuracy(path, hull):
    import numpy as np

    path, hull = np.asarray(path, float), np.asarray(hull, float)
    if (path.ndim != 2 or path.shape[1] != 3 or not len(path) or hull.shape != (len(path), 3, 3)
            or not np.isfinite(path).all() or not np.isfinite(hull).all()):
        raise ValueError('aligned finite positions and three receiver vertices per epoch required')
    error = path[:, None, :]-hull
    horizontal = np.hypot(error[:, :, 0], error[:, :, 1]).max(axis=1)
    height = np.abs(error[:, :, 2]).max(axis=1)
    metrics = dict(horizontal_rms_m=float(np.sqrt(np.mean(horizontal**2))),
        vertical_rms_m=float(np.sqrt(np.mean(height**2))), maximum_horizontal_m=float(horizontal.max()),
        maximum_absolute_up_m=float(height.max()))
    return dict(**{'worst_'+key: value for key, value in metrics.items()}, accuracy=accuracy_screen(metrics))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing receiver spread allowance')
    raw = (root/parent.RECEIPT).read_bytes()
    if digest(raw) != FORECAST_HASH:
        raise ValueError('the exact sealed eight-fit comparison is required')
    result = json.loads(raw)
    inputs, cases = dict(plan=PLAN, forecast_report=parent.RECEIPT), []
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        if (any(result[key] != value for key, value in study.completion.items()) or not study.summary['passed']
                or set(study.tasks) != set(study.rows) or len(study.rows) != 8):
            raise ValueError('every original fit must pass its stopping and prediction checks')
        for row in result['comparisons']:
            segment = row['segment_id']
            data = {name: study.input(segment+'-'+name) for name in ('scoring', 'queries')}
            data['forecasts'] = {model: study.artifact(segment+'-'+model, 'forecast.json') for model in shared.MODELS}
            path = f'data/{ID}-inputs/{segment}.json'
            _write_equal(root/path, encoded(data))
            inputs[segment] = path
            cases.append(dict(identity=segment, input_key=segment, later_reports=row['scoring_epochs'],
                              imu_type=row['imu_type'], limits=LIMITS))
    if len(cases) != 2:
        raise ValueError('both added flight groups must be present')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter, tasks=cases,
        workers=1, threads=1, maximum_wall_s=60., sources=source_closure(root, (adapter, PLAN, TEST)))
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .ilvis0_solver_position import physical_metric

    if context.manifest['scope'] != SCOPE or task['limits'] != LIMITS:
        raise ValueError('the fixed saved receiver study allowance is required')
    data = json.loads(context.input_path().read_bytes())
    scoring, queries = data['scoring'], data['queries']
    times, cut, later = queries['query_times_s'], queries['training_epochs'], scoring['query_times_s']
    if (len(later) != task['later_reports'] or times[cut:] != later
            or set(scoring['coordinates']) != set(shared.TRACKS)):
        raise ValueError('the held-back receiver support does not match the saved forecast')
    reference = np.asarray(scoring['coordinates']['onboard'], float)
    metric = physical_metric(reference)
    hull = np.stack([shared._local(scoring['coordinates'][name], reference, metric) for name in shared.TRACKS], axis=1)
    paths = {}
    for model, forecast in data['forecasts'].items():
        if forecast['training_epochs'] != cut or forecast['query_times_s'] != times or forecast['later_positions_used']:
            raise ValueError('the sealed forecast alignment or provenance differs')
        paths[model] = shared._local(forecast['coordinates'][cut:], reference, metric)

    def charge():
        context.charge(bound_calls=1, bound_steps=1)

    ranks = shared.compare(np.asarray(later)-times[cut-1], paths, hull, reserve=charge)
    robust = {}
    for model, path in paths.items():
        charge()
        robust[model] = worst_accuracy(path, hull)
    result = dict(segment_id=task['identity'], imu_type=task['imu_type'], later_reports=len(later),
                  horizons=ranks, worst_accuracy=robust, passed=True, scientific_decision='abstain')
    context.save_bytes('receiver-hull.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if (not study.summary['passed'] or len(study.rows) != 2
                or study.summary['charged']['bound_calls'] != 2*WORK):
            raise ValueError('the two sealed receiver comparisons and charges are required')
        rows = [study.artifact(identity, 'receiver-hull.json') for identity in study.rows]
        result = dict(study.completion, flights=rows, charged=study.summary['charged'],
                      new_fits=0, scientific_decision='abstain')
    raw = encoded(result)
    _write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), charged=result['charged'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
