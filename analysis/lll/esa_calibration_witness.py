# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure attainable scores on the saved ESA calibration design."""

from contextlib import ExitStack, closing
from fractions import Fraction
from io import BytesIO
import json
from pathlib import Path

from .esa_linked_training_support import INCREASE, MODELS


ID = 'esa-calibration-witness-v2-20261119'
PLAN = 'docs/prediction-observed-development/ESA_CALIBRATION_WITNESS_PLAN.md'
SCOPE = 'Verified feasible points on the saved ESA 187 calibration design'
PARENT_SHA = 'a9ee4ce5ceeff698971d36b36676b3000df51fe08d40e4d2dd38c1bfed94d084'
FRACTIONS = (1., .8, .5, .25, .125)
CHECKS_PER_PROPOSAL = 1+len(FRACTIONS)
CHECKS = 2*CHECKS_PER_PROPOSAL


def tasks():
    return [dict(identity=model, input_key=model, payload=dict(model=model),
                 limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=CHECKS))
            for model in MODELS]


def check_point(earlier, raw_design, residual, target, point, *, unshared=0.):
    """Bound an achieved loss and score directly from the saved factor inputs."""
    from math import inf, nextafter
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_saved_prediction_audit import endpoint
    from .state_space_directional_bound import whiten_intervals

    weights = tuple(map(Fraction, point))
    coordinates = (
        sum(Fraction(float(a))*b for a, b in zip(row, weights, strict=True) if a and b)
        for row in raw_design
    )
    loss_low = loss_high = Fraction(0)
    for residual_value, (left, right) in zip(residual, whiten_intervals(earlier, coordinates), strict=True):
        reference = Fraction(float(residual_value))
        low, high = reference+Fraction(left), reference+Fraction(right)
        a, b = sorted((low*low, high*high))
        loss_low += (0 if low <= 0 <= high else a) - reference*reference
        loss_high += b - reference*reference
    score_low = score_high = Fraction(0)
    for (a, b), value in zip(target, weights, strict=True):
        score_low += value*(a if value >= 0 else b)
        score_high += value*(b if value >= 0 else a)
    allowance = Fraction(INCREASE)
    if unshared:
        gamma = Fraction(unshared)
        if gamma < 0:
            raise ValueError('nonnegative unshared error norm required')
        norm_squared = sum(Fraction(float(value))**2 for value in residual)+allowance
        norm_upper = sqrt_upper(norm_squared)
        norm_lower = (norm_upper if Fraction(norm_upper)**2 == norm_squared
                      else nextafter(norm_upper, -inf))
        allowance += 2*gamma*Fraction(norm_lower)+gamma*gamma
    return dict(loss_lower=endpoint(loss_low, False), loss_upper=endpoint(loss_high, True),
                score_lower=endpoint(score_low, False), score_upper=endpoint(score_high, True),
                loss_passed=loss_high<=allowance)


def evaluate(task, context):
    import numpy as np
    from .esa_force_score import force_transform
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_linked_training_support import propose_point
    from .ilvis0_reference_acceleration import AccelerationTerms

    model = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact saved calibration-witness task required')
    residual, raw, design, lower, upper, earlier, target, settings = load_projection_inputs(context, model)
    force_record = json.loads(context.input_path(model+'-force').read_bytes())
    sample = json.loads(context.input_path(model+'-first-sample').read_bytes())
    transform = force_transform(force_record)
    reference = transform.reference
    acceleration = AccelerationTerms(reference, sample['dv'], sample['dt'],
                                     force_record['configuration']['gravity'], outward_initial_force=True)
    if acceleration.report() != sample['acceleration']:
        raise ValueError('original shared acceleration convention required')

    radius = sqrt_upper(sum(Fraction(float(v))**2 for v in residual) + Fraction(.008))
    goal = np.array([float((lo+hi)/2) for lo, hi in target])
    rows = []
    for label, n in (('independent_shared', 51), ('physical_columns', 27)):
        context.charge(bound_calls=1, bound_steps=CHECKS_PER_PROPOSAL)
        point, success = propose_point(design[:, :n], residual, goal[:n], lower[:n], upper[:n], radius)
        for weight in FRACTIONS:
            candidate = np.clip(reference.center + .999*weight*point[:27], reference.lower, reference.upper)
            step = [Fraction(float(value))-Fraction(float(center))
                    for value, center in zip(candidate, reference.center, strict=True)]
            shared = np.r_[reference.normalized_values_at(candidate), acceleration.normalized_values_at(candidate),
                           transform.normalized_values_at(candidate)]
            alternatives = [('linked_shared', shared)]
            if weight == 1.:
                alternatives.append((label, .999*point[27:] if n==51 else np.zeros(24)))
            for variant, coefficients in alternatives:
                box = np.all(np.isfinite(coefficients)) and np.all(np.abs(coefficients)<=1.)
                if not box:
                    raise ValueError('saved witness leaves the complete shared coefficient box')
                vector = [*step, *map(float, coefficients)]
                verified = check_point(earlier, raw, residual, target, vector)
                rows.append(dict(source=label, variant=variant, fraction=weight,
                                 proposal_success=success, physical_point=candidate.tolist(),
                                 shared=coefficients.tolist(), **verified))
    if len(rows) != CHECKS:
        raise ValueError('all frozen calibration witnesses must be recorded')
    context.save('witnesses.json', dict(rows=rows, nominal_separation=settings['shape']['nominal']))
    return dict(passed=True, loss_passes=sum(row['loss_passed'] for row in rows),
                cases=len(rows), fit_starts=0, later_observations_used=0,
                nonlinear_propagation_checked=False, scientific_decision='abstain')


def prepare(root):
    import numpy as np
    from .esa_joint_force_support import ID as PARENT
    from .esa_shared_profile import PRECHECK, PRECHECK_SHA
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing calibration witness run')
    staged = {}
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, 'data/'+PARENT)))
        prefix = stack.enter_context(closing(ClosedStudy(root, PRECHECK, store=parent.store)))
        for study, expected in ((parent, PARENT_SHA), (prefix, PRECHECK_SHA)):
            if study.completion['manifest_sha256'] != expected or not study.summary['passed']:
                raise ValueError('exact completed parent studies required')
        staged['later-operator.npz'] = parent.input('later-operator', raw=True)
        for model in MODELS:
            for suffix, extension in (('', '.npz'), ('-weights', '.npz'), ('-settings', '.json'), ('-force', '.json')):
                staged[model+suffix+extension] = parent.input(model+suffix, raw=True)
            source = prefix.artifact(model, 'reference.json')
            with np.load(BytesIO(prefix.input(model, raw=True)), allow_pickle=False) as packets:
                staged[model+'-first-sample.json'] = encoded(dict(
                    dv=packets['dv'][0].tolist(), dt=float(packets['dt'][0]),
                    acceleration=source['acceleration']))
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
