# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact scalar replay of selected conditioned shape-calibration steps."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path
import sys


ID = 'esa-shape-remainder-witness-v1-20261119'
SCOPE = 'finite exact nonlinear witnesses in the ESA conditioned shape direction'
ADAPTER = 'analysis/lll/shape_remainder_witness.py'
BASE = 'docs/prediction-observed-development/'
PLAN = BASE + 'SHAPE_REMAINDER_WITNESS_PLAN.md'
MODELS = ('sphere_still', 'flat_still')
EARLIER, LATER, PACKETS = 400, 120, 155868
STEPS = ((0., 1.), (0., .98), (.1, 1.), (1., 1.))
CALLS = 1 + len(STEPS)
SOURCE = 'data/esa-calibration-contrast-v1-20261118'
SOURCE_SHA = 'b6090b845e20a82e617e05e4f00e97c342729dcecd2150a7ce4bd56e40bbb3ef'
PRIOR = 'data/esa-conditioned-witness-v1-20261118'
PRIOR_SHA = '52cddc2cdfdd4bfc5cec3ae5d46313416b1d87c60e19108a24ec66979c6a772a'
HEADROOM_SHA = 'b7b713164e4df37f8fa11bff641ebd91ec01f2b1e32f13bdedbe81dbfd968d3d'
SHARED = ('interval', 'training', 'forecast_times', 'recipe', 'environment', 'parent', 'frozen_python_native')
MODEL_INPUTS = ('fit', 'forecast', 'training_observations', 'compiler', 'weights', 'weights-receipt')
COMPANIONS = tuple('analysis/lll/'+name+'.py' for name in (
    'esa_tangent_remainder', 'esa_original_whitening', 'innovations_snapshot'))


def declared_probes(rows, model):
    by_delta = {row['assumed_earlier_remainder']: row['support'][model] for row in rows}
    output = []
    for delta, fraction in STEPS:
        selected = by_delta[delta]
        point = selected['point']
        if len(point) != 27 or not all(math.isfinite(v) and abs(v) <= .1 for v in point):
            raise ValueError('exact local 27-coordinate calibration step required')
        output.append(dict(delta=delta, fraction=fraction, point=[fraction*v for v in point],
                           affine_projection=fraction*selected['achieved']))
    return output


def tasks():
    return [dict(identity=model, input_key='interval', native_kind='value', payload=dict(model=model),
                 limits=dict(native_calls=CALLS, packet_visits=CALLS*PACKETS*(EARLIER+LATER),
                             bound_calls=0, bound_steps=0)) for model in MODELS]


def prepare(root):
    import numpy as np
    from . import esa_changing_drift_transfer as full
    from .airquantumgrav_inventory import environment
    from .conditioned_shape_calibration import projected_direction
    from .esa_conditional_forecast_study import require_guarded_environment
    from .esa_joint_path_score import _ranges
    from .ilvis0_solver_position import physical_metric
    from .innovations_snapshot import capture
    from .matched_shape_metric import REFERENCE, REFERENCE_SHA
    from .shape_remainder_headroom import RESULT as HEADROOM
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing witness freeze')
    current = require_guarded_environment(environment())
    reference_raw = (root/REFERENCE).read_bytes()
    headroom_raw = (root/HEADROOM).read_bytes()
    if digest(reference_raw) != REFERENCE_SHA or digest(headroom_raw) != HEADROOM_SHA:
        raise ValueError('the original directional support and sensitivity are required')
    headroom = next(row for row in json.loads(headroom_raw)['rows'] if
                    row['covariance'] == 'full' and row['receiver_weight'] == 'fixed_3cm')
    reference = next(row for row in json.loads(reference_raw)['settings'] if
                     row['complete'] and row['imu_law'] == 'increment')
    saved = _ranges({name: (root/name).read_bytes() for name in (full.SEAL, full.RANGES, full.FREEZE)}, full)
    with closing(ClosedStudy(root, SOURCE)) as source, closing(ClosedStudy(root, PRIOR, store=source.store)) as prior:
        if (source.completion['manifest_sha256'] != SOURCE_SHA or source.completion['state'] != 'complete'
                or prior.completion['manifest_sha256'] != PRIOR_SHA or not prior.summary['passed']
                or source.input('environment') != current):
            raise ValueError('closed calibration evidence and original scalar environment required')
        materials = {name: source.input(name, raw=True) for name in SHARED}
        for model in MODELS:
            materials.update({model+'-'+name: source.input(model+'-'+name, raw=True) for name in MODEL_INPUTS})
            tangent = source.artifact(model, 'full-tangent.json')
            if digest(materials[model+'-forecast']) != tangent['source_forecast_sha256']:
                raise ValueError('step and model forecast must agree with the earlier linearization')
            materials[model+'-probes'] = encoded(declared_probes(headroom['rows'], model))
        materials['prior-completion'] = encoded(prior.completion)
    times = json.loads(materials['forecast_times'])
    centers = {row['identity']: row['ranges']['fixed_3cm']['center_m'] for row in saved['rows']
               if row['identity'] in {reference['selected'][model] for model in MODELS}}
    a, b = (np.asarray(centers[reference['selected'][model]]) for model in MODELS)
    weights = np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3))
    operator = full.operator(times, weights)
    direction, nominal = projected_direction(operator, times, b-a, EARLIER)
    if (operator.configuration != saved['operator_configurations']['fixed_3cm']
            or not math.isclose(nominal, headroom['nominal'], rel_tol=1e-9)):
        raise ValueError('archived covariance and separation must replay exactly')
    materials['later-operator'] = capture(operator)
    materials['shape-direction'] = encoded(dict(configuration=operator.configuration,
        factors_sha256=digest(materials['later-operator']), direction=direction.tolist(),
        metric=physical_metric([saved['anchor']])[0].tolist(), nominal=nominal,
        headroom_sha256=digest(headroom_raw)))
    base.mkdir(parents=True, exist_ok=False)
    inputs = {}
    for name, raw in materials.items():
        path = base/name
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, inputs=inputs, tasks=tasks(), workers=1,
                      threads=1, maximum_wall_s=120., sources=source_closure(root, (ADAPTER, PLAN,
                      'analysis/tests/test_shape_remainder_witness.py', *COMPANIONS)))
    atomic(base/'definition.json', encoded(definition))
    Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=2, manifest_sha256=digest((root/'data'/ID/'manifest.json').read_bytes()))


def evaluate(declared, context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import invoke_frozen

    model = declared['identity']
    task = {name: value for name, value in declared.items() if name not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE
            or task != next((case for case in tasks() if case['identity'] == model), None)
            or environment() != json.loads(context.input_path('environment').read_bytes())):
        raise ValueError('exact finite scalar task required')
    inputs = (*SHARED, 'shape-direction', 'later-operator', *(model+'-'+key for key in (*MODEL_INPUTS, 'probes')))
    raw = invoke_frozen(context, entry=Path(__file__), calls=CALLS, inputs=inputs, companions=COMPANIONS)
    result = json.loads(raw)
    if result['model'] != model or len(result['checks']) != len(STEPS):
        raise ValueError('every declared witness must be retained')
    context.save_bytes('shape-witnesses.json', raw)
    return dict(passed=True, model=model, fit_starts=0, protected_reads=0,
                later_receiver_positions_read=0, scientific_decision='abstain')


def frozen_replay(inputs, output):
    import numpy as np
    from lll.esa_original_whitening import score_change
    from lll.esa_tangent_remainder import scalar_replay
    from lll.innovations_snapshot import restore
    from lll.studies.artifacts import encoded

    model, = [candidate for candidate in MODELS if candidate+'-fit' in inputs]
    inputs.update({name: inputs[model+'-'+name] for name in (*MODEL_INPUTS, 'probes')})

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    fit, point, _, _, baseline, baseline_max, displacement = scalar_replay(inputs, output, expected_model=model)
    archived, direction = read('weights-receipt'), read('shape-direction')
    old = restore(Path(inputs['weights']).read_bytes(), expected_sha256=archived['snapshot_sha256'],
                  expected_configuration=read('forecast')['error_training_configuration'], maximum_bytes=2**26)
    later = restore(Path(inputs['later-operator']).read_bytes(), expected_sha256=direction['factors_sha256'],
                    expected_configuration=direction['configuration'], maximum_bytes=2**26)
    local = fit['local_linearization']
    jacobian, residual = np.asarray(local['jacobian']), np.asarray(local['residual'])
    probes = read('probes')
    if [(trial['delta'], trial['fraction']) for trial in probes] != list(STEPS):
        raise ValueError('all four original probes required')
    checks = []
    for trial in probes:
        step = np.asarray(trial['point'])
        target = point+step
        if np.any(np.abs(target) > 1.+4*np.finfo(float).eps):
            raise ValueError('exact probe leaves the original parameter box')
        change = displacement(np.clip(target, -1., 1.))-baseline
        score_change_earlier = old.whiten(change[:EARLIER].ravel())
        earlier_remainder = float(np.linalg.norm(score_change_earlier-jacobian@step))
        later_change = later.whiten((change*np.asarray(direction['metric'])).ravel())[3*EARLIER:]
        projection = (1 if model == MODELS[0] else -1)*float(np.asarray(direction['direction'])@later_change)
        loss = score_change(residual, score_change_earlier)
        checks.append(dict(delta=trial['delta'], fraction=trial['fraction'], exact_loss_increase=loss,
                           original_loss_passed=loss <= .01, earlier_remainder_norm=earlier_remainder,
                           exact_projection=projection, affine_projection=trial['affine_projection'],
                           projected_remainder=abs(projection-trial['affine_projection'])))
    output.write_bytes(encoded(dict(model=model, baseline_scalar_max_m=baseline_max, checks=checks,
                                   fit_starts=0, later_receiver_positions_read=0,
                                   protected_reads=0, scientific_decision='abstain')))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '_frozen':
        frozen_replay(json.loads(sys.argv[2]), Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('prepare',))
        parser.parse_args()
        print(json.dumps(prepare(Path.cwd()), sort_keys=True))
