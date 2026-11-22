# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tighten a saved ESA score bound with verified cuts of the calibration map."""

import argparse
from contextlib import closing
from fractions import Fraction as F
from functools import partial
import json
import math
from pathlib import Path

from .esa_linked_child_certificates import RANGES, task_for
from .esa_linked_floor_support import ID as PARENT, RESULT as PRIOR
from .esa_linked_scaled_proposals import collect_refinement
from .ilvis0_saved_prediction_audit import endpoint
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-graph-cuts-v1'
SCOPE = 'Physical graph cuts on eleven saved ESA calibration ranges'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_LINKED_GRAPH_CUTS_PLAN.md'
RESULT = FOLDER+'esa-linked-graph-cuts-result.json'
REQUEST = FOLDER+'esa-linked-graph-cuts-qualification.json'
TEST_REPORT = FOLDER+'esa-linked-graph-cuts-tests.xml'
PRIOR_SHA = 'bf1cfb1a5b3e77468b5eb4679c0bc7c3052fbe60b6776a1c4c0881032b3a538c'
TEST = 'analysis/tests/test_esa_linked_graph_cuts.py'
TESTS = ('test_centering_a_graph_cut_keeps_every_physical_point_and_rejects_a_lift',
         'test_cut_rounds_exact_bound_outward_and_keeps_auxiliary_columns',
         'test_checked_graph_cut_removes_false_forecast_overlap')
PROPOSALS = 6
DIRECTIONS = 3
frozen_task = partial(task_for, bound_calls=PROPOSALS+(PROPOSALS-1)*(DIRECTIONS+1),
                      bound_steps=3*PROPOSALS+(PROPOSALS-1)*(3*DIRECTIONS+1))


def centered_cut(weights, derivative, checked_upper, *, auxiliaries=0):
    """Build a row whose bound comes from the full linked map, not its tangent."""
    coefficients = [-float(v) for v in derivative]+[float(v) for v in weights]
    return coefficients+[0.]*auxiliaries, endpoint(F(checked_upper(coefficients)), True)


def violated_cut(row, bound, point):
    return sum(F(float(a))*F(float(x)) for a, x in zip(row, point, strict=True)) > F(bound)


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    base = root/'data'/(ID+'-inputs')
    if (root/'data'/ID).exists() or base.exists():
        raise ValueError('reuse the existing physical graph study')
    prior_bytes = (root/PRIOR).read_bytes()
    if digest(prior_bytes) != PRIOR_SHA:
        raise ValueError('previous physical bounds changed')
    prior = json.loads(prior_bytes)
    deps, environment = sources(root), runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    staged = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=600)))
    tasks = []
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (any(prior[key] != parent.completion[key] for key in ('manifest_sha256', 'summary_sha256'))
                or not parent.summary['passed'] or len(parent.tasks) != 11
                or set(prior['rows']) != set(parent.tasks)):
            raise ValueError('all eleven exact closed physical checks required')
        keys = ['cover', 'sensitivity', 'later-operator', 'earlier-linked-report', 'first-split']
        keys.extend(model+suffix for model in RANGES for suffix in ('', '-weights', '-settings', '-support'))
        staged.update({key: parent.input(key, raw=True) for key in keys})
        for identity, task in parent.tasks.items():
            row = parent.envelope(identity)['result']
            if row != prior['rows'][identity] or row['excluded'] or prior['dispositions'][identity]['excluded']:
                raise ValueError('exact original bounds and retained task identities required')
            child = parent.input(identity+'-child')
            child['prior']['upper'] = prior['dispositions'][identity]['upper']
            staged[identity+'-child'] = encoded(child)
            staged[identity+'-floors'] = parent.input(identity+'-floors', raw=True)
            tasks.append(frozen_task(*(task['payload'][key] for key in ('parent', 'model', 'child'))))
    inputs = dict(plan=PLAN, prior=PRIOR)
    for key, value in staged.items():
        path = base/key
        atomic(path, value)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        inputs=inputs, tasks=tasks, sources=deps, workers=2, threads=1, maximum_wall_s=300.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def scaled_proposal(lower, upper, rows, limits, objective):
    import numpy as np

    from .ilvis0_affine_support import linear_proposal

    lo, hi, rows, limits, objective = map(np.asarray, (lower, upper, rows, limits, objective))
    width = (hi-lo)/2.
    center = lo+width
    matrix, bounds = rows*width, limits-rows@center
    scale = np.maximum(1e-20, np.maximum(np.max(abs(matrix), axis=1), abs(bounds)))
    extent = (width > 0.).astype(float)
    score = objective*width
    score_scale = max(1., float(np.max(abs(score))))
    proposal = linear_proposal(-extent, extent, matrix/scale[:, None], bounds/scale, score/score_scale)
    if proposal is None:
        return None
    point, multipliers = proposal
    return np.clip(center+point*width, lo, hi), multipliers*score_scale/scale


def linked_values(reference, point):
    import numpy as np

    return np.concatenate([part.normalized_values_at(point)
                           for part in (reference.parent, reference.acceleration, reference.transform)])


def graph_row(model, lower, upper, point, direction):
    from .ilvis0_linked_directional import _linked_expression, directional_bound

    slope = _linked_expression(model, point, point, [0.]*27+list(direction)).derivative
    derivatives = [(float(value.lo)+float(value.hi))/2. for value in slope]

    def checked(coefficients):
        intervals = [(F(v), F(v)) for v in coefficients]
        return directional_bound(model, lower, upper, intervals).hi

    return centered_cut(direction, derivatives, checked, auxiliaries=9)


def candidate_directions(delta, training, score):
    import numpy as np

    effect = training.T@(training@delta)
    return delta, effect, math.copysign(1., float(score@delta))*np.asarray(score)


def evaluate(task, context):
    import numpy as np

    from .esa_linked_coordinates import INCREASE, _training_row
    from .esa_linked_joint_score import checked_score, score_objective
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_coupled_map import StaticMap, restore_static_reference
    from .ilvis0_exact_scale import sqrt_upper

    parent, model, index = (task['payload'][key] for key in ('parent', 'model', 'child'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != frozen_task(parent, model, index):
        raise ValueError('exact physical graph task required')
    identity = task['identity']
    frozen, region = [json.loads(context.input_path(identity+suffix).read_bytes())
                      for suffix in ('-child', '-floors')]
    saved = json.loads(context.input_path(model+'-support').read_bytes())
    cell = next(row for row in saved['ranges'] if row['identity'] == frozen['pair'])
    child, prior = frozen['child'], frozen['prior']
    lower, upper = region['lower'], region['upper']
    if len(lower) != 60 or len(upper) != 60 or len(region['rows']) != 12 or len(cell['static']) != 270:
        raise ValueError('all archived earlier and static constraints required')
    rows = [*cell['static'], *(row for row, _ in region['rows'])]
    limits = [*cell['limits'], *(limit for _, limit in region['rows'])]
    residual, raw, design, _, _, earlier, target, _ = load_projection_inputs(context, model)
    objective, allowance = score_objective(target+((F(0), F(0)),)*9, lower, upper)
    radius = sqrt_upper(sum(F(float(v))**2 for v in residual)+F(INCREASE))
    force = saved['force']
    packet = saved['first_sample']
    reference = restore_static_reference(force['configuration'], packet['dv'], packet['dt'],
        lower=force['lower'], upper=force['upper'], center=force['center'], expected_report=saved['reference'])
    static = StaticMap(reference, expected_report=saved['reference'], numerical_allowance=saved['map_allowance'])
    center = np.asarray(force['center'])
    child_lo, child_hi = child['lower'], child['upper']
    witnesses = [row for row in saved['points'] if all(a <= x <= b for a, x, b in
                 zip(child_lo, row['point'], child_hi, strict=True))]
    if len(witnesses) != prior['witnesses']:
        raise ValueError('preserve all saved witness memberships')
    witness_points = [np.r_[np.asarray(row['point'])-center, linked_values(reference, row['point']), np.zeros(9)]
                      for row in witnesses]
    best = F(prior['upper'])
    trials, cuts = [], []
    for iteration in range(PROPOSALS):
        context.charge(bound_calls=1, bound_steps=3)
        proposal = scaled_proposal(lower, upper, rows, limits, objective)
        if proposal is None:
            trials.append(dict(status='proposal_unavailable'))
            break
        x, weights = proposal
        verified = checked_score(lower, upper, rows, limits, objective, weights, allowance)
        best = min(best, verified)
        physical = np.clip(center+x[:27], child_lo, child_hi)
        exact_shared = linked_values(reference, physical)
        delta = x[27:51]-exact_shared
        relaxed = residual+design@x[:51]
        linked = residual+design@np.r_[physical-center, exact_shared]
        trials.append(dict(status='checked', exact_upper=str(verified), multipliers=weights.tolist(),
            point=x.tolist(), physical_point=physical.tolist(), relaxed_norm=float(np.linalg.norm(relaxed)),
            linked_norm=float(np.linalg.norm(linked)), shared_mismatch_norm=float(np.linalg.norm(delta))))
        if iteration+1 == PROPOSALS:
            break
        before = len(rows)
        for name, direction in zip(('shared', 'earlier', 'later'),
                                   candidate_directions(delta, design[:, 27:], objective[27:51]), strict=True):
            size = float(np.max(np.abs(direction)))
            if size <= 1e-12:
                continue
            context.charge(bound_calls=1, bound_steps=3)
            row, right = graph_row(static, child_lo, child_hi, physical, direction/size)
            if any(violated_cut(row, right, w) for w in witness_points):
                raise ValueError('linked graph cut excludes an archived physical point')
            added = violated_cut(row, right, x)
            cuts.append(dict(iteration=iteration, name=name, added=added, row=row, limit=right))
            if added:
                rows.append(row)
                limits.append(right)
        if np.linalg.norm(relaxed) > radius:
            context.charge(bound_calls=1, bound_steps=1)
            row, right = _training_row(relaxed, earlier, residual, raw, lower, upper)
            added = violated_cut(row, right, x)
            cuts.append(dict(iteration=iteration, name='training', added=added, row=row, limit=right))
            if added:
                rows.append(row)
                limits.append(right)
        if len(rows) == before:
            break
    if any(best < F(row['score_lower']) for row in witnesses):
        raise ValueError('an updated forecast bound excludes a saved witness')
    context.save('graph-cuts.json', dict(trials=trials, cuts=cuts, objective=objective,
                                         coefficient_allowance=allowance))
    result = dict(identity=identity, model=model, parent=parent, child=index, excluded=False,
        previous_upper=prior['upper'], upper=endpoint(best, True), witnesses=len(witnesses),
        proposals=len(trials), graphs_checked=sum(row['name'] != 'training' for row in cuts),
        graph_cuts=sum(row['added'] and row['name'] != 'training' for row in cuts),
        training_cuts=sum(row['added'] and row['name'] == 'training' for row in cuts),
        passed=True, scientific_decision='abstain')
    context.save('child-certificate.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    if action == 'report':
        collect_refinement(root, ID, RESULT)
    else:
        print(json.dumps({'request': request, 'prepare': prepare}[action](root), sort_keys=True))


if __name__ == '__main__':
    main()
