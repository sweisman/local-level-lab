# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay conditioned contrast steps under the exact archived training score."""

import argparse
from contextlib import closing
import json
from pathlib import Path
import sys


ID = 'esa-conditioned-witness-v1-20261118'
ADAPTER = 'analysis/lll/esa_conditioned_witness.py'
PLAN = 'docs/prediction-observed-development/ESA_CONDITIONED_WITNESS_PLAN.md'
SCOPE = 'finite nonlinear verification of calibration witnesses in conditioned ESA forecasts'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
TRAIN, FORECAST, PACKETS = 400, 120, 155868
FRACTIONS = (1., .98)
CHECKS = 4
CALLS = 1+CHECKS*len(FRACTIONS)
SHARED = ('interval', 'training', 'forecast_times', 'recipe', 'environment', 'parent',
          'frozen_python_native', 'family')
PER_MODEL = ('fit', 'forecast', 'training_observations', 'compiler', 'full-factors',
             'full-receipt', 'trials')
COMPANIONS = tuple('analysis/lll/'+name+'.py' for name in (
    'esa_tangent_remainder', 'esa_original_whitening',
    'innovations_snapshot', 'conditioned_calibration'))


def key(model, name):
    return model+'-'+name


def tasks():
    return [dict(identity=model, input_key='interval', native_kind='value', payload=dict(model=model),
                 limits=dict(native_calls=CALLS, packet_visits=CALLS*PACKETS*(TRAIN+FORECAST),
                             bound_calls=0, bound_steps=0)) for model in MODELS]


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .esa_conditioned_tangent import ID as CONDITIONED, SOURCE, SOURCE_SHA, REPORT, summarize
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the already frozen witness study')
    # Recompute the small saved-only summary to verify the exact witness selection.
    summarize(root)
    results = json.loads((root/REPORT).read_bytes())
    with closing(ClosedStudy(root, 'data/'+CONDITIONED)) as conditioned, closing(
            ClosedStudy(root, SOURCE, store=conditioned.store)) as source:
        if (source.completion['manifest_sha256'] != SOURCE_SHA
                or conditioned.completion['manifest_sha256'] != results['manifest_sha256']
                or conditioned.completion['state'] != 'complete'
                or conditioned.input('environment') != require_guarded_environment(environment())):
            raise ValueError('closed forecast condition law and saved selected steps required')
        materials = {name: conditioned.input(name, raw=True) for name in SHARED[:-1]}
        family = {}
        for model in MODELS:
            materials.update({key(model, name): source.input(key(model, name), raw=True)
                              for name in PER_MODEL[:4]})
            raw = conditioned.artifact(model, 'conditioned-tangent.json', raw=True)
            family[model] = json.loads(raw)['conditioned_mean']
            materials[key(model, 'full-receipt')] = raw
            materials[key(model, 'full-factors')] = conditioned.artifact(model, 'full-factors.npz', raw=True)
            tests = [dict(other=next(label for label in case['pair'] if label != model),
                          allowance=case['allowance'],
                          change=case['per_candidate'][model]['point'],
                          affine_m=case['per_candidate'][model]['achieved'])
                     for case in results['cases'] if model in case['pair']]
            if len(tests) != CHECKS:
                raise ValueError('complete deterministic witness matrix required')
            materials[key(model, 'trials')] = encoded(tests)
        materials['family'] = encoded(family)
    inputs = {}
    for name, payload in materials.items():
        path = base/name
        atomic(path, payload)
        inputs[name] = path.relative_to(root).as_posix()
    freeze = dict(id=ID, scope=SCOPE, adapter=ADAPTER, tasks=tasks(), inputs=inputs,
                  sources=source_closure(root, [ADAPTER, PLAN, *COMPANIONS]),
                  workers=1, threads=1, maximum_wall_s=120.)
    atomic(base/'definition.json', encoded(freeze))
    manifest = Definition.from_dict(freeze, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']))


def evaluate(declared, context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import invoke_frozen

    model = declared['identity']
    fields = {k: v for k, v in declared.items() if k not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE
            or fields != next((row for row in tasks() if row['identity'] == model), None)
            or json.loads(context.input_path('environment').read_bytes()) != environment()):
        raise ValueError('exact saved witness and scalar environment required')
    names = (*SHARED, *(key(model, name) for name in PER_MODEL))
    raw = invoke_frozen(context, entry=Path(__file__), calls=CALLS,
                        inputs=names, companions=COMPANIONS)
    result = json.loads(raw)
    if result['model'] != model or len(result['comparisons']) != CHECKS*len(FRACTIONS):
        raise ValueError('each declared exact scalar replay must be present')
    context.save_bytes('conditioned-witnesses.json', raw)
    return dict(passed=True, model=model, fit_starts=0, later_receiver_positions_read=0,
                protected_reads=0, scientific_decision='abstain')


def frozen_replay(inputs, output):
    import numpy as np
    from lll.conditioned_calibration import conditioned_tangent
    from lll.esa_original_whitening import score_change
    from lll.esa_tangent_remainder import scalar_replay
    from lll.ilvis0_precision_value import longitude_residual
    from lll.ilvis0_solver_position import physical_metric
    from lll.innovations_snapshot import restore
    from lll.studies.artifacts import encoded

    model, = [label for label in MODELS if key(label, 'fit') in inputs]
    inputs.update({name: inputs[key(model, name)] for name in PER_MODEL})

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    fit, point, _, _, baseline, _, displacement = scalar_replay(inputs, output, expected_model=model)
    family = {label: np.asarray(path) for label, path in read('family').items()}
    receipt, forecast, earlier = (read(name) for name in ('full-receipt','forecast','training_observations'))
    operator = restore(Path(inputs['full-factors']).read_bytes(), expected_sha256=receipt['snapshot_sha256'],
                       expected_configuration=receipt['operator_configuration'], maximum_bytes=64*1024**2)
    prefix = operator.prefix(TRAIN)
    nominal = np.asarray(forecast['training_coordinate_difference'])
    nominal[:, 1] = longitude_residual(nominal[:, 1])
    raw_nominal = np.asarray(forecast['coordinates'])
    rounded = raw_nominal[:TRAIN]-np.asarray(earlier['coordinates'])
    rounded[:, 1] = longitude_residual(rounded[:, 1])
    nominal_offset = nominal-rounded
    residual = np.asarray(fit['local_linearization']['residual'])
    if (prefix.configuration != receipt['prefix_configuration']
            or not np.array_equal(prefix.whiten(nominal.ravel()), residual)
            or not np.allclose(family[model], receipt['conditioned_mean'], rtol=0., atol=0.)):
        raise ValueError('exact earlier residual and conditioned forecast required')
    metric = physical_metric(family[MODELS[0]]).ravel()
    comparisons = []
    for trial in read('trials'):
        delta = family[trial['other']]-family[model]
        delta[:, 1] = longitude_residual(delta[:, 1])
        trend = delta.ravel()*metric
        axis = trend/(np.linalg.norm(trend)*np.sqrt(FORECAST))
        shift = np.asarray(trial['change'])
        for fraction in FRACTIONS:
            target = point+fraction*shift
            if np.any(np.abs(target)>1+4*np.finfo(float).eps):
                raise ValueError('replay target leaves the original calibration box')
            moved = displacement(np.clip(target, -1., 1.))
            true_loss = score_change(residual, prefix.whiten((moved[:TRAIN]-nominal_offset).ravel()))
            change = (moved-baseline).ravel()
            adjusted = conditioned_tangent(operator, change, np.empty((change.size, 0)),
                                           change[:3*TRAIN], training_epochs=TRAIN)['mean']
            projected = float(axis@(adjusted*metric))
            comparisons.append(dict(other=trial['other'], allowance=trial['allowance'], fraction=fraction,
                affine_m=fraction*trial['affine_m'], exact_m=projected,
                exact_loss_increase=true_loss, inside=true_loss<=trial['allowance']))
    output.write_bytes(encoded(dict(model=model, comparisons=comparisons, fit_starts=0,
        later_receiver_positions_read=0, protected_reads=0, scientific_decision='abstain')))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '_frozen':
        frozen_replay(json.loads(sys.argv[2]), Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('prepare',))
        parser.parse_args()
        print(json.dumps(prepare(Path.cwd()), sort_keys=True))
