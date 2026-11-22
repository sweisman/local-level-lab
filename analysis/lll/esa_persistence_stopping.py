# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay and differentiate the eight archived ESA donor-only solutions."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path
from typing import NamedTuple

from .esa_joint_persistence import BASE, BOUNDS, LAWS, NAMES, PersistenceScore, scorer
from .esa_joint_persistence import ID as PARENT, RESULT as PRIOR
from .esa_persistence_gradient import loss_and_gradient
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-persistence-stopping-v1'
SCOPE = 'Gradients at the eight selected ESA 187 donor-only covariance settings'
PLAN = BASE+'ESA_JOINT_PERSISTENCE_STOPPING_PLAN.md'
RESULT = BASE+'esa-persistence-stopping-result.json'
REQUEST = BASE+'esa-persistence-stopping-qualification.json'
REPORT = BASE+'esa-persistence-stopping-tests.xml'
TEST = 'analysis/tests/test_esa_persistence_gradient.py'
TESTS = ('test_gradient_matches_dense_likelihood_on_irregular_times[0]',
         'test_gradient_matches_dense_likelihood_on_irregular_times[4]',
         'test_motion_derivatives_vanish_with_no_motion', 'test_probe_sides_and_projected_gradient_at_bounds')
PRIOR_SHA = '42237c0533b26cdfad843b54fecf2883f490783f897f19cc776b58a8d2e45e6d'
STEPS = (.0001, .00005)
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=6+26, bound_steps=12+26*6)


def differences(loss, point, base, step):
    slopes, methods = [], []
    for index, (value, (lo, hi)) in enumerate(zip(point, BOUNDS, strict=True)):
        def offset(delta):
            proposal = list(point)
            proposal[index] += delta
            return loss(proposal)

        if value-lo >= step and hi-value >= step:
            derivative = (offset(step)-offset(-step))/(2.*step)
            method = 'central'
        else:
            sign = 1 if value-lo < step else -1
            first, second = offset(sign*step)-base, offset(sign*2.*step)-base
            derivative = (4.*first-second)/(2.*sign*step)
            method = 'forward' if sign == 1 else 'backward'
        slopes.append(derivative)
        methods.append(method)
    return dict(step=step, gradient=slopes, methods=methods)


def project(point, gradient):
    return [0. if (value == lo and slope > 0.) or (value == hi and slope < 0.) else float(slope)
            for value, slope, (lo, hi) in zip(point, gradient, BOUNDS, strict=True)]


class DonorInputs(NamedTuple):
    context: object
    allowed: frozenset

    def charge(self, **counts):
        return self.context.charge(**counts)

    def input_path(self, key):
        if key not in self.allowed:
            raise ValueError('only the six named donor inputs are available to this fold')
        return self.context.input_path(key)


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
        raise ValueError('reuse the existing gradient study and allowance')
    prior_raw = (root/PRIOR).read_bytes()
    if digest(prior_raw) != PRIOR_SHA:
        raise ValueError('exact joint covariance report required')
    prior = json.loads(prior_raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion != prior['closures'][parent.prefix] or not parent.summary['passed']:
            raise ValueError('original covariance closure required')
        design = parent.input('design')
        indices = [index for pair in design['pairs'] for index in pair]
        tasks = [task_for(pair, law) for pair in design['pairs'] for law in LAWS]
        if len(tasks) != 8 or len(indices) != 8 or len(set(indices)) != 8:
            raise ValueError('four exact disjoint pairs required')
        keys = ['design', *(f'observed-{index}' for index in indices)]
        keys.extend(f'forecast-{index}-{law}' for index in indices for law in LAWS)
        staged = {key: parent.input(key, raw=True) for key in keys}
        for task in tasks:
            identity = task['identity']
            row = parent.artifact(identity, 'joint-persistence.json')
            if row != prior['folds'][identity] or row != parent.envelope(identity)['result']:
                raise ValueError('exact archived solution required')
            staged[identity] = encoded({key: row[key] for key in ('pair', 'law', 'donor_ids', 'fits', 'selected')})
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
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
        raise ValueError('exact frozen gradient task required')
    saved = json.loads(context.input_path(task['identity']).read_bytes())
    donor_ids = [index for other in design['pairs'] for index in other if index not in pair]
    if (saved['pair'] != pair or saved['law'] != law or saved['donor_ids'] != donor_ids
            or len(donor_ids) != 6 or len(set(donor_ids+pair)) != 8):
        raise ValueError('six original donors and two excluded windows required')
    donor_context = DonorInputs(context, frozenset(key for i in donor_ids
                             for key in (f'observed-{i}', f'forecast-{i}-{law}')))
    donors = [(scorer(donor_context, i, law, design['scores'][f'{i}-{law}']),
               json.loads(donor_context.input_path(f'forecast-{i}-{law}').read_bytes())['times_s']) for i in donor_ids]
    fit = saved['fits'][saved['selected']]
    point = fit['parameters']
    if (len(point) != 6 or not all(lo <= value <= hi for value, (lo, hi) in zip(point, BOUNDS, strict=True))
            or fit['converged'] or fit['status'] != 'evaluation_limit'):
        raise ValueError('the original bounded, capped solution is required')

    def loss(values):
        if not all(lo <= value <= hi for value, (lo, hi) in zip(values, BOUNDS, strict=True)):
            raise ValueError('probe outside original bounds')
        context.charge(bound_calls=1, bound_steps=6)
        return math.fsum(PersistenceScore(score, times, values[:4]).score(
                         *map(math.exp, values[4:]))['negative_log_score'] for score, times in donors)

    base = loss(point)
    context.charge(bound_calls=1, bound_steps=6)
    values, derivatives = zip(*(loss_and_gradient(score, times, point) for score, times in donors), strict=True)
    gradient = [math.fsum(column) for column in zip(*derivatives, strict=True)]
    analytic = math.fsum(values)
    probes = [differences(loss, point, base, step) for step in STEPS]
    for probe in probes:
        probe['discrepancy'] = [estimate-exact for estimate, exact in zip(probe['gradient'], gradient, strict=True)]
    reproduced = all(math.isclose(v, fit['negative_log_score'], rel_tol=0., abs_tol=1e-6) for v in (base, analytic))
    result = dict(pair=pair, law=law, donor_ids=donor_ids, point=dict(zip(NAMES, point, strict=True)),
                  saved_status=fit['status'], saved_score=fit['negative_log_score'], replay=base,
                  analytic=analytic, gradient=gradient, projected=project(point, gradient), probes=probes,
                  new_fits=0, protected_reads=0, passed=reproduced, scientific_decision='abstain')
    context.save('stopping.json', result)
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 8:
            raise ValueError('eight sealed gradient diagnostics required')
        rows = {}
        for identity in study.rows:
            record = study.envelope(identity)
            if (record['status'] != 'complete' or record['charged'] != LIMITS
                    or record['result'] != study.artifact(identity, 'stopping.json')):
                raise ValueError('gradient diagnostic differs from its seal or charge')
            rows[identity] = record['result']
        result = dict(names=NAMES, folds=rows, completion=study.completion, max_steps=LIMITS, new_fits=0)
    _write_equal(root/RESULT, encoded(result))
    return dict(passing=sum(row['passed'] for row in rows.values()), total=len(rows), new_fits=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
