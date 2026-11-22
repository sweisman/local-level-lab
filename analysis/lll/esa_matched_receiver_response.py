# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare force and direction using a common position/velocity response."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_direction_receiver_derivative as direction
from . import esa_force_position_derivative as position
from . import esa_girafe_force_contrast as force
from .esa_doppler_force import CENTERS, GRAVITY_LAWS, WIDTHS, coordinate_rates, predicted_force_batch, rate_operator
from .esa_force_direction_transfer import FIELDS, FOLDER, TRAINING, _predicted_vectors, matched_field_frames
from .esa_rinex_code_comparison import coordinates
from .force_direction_alignment import direction_pair_angles_deg
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-matched-receiver-response-v1'
SCOPE = 'compare ESA 187 position and velocity force predictions with matched discrete integration'
PLAN = FOLDER+'ESA_MATCHED_RECEIVER_RESPONSE_PLAN.md'
RESULT = FOLDER+'esa-matched-receiver-response-result.json'
POSITION_SHA = '355f8bcc8c5c69f59e78a28483d324b6e051a81be576b85f7a053f1726dc240e'
DIRECTION_SHA = 'dd069067afe1024e7171bc7ec246403c4f79b292537175b9ff8d420dea91b96f'
MODELS_PER_NODE = 5+len(force.MODELS)*len(GRAVITY_LAWS)
TASKS = [task | dict(input_key=task['identity'], limits=dict(native_calls=0, packet_visits=0,
    bound_calls=direction.SOURCE_CALLS,
    bound_steps=len(direction.METHODS)*len(direction.RECEIVERS)*len(CENTERS)*4*
        MODELS_PER_NODE*sum(width-1 for width in WIDTHS))) for task in direction.TASKS]


def paired_rate_coefficients(positions, rates, sample_time, reference_time):
    """Use one quadratic fit on two nodal series modulo the trapezoid null mode."""
    import numpy as np

    q, v, t, reference = (np.asarray(x, float) for x in (positions, rates, sample_time, reference_time))
    if (t.ndim != 1 or len(t) < 4 or reference.shape != t.shape or q.shape != (len(t), 3)
            or q.shape != v.shape or not all(np.isfinite(x).all() for x in (q, v, t, reference))
            or np.any(np.diff(t) <= 0.) or np.any(np.diff(reference) <= 0.)):
        raise ValueError('matched finite position and velocity rows on ordered times required')
    delta = np.diff(q, axis=0)/np.diff(t)[:, None]
    recovered = np.zeros_like(v)
    for index, average in enumerate(delta):
        recovered[index+1] = 2.*average-recovered[index]
    alternating = (-1.)**np.arange(len(t))
    recovered -= np.outer(alternating, (alternating@recovered)/len(t))
    span = max(abs(reference))
    design = np.column_stack((np.polynomial.polynomial.polyvander(reference/span, 2), alternating))
    weights = np.linalg.pinv(design)[:3]/span**np.arange(3)[:, None]
    return weights@recovered, weights@v


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID+'-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing matched receiver response freeze must stay intact')
    paths = {}
    with closing(ClosedStudy(root, 'data/'+direction.ID)) as angles, closing(
            ClosedStudy(root, 'data/'+position.ID)) as magnitudes:
        if (angles.completion['manifest_sha256'] != DIRECTION_SHA or not angles.summary['passed']
                or magnitudes.completion['manifest_sha256'] != POSITION_SHA or not magnitudes.summary['passed']):
            raise ValueError('the two completed derivative studies are required')
        for task in TASKS:
            name = task['identity']
            angle_input, force_input = angles.input(name), magnitudes.input(name)
            if angle_input['receiver'] != force_input['receiver']:
                raise ValueError('the original angle and force receiver rows differ')
            measured = {}
            for width in WIDTHS:
                saved_force, = (row for row in force_input['scores']['widths'] if row['width_reports'] == width)
                band, = (row for row in force_input['matched_sensors']['widths'] if row['width_reports'] == width)
                measured[str(width)] = saved_force['sensor_magnitudes_mps2'] | {
                    'imar_matched_gyro_assisted': [row['imar']['matched_cells'] for row in band['supports']]}
            target = directory / name
            atomic(target, encoded(angle_input | {'measured_force_by_width': measured}))
            paths[name] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=paths, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_matched_receiver_response.py']),
        workers=1, threads=1, maximum_wall_s=150.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def _by_receiver(rows, time, width, context):
    import numpy as np

    actual_time = np.asarray([r['time_s'] for r in rows])
    if len(actual_time) != 400 or np.any(abs(actual_time-time) > .002):
        raise ValueError('full original matched receiver window required')
    coords = np.asarray(coordinates(rows))
    coords[:, 1] = np.unwrap(coords[:, 1])
    rates = coordinate_rates(coords, [[row[k] for k in ('north_mps', 'east_mps', 'up_mps')] for row in rows])
    frames = matched_field_frames(time, coords)
    pos, vel, kernels = [], [], []
    half = width//2
    for index in CENTERS:
        sl = slice(index-half, index+half+1)
        knots = time[sl]-time[index]
        _, kernel = rate_operator(knots)
        a, b = paired_rate_coefficients(coords[sl], rates[sl], actual_time[sl]-time[index], knots)
        pos.append(a)
        vel.append(b)
        kernels.append((knots, kernel, coords[index]))
    result = {}
    for method, coefficients in (('position', pos), ('velocity', vel)):
        context.charge(bound_calls=1, bound_steps=len(CENTERS)*(width-1)*4*MODELS_PER_NODE)
        vectors = _predicted_vectors(time, coords, rates, width, frames, coefficients=coefficients)
        angles = {field: {shape: direction_pair_angles_deg(target[TRAINING:]).tolist()
                         for shape, target in shapes.items()} for field, shapes in vectors.items()}
        magnitudes = {law: {model: [predicted_force_batch(knots, kernel, coordinate, coef,
                            model, law, coords[0, 2])
                            for (knots, kernel, coordinate), coef in zip(kernels, coefficients, strict=True)]
                      for model in force.MODELS} for law in GRAVITY_LAWS}
        result[method] = dict(angles=angles, magnitudes=magnitudes)
    return result


def _score(prediction, angles, sensors):
    bearings = {field: {label: direction.angle_scores(angles[field][label], target)
                 for label in angles[field]} for field, target in prediction['angles'].items()}
    magnitudes = {}
    for law, values in prediction['magnitudes'].items():
        magnitudes[law] = dict(sensor_scores={name: {model: force._offset_rms(v, estimate)
                        for model, estimate in values.items()} for name, v in sensors.items()},
            shape_differences={field: force._offset_rms(values[g], values[d])
                               for field, (g, d) in force.CONTRASTS.items()})
    return dict(angles=bearings, magnitudes=magnitudes)


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact matched receiver response task required')
    data = json.loads(context.input_path(task['identity']).read_bytes())
    rows = data['receiver']
    times = np.asarray([row['time_s'] for row in rows['primary']])
    sources = dict(air1=rows['primary'], **{name: rows['alternatives'][name]['rows'] for name in direction.RECEIVERS[1:]})
    widths = []
    for width in WIDTHS:
        observations, _ = direction._observations(data['angles'], width)
        if set(observations) != set(FIELDS):
            raise ValueError('all matched field observations are required')
        sensors = data['measured_force_by_width'][str(width)]
        estimates = {name: _by_receiver(source, times, width, context) for name, source in sources.items()}
        scores = {name: {method: _score(forecast, observations, sensors) for method, forecast in values.items()}
                  for name, values in estimates.items()}
        widths.append(dict(width_reports=width, predictions=estimates, observed_angles=observations,
                           measured_mps2=sensors, scores=scores))
    context.save_bytes('receiver-response.json', encoded(task['payload'] | dict(widths=widths,
        scientific_decision='abstain')))
    return dict(passed=len(widths) == len(WIDTHS), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(TASKS):
            raise ValueError('complete eight-window matched receiver response required')
        windows = []
        for task in TASKS:
            name = task['identity']
            if any(study.rows[name]['charged'][key] != value for key, value in task['limits'].items()):
                raise ValueError('receiver response and ledger charges differ')
            windows.append(study.artifact(name, 'receiver-response.json'))
        result = dict(windows=windows, charged=study.summary['charged'], manifest_sha256=study.completion['manifest_sha256'],
            direction_manifest_sha256=DIRECTION_SHA, position_manifest_sha256=POSITION_SHA,
            original_data_reads=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved matched receiver response report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_matched_receiver_response {prepare,report}')
