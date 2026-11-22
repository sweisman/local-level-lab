# SPDX-License-Identifier: AGPL-3.0-or-later
"""Match finite ESA stress steps by their earlier affine cost increase."""

import argparse
from contextlib import closing
import gzip
import json
import math
from pathlib import Path
import sys


ID = 'esa-earlier-fit-cost-v1-20261118'
ADAPTER = 'analysis/lll/esa_earlier_fit_cost.py'
PLAN = 'docs/prediction-observed-development/ESA_EARLIER_FIT_COST_PLAN.md'
SCOPE = 'earlier-cost-matched three-model scalar forecast sensitivity'
MIXED = 'data/esa-mixed-calibration-v1-20261118'
MIXED_SHA = '17c12dc3c4852668ca5ef86011648c51d72d1d362ab1bafefd52ce637101af2a'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
BUDGETS = (.001, .01)
CALLS = 1+len(BUDGETS)
SHARED = ('interval', 'training', 'forecast_times', 'recipe', 'environment',
          'parent', 'frozen_python_native')
CANDIDATE = ('fit', 'forecast', 'training_observations', 'compiler', 'earlier_operator', 'ray')
HELPER = 'analysis/lll/esa_tangent_remainder.py'


def loss_limited_step(residual, jacobian, direction, *, limit, maximum=1.):
    """Find the farthest step on a feasible ray with bounded affine loss increase."""
    import numpy as np

    residual, jacobian, direction = (np.asarray(val, float) for val in
                                    (residual, jacobian, direction))
    if (jacobian.ndim != 2 or (len(residual), len(direction)) != jacobian.shape
            or residual.ndim != 1 or direction.ndim != 1
            or min(limit, maximum) <= 0 or not math.isfinite(limit+maximum)
            or any(not np.all(np.isfinite(val)) for val in (residual, jacobian, direction))):
        raise ValueError('finite aligned residual, Jacobian, ray and positive limits required')
    response = jacobian@direction
    slope = float(2*(residual@response))
    curvature = float(response@response)
    cap_loss = maximum*(slope+maximum*curvature)
    if cap_loss <= limit:
        return maximum, cap_loss, True
    radical = math.hypot(slope, 2*math.sqrt(curvature*limit))
    scale = (2*limit/(radical+slope) if slope >= 0 else
             (radical-slope)/(2*curvature))
    return scale, scale*(slope+scale*curvature), False


def loss_interval(loss, white_norm):
    """Triangle bounds when the original covariance includes this white floor."""
    if min(loss, white_norm) < 0 or not math.isfinite(loss+white_norm):
        raise ValueError('finite nonnegative squared loss and displacement norm required')
    nominal = math.sqrt(loss)
    return (max(0., nominal-white_norm)**2-loss,
            white_norm*(2*nominal+white_norm))


def key(model, name):
    return model+'-'+name


def tasks():
    from .esa_tangent_remainder import FORECAST, PACKETS, TRAIN
    return [dict(identity=model, input_key='interval', native_kind='value',
                 payload=dict(model=model, budgets=list(BUDGETS)),
                 limits=dict(native_calls=CALLS, packet_visits=CALLS*PACKETS*(TRAIN+FORECAST),
                             bound_calls=0, bound_steps=0)) for model in MODELS]


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .esa_native_tangent_replay import AUTHORITATIVE, PARENT_SHA
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the frozen earlier-cost study')
    with closing(ClosedStudy(root, MIXED)) as parent:
        if (parent.completion['manifest_sha256'] != MIXED_SHA
                or parent.completion['state'] != 'complete'
                or set(parent.tasks) != set(MODELS)
                or not all(row['passed'] for row in parent.rows.values())
                or parent.input('environment') != require_guarded_environment(environment())):
            raise ValueError('exact completed mixed study and environment required')
        materials = {name: parent.input(name, raw=True) for name in SHARED}
        for model in MODELS:
            for name in ('fit', 'forecast', 'training_observations', 'compiler'):
                materials[key(model, name)] = parent.input(key(model, name), raw=True)
            large = parent.artifact(model, 'mixed-changes.json')['comparisons'][1]
            ray, = [row['change'] for row in large['parameter_steps'] if row['axes'] == [0, 1, 2]]
            if large['radius'] != .10:
                raise ValueError('the original feasible joint ray is required')
            materials[key(model, 'ray')] = encoded(ray)
        with closing(ClosedStudy(root, AUTHORITATIVE, store=parent.store)) as original:
            if original.completion['manifest_sha256'] != PARENT_SHA:
                raise ValueError('exact original fit matrix required')
            for model in MODELS:
                identity = model+'-1-increment-0'
                if (digest(materials[key(model, 'forecast')]) !=
                        digest(original.artifact(identity, 'forecast.json', raw=True))):
                    raise ValueError('sealed model forecast differs')
                materials[key(model, 'earlier_operator')] = original.artifact(
                    identity, 'training-error-operator.json', raw=True)
    inputs = {}
    for name, raw in materials.items():
        path = base/name
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, tasks=tasks(),
                      inputs=inputs, sources=source_closure(root, [ADAPTER, PLAN]),
                      workers=1, threads=1, maximum_wall_s=120.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']))


def evaluate(declared, context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import invoke_frozen

    model = declared['identity']
    task = {name: val for name, val in declared.items() if name not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE
            or task != next((row for row in tasks() if row['identity'] == model), None)
            or json.loads(context.input_path('environment').read_bytes()) != environment()):
        raise ValueError('unchanged frozen task, candidate and environment required')
    names = (*SHARED, *(key(model, name) for name in CANDIDATE))
    raw = invoke_frozen(context, entry=Path(__file__), calls=CALLS,
                        inputs=names, companions=(HELPER,))
    result = json.loads(raw)
    if result['model'] != model or len(result['comparisons']) != len(BUDGETS):
        raise ValueError('complete earlier-cost check required for declared candidate')
    context.save_bytes('earlier-cost.json', raw)
    return dict(passed=True, new_fits=0, later_receiver_positions_read=0,
                protected_reads=0, scientific_decision='abstain')


def frozen_replay(inputs, output):
    import numpy as np
    from lll.airquantumgrav_error_policy import build
    from lll.esa_tangent_remainder import TRAIN, scalar_replay
    from lll.ilvis0_error_model import factor
    from lll.ilvis0_precision_value import longitude_residual
    from lll.studies.artifacts import digest, encoded

    model, = [candidate for candidate in MODELS if key(candidate, 'fit') in inputs]
    inputs.update({name: inputs[key(model, name)] for name in CANDIDATE})
    fit, point, metric, compiler, baseline, baseline_max, displacement = scalar_replay(
        inputs, output, expected_model=model)

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    older = read('earlier_operator')
    saved = read('forecast')
    earlier = np.array(read('training_observations')['coordinates'])
    rows = json.loads(gzip.decompress(Path(inputs['training']).read_bytes()))
    receiver = build(rows, policy_id='reported-short-v1')
    white = np.asarray(older['receiver_white'])
    if (older['model'] != model
            or saved['error_training_configuration'] != older['operator_configuration']
            or older['input_sha256']['receiver_transforms'] !=
               digest(receiver.transforms.astype('<f8').tobytes())
            or not np.array_equal(white, receiver.spec.white)):
        raise ValueError('exact frozen receiver white covariance required')
    white_factor = receiver.transforms@factor(white)
    # Recover the nominal offset at higher precision from its stored residual.
    # The scalar kernel subtracts saved (rounded) nominal coordinates.
    rounded_difference = np.asarray(saved['coordinates'])[:TRAIN]-earlier
    rounded_difference[:, 1] = longitude_residual(rounded_difference[:, 1])
    nominal_offset = np.asarray(saved['training_coordinate_difference'])-rounded_difference
    local = fit['local_linearization']
    residual = np.asarray(local['residual'])
    jacobian = np.asarray(local['jacobian'])
    loss = float(residual@residual)
    ray = np.asarray(read('ray'))
    if (not np.isclose(loss, fit['residual_sum_squares'], rtol=1e-12, atol=1e-12)
            or not np.isclose(np.linalg.norm(ray), .1, rtol=1e-10)
            or np.any(np.abs(point+ray)>1)):
        raise ValueError('exact archived model loss and feasible 0.10 ray required')
    comparisons = []
    for budget in BUDGETS:
        scale, achieved, capped = loss_limited_step(residual, jacobian, ray, limit=budget)
        changes = displacement(point+scale*ray)
        raw_delta = changes[:TRAIN]-nominal_offset
        delta_white_bound = float(np.linalg.norm(np.linalg.solve(white_factor, raw_delta[..., None])))
        low, high = loss_interval(loss, delta_white_bound)
        metres = (changes-baseline)*metric
        comparisons.append(dict(budget=budget, parameter_norm=float(np.linalg.norm(scale*ray)),
            affine_loss_increase=achieved, cap_limited=capped, white_bound=delta_white_bound,
            scalar_loss_increase_bracket=[low, high], scalar_guaranteed_inside=high<=budget,
            early_displacement_rms_m=float(np.sqrt(np.mean(np.sum(metres[:TRAIN]**2, axis=1)))),
            forecast_displacement_rms_m=float(np.sqrt(np.mean(np.sum(metres[TRAIN:]**2, axis=1))))))
    output.write_bytes(encoded(dict(model=model, original_earlier_loss=loss, comparisons=comparisons,
         baseline_scalar_max_m=baseline_max, compiler=compiler, fit_starts=0,
         later_receiver_positions_read=0, protected_reads=0, scientific_decision='abstain')))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '_frozen':
        frozen_replay(json.loads(sys.argv[2]), Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('prepare',))
        parser.parse_args()
        print(json.dumps(prepare(Path.cwd()), sort_keys=True))
