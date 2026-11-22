# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exclude scores only if the full earlier loss is provably incompatible."""

from contextlib import closing
from fractions import Fraction as F
from functools import partial
import json
from pathlib import Path
import sys

from .esa_linked_child_certificates import RANGES, read_dispositions, task_for
from .esa_linked_coordinates import _training_row
from .esa_linked_joint_score import ID as PARENT, RESULT as PRIOR
from .esa_linked_joint_score import checked_score, score_objective
from .esa_linked_scaled_proposals import collect_refinement, scaled_problem
from .ilvis0_saved_prediction_audit import endpoint
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-score-floor-v1'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_SCORE_FLOOR_PLAN.md'
RESULT = 'docs/prediction-observed-development/esa-linked-score-floor-result.json'
SCOPE = 'full earlier loss infeasibility checks at four score floors per ESA calibration child'
PRIOR_SHA = '2fa40ad7c7a4a18e05caecff9b78b8ad65d217f26f329e479475898174d8959f'
FLOORS = 4
ITERATIONS = 120
frozen_task = partial(task_for, bound_calls=2*FLOORS, bound_steps=FLOORS*(ITERATIONS+7))


def score_floor_row(objective, allowance, floor):
    """A necessary affine row for all exact scores at least the given floor."""
    return [-value for value in objective], endpoint(F(allowance)-F(floor), True)


def floor_certificate(lo, hi, rows, limits, training, training_limit, weights):
    """A negative result excludes the floor using the separate training row."""
    return F(training_limit)+checked_score(lo, hi, rows, limits, [-v for v in training], weights, 0.)


def _floor_trial(context, floor, lower, upper, rows, limits, objective, allowance,
                 residual, raw, design, earlier):
    import numpy as np

    from .ilvis0_training_feasibility import loss_proposal, static_proposal

    row, limit = score_floor_row(objective, allowance, floor)
    matrix = [*rows, row]
    bounds = [*limits, limit]
    zero = np.zeros(len(lower))
    scaled_design, scaled_residual, lo, hi, scaled_rows, scaled_bounds, _, _ = scaled_problem(
        design, residual, lower, upper, matrix, bounds, zero, zero)
    context.charge(bound_calls=1, bound_steps=3)
    start, weights, slack = static_proposal(lo, hi, scaled_rows, scaled_bounds)
    value = checked_score(lower, upper, matrix, bounds, zero.tolist(), weights, 0.)
    record = dict(floor=floor, floor_row=row, floor_limit=limit,
                  static=dict(exact_upper=str(value), weights=weights.tolist(), proposed_slack=slack))
    if value < 0:
        return dict(record, excluded=True, certificate='affine')

    context.charge(bound_calls=1, bound_steps=ITERATIONS+4)
    proposal = loss_proposal(scaled_design, scaled_residual, lo, hi, scaled_rows, scaled_bounds,
                             start, iterations=ITERATIONS)
    training, training_limit = _training_row(proposal['direction'], earlier, residual, raw, lower, upper)
    value = floor_certificate(lower, upper, matrix, bounds, training, training_limit, proposal['weights'])
    loss = dict(exact_upper=str(value), training_row=training, training_limit=training_limit,
                direction=proposal['direction'].tolist(), weights=proposal['weights'].tolist(),
                proposed_norm=proposal['proposed_norm'], solver_reported_success=proposal['success'],
                iterations=proposal['iterations'], tangent_proposed=proposal['tangent_proposed'])
    return dict(record, loss=loss, excluded=value < 0,
                certificate='earlier_loss' if value < 0 else None)


def evaluate(task, context):
    import numpy as np

    from .esa_linked_training_support import load_projection_inputs

    parent, model, index = (task['payload'][key] for key in ('parent', 'model', 'child'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != frozen_task(parent, model, index):
        raise ValueError('exact declared floor-check task required')
    identity = task['identity']
    frozen = json.loads(context.input_path(identity+'-child').read_bytes())
    region = json.loads(context.input_path(identity+'-floors').read_bytes())
    saved = json.loads(context.input_path(model+'-support').read_bytes())
    prior, child = frozen['prior'], frozen['child']
    static = next(row for row in saved['ranges'] if row['identity'] == frozen['pair'])
    residual, raw, design, _, _, earlier, target, settings = load_projection_inputs(context, model)
    lower, upper = region['lower'], region['upper']
    if (prior['excluded'] or prior['index'] != index or child['index'] != index
            or len(lower) != 60 or len(upper) != 60 or len(static['static']) != 270
            or len(region['rows']) != 12 or settings['shape']['nominal'] != frozen['nominal']):
        raise ValueError('unchanged surviving region, archived rows and signed score required')
    rows = list(static['static'])+[row for row, _ in region['rows']]
    limits = list(static['limits'])+[limit for _, limit in region['rows']]
    objective, allowance = score_objective(target+((F(0), F(0)),)*9, lower, upper)
    design = np.c_[design, np.zeros((len(residual), 9))]
    witnesses = [row['score_lower'] for row in saved['points'] if all(a <= x <= b for a, x, b in
                 zip(child['lower'], row['point'], child['upper'], strict=True))]
    if len(witnesses) != prior['witnesses'] or any(w > prior['upper'] for w in witnesses):
        raise ValueError('all archived witness memberships must match the prior certificate')
    lo, hi = max([0., *witnesses]), prior['upper']
    trials = []
    for _ in range(FLOORS):
        floor = float((F(lo)+F(hi))/2)
        if not lo < floor < hi:
            break
        trial = _floor_trial(context, floor, lower, upper, rows, limits, objective, allowance,
                             residual, raw, design, earlier)
        trials.append(trial)
        if trial['excluded']:
            if any(w >= floor for w in witnesses):
                raise ValueError('excluded score floor contradicts an archived witness')
            hi = floor
        else:
            lo = floor
    context.save('floor-certificates.json', dict(trials=trials, score_objective=objective,
        coefficient_allowance=allowance, witness_scores=witnesses, source_sha256=region['source_sha256']))
    result = dict(identity=identity, parent=parent, model=model, child=index, excluded=False,
        previous_upper=prior['upper'], upper=hi, witnesses=len(witnesses), floors_tested=len(trials),
        scores_excluded=sum(trial['excluded'] for trial in trials),
        affine_exclusions=sum(trial['certificate']=='affine' for trial in trials),
        full_loss_exclusions=sum(trial['certificate']=='earlier_loss' for trial in trials),
        passed=True, scientific_decision='abstain')
    context.save('child-certificate.json', result)
    return result


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the frozen score-floor study')
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('original checked joint score result required')
    prior = json.loads(raw)
    staged, tasks = {}, []
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (any(prior[key] != parent.completion[key] for key in ('manifest_sha256', 'summary_sha256'))
                or not parent.summary['passed']):
            raise ValueError('saved result must match the original joint score closure')
        records, dispositions = read_dispositions(parent)
        if records != prior['rows'] or any(prior['dispositions'][key] != row for key, row in dispositions.items()):
            raise ValueError('all original upper bounds and dispositions must reproduce')
        for model in RANGES:
            for suffix in ('', '-weights', '-settings', '-support'):
                staged[model+suffix] = parent.input(model+suffix, raw=True)
        for name in ('cover', 'sensitivity', 'later-operator', 'earlier-linked-report', 'first-split'):
            staged[name] = parent.input(name, raw=True)
        for identity, task in parent.tasks.items():
            row = dispositions[identity]
            if row['excluded']:
                raise ValueError('do not reopen discarded ranges')
            child = parent.input(identity+'-child')
            child['prior']['upper'] = row['upper']
            projection = parent.input(identity+'-projection')
            raw_joint = parent.artifact(identity, 'joint-certificate.json', raw=True)
            joint = json.loads(raw_joint)
            if joint['projection_sha256'] != projection['source_sha256'] or len(joint['added']) != 7:
                raise ValueError('all preceding loss rows must be verified and reused')
            rows = projection['training_rows']+[[record['row'], record['limit']] for record in joint['added']]
            staged[identity+'-floors'] = encoded(dict(lower=joint['lower'], upper=joint['upper'], rows=rows,
                                                        source_sha256=digest(raw_joint)))
            staged[identity+'-child'] = encoded(child)
            tasks.append(frozen_task(*(task['payload'][key] for key in ('parent', 'model', 'child'))))
    if len(tasks) != 11:
        raise ValueError('all eleven surviving child bounds required')
    base.mkdir(parents=True)
    inputs = {'plan': PLAN, 'prior': PRIOR}
    for name, content in staged.items():
        path = base/name
        atomic(path, content)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=tasks,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_linked_score_floor.py']),
        workers=2, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


if __name__ == '__main__':
    root = Path.cwd()
    if sys.argv[1] == 'prepare':
        print(json.dumps(prepare(root), sort_keys=True))
    elif sys.argv[1] == 'report':
        collect_refinement(root, ID, RESULT)
    else:
        raise ValueError('unknown score-floor operation')
