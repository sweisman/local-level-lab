# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound calibration shifts toward other saved ESA forecasts."""

import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import subprocess
import sys


ID = 'esa-calibration-contrast-v1-20261118'
ADAPTER = 'analysis/lll/esa_calibration_contrast.py'
PLAN = 'docs/prediction-observed-development/ESA_CALIBRATION_CONTRAST_PLAN.md'
SCOPE = 'earlier-loss-constrained affine forecast contrast support and nonlinear witness checks'
WEIGHTS = 'data/esa-original-whitening-v1-20261118'
WEIGHTS_SHA = '41b966cd477a2ac0fa5bf3b950d19523e6909ed2bbbae9bcc91a2addbadf337d'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
BUDGETS = (.001, .01)
RADIUS = .1
TRAIN, FORECAST, PACKETS = 400, 120, 155868
VISITS = PACKETS*(TRAIN+FORECAST)
VALUE_CALLS = 5
COMPANIONS = tuple('analysis/lll/'+name+'.py' for name in (
    'esa_tangent_remainder', 'esa_native_tangent_replay', 'esa_original_whitening',
    'calibration_loss_support', 'innovations_snapshot'))
SHARED = ('interval', 'training', 'forecast_times', 'recipe', 'environment',
          'parent', 'frozen_python_native', 'forecast-family')
PER_MODEL = ('fit', 'forecast', 'training_observations', 'compiler', 'weights', 'weights-receipt')


def key(model, name):
    return model+'-'+name


def tasks():
    return [dict(identity=model, input_key='interval', native_kind='mixed',
                 payload=dict(model=model, budgets=list(BUDGETS), box_radius=RADIUS),
                 limits=dict(native_calls=VALUE_CALLS+int(model!=MODELS[0]),
                     packet_visits=VISITS*(VALUE_CALLS+int(model!=MODELS[0])),
                     bound_calls=0, bound_steps=0)) for model in MODELS]


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .esa_native_tangent_replay import ID as TANGENT, CASE
    from .esa_original_whitening import QUAL
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing frozen contrast study')
    checked(root, QUAL+'/request.json', sources=qualification_sources(root),
            environment=runtime_environment(), required_tests=REQUIRED_TESTS,
            minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, WEIGHTS)) as prior:
        if (prior.completion['manifest_sha256'] != WEIGHTS_SHA
                or prior.completion['state'] != 'complete'
                or not all(prior.rows[model]['passed'] for model in MODELS)
                or prior.input('environment') != require_guarded_environment(environment())):
            raise ValueError('the closed original whitening study and matching environment are required')
        materials = {name: prior.input(name, raw=True) for name in SHARED[:-1]}
        family = {}
        for model in MODELS:
            materials.update({key(model, name): prior.input(key(model, name), raw=True)
                              for name in PER_MODEL[:4]})
            for name, filename in [('weights', 'training-factors.npz'),
                                   ('weights-receipt', 'exact-earlier-cost.json')]:
                materials[key(model, name)] = prior.artifact(model, filename, raw=True)
            forecast = json.loads(materials[key(model, 'forecast')])
            if forecast['prediction_receiver_positions_used'] is not False:
                raise ValueError('only previously sealed earlier-only predictions are allowed')
            family[model] = forecast['coordinates'][-FORECAST:]
        materials['forecast-family'] = encoded(family)
    with closing(ClosedStudy(root, 'data/'+TANGENT)) as tangent:
        raw = tangent.artifact('fixed-forecast-tangent', 'full-tangent.json', raw=True)
        if (tangent.completion['state'] != 'complete'
                or tangent.input('parent')['case'] != CASE
                or json.loads(raw)['source_forecast_sha256'] != digest(materials[key(MODELS[0], 'forecast')])):
            raise ValueError('exact sealed specified-field tangent is required')
        materials['specified-tangent'] = raw
    inputs = {}
    for name, raw in materials.items():
        path = base/name
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, tasks=tasks(), inputs=inputs,
                      sources=source_closure(root, [ADAPTER, PLAN, *COMPANIONS]),
                      workers=3, threads=1, maximum_wall_s=240.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']))


def evaluate(declared, context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import frozen_workspace

    model = declared['identity']
    body = {name: value for name, value in declared.items() if name not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE
            or body != next((row for row in tasks() if row['identity'] == model), None)
            or json.loads(context.input_path('environment').read_bytes()) != environment()):
        raise ValueError('exact earlier-loss contrast task and environment required')
    inputs = {name: str(context.input_path(name).resolve()) for name in SHARED}
    inputs.update({name: str(context.input_path(key(model, name)).resolve())
                   for name in PER_MODEL})
    if model == MODELS[0]:
        inputs['specified-tangent'] = str(context.input_path('specified-tangent').resolve())
    else:
        context.charge(native_kind='tangent', native_calls=1, packet_visits=VISITS)
    with frozen_workspace(context, COMPANIONS) as work:
        with context.prepay_native(native_calls=VALUE_CALLS, packet_visits=VALUE_CALLS*VISITS,
                                   native_kind='value') as budget:
            for _ in range(VALUE_CALLS):
                budget.reserve(native_calls=1, packet_visits=VISITS)
            subprocess.run([sys.executable, str(Path(__file__).resolve()), '_frozen',
                            model, json.dumps(inputs), str(work)], cwd=work,
                           env={**os.environ, 'PYTHONPATH': str(work/'analysis')}, check=True)
        report = json.loads((work/'contrast-support.json').read_bytes())
        if report['model'] != model or len(report['comparisons']) != VALUE_CALLS-1:
            raise ValueError('all forecast contrast tests required')
        if model != MODELS[0]:
            context.save_bytes('full-tangent.json', (work/'full-tangent.json').read_bytes())
    context.save('contrast-support.json', report)
    return dict(passed=True, model=model, checks=len(report['comparisons']), new_fits=0,
                later_receiver_positions_read=0, protected_reads=0, scientific_decision='abstain')


def frozen_replay(model, inputs, work):
    import numpy as np
    from lll.calibration_loss_support import support
    from lll.esa_native_tangent_replay import frozen_replay as tangent_replay
    from lll.esa_original_whitening import score_change
    from lll.esa_tangent_remainder import scalar_replay
    from lll.ilvis0_precision_value import longitude_residual
    from lll.ilvis0_solver_position import physical_metric
    from lll.innovations_snapshot import restore
    from lll.studies.artifacts import digest, encoded

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    if model == MODELS[0]:
        tangent = read('specified-tangent')
    else:
        target = work/'full-tangent.json'
        tangent_replay(inputs, target, model=model)
        tangent = json.loads(target.read_bytes())
    fit, point, _, _, baseline, _, displacement = scalar_replay(
        inputs, work/'contrast-support.json', expected_model=model)
    saved = read('forecast')
    receipt = read('weights-receipt')
    cached = restore(Path(inputs['weights']).read_bytes(), expected_sha256=receipt['snapshot_sha256'],
                     expected_configuration=saved['error_training_configuration'], maximum_bytes=64*1024**2)
    jac = np.asarray(tangent['jacobian'])
    local = fit['local_linearization']
    earlier_jac = np.asarray(local['jacobian'])
    residual = np.asarray(local['residual'])
    if (tangent['source_forecast_sha256'] != digest(Path(inputs['forecast']).read_bytes())
            or tangent['active_parameters'] != fit['active_parameters']
            or not np.allclose(cached.whiten(jac[:3*TRAIN]), earlier_jac, rtol=1e-10, atol=1e-8)):
        raise ValueError('full tangent does not reproduce the original earlier derivatives')
    earlier = np.asarray(read('training_observations')['coordinates'])
    nominal = np.asarray(saved['training_coordinate_difference'])
    nominal[:, 1] = longitude_residual(nominal[:, 1])
    rounded = np.asarray(saved['coordinates'])[:TRAIN]-earlier
    rounded[:, 1] = longitude_residual(rounded[:, 1])
    nominal_offset = nominal-rounded
    if not np.array_equal(cached.whiten(nominal.ravel()), residual):
        raise ValueError('stored weights do not reproduce the archived earlier residual')

    family = {label: np.asarray(path) for label, path in read('forecast-family').items()}
    if not np.array_equal(family[model], np.asarray(saved['coordinates'])[-FORECAST:]):
        raise ValueError('model contrast path differs from exact saved forecast')
    metric = physical_metric(family[MODELS[0]]).ravel()
    future_jac = metric[:, None]*jac[3*TRAIN:]
    lower, upper = np.maximum(-RADIUS, -1-point), np.minimum(RADIUS, 1-point)
    comparisons = []
    for other in MODELS:
        if other == model:
            continue
        delta = family[other]-family[model]
        delta[:, 1] = longitude_residual(delta[:, 1])
        direction = delta.ravel()*metric
        distance = np.linalg.norm(direction)
        vector = direction/(distance*np.sqrt(FORECAST))
        for allowance in BUDGETS:
            result = support(earlier_jac, residual, vector@future_jac, lower, upper, budget=allowance)
            target = point+np.asarray(result['point'])
            if np.any(np.abs(target) > 1+4*np.finfo(float).eps):
                raise ValueError('affine witness leaves the declared calibration box')
            moved = displacement(np.clip(target, -1., 1.))
            change = cached.whiten((moved[:TRAIN]-nominal_offset).ravel())
            actual_loss = score_change(residual, change)
            projected = float(vector@((moved[TRAIN:]-baseline[TRAIN:]).ravel()*metric))
            comparisons.append(dict(other=other, earlier_allowance=allowance,
                nominal_separation_rms_m=float(distance/np.sqrt(FORECAST)),
                nonlinear_witness_toward_other_m=projected, nonlinear_witness_earlier_loss=actual_loss,
                witness_exactly_inside=actual_loss<=allowance, **result))
    (work/'contrast-support.json').write_bytes(encoded(dict(model=model, comparisons=comparisons,
                 linear_region_only=True, fit_starts=0, later_receiver_positions_read=0,
                 protected_reads=0, scientific_decision='abstain')))


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '_frozen':
        frozen_replay(sys.argv[2], json.loads(sys.argv[3]), Path(sys.argv[4]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('prepare',))
        parser.parse_args()
        print(json.dumps(prepare(Path.cwd()), sort_keys=True))
