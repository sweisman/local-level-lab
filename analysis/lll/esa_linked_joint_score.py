# SPDX-License-Identifier: AGPL-3.0-or-later
"""Certify signed scores on the full static and earlier-loss outer region."""

from contextlib import closing
from fractions import Fraction as F
from functools import partial
import json
from pathlib import Path
import sys

from .esa_linked_coordinates import ID as PARENT, RESULT as PRIOR
from .esa_linked_coordinates import INCREASE, RANGES, _training_row, relaxed_row, task_for
from .esa_linked_child_certificates import read_dispositions
from .esa_linked_scaled_proposals import collect_refinement
from .ilvis0_saved_prediction_audit import endpoint
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-joint-score-v1'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_JOINT_SCORE_PLAN.md'
RESULT = 'docs/prediction-observed-development/esa-linked-joint-score-result.json'
SCOPE = 'direct outward score bound on all eleven contracted ESA calibration children'
PRIOR_SHA = 'e5b9add37ced3618af8c2771bbfc1ff626497ea51e4fd09099b5f59c2d1209f9'
PROPOSALS = 8
frozen_task = partial(task_for, bound_calls=2*PROPOSALS-1, bound_steps=4*PROPOSALS-1)


def score_objective(intervals, lower, upper):
    """Return a binary objective and an outward upper allowance over the box."""
    row, allowance = relaxed_row([(-b, -a) for a, b in intervals], 0, lower, upper)
    return [-value for value in row], allowance


def checked_score(lo, hi, rows, bounds, objective, weights, allowance):
    from .ilvis0_affine_support import upper
    from .ilvis0_saved_prediction_audit import support

    checked = upper(lo, hi, rows, bounds, objective, weights)['exact_upper']
    independent = support(lo, hi, rows, bounds, objective, list(map(float, weights)))
    if checked != independent:
        raise ValueError('independent joint support bounds disagree')
    return checked+F(allowance)


def _joint_bounds(context, lo, hi, rows, limits, target, residual, raw, design, earlier):
    import numpy as np

    from .ilvis0_affine_support import linear_proposal
    from .ilvis0_exact_scale import sqrt_upper

    objective, allowance = score_objective(target+((F(0), F(0)),)*9, lo, hi)
    radius = sqrt_upper(sum(F(float(value))**2 for value in residual)+F(INCREASE))
    trials, added_rows = [], []
    for index in range(PROPOSALS):
        context.charge(bound_calls=1, bound_steps=3)
        proposal = linear_proposal(lo, hi, rows, limits, objective)
        if proposal is None:
            trials.append(dict(status='proposal_unavailable'))
            break
        point, weights = proposal
        verified = checked_score(lo, hi, rows, limits, objective, weights, allowance)
        direction = residual+design@np.clip(point, lo, hi)[:51]
        norm = float(np.linalg.norm(direction))
        trials.append(dict(status='certificate_checked', exact_upper=str(verified),
                           multipliers=weights.tolist(), outer_point_loss_norm=norm))
        if norm <= radius or index == PROPOSALS-1:
            break
        context.charge(bound_calls=1, bound_steps=1)
        row, bound = _training_row(direction, earlier, residual, raw, lo, hi)
        rows.append(row)
        limits.append(bound)
        added_rows.append(dict(row=row, limit=bound, direction=direction.tolist()))
    return trials, added_rows, objective, allowance


def evaluate(task, context):
    from .esa_linked_training_support import load_projection_inputs

    parent, model, index = (task['payload'][key] for key in ('parent', 'model', 'child'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != frozen_task(parent, model, index):
        raise ValueError('exact declared joint score task required')
    identity = task['identity']
    frozen = json.loads(context.input_path(identity+'-child').read_bytes())
    contracted = json.loads(context.input_path(identity+'-projection').read_bytes())
    saved = json.loads(context.input_path(model+'-support').read_bytes())
    child, prior = frozen['child'], frozen['prior']
    cell = next(row for row in saved['ranges'] if row['identity'] == frozen['pair'])
    residual, raw, design, _, _, earlier, target, settings = load_projection_inputs(context, model)
    lower, upper = contracted['lower'], contracted['upper']
    if (child['index'] != index or prior['index'] != index or prior['excluded']
            or settings['shape']['nominal'] != frozen['nominal'] or len(cell['static']) != 270
            or len(contracted['training_rows']) != 5
            or any(not a <= lo <= hi <= b for a, lo, hi, b in zip(child['lower'], lower, upper, child['upper'], strict=True))):
        raise ValueError('unchanged contracted child and all archived inequalities required')
    center = tuple(map(F, saved['force']['center']))
    lo = [endpoint(F(x)-c, False) for x, c in zip(lower, center, strict=True)]+contracted['displacement_lower'][27:]
    hi = [endpoint(F(x)-c, True) for x, c in zip(upper, center, strict=True)]+contracted['displacement_upper'][27:]
    rows = list(cell['static'])+[row for row, _ in contracted['training_rows']]
    limits = list(cell['limits'])+[bound for _, bound in contracted['training_rows']]
    if len(lo) != 60 or len(hi) != 60 or any(len(row) != 60 for row in rows):
        raise ValueError('all sixty physical and lifted columns are required')
    trials, added, objective, allowance = _joint_bounds(context, lo, hi, rows, limits, target,
                                                       residual, raw, design, earlier)
    checked = [F(proposal['exact_upper']) for proposal in trials if proposal['status'] == 'certificate_checked']
    value = min([F(prior['upper']), *checked])
    witnesses = [row for row in saved['points'] if all(a <= x <= b for a, x, b in
                 zip(child['lower'], row['point'], child['upper'], strict=True))]
    if len(witnesses) != prior['witnesses'] or any(value < F(row['score_lower']) for row in witnesses):
        raise ValueError('joint bound contradicts an archived feasible point')
    context.save('joint-certificate.json', dict(trials=trials, added=added, objective=objective,
        coefficient_allowance=allowance, lower=lo, upper=hi, projection_sha256=contracted['source_sha256']))
    result = dict(identity=identity, parent=parent, model=model, child=index, excluded=False,
        previous_upper=prior['upper'], upper=endpoint(value, True), witnesses=len(witnesses),
        proposals=len(trials), certificates=len(checked), additional_training_rows=len(added),
        unavailable_proposals=len(trials)-len(checked), passed=True, scientific_decision='abstain')
    context.save('child-certificate.json', result)
    return result


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('reuse the frozen joint score study')
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('original coordinate result required')
    prior = json.loads(raw)
    staged, tasks = {}, []
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (any(prior[key] != parent.completion[key] for key in ('manifest_sha256', 'summary_sha256'))
                or not parent.summary['passed']):
            raise ValueError('saved coordinate report must match the closed study')
        records, dispositions = read_dispositions(parent)
        if records != prior['rows'] or any(prior['dispositions'][key] != row for key, row in dispositions.items()):
            raise ValueError('all prior bounds and exclusions must reproduce')
        for model in RANGES:
            for suffix in ('', '-weights', '-settings', '-support'):
                staged[model+suffix] = parent.input(model+suffix, raw=True)
        for name in ('cover', 'sensitivity', 'later-operator', 'earlier-linked-report', 'first-split'):
            staged[name] = parent.input(name, raw=True)
        for identity, task in parent.tasks.items():
            row = dispositions[identity]
            if row['excluded']:
                raise ValueError('do not revisit a previously excluded child')
            child = parent.input(identity+'-child')
            child['prior']['upper'] = row['upper']
            raw_projection = parent.artifact(identity, 'coordinate-projection.json', raw=True)
            projection = json.loads(raw_projection)
            if projection['changed_coordinates'] != records[identity]['changed_coordinates']:
                raise ValueError('linked coordinate and score records differ')
            fields = ('lower', 'upper', 'displacement_lower', 'displacement_upper', 'training_rows')
            staged[identity+'-projection'] = encoded(dict(source_sha256=digest(raw_projection),
                **{key: projection[key] for key in fields}))
            staged[identity+'-child'] = encoded(child)
            tasks.append(frozen_task(*(task['payload'][key] for key in ('parent', 'model', 'child'))))
    if len(tasks) != 11:
        raise ValueError('all eleven surviving child ranges required')
    base.mkdir(parents=True)
    inputs = {'plan': PLAN, 'prior': PRIOR}
    for name, content in staged.items():
        path = base/name
        atomic(path, content)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=tasks,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_linked_joint_score.py']),
        workers=2, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


if __name__ == '__main__':
    root = Path.cwd()
    if sys.argv[1] == 'prepare':
        print(json.dumps(prepare(root), sort_keys=True))
    elif sys.argv[1] == 'report':
        collect_refinement(root, ID, RESULT)
    else:
        raise ValueError('unknown joint-score command')
