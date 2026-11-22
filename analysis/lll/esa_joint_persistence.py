# SPDX-License-Identifier: AGPL-3.0-or-later
"""Select innovation magnitude and persistence together on saved ESA donors."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_component_scale_transfer import LOG_BOUNDS
from .esa_innovation_persistence import ID as PARENT, RESULT as PRIOR, PersistenceScore
from .esa_motion_innovation_scale import BASE, LAWS, scorer
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-joint-persistence-v1'
SCOPE = 'Joint temporal persistence and variance transfer across four ESA 187 forecast pairs'
PLAN = BASE+'ESA_JOINT_PERSISTENCE_PLAN.md'
RESULT = BASE+'esa-joint-persistence-result.json'
REQUEST = BASE+'esa-joint-persistence-qualification.json'
REPORT = BASE+'esa-joint-persistence-tests.xml'
PRIOR_SHA = '2373f8623904b60c69c6d35d4ec08ad5713f834509eb4be5d4f2518cd4bfa857'
TEST = 'analysis/tests/test_esa_joint_persistence.py'
TESTS = ('test_joint_fit_recovers_six_parameters_with_every_probe_charged',
         'test_budget_exhaustion_keeps_the_best_scored_vector_and_rejects_bad_starts',
         'test_joint_fit_reports_parameters_at_limits')
MAXIMUM = 192
NAMES = ('north_quiet_variance', 'east_quiet_variance', 'height_quiet_variance',
         'motion_variance', 'quiet_seconds', 'motion_seconds')
BOUNDS = (LOG_BOUNDS,)*4+((math.log(.25), math.log(256.)),)*2
MODES = ('diagonal', 'fixed_variance_persistence', 'joint')
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=8+2*MAXIMUM+6,
              bound_steps=16+2*MAXIMUM*6+6)


class EvaluationLimit(Exception):
    """Stop before an uncharged parameter score."""


def fit_joint(loss, start, *, maximum, reserve):
    """Keep the best actually scored parameters within the declared start budget."""
    from scipy.optimize import minimize

    def inside(p):
        return len(p) == len(BOUNDS) and all(lo <= value <= hi for value, (lo, hi) in zip(p, BOUNDS, strict=True))

    if not inside(start) or type(maximum) is not int or maximum < 1:
        raise ValueError('complete joint parameters within bounds and a positive evaluation limit required')
    visited = {}

    def objective(x):
        point = tuple(map(float, x))
        if not inside(point):
            raise ValueError('numerical probe outside the frozen bounds')
        if point in visited:
            return visited[point]
        if len(visited) >= maximum:
            raise EvaluationLimit
        reserve()
        value = float(loss(point))
        if not math.isfinite(value):
            raise ValueError('finite donor score required')
        visited[point] = value
        return value

    try:
        fit = minimize(objective, start, method='L-BFGS-B', bounds=BOUNDS, jac='2-point',
                       options=dict(maxiter=maximum, maxfun=maximum, finite_diff_rel_step=1e-5,
                                    ftol=1e-12, gtol=1e-5))
        status = 'evaluation_limit' if len(visited) == maximum and not fit.success else int(fit.status)
        converged = bool(fit.success)
    except EvaluationLimit:
        status, converged = 'evaluation_limit', False
    point, score = min(visited.items(), key=lambda item: (item[1], item[0]))
    limits = {}
    for name, value, (lo, hi) in zip(NAMES, point, BOUNDS, strict=True):
        if abs(value-lo) <= 1e-5:
            limits[name] = 'lower'
        if abs(value-hi) <= 1e-5:
            limits[name] = 'upper'
    return dict(parameters=list(point), negative_log_score=score, status=status, converged=converged,
                evaluations=len(visited), at_limits=limits)


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
        raise ValueError('reuse the existing joint persistence study and allowance')
    prior_raw = (root/PRIOR).read_bytes()
    if digest(prior_raw) != PRIOR_SHA:
        raise ValueError('exact fixed-variance persistence report required')
    prior = json.loads(prior_raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (not parent.summary['passed'] or len(parent.rows) != 8
                or parent.completion != prior['closures'][parent.prefix]):
            raise ValueError('exact eight completed persistence folds required')
        design = parent.input('design')
        windows = [i for pair in design['pairs'] for i in pair]
        tasks = [task_for(pair, law) for pair in design['pairs'] for law in LAWS]
        if len(windows) != len(set(windows)) or len(tasks) != 8:
            raise ValueError('the original four disjoint forecast pairs are required')
        keys = ['design', *(f'observed-{index}' for index in windows)]
        keys.extend(f'forecast-{index}-{law}' for index in windows for law in LAWS)
        staged = {name: parent.input(name, raw=True) for name in keys}
        for task in tasks:
            identity = task['identity']
            row = parent.artifact(identity, 'persistence.json')
            if row != prior['folds'][identity] or row != parent.envelope(identity)['result']:
                raise ValueError('saved persistence case differs from its scoring seal')
            scales = parent.input(identity)
            staged[identity] = encoded(dict(persistence=row, scales=scales['selected']['axis_quiet']['log_scales']))
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, raw in staged.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                         sources=sources, tasks=tasks, workers=2, threads=1, maximum_wall_s=240.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    law, pair = (task['payload'][key] for key in ('law', 'pair'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    design = json.loads(context.input_path('design').read_bytes())
    if (context.manifest['scope'] != SCOPE or law not in LAWS or pair not in design['pairs']
            or declared != task_for(pair, law)):
        raise ValueError('exact omitted forecast pair and allowance required')
    previous = json.loads(context.input_path(task['identity']).read_bytes())
    scales, fixed = previous['scales'], previous['persistence']
    donor_ids = [i for other in design['pairs'] for i in other if i not in pair]
    if (len(donor_ids) != 6 or len(set((*donor_ids, *pair))) != 8
            or fixed['pair'] != pair or fixed['law'] != law or fixed['donors'] != donor_ids):
        raise ValueError('exact six donor windows from the frozen study required')

    def read(index):
        score = scorer(context, index, law, design['scores'][f'{index}-{law}'])
        forecast = json.loads(context.input_path(f'forecast-{index}-{law}').read_bytes())
        return score, forecast['times_s']

    donors = [read(index) for index in donor_ids]

    def donor_score(parameters):
        seconds = [math.exp(value) for value in parameters[4:]]
        return math.fsum(PersistenceScore(score, times, parameters[:4]).score(*seconds)['negative_log_score']
                         for score, times in donors)

    seconds = fixed['choices']['motion']['seconds']
    starts = dict(saved=[*scales, *map(math.log, seconds)], one_second=[*scales, 0., 0.])
    fits = {key: fit_joint(donor_score, value, maximum=MAXIMUM,
                         reserve=lambda: context.charge(bound_calls=1, bound_steps=6)) for key, value in starts.items()}
    winning = min(fits, key=lambda key: (fits[key]['negative_log_score'], fits[key]['parameters'], key))
    chosen = fits[winning]['parameters']
    context.save('joint-selection.json', dict(donors=donor_ids, pair=pair, law=law, fits=fits, winner=winning))

    held = []
    for index, row in zip(pair, fixed['heldout'], strict=True):
        if index != row['index']:
            raise ValueError('verified omitted row order required')
        score, times = read(index)
        results = {}
        settings = ((scales, (0., 0.)), (scales, seconds), (chosen[:4], [math.exp(value) for value in chosen[4:]]))
        for kind, (variance, memory) in zip(MODES, settings, strict=True):
            context.charge(bound_calls=1, bound_steps=1)
            results[kind] = PersistenceScore(score, times, variance).score(*memory)
        for name, prior in (('diagonal', 'diagonal'), ('fixed_variance_persistence', 'motion')):
            if any(not math.isclose(results[name][key], row['scores'][prior][key], rel_tol=1e-8, abs_tol=1e-8)
                   for key in ('quadratic', 'negative_log_score')):
                raise ValueError('saved comparison score did not reproduce')
        held.append(dict(index=index, scores=results))
    result = dict(pair=pair, law=law, donor_ids=donor_ids, fits=fits, selected=winning, heldout=held,
                  passed=True, new_fits=0, protected_reads=0, scientific_decision='abstain')
    context.save('joint-persistence.json', result)
    return result


def report(root):
    from .studies.task_resume import resume_campaign
    from .studies.validation_resume import _stage_paths

    prefix = 'data/'+ID
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        sources = [study]
        if len(study.rows) != len(study.tasks) or any(study.envelope(identity)['status'] == 'interrupted'
                                                       for identity in study.rows):
            continuation = root/(prefix+'-recovery')
            if resume_campaign(root, continuation, launch=False)['state'] != 'all_tasks_finished':
                raise ValueError('verified recovery closure required before reporting')
            sources.extend(stack.enter_context(closing(ClosedStudy(root, path.relative_to(root).as_posix(),
                store=study.store))) for path in _stage_paths(continuation))
        folds = {}
        for source in sources:
            for identity in source.rows:
                record = source.envelope(identity)
                if record['status'] == 'interrupted':
                    continue
                if identity in folds or identity not in study.tasks or record['status'] != 'complete':
                    raise ValueError('one terminal outcome per original scoring fold required')
                result = record['result']
                if result['passed']:
                    evaluations = sum(row['evaluations'] for row in result['fits'].values())
                    charged = dict(native_calls=0, packet_visits=0, bound_calls=14+evaluations, bound_steps=22+6*evaluations)
                    if record['charged'] != charged or result != source.artifact(identity, 'joint-persistence.json'):
                        raise ValueError('scoring record does not match its charges and sealed results')
                folds[identity] = result
        if len(folds) != 8 or study.manifest['scope'] != SCOPE:
            raise ValueError('exact eight sealed terminal folds required')
        closures = {source.prefix: source.completion for source in sources}
    groups = {}
    for law in LAWS:
        held = [row for result in folds.values() if result['passed'] and result['law'] == law for row in result['heldout']]
        if len(held) != len({row['index'] for row in held}):
            raise ValueError('each held-out window may contribute only once')
        groups[law] = dict(windows=len(held), scores={name: dict(
            within_reference=sum(row['scores'][name]['within_reference'] for row in held),
            negative_log_score=math.fsum(row['scores'][name]['negative_log_score'] for row in held)) for name in MODES})
    gate = all(row['windows'] == 8 and row['scores']['joint']['within_reference'] == 8
               and row['scores']['joint']['negative_log_score'] < row['scores']['fixed_variance_persistence']['negative_log_score']
               for row in groups.values())
    result = dict(groups=groups, folds=folds, closures=closures, development_gate=gate, new_fits=0, protected_reads=0,
                  scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return dict(groups=groups, development_gate=gate)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
