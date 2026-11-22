# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare position-derived force with the sealed velocity-based predictions."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_force_velocity_error as velocity
from . import esa_girafe_force_bandwidth as bandwidth
from . import esa_girafe_force_contrast as force
from .esa_doppler_force import CENTERS, GRAVITY_LAWS, WIDTHS, coordinate_rates, rate_operator
from .esa_gnss_covariance_audit import covariance_matrix
from .esa_rinex_code_comparison import coordinates
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-force-position-derivative-v1'
SCOPE = 'force from cubic receiver position derivatives and reported position covariance on ESA 187'
PLAN = force.PLAN.replace('ESA_GIRAFE_FORCE_CONTRAST_PLAN', 'ESA_FORCE_POSITION_DERIVATIVE_PLAN')
RESULT = force.RESULT.replace('esa-girafe-force-contrast-result', 'esa-force-position-derivative-result')
PARENT_SHA = 'ced3196a4bc8674659e799f5572847d2961bcfb11b0c7a17731d7efeafb95efb'
BANDWIDTH_SHA = 'd074365e9ce563c7f969211d2e8dfb4f4022501bd3f0cf059e97797da5ee0699'
TASKS = velocity.TASKS


def position_weights(times):
    """Map ordered position samples to their local cubic's velocity coefficients."""
    import numpy as np

    t = np.asarray(times, float)
    if (t.ndim != 1 or len(t) < 4 or not np.isfinite(t).all()
            or np.any(np.diff(t) <= 0.) or not t[0] < 0. < t[-1]):
        raise ValueError('ordered cubic position observations around the reference time required')
    span = max(abs(t))
    power = np.arange(1, 4)
    design = np.polynomial.polynomial.polyvander(t/span, 3)
    return (power/span**power)[:, None]*np.linalg.pinv(design)[1:]


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID+'-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing position derivative freeze must stay intact')
    raw = (root / bandwidth.RESULT).read_bytes()
    if digest(raw) != BANDWIDTH_SHA:
        raise ValueError('original matched bandwidth report required')
    matched = {f"{w['kind']}-{w['window']}": w for w in json.loads(raw)['windows']}
    inputs = {}
    with closing(ClosedStudy(root, 'data/'+velocity.ID)) as parent:
        if (parent.completion['manifest_sha256'] != PARENT_SHA or not parent.summary['passed']
                or set(parent.rows) != set(matched)):
            raise ValueError('exact completed velocity sensitivity study required')
        for task in TASKS:
            key = task['identity']
            target = directory / key
            atomic(target, encoded(parent.input(key) | {'matched_sensors': matched[key]}))
            inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_force_position_derivative.py']),
        workers=1, threads=1, maximum_wall_s=150.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def _position_predictions(rows, width, reference_time, context):
    import numpy as np

    own_time = np.asarray([row['time_s'] for row in rows])
    if (len(rows) != 400 or np.max(abs(own_time-reference_time)) > .002
            or np.any(np.diff(own_time) <= 0.)):
        raise ValueError('full original matched receiver window required')
    coord = np.asarray(coordinates(rows))
    coord[:, 1] = np.unwrap(coord[:, 1])
    scale = coordinate_rates(coord, np.ones_like(coord))
    factors = np.linalg.cholesky(np.asarray([
        covariance_matrix(row['position_variance_m2']+row['position_cross_covariance_m2']) for row in rows]))
    kernels = velocity._time_kernels(own_time)
    estimates = {law: {model: [] for model in force.MODELS} for law in GRAVITY_LAWS}
    slopes = {law: {model: np.zeros((len(CENTERS), len(rows), 3)) for model in force.MODELS} for law in GRAVITY_LAWS}
    half = width//2
    for index, center in enumerate(CENTERS):
        context.charge(bound_calls=1, bound_steps=4*(width-1)*velocity.PER_SUPPORT)
        sl = slice(center-half, center+half+1)
        knots = reference_time[sl]-reference_time[center]
        _, kernel = rate_operator(knots)
        weights = position_weights(own_time[sl]-reference_time[center])
        coeff = weights@(coord[sl]-coord[center])
        for law in GRAVITY_LAWS:
            for model in force.MODELS:
                value, slope = velocity.force_sensitivity(knots, kernel, coord[center], coeff, weights,
                    scale[sl], model, law, coord[0, 2])
                estimates[law][model].append(value)
                slopes[law][model][index, sl] = slope
    return estimates, slopes, factors, kernels


def _summaries(predictions, shapes, prior, sensors, factors, kernels, reference):
    cases = {}
    for law in GRAVITY_LAWS:
        estimates = predictions[law]
        slopes = shapes[law]
        cases[law] = dict(
            predicted_magnitudes_mps2=estimates,
            sensor_scores={name: {model: force._offset_rms(signal, forecast)
                                  for model, forecast in estimates.items()} for name, signal in sensors.items()},
            derivative_method_difference={model: force._offset_rms(v, prior[law][model])
                                          for model, v in estimates.items()},
            receiver_difference_vs_air1={model: force._offset_rms(v, reference[law][model])
                                         for model, v in estimates.items()},
            prediction_uncertainty={model: velocity._summarize(j, factors, kernels) for model, j in slopes.items()},
            contrasts={field: dict(difference=force._offset_rms(estimates[g], estimates[d]),
                                   uncertainty=velocity._summarize(slopes[g]-slopes[d], factors, kernels))
                       for field, (g, d) in force.CONTRASTS.items()})
    return cases


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact matched position derivative task required')
    data = json.loads(context.input_path(task['identity']).read_bytes())
    previous, matched = data['scores'], data['matched_sensors']
    if previous['window'] != matched['window']:
        raise ValueError('matched sensor and receiver windows differ')
    primary = data['receiver']['primary']
    time = np.asarray([r['time_s'] for r in primary])
    sources = dict(air1=primary, **{name: data['receiver']['alternatives'][name]['rows']
                                   for name in velocity.RECEIVERS[1:]})
    widths = []
    for recorded in previous['widths']:
        width = recorded['width_reports']
        match, = (row for row in matched['widths'] if row['width_reports'] == width)
        old = {(row['source'], row['gravity']): row['models_mps2'] for row in recorded['comparisons']}
        sensors = recorded['sensor_magnitudes_mps2'] | {
            'imar_matched_gyro_assisted': [row['imar']['matched_cells'] for row in match['supports']]}
        if not np.allclose(sensors['girafe'], [row['girafe']['native'] for row in match['supports']],
                           rtol=0., atol=2e-12):
            raise ValueError('the saved GIRAFE measurements differ')
        statistics = {}
        for name, rows in sources.items():
            expected = {law: old[name, law] for law in GRAVITY_LAWS}
            estimates, slopes, factors, kernels = _position_predictions(rows, width, time, context)
            if name == 'air1':
                reference = estimates
            statistics[name] = _summaries(estimates, slopes, expected, sensors, factors, kernels, reference)
        widths.append(dict(width_reports=width, receivers=statistics,
                           sensor_difference=force._offset_rms(sensors['girafe'], sensors['imar_matched_gyro_assisted'])))
    context.save_bytes('position-derivative.json', encoded(dict(window=previous['window'], kind=previous['kind'],
        widths=widths, scientific_decision='abstain')))
    return dict(passed=len(widths) == len(WIDTHS), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(TASKS):
            raise ValueError('complete eight-window position derivative comparison required')
        windows = []
        for task in TASKS:
            name = task['identity']
            charged = study.rows[name]['charged']
            if any(charged[key] != expected for key, expected in task['limits'].items()):
                raise ValueError('position sensitivities and charges differ')
            windows.append(study.artifact(name, 'position-derivative.json'))
        result = dict(windows=windows, charged=study.summary['charged'], manifest_sha256=study.completion['manifest_sha256'],
                      parent_manifest_sha256=PARENT_SHA, bandwidth_report_sha256=BANDWIDTH_SHA,
                      protected_reads=0, original_data_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved position derivative report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_force_position_derivative {prepare,report}')
