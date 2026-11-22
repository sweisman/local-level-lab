# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rescore gyro-derived force directions under two receiver derivative methods."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_direction_angle_pairs as pairs
from . import esa_direction_lever_arm as lever
from . import esa_force_position_derivative as position
from .esa_direction_evidence import FILES, _angle_comparison
from .esa_doppler_force import CENTERS, WIDTHS, coordinate_rates
from .esa_force_direction_transfer import FIELDS, FOLDER, TRAINING, _predicted_vectors, matched_field_frames
from .esa_rinex_code_comparison import coordinates
from .force_direction_alignment import direction_pair_angles_deg
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-direction-receiver-derivative-v1'
SCOPE = 'reported velocity and cubic position directions on three paired receivers on ESA 187'
PLAN = FOLDER+'ESA_DIRECTION_RECEIVER_DERIVATIVE_PLAN.md'
RESULT = FOLDER+'esa-direction-receiver-derivative-result.json'
PARENT_SHA = '355f8bcc8c5c69f59e78a28483d324b6e051a81be576b85f7a053f1726dc240e'
SHAPES = ('globe', 'disc')
METHODS = ('velocity', 'position')
RECEIVERS = ('air1', 'mosaic03', 'pwrpak7')
SOURCE_CALLS = len(WIDTHS)*len(METHODS)*len(RECEIVERS)
POINTS_PER_REPORT_INTERVAL = 4*5  # four quadrature nodes and five force evaluations each


def quadrature_points(width):
    return len(CENTERS)*(width-1)*POINTS_PER_REPORT_INTERVAL


TASKS = [task | dict(input_key=task['identity'], limits=dict(native_calls=0, packet_visits=0,
    bound_calls=SOURCE_CALLS, bound_steps=len(METHODS)*len(RECEIVERS)*sum(map(quadrature_points, WIDTHS))))
         for task in pairs.TASKS]


def angle_scores(observed, predicted):
    g, d, tie = _angle_comparison(observed, {name: {'predicted_deg': predicted[name]} for name in SHAPES})
    return dict(rms_deg={'globe': g, 'disc': d}, disc_minus_globe_deg=d-g,
                minimum_change_to_tie_rms_deg=tie)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID+'-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing receiver derivative direction freeze must stay intact')
    observations = {}
    for label, path in (('uncorrected', pairs.RESULT), ('antenna_corrected', lever.RESULT)):
        raw = (root / path).read_bytes()
        if digest(raw) != FILES[Path(path).name]:
            raise ValueError('original observed direction report required')
        observations[label] = {f"{w['kind']}-{w['window']}": w for w in json.loads(raw)['windows']}
    paths = {}
    with closing(ClosedStudy(root, 'data/'+position.ID)) as source:
        if source.completion['manifest_sha256'] != PARENT_SHA or not source.summary['passed']:
            raise ValueError('exact completed position derivative study required')
        for task in TASKS:
            name = task['identity']
            target = directory / name
            input_rows = source.input(name)['receiver']
            angles = {key: values[name]['settings'] for key, values in observations.items()}
            atomic(target, encoded(dict(receiver=input_rows, angles=angles)))
            paths[name] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=paths, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_direction_receiver_derivative.py']),
        workers=1, threads=1, maximum_wall_s=150.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def _case_predictions(rows, reference_time, width, context):
    import numpy as np

    times = np.asarray([r['time_s'] for r in rows])
    if (len(times) != 400 or np.any(abs(times-reference_time) > .002)
            or np.any(np.diff(times) <= 0.)):
        raise ValueError('original matched receiver clock required')
    coordinate = np.asarray(coordinates(rows))
    coordinate[:, 1] = np.unwrap(coordinate[:, 1])
    rates = coordinate_rates(coordinate, [[r[k] for k in ('north_mps', 'east_mps', 'up_mps')] for r in rows])
    field_frames = matched_field_frames(reference_time, coordinate)
    half = width//2
    coefficients = []
    for center in CENTERS:
        sl = slice(center-half, center+half+1)
        weights = position.position_weights(times[sl]-reference_time[center])
        coefficients.append(weights@(coordinate[sl]-coordinate[center]))
    result = {}
    for method, supplied in (('velocity', None), ('position', coefficients)):
        context.charge(bound_calls=1, bound_steps=quadrature_points(width))
        vectors = _predicted_vectors(reference_time, coordinate, rates, width, field_frames, coefficients=supplied)
        result[method] = {field: {shape: direction_pair_angles_deg(target[TRAINING:]).tolist()
                                   for shape, target in fields.items()} for field, fields in vectors.items()}
    return result


def _observations(data, width):
    uncorrected = {row['field']: row for row in data['uncorrected'] if row['width_reports'] == width}
    corrected = {row['field']: row for row in data['antenna_corrected'] if row['width_reports'] == width}
    if set(uncorrected) != set(FIELDS) or set(corrected) != set(FIELDS):
        raise ValueError('complete original direction settings required')
    return {field: dict(uncorrected=uncorrected[field]['observed_deg'],
                         antenna_corrected=corrected[field]['observed_corrected_deg']) for field in FIELDS}, (
                         uncorrected, corrected)


def _require_original(predicted, observed, reference):
    import numpy as np

    unc, corrected = reference
    for field in FIELDS:
        target = predicted[field]
        if any(not np.allclose(target[shape], unc[field]['scores'][shape]['predicted_deg'], rtol=0., atol=2e-10)
               for shape in SHAPES):
            raise ValueError('the original predicted angles did not reproduce')
        for label, expected in (('uncorrected', {k: v['rms_deg'] for k, v in unc[field]['scores'].items()}),
                                ('antenna_corrected', corrected[field]['corrected_rms_deg'])):
            replay = angle_scores(observed[field][label], target)['rms_deg']
            if any(abs(replay[shape]-expected[shape]) > 2e-10 for shape in SHAPES):
                raise ValueError('the original observed RMS did not reproduce')


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact receiver-direction task required')
    data = json.loads(context.input_path(task['identity']).read_bytes())
    receiver = data['receiver']
    time = np.asarray([r['time_s'] for r in receiver['primary']])
    sources = {'air1': receiver['primary'],
               **{name: receiver['alternatives'][name]['rows'] for name in RECEIVERS[1:]}}
    widths = []
    for width in WIDTHS:
        measured, original = _observations(data['angles'], width)
        fitted = {name: _case_predictions(rows, time, width, context) for name, rows in sources.items()}
        _require_original(fitted['air1']['velocity'], measured, original)
        scores = {name: {method: {field: {label: angle_scores(angles, target)
                          for label, angles in measured[field].items()} for field, target in by_field.items()}
                  for method, by_field in values.items()} for name, values in fitted.items()}
        widths.append(dict(width_reports=width, predicted_deg=fitted, observed_deg=measured, scores=scores))
    window = task['payload']
    context.save_bytes('direction-derivative.json', encoded(window | dict(widths=widths, scientific_decision='abstain')))
    return dict(passed=len(widths) == len(WIDTHS), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(TASKS):
            raise ValueError('complete eight-window derivative direction comparison required')
        windows = []
        for task in TASKS:
            name = task['identity']
            if any(study.rows[name]['charged'][key] != value for key, value in task['limits'].items()):
                raise ValueError('direction results and quadrature charges differ')
            windows.append(study.artifact(name, 'direction-derivative.json'))
        result = dict(windows=windows, charged=study.summary['charged'],
            manifest_sha256=study.completion['manifest_sha256'], input_manifest_sha256=PARENT_SHA,
            protected_reads=0, new_calibration_fits=0, original_data_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved direction derivative report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_receiver_derivative {prepare,report}')
