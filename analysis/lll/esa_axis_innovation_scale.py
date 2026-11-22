# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test separate ordered-innovation scales on the preserved ESA forecasts."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from .esa_motion_innovation_scale import BASE, ID as PARENT, RESULT as PRIOR
from .esa_motion_innovation_scale import LAWS, SCALES, scorer
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-axis-innovation-scale-v1'
SCOPE = 'ESA 187 donor-only quiet and maneuver scales by ordered innovation slot'
PLAN = BASE+'ESA_AXIS_INNOVATION_SCALE_PLAN.md'
RESULT = BASE+'esa-axis-innovation-scale-result.json'
REQUEST = BASE+'esa-axis-innovation-scale-qualification.json'
TEST_REPORT = BASE+'esa-axis-innovation-scale-tests.xml'
PRIOR_SHA = 'f998b5a0656576e7d9f7778687af8ee84a456bc4522d3edfeb0c95ee17018302'
TEST = 'analysis/tests/test_esa_axis_innovation_scale.py'
TESTS = ('test_axis_scale_likelihood_matches_dense_correlated_reference',
         'test_repeated_axis_scales_reproduce_pooled_score',
         'test_coordinate_fit_stays_on_grid_with_finite_budget')
SWEEPS = 3
GRID = tuple(float(round(math.log(scale))) for scale in SCALES)
SLOT_COUNTS = {'axis_quiet': 4, 'axis_motion': 6}
ARMS = ('original', 'shared_motion', *SLOT_COUNTS)
SEARCH = SWEEPS*len(GRID)*sum(SLOT_COUNTS.values())
DONORS, OMITTED = 6, 2
CHECKS = DONORS+OMITTED
SCORES = OMITTED*len(ARMS)
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=SEARCH+CHECKS+SCORES,
              bound_steps=DONORS*SEARCH+2*CHECKS+SCORES)


def axis_score(score, log_scales):
    import numpy as np

    values = tuple(map(float, log_scales))
    if len(values) not in SLOT_COUNTS.values() or len(score.y) % 3 or not all(map(math.isfinite, values)):
        raise ValueError('ordered triples and four or six finite log scales required')
    quiet = np.tile([math.exp(v) for v in values[:3]], len(score.y)//3)
    motion = tuple(math.exp(v) for v in values[3:])
    return score.score(quiet, motion[0] if len(motion) == 1 else np.tile(motion, len(score.y)//3))


def select_scales(loss, start, *, reserve):
    """Select a bounded deterministic coordinate search from donor windows only."""
    point = tuple(start)
    if len(point) not in SLOT_COUNTS.values() or any(v not in GRID for v in point):
        raise ValueError('the initial scales must be on the frozen grid')

    def proposal(candidate):
        reserve()
        value = loss(candidate)
        if not math.isfinite(value):
            raise ValueError('finite candidate training score required')
        return value, candidate

    for _ in range(SWEEPS):
        for slot in range(len(point)):
            score, point = min(proposal(point[:slot]+(v,)+point[slot+1:]) for v in GRID)
    return dict(log_scales=point, training_negative_log_score=score)


def task_for(pair, law):
    return dict(identity=f'{pair[0]}-{law}', input_key='design', payload=dict(pair=pair, law=law), limits=LIMITS)


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
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing frozen axis scale study')
    prior = (root/PRIOR).read_bytes()
    if digest(prior) != PRIOR_SHA:
        raise ValueError('exact saved shared-scale results required')
    report = json.loads(prior)
    deps, environment = sources(root), runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=360)))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (not parent.summary['passed'] or len(parent.rows) != 8
                or parent.completion['manifest_sha256'] != report['manifest_sha256']):
            raise ValueError('all eight completed shared-scale folds required')
        design = parent.input('design')
        indices = [n for pair in design['pairs'] for n in pair]
        tasks = [task_for(pair, law) for pair in design['pairs'] for law in LAWS]
        seeds = {row['identity']: parent.artifact(row['identity'], 'motion-scale.json') for row in tasks}
        saved = {f'{row["pair"][0]}-{row["law"]}': row for row in report['folds']}
        if seeds != saved or len(set(indices)) != 8:
            raise ValueError('archived folds or their time selections differ')
        keys = ['design', *(f'observed-{index}' for index in indices)]
        keys.extend(f'forecast-{index}-{law}' for index in indices for law in LAWS)
        materials.update({key: parent.input(key, raw=True) for key in keys})
        materials.update({f'{key}-seed': encoded(value) for key, value in seeds.items()})
    inputs = dict(plan=PLAN, prior=PRIOR)
    for key, value in materials.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, sources=deps, inputs=inputs, tasks=tasks,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=240.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    pair, law = (task['payload'][k] for k in ('pair', 'law'))
    design = json.loads(context.input_path('design').read_bytes())
    declared = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != task_for(pair, law) or pair not in design['pairs']:
        raise ValueError('exact frozen axis scale fold required')
    previous = json.loads(context.input_path(task['identity']+'-seed').read_bytes())
    donor_ids = [index for source in design['pairs'] for index in source if index not in pair]
    if (previous['pair'] != pair or previous['law'] != law or previous['fitting'] != donor_ids
            or len(donor_ids) != DONORS or len(set((*donor_ids, *pair))) != 8):
        raise ValueError('same six donors and two separately held windows required')

    def read(index):
        return scorer(context, index, law, design['scores'][f'{index}-{law}'])

    donors = [read(index) for index in donor_ids]
    pooled = previous['fitted']['motion']
    quiet, motion = (float(round(math.log(v))) for v in pooled)
    starts = {'axis_quiet': (quiet,)*3+(motion,), 'axis_motion': (quiet,)*3+(motion,)*3}

    def donor_loss(scales):
        return math.fsum(axis_score(evidence, scales)['negative_log_score'] for evidence in donors)

    def reserve_donors():
        context.charge(bound_calls=1, bound_steps=DONORS)

    fitted = {name: select_scales(donor_loss, start, reserve=reserve_donors) for name, start in starts.items()}
    results = []
    for original in previous['target']:
        index = original['index']
        if index != pair[len(results)]:
            raise ValueError('held-out order differs from the frozen fold')
        evidence = read(index)
        functions = dict(original=lambda: evidence.score(1., 0.), shared_motion=lambda: evidence.score(*pooled))
        for name, value in fitted.items():
            functions[name] = lambda scales=value['log_scales']: axis_score(evidence, scales)
        scored = {}
        for name, operation in functions.items():
            context.charge(bound_calls=1, bound_steps=1)
            scored[name] = operation()
        for name, predecessor in (('original', 'fixed'), ('shared_motion', 'motion')):
            if any(not math.isclose(scored[name][key], original['scores'][predecessor][key], rel_tol=1e-8, abs_tol=1e-8)
                   for key in ('quadratic', 'negative_log_score')):
                raise ValueError('held-out baseline scoring did not reproduce')
        results.append(dict(index=index, scores=scored))
    result = dict(law=law, pair=pair, fitting=donor_ids, selected=fitted, heldout=results,
                  passed=True, scientific_decision='abstain')
    context.save('axis-scale.json', result)
    return result


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 8 or study.manifest['scope'] != SCOPE:
            raise ValueError('all eight axis-scale folds must seal')
        folds, outcomes = [], {}
        for identity in study.rows:
            envelope = study.envelope(identity)
            result = envelope['result']
            if result['passed'] and (result != study.artifact(identity, 'axis-scale.json')
                    or envelope['charged'] != LIMITS or len(result['heldout']) != OMITTED):
                raise ValueError('axis scale evidence differs from the sealed work')
            folds.append(result)
        for law in LAWS:
            held = [row for f in folds if f.get('law') == law and f['passed'] for row in f['heldout']]
            if len({row['index'] for row in held}) != len(held):
                raise ValueError('each window must be counted only once per error law')
            total = {arm: math.fsum(row['scores'][arm]['negative_log_score'] for row in held) for arm in ARMS}
            inside = {arm: sum(row['scores'][arm]['within_reference'] for row in held) for arm in ARMS}
            qualified = {arm: inside[arm] == 8 and total[arm] < total['shared_motion'] for arm in SLOT_COUNTS}
            outcomes[law] = dict(windows=len(held), log_scores=total, inside_reference=inside,
                                 clears_development_screen=qualified)
        value = dict(study.completion, folds=folds, outcomes=outcomes, charged=study.summary['charged'],
                     new_fits=0, scientific_decision='abstain')
    raw = encoded(value)
    _write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), outcomes=outcomes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
