# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply a complete static calibration map inside the saved ESA loss bound."""

from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_linked_training_support import INCREASE, MODELS


ID = 'esa-coupled-training-score-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_COUPLED_TRAINING_SCORE_PLAN.md'
SCOPE = 'Complete static calibration constraints on the saved ESA 187 shape score'
WITNESS_SHA = 'b292eb0ce7558fc74689a86669e771640112207fba36819e07f55e739615b10c'
GAMMAS = (0., .1)
PROPOSALS = 16
STATIC_STEPS = 15


def tasks():
    return [dict(identity=model, input_key=model, payload=dict(model=model),
                 limits=dict(native_calls=0, packet_visits=0, bound_calls=1+len(GAMMAS),
                             bound_steps=STATIC_STEPS+len(GAMMAS)*(PROPOSALS+1))) for model in MODELS]


def evaluate(task, context):
    import numpy as np
    from .esa_linked_training_support import load_projection_inputs
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_calibration_consistency import build as consistency_cuts
    from .ilvis0_coupled_map import StaticMap, restore_static_reference
    from .ilvis0_coupled_prediction import audit_cuts, build
    from .ilvis0_coupled_training_score import certify, propose, translate_rows
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_orientation_gain import build as orientation_cuts
    from .ilvis0_saved_prediction_audit import endpoint
    from .state_space_directional_bound import adjoint_intervals

    model = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact complete calibration task required')
    raw = json.loads(context.input_path(model+'-force').read_bytes())
    sample = json.loads(context.input_path(model+'-first-sample').read_bytes())
    saved = json.loads(context.input_path(model+'-reference').read_bytes())
    witnesses = json.loads(context.input_path(model+'-witnesses').read_bytes())
    residual, raw_design, design, lower, upper, earlier, target, settings = load_projection_inputs(context, model)
    context.charge(bound_calls=1, bound_steps=STATIC_STEPS)
    reference = restore_static_reference(raw['configuration'], sample['dv'], sample['dt'],
        lower=raw['lower'], upper=raw['upper'], center=raw['center'], expected_report=saved)
    mapping = StaticMap(reference, expected_report=saved, numerical_allowance=3e-10)
    cuts = build(mapping, raw['lower'], raw['upper'], reserve=lambda: None)
    audit_cuts(cuts, mapping.report(), raw['lower'], raw['upper'])
    consistency = consistency_cuts(reference.acceleration, reference.transform)
    orientation = orientation_cuts(reference.acceleration, reference.transform)
    static = cuts['design']+consistency.design.tolist()+orientation.design.tolist()
    static_upper = cuts['upper']+consistency.upper.tolist()+orientation.upper.tolist()
    center = raw['center']+[0.]*24
    limits = translate_rows(static, static_upper, center)
    witness_floor = 0.
    linked = [row for row in witnesses['rows'] if row['variant']=='linked_shared']
    if len(linked)!=10:
        raise ValueError('all sealed linked calibration checks required')
    for witness in linked:
        point = tuple(map(F, witness['physical_point']+witness['shared']))
        if any(sum(F(a)*b for a,b in zip(row, point, strict=True) if a)>F(limit)
               for row,limit in zip(static, static_upper, strict=True)):
            raise ValueError('the structural inequalities exclude a saved linked point')
        if witness['loss_passed']:
            witness_floor = max(witness_floor, witness['score_lower'])
    context.save('static-cuts.json', dict(coupling=cuts, consistency=consistency.report(),
        orientation=orientation.report(), translated_upper=limits, linked_witnesses_checked=len(linked)))

    objective = np.array([float((a+b)/2) for a,b in target])
    rows = []
    for gamma in GAMMAS:
        context.charge(bound_calls=1, bound_steps=PROPOSALS+1)
        radius = sqrt_upper(sum(F(float(v))**2 for v in residual)+F(INCREASE))+gamma
        proposal = propose(design, residual, lower, upper, objective, static, limits,
                           radius=radius, iterations=PROPOSALS, seed=residual)
        direction = proposal['direction']
        lo, hi = adjoint_intervals(earlier, direction)
        projected = coefficients(lo, hi, np.ones(len(residual)), raw_design)
        training = tuple(zip(projected['lower'], projected['upper'], strict=True))
        exact = certify(residual, direction, training, target, lower, upper, static, limits,
                        proposal['weights'], increase=INCREASE, unshared=gamma)
        value = endpoint(exact, True)
        if value < witness_floor:
            raise ValueError('upper bound contradicts an earlier feasible point')
        rows.append(dict(earlier_unshared=gamma, upper=value, exact_upper=str(exact),
            lp_proposals=proposal['iterations'], direction=direction.tolist(),
            weights=proposal['weights'].tolist(), feasible_linked_score_floor=witness_floor))
    context.save('composed-support.json', dict(rows=rows, nominal_separation=settings['shape']['nominal']))
    return dict(passed=True, rows=[{k: v for k, v in row.items() if k not in ('direction', 'weights')}
                for row in rows], static_rows=len(static), fit_starts=0, later_observations_used=0,
                map_allowance_qualified=False, unshared_error_qualified=False, scientific_decision='abstain')


def prepare(root):
    from .esa_calibration_witness import ID as WITNESS
    from .esa_shared_profile import PRECHECK, PRECHECK_SHA
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing composed calibration freeze')
    staged = {}
    with ExitStack() as stack:
        witness = stack.enter_context(closing(ClosedStudy(root, 'data/'+WITNESS)))
        prefix = stack.enter_context(closing(ClosedStudy(root, PRECHECK, store=witness.store)))
        for study, expected in ((witness, WITNESS_SHA), (prefix, PRECHECK_SHA)):
            if study.completion['manifest_sha256'] != expected or not study.summary['passed']:
                raise ValueError('exact completed parent studies required')
        staged['later-operator.npz'] = witness.input('later-operator', raw=True)
        for model in MODELS:
            for suffix, extension in (('', '.npz'), ('-weights', '.npz'), ('-settings', '.json'),
                                      ('-force', '.json'), ('-first-sample', '.json')):
                staged[model+suffix+extension] = witness.input(model+suffix, raw=True)
            staged[model+'-witnesses.json'] = witness.artifact(model, 'witnesses.json', raw=True)
            staged[model+'-reference.json'] = encoded(prefix.artifact(model, 'reference.json'))
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name, payload in staged.items():
        path = base/name
        atomic(path, payload)
        inputs[path.stem] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, adapter=adapter,
        sources=source_closure(root, [adapter, PLAN]), inputs=inputs, tasks=tasks(), scope=SCOPE,
        workers=2, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    prepare(Path.cwd())
