# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply the same physical force transform to earlier and later ESA scores."""

from contextlib import ExitStack, closing
from fractions import Fraction
import json
from pathlib import Path

from .esa_linked_training_support import INCREASE, MODELS, REMAINDERS


ID = 'esa-joint-force-support-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_JOINT_FORCE_SUPPORT_PLAN.md'
SCOPE = 'Coupled force map inside the sealed ESA 187 earlier-loss bound'
EARLIER_SHA = '3e5415b9f41dbcdc7f420e9857b8e7d6558132354a038fabdd0e8f354e60d3ab'
FORCE_SHA = '4c2ecb8b6b14179c37dcf6c6df27e6f9985c834db2a1903684f99dad83611cd9'
FORCE_START = 42
BOXES = 63


def tasks():
    return [dict(identity=model, input_key=model, payload=dict(model=model),
                 limits=dict(native_calls=0, packet_visits=0, bound_calls=len(REMAINDERS),
                             bound_steps=BOXES*len(REMAINDERS))) for model in MODELS]


def evaluate(task, context):
    import numpy as np
    from .esa_force_score import force_transform
    from .esa_linked_training_support import load_projection_inputs
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_force_score_bound import bound
    from .ilvis0_linked_training_support import split_support, support, training_upper
    from .ilvis0_saved_prediction_audit import endpoint
    from .state_space_directional_bound import adjoint_intervals
    from .studies.artifacts import digest

    model = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact coupled force-support task required')
    residual, raw_earlier, _, lower, upper, earlier, target, settings = load_projection_inputs(context, model)
    prior = json.loads(context.input_path(model+'-directions').read_bytes())
    transform = force_transform(json.loads(context.input_path(model+'-force').read_bytes()))
    ref = transform.reference
    ref_lower = [endpoint(Fraction(float(a))-Fraction(float(c)), False)
                 for a, c in zip(ref.lower, ref.center, strict=True)] + [-1.]*24
    ref_upper = [endpoint(Fraction(float(b))-Fraction(float(c)), True)
                 for b, c in zip(ref.upper, ref.center, strict=True)] + [1.]*24
    if (prior['input_sha256'] != digest(context.input_path().read_bytes())
            or prior['nominal_separation'] != settings['shape']['nominal']
            or not np.array_equal(lower, ref_lower) or not np.array_equal(upper, ref_upper)
            or [row['unshared_earlier_norm'] for row in prior['rows']] != list(REMAINDERS)):
        raise ValueError('the force map and preceding projection must share the original box and inputs')

    rows = []
    for row in prior['rows']:
        context.charge(bound_calls=1, bound_steps=BOXES)
        gamma, direction = row['unshared_earlier_norm'], row['direction']
        lo, hi = adjoint_intervals(earlier, direction)
        projected = coefficients(lo, hi, np.ones(len(residual)), raw_earlier)
        training = tuple(zip(projected['lower'], projected['upper'], strict=True))
        original = support(residual, direction, training, target, lower, upper,
                           increase=INCREASE, unshared=gamma)
        if any(row[key] != original[key] for key in ('exact_upper', 'multiplier', 'box_upper')):
            raise ValueError('sealed independent-box certificate did not replay')
        constraint = training_upper(residual, direction, increase=INCREASE, unshared=gamma)
        linear, force = split_support(training, target, lower, upper, multiplier=row['multiplier'],
                                      bound=constraint, shared_start=FORCE_START)
        left, right = zip(*force, strict=True)
        result = bound(transform, left, right, maximum_boxes=BOXES, maximum_seconds=40.)
        force_independent = sum(max(-a, b) for a, b in force)
        if linear+force_independent != Fraction(original['exact_upper']):
            raise ValueError('separating the force coefficients changed the independent box')
        coupled = min(Fraction(float(result['upper'])), force_independent)
        rows.append(dict(unshared_earlier_norm=gamma, original_upper=original['upper'],
                         coupled_upper=endpoint(linear+coupled, True),
                         nonforce_upper=endpoint(linear, True),
                         independent_force_upper=endpoint(force_independent, True),
                         force_bound=result, exact_coupled_upper=str(linear+coupled),
                         adjusted_force_lower=list(map(str, left)), adjusted_force_upper=list(map(str, right))))
    context.save('joint-supports.json', dict(rows=rows, nominal_separation=prior['nominal_separation']))
    return dict(passed=True, rows=[{key: row[key] for key in
                ('unshared_earlier_norm', 'original_upper', 'coupled_upper', 'nonforce_upper',
                 'independent_force_upper')} for row in rows],
                fit_starts=0, later_observations_used=0, unshared_remainder_qualified=False,
                observational_coverage_qualified=False, scientific_decision='abstain')


def prepare(root):
    from .esa_force_score import ID as FORCE
    from .esa_linked_training_support import ID as EARLIER
    from .studies.artifacts import atomic
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing joint force support freeze')
    staged = {}
    with ExitStack() as stack:
        earlier = stack.enter_context(closing(ClosedStudy(root, 'data/'+EARLIER)))
        force = stack.enter_context(closing(ClosedStudy(root, 'data/'+FORCE, store=earlier.store)))
        for study, expected in ((earlier, EARLIER_SHA), (force, FORCE_SHA)):
            if study.completion['manifest_sha256'] != expected or not study.summary['passed']:
                raise ValueError('exact completed parent studies required')
        staged['later-operator.npz'] = earlier.input('later-operator', raw=True)
        for model in MODELS:
            staged.update({
                model+'.npz': earlier.input(model, raw=True),
                model+'-settings.json': earlier.input(model+'-settings', raw=True),
                model+'-weights.npz': earlier.input(model+'-weights', raw=True),
                model+'-directions.json': earlier.artifact(model, 'supports.json', raw=True),
                model+'-force.json': force.input(model, raw=True),
            })
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name, payload in staged.items():
        path = base/name
        atomic(path, payload)
        inputs[path.stem] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, adapter=adapter,
        sources=source_closure(root, [adapter, PLAN]), inputs=inputs, tasks=tasks(), scope=SCOPE,
        workers=2, threads=1, maximum_wall_s=150.), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    prepare(Path.cwd())
