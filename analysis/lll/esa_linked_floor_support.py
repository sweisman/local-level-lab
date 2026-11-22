# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound the joint earlier-loss and score slacks on linked calibration boxes."""

from contextlib import closing
from fractions import Fraction as F
from functools import partial
import json
from pathlib import Path
import sys

from .esa_linked_child_certificates import RANGES, task_for
from .esa_linked_floor_witness import ID as WITNESS, RESULT as WITNESS_RESULT
from .esa_linked_scaled_proposals import collect_refinement
from .esa_linked_score_floor import ID as PARENT, RESULT as PRIOR
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-floor-support-v2'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER + 'ESA_LINKED_FLOOR_SUPPORT_PLAN.md'
CORRECTION = FOLDER + 'ESA_LINKED_FLOOR_SUPPORT_ACCOUNTING.md'
RESULT = FOLDER + 'esa-linked-floor-support-result.json'
SCOPE = 'Linked physical interval tests of two ESA score floors per surviving calibration range'
PRIOR_SHA = '35a27e8280cada9a1fc21ab1867c03782acd30a86b70be62e9d4aa0c0f14fd99'
WITNESS_SHA = 'cffe034bb049e21158e1dc59fe5cc1a1875b16594baa616fe9572ac01aa0f1c1'
frozen_task = partial(task_for, bound_calls=12, bound_steps=24)


def certificate_terms(score, training, loss_limit, floor, rows, limits, weights, floor_weight,
                      extra_lower, extra_upper):
    """Construct an upper bound expression for a sum of necessary nonnegative slacks."""
    lam = F(floor_weight)
    multipliers = list(map(F, weights))
    if lam < 0 or any(v < 0 for v in multipliers):
        raise ValueError('nonnegative certificate weights required')
    count = len(score) + len(extra_lower)
    shifts = [F(0)] * count
    offset = F(loss_limit) - lam*F(floor)
    for row, value, weight in zip(rows, limits, multipliers, strict=True):
        if len(row) != count:
            raise ValueError('every row must include all physical and auxiliary terms')
        if weight:
            offset += weight * F(value)
            for index, value in enumerate(row):
                shifts[index] += weight * F(value)
    coefficients = [(lam*lo - b - shift, lam*hi - a - shift)
                    for (lo, hi), (a, b), shift in zip(score, training, shifts[:len(score)], strict=True)]
    offset += sum(max(-shift*F(lo), -shift*F(hi))
                  for shift, lo, hi in zip(shifts[len(score):], extra_lower, extra_upper, strict=True))
    return coefficients, offset


def propose_weights(lower, upper, rows, limits, score, allowance, floor, training):
    import numpy as np

    from .esa_linked_score_floor import score_floor_row
    from .ilvis0_affine_support import linear_proposal

    new_row, new_limit = score_floor_row(score, allowance, floor)
    a = np.asarray([*rows, new_row])
    b = np.asarray([*limits, new_limit])
    width = (np.asarray(upper) - lower)/2
    center = np.asarray(lower) + width
    d = np.r_[[-float((lo+hi)/2) for lo, hi in training], np.zeros(len(width)-len(training))]
    a, b = a*width, b-a@center
    scales = np.maximum(1e-20, np.maximum(np.max(abs(a), axis=1), abs(b)))
    c = d*width
    goal_scale = max(1., float(np.max(np.abs(c))))
    extent = (width > 0).astype(float)
    approximation = linear_proposal(-extent, extent, a/scales[:, None], b/scales, c/goal_scale)
    if approximation is None:
        return [0.] * len(rows), 1., False
    dual = approximation[1] * goal_scale / scales
    return dual[:-1].tolist(), float(dual[-1]), True


def assess_box(context, model, box, weights, offset):
    from .esa_linked_split import choose_axis
    from .ilvis0_linked_directional import _linked_expression, directional_bound
    from .ilvis0_physical_partition import audit, split

    lower, upper = box['lower'], box['upper']
    # Reserve the derivative before evaluating the whole box; a successful
    # whole-box exclusion may leave that step unused.
    context.charge(bound_calls=1, bound_steps=3)
    value = offset + F(directional_bound(model, lower, upper, weights).hi)
    result = dict(whole_exact_upper=str(value), exact_upper=str(value), excluded=value < 0)
    if value < 0:
        return result
    expression = _linked_expression(model, lower, upper, [(a+b)/2 for a, b in weights])
    derivative = [(item.lo, item.hi) for item in expression.derivative]
    first, impacts = choose_axis(lower, upper, derivative)
    remainder = [axis for axis in range(27) if axis != first
                 and lower[axis] < float((F(lower[axis])+F(upper[axis]))/2) < upper[axis]]
    axes = (first, max(remainder, key=lambda i: (impacts[i], -i))) if remainder else (first,)
    partition = split(lower, upper, axes=axes)
    coverage = audit(partition, lower, upper, axes=axes)
    children = []
    for child in partition['children']:
        context.charge(bound_calls=1, bound_steps=2)
        children.append(offset+F(directional_bound(model, child['lower'], child['upper'], weights).hi))
    bound = min(value, max(children))
    return dict(result, exact_upper=str(bound), excluded=bound < 0,
                partition=partition, coverage=coverage, child_exact_uppers=list(map(str, children)))


def evaluate(task, context):
    import numpy as np

    from .esa_linked_joint_score import score_objective
    from .esa_linked_training_support import INCREASE, load_projection_inputs
    from .esa_shared_profile_score import support
    from .ilvis0_coupled_map import StaticMap, restore_static_reference
    from .ilvis0_linked_training_support import training_upper
    from .state_space_directional_bound import adjoint_intervals

    parent, model, index = (task['payload'][key] for key in ('parent', 'model', 'child'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != frozen_task(parent, model, index):
        raise ValueError('exact saved physical score-floor task required')
    identity = task['identity']
    frozen, region, witness = [json.loads(context.input_path(identity+suffix).read_bytes())
                               for suffix in ('-child', '-floors', '-witness')]
    saved = json.loads(context.input_path(model+'-support').read_bytes())
    box, previous = frozen['child'], frozen['prior']
    old = previous['upper']
    points = [F(row['score_lower']) for row in saved['points'] if all(a <= p <= b for a, p, b in
              zip(box['lower'], row['point'], box['upper'], strict=True))]
    if len(points) != previous['witnesses'] or witness['identity'] != identity or witness['model'] != model:
        raise ValueError('preserve exact linked witnesses and range identity')
    checked = next((row for row in witness['checks'] if row.get('linked')), None)
    trials = []
    if checked is not None:
        residual, raw, design, _, _, earlier, target, settings = load_projection_inputs(context, model)
        lower, upper = region['lower'], region['upper']
        cell = next(row for row in saved['ranges'] if row['identity'] == frozen['pair'])
        if len(lower) != 60 or len(upper) != 60 or len(region['rows']) != 12 or len(cell['static']) != 270:
            raise ValueError('all archived affine cuts and 60 ranges required')
        rows = [*cell['static'], *(row for row, _ in region['rows'])]
        limits = [*cell['limits'], *(limit for _, limit in region['rows'])]
        force, packet = saved['force'], saved['first_sample']
        reference = restore_static_reference(force['configuration'], packet['dv'], packet['dt'],
            lower=force['lower'], upper=force['upper'], center=force['center'], expected_report=saved['reference'])
        static = StaticMap(reference, expected_report=saved['reference'], numerical_allowance=saved['map_allowance'])
        physical = np.asarray(checked['physical_parameters'])
        common = reference.normalized_values_at(physical)
        vec = np.r_[physical-reference.parent.center, common]
        direction = residual + design @ vec
        direction /= max(1., float(np.linalg.norm(direction)))
        a, b = adjoint_intervals(earlier, direction)
        projection = support(a, b, np.ones(len(residual)), raw)
        training = tuple(zip(projection['lower'], projection['upper'], strict=True))
        loss = training_upper(residual, direction, increase=INCREASE, unshared=0)
        objective, allowance = score_objective(target+((F(0), F(0)),)*9, lower, upper)
        for floor in (settings['shape']['nominal']/2-.1, witness['score_floor']):
            context.charge(bound_calls=1, bound_steps=1)
            dual, lam, proposed = propose_weights(lower, upper, rows, limits, objective, allowance, floor, training)
            coefficients, offset = certificate_terms(target, training, loss, floor, rows, limits, dual,
                                                       lam, lower[51:], upper[51:])
            certificate = assess_box(context, static, box, coefficients, offset)
            if certificate['excluded'] and any(value >= F(floor) for value in points):
                raise ValueError('endpoint excludes an archived feasible witness')
            trials.append(dict(floor=floor, floor_weight=lam, weights=dual, proposed=proposed,
                               offset=str(offset), **certificate))
        context.save('linked-direction.json', dict(direction=direction.tolist(), residual_source=checked['inward_margin'],
                                                   training_limit=str(loss)))
    context.save('floor-support.json', dict(trials=trials, checked_direction=checked is not None))
    upper = min([old, *(row['floor'] for row in trials if row['excluded'])])
    result = dict(identity=identity, model=model, parent=parent, child=index, previous_upper=old,
        upper=upper, excluded=False, witnesses=len(points), floors_tested=len(trials),
        floors_excluded=sum(row['excluded'] for row in trials), passed=True, scientific_decision='abstain')
    context.save('child-certificate.json', result)
    return result


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing frozen linked floor-support study')
    prior_raw, witness_raw = [(root/file).read_bytes() for file in (PRIOR, WITNESS_RESULT)]
    if digest(prior_raw) != PRIOR_SHA or digest(witness_raw) != WITNESS_SHA:
        raise ValueError('the exact two predecessor reports are required')
    prior, witnesses = json.loads(prior_raw), json.loads(witness_raw)
    checked = {record['identity']: record for record in witnesses['ranges']}
    staged, tasks = {}, []
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent, closing(
            ClosedStudy(root, 'data/'+WITNESS, store=parent.store)) as witness:
        if (any(prior[key] != parent.completion[key] for key in ('manifest_sha256', 'summary_sha256'))
                or witnesses['manifest_sha256'] != witness.completion['manifest_sha256']
                or not parent.summary['passed'] or not witness.summary['passed']
                or set(checked) != set(parent.tasks) or set(checked) != set(witness.tasks)):
            raise ValueError('both exact closed predecessors and every surviving box required')
        for model in RANGES:
            for suffix in ('', '-weights', '-settings', '-support'):
                staged[model+suffix] = parent.input(model+suffix, raw=True)
        for key in ('cover', 'sensitivity', 'later-operator', 'earlier-linked-report', 'first-split'):
            staged[key] = parent.input(key, raw=True)
        for identity, task in parent.tasks.items():
            record = witness.artifact(identity, 'checked-witness.json')
            if record != checked[identity] or prior['dispositions'][identity]['excluded']:
                raise ValueError('preserve all prior witness outcomes and exclusions')
            child = parent.input(identity+'-child')
            child['prior']['upper'] = prior['dispositions'][identity]['upper']
            staged[identity+'-child'] = encoded(child)
            staged[identity+'-floors'] = parent.input(identity+'-floors', raw=True)
            staged[identity+'-witness'] = encoded(record)
            tasks.append(frozen_task(*(task['payload'][key] for key in ('parent', 'model', 'child'))))
    if len(tasks) != 11:
        raise ValueError('exactly eleven surviving boxes required')
    inputs = dict(plan=PLAN, accounting_correction=CORRECTION, prior=PRIOR, witness_report=WITNESS_RESULT)
    for name, raw in staged.items():
        path = base/name
        atomic(root/path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=tasks,
        sources=source_closure(root, [adapter, PLAN, CORRECTION, 'analysis/tests/test_esa_linked_floor_support.py']),
        workers=2, threads=1, maximum_wall_s=180.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        collect_refinement(Path.cwd(), ID, RESULT)
    else:
        raise SystemExit('usage: python -m lll.esa_linked_floor_support {prepare,report}')
