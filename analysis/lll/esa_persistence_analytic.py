# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded analytic optimization of the existing donor-only error law."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from .esa_joint_persistence import BASE, BOUNDS, LAWS, EvaluationLimit, PersistenceScore, scorer
from .esa_joint_persistence import ID as JOINT
from .esa_persistence_gradient import loss_and_gradient
from .esa_persistence_stopping import DonorInputs, ID as AUDIT, RESULT as AUDIT_RESULT, project
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-persistence-analytic-v1'
SCOPE = 'Bounded gradient refinement of eight ESA 187 donor-only covariance settings'
PLAN = BASE+'ESA_JOINT_PERSISTENCE_ANALYTIC_PLAN.md'
RESULT = BASE+'esa-persistence-analytic-result.json'
REQUEST = BASE+'esa-persistence-analytic-qualification-v2.json'
REPORT = BASE+'esa-persistence-analytic-tests-v2.xml'
TEST = 'analysis/tests/test_esa_persistence_analytic.py'
TESTS = ('test_analytic_solver_recovers_interior_and_bound_active_optima[False]',
         'test_analytic_solver_recovers_interior_and_bound_active_optima[True]',
         'test_analytic_budget_retains_best_charged_score')
MAXIMUM = 128
GTOL = .00001
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=11+MAXIMUM, bound_steps=24+6*MAXIMUM)


def fit_analytic(score, start, *, maximum, reserve):
    import numpy as np
    from scipy.optimize import minimize

    def feasible(point):
        return len(point) == 6 and all(lo <= v <= hi for v, (lo, hi) in zip(point, BOUNDS, strict=True))

    if not feasible(start) or type(maximum) is not int or maximum < 1:
        raise ValueError('finite feasible start and positive allowance required')
    evaluations = {}

    def objective(proposal):
        point = tuple(map(float, proposal))
        if not feasible(point):
            raise ValueError('proposal outside frozen bounds')
        if point not in evaluations:
            if len(evaluations) >= maximum:
                raise EvaluationLimit
            reserve()
            loss, gradient = score(point)
            gradient = np.asarray(gradient, dtype=float)
            if not math.isfinite(loss) or gradient.shape != (6,) or not np.isfinite(gradient).all():
                raise ValueError('finite complete value and derivative required')
            evaluations[point] = (float(loss), gradient)
        return evaluations[point]

    initial = objective(start)[0]

    def shifted_objective(point):
        loss, gradient = objective(point)
        return loss-initial, gradient

    try:
        fit = minimize(shifted_objective, start, method='L-BFGS-B', bounds=BOUNDS, jac=True,
                       options=dict(maxfun=maximum, maxiter=maximum, ftol=0., gtol=GTOL))
        reached_limit = not fit.success and len(evaluations) == maximum
        status = 'evaluation_limit' if reached_limit else int(fit.status)
    except EvaluationLimit:
        status = 'evaluation_limit'
    point = min(evaluations, key=lambda p: (evaluations[p][0], max(map(abs, project(p, evaluations[p][1]))), p))
    loss, gradient = evaluations[point]
    projected = project(point, gradient)
    return dict(parameters=list(point), negative_log_score=loss, initial_score=initial, projected=projected,
                gradient=gradient.tolist(), evaluations=len(evaluations), status=status,
                converged=max(map(abs, projected)) <= GTOL)


def task_for(pair, law):
    return dict(identity=f'{pair[0]}-{law}', input_key='design', payload=dict(pair=pair, law=law), limits=LIMITS)


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('reuse the existing analytic comparison and allowance')
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    audit = json.loads((root/AUDIT_RESULT).read_bytes())
    with closing(ClosedStudy(root, 'data/'+AUDIT)) as parent, closing(ClosedStudy(root, 'data/'+JOINT)) as joint:
        if (parent.completion != audit['completion'] or not parent.summary['passed']
                or not joint.summary['passed'] or len(parent.rows) != 8 or len(joint.rows) != 8):
            raise ValueError('eight verified donors and gradient checks required')
        design = parent.input('design')
        indices = [index for pair in design['pairs'] for index in pair]
        tasks = [task_for(pair, law) for pair in design['pairs'] for law in LAWS]
        if len(tasks) != 8 or len(indices) != 8 or len(set(indices)) != 8:
            raise ValueError('original four disjoint pairs required')
        keys = ['design', *(f'observed-{index}' for index in indices)]
        keys.extend(f'forecast-{index}-{law}' for index in indices for law in LAWS)
        staged = {key: parent.input(key, raw=True) for key in keys}
        for task in tasks:
            identity = task['identity']
            gradient = parent.artifact(identity, 'stopping.json')
            previous = joint.artifact(identity, 'joint-persistence.json')
            selected = previous['fits'][previous['selected']]
            if (gradient != audit['folds'][identity] or gradient != parent.envelope(identity)['result']
                    or previous != joint.envelope(identity)['result'] or not gradient['passed']
                    or selected['negative_log_score'] != gradient['saved_score']
                    or selected['parameters'] != [gradient['point'][name] for name in audit['names']]):
                raise ValueError('the previously audited settings and forecasts are required')
            staged[identity] = encoded(previous)
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, prior=AUDIT_RESULT, qualification=REQUEST, qualification_tests=REPORT)
    for key, raw in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, raw)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources, tasks=tasks, workers=2, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    pair, law = (task['payload'][key] for key in ('pair', 'law'))
    design = json.loads(context.input_path('design').read_bytes())
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in design['pairs'] or law not in LAWS
            or declared != task_for(pair, law)):
        raise ValueError('exact frozen analytic refinement task required')
    saved = json.loads(context.input_path(task['identity']).read_bytes())
    donor_ids = [index for other in design['pairs'] for index in other if index not in pair]
    if (saved['pair'] != pair or saved['law'] != law or saved['donor_ids'] != donor_ids
            or len(donor_ids) != 6 or len(set(donor_ids+pair)) != 8):
        raise ValueError('six original donors and two distinct omitted windows required')
    donor_context = DonorInputs(context, frozenset(key for i in donor_ids
                             for key in (f'observed-{i}', f'forecast-{i}-{law}')))

    def read(source, index):
        score = scorer(source, index, law, design['scores'][f'{index}-{law}'])
        times = json.loads(source.input_path(f'forecast-{index}-{law}').read_bytes())['times_s']
        return score, times

    donors = [read(donor_context, index) for index in donor_ids]
    original = saved['fits'][saved['selected']]

    def score(point):
        values, gradients = zip(*(loss_and_gradient(item, times, point) for item, times in donors), strict=True)
        return math.fsum(values), [math.fsum(column) for column in zip(*gradients, strict=True)]

    def stored_method(item, times, point):
        return PersistenceScore(item, times, point[:4]).score(*map(math.exp, point[4:]))

    fit = fit_analytic(score, original['parameters'], maximum=MAXIMUM,
                       reserve=lambda: context.charge(bound_calls=1, bound_steps=6))
    context.charge(bound_calls=1, bound_steps=6)
    replay = math.fsum(stored_method(item, times, fit['parameters'])['negative_log_score'] for item, times in donors)
    verified = (abs(fit['initial_score']-original['negative_log_score']) <= 1e-6
                and abs(replay-fit['negative_log_score']) <= 1e-6)
    selection = dict(pair=pair, law=law, donor_ids=donor_ids, fit=fit, replay=replay, verified=verified)
    context.save('analytic-selection.json', selection)
    held = []
    for index, row in zip(pair, saved['heldout'], strict=True):
        if index != row['index']:
            raise ValueError('exact archived omitted row required')
        item, times = read(context, index)
        context.charge(bound_calls=1, bound_steps=1)
        held.append(dict(index=index, previous=row['scores']['joint'],
                         updated=stored_method(item, times, fit['parameters'])))
    result = dict(**selection, heldout=held, passed=verified, new_trajectory_fits=0, scientific_decision='abstain')
    context.save('analytic-result.json', result)
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 8:
            raise ValueError('eight sealed refinement tasks required')
        folds = {}
        for identity in study.rows:
            record = study.envelope(identity)
            row = record['result']
            evaluations = row['fit']['evaluations']
            expected = dict(native_calls=0, packet_visits=0, bound_calls=11+evaluations, bound_steps=24+6*evaluations)
            if (record['status'] != 'complete' or record['charged'] != expected
                    or row != study.artifact(identity, 'analytic-result.json')):
                raise ValueError('analytic refinement differs from its seal or charge')
            folds[identity] = row
        result = dict(folds=folds, completion=study.completion, new_trajectory_fits=0)
    _write_equal(root/RESULT, encoded(result))
    return dict(stopped=sum(row['verified'] and row['fit']['converged'] for row in folds.values()), total=len(folds))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
