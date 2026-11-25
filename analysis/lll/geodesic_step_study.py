# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify a corrected nonlinear trial using only the eight generated starts."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import curvature_retry_study as prior
from .ilvis0_matched_observed_inputs import _write_equal
from .residual_curvature_study import prior_evidence
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'geodesic-step-controls-v1'
SCOPE = 'Direction-corrected trial on the original eight generated bounded optima'
PLAN = prior.FOLDER+'GEODESIC_STEP_PLAN.md'
RESULT = prior.FOLDER+'geodesic-step-controls-result.json'
TEST = 'analysis/tests/test_geodesic_step.py'
REQUIRED = ('test_corrected_trial_changes_direction_to_follow_a_known_quadratic_valley',
            'test_corrected_trial_preserves_the_original_parameter_box',
            'test_corrected_trial_requires_an_actual_transverse_bend')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification-v2.json', 'tests-v2.xml'))
TASKS = tuple(dict(identity=f'{case}-{index}', input_key='design', payload=dict(case=case, start=index),
                   limits=dict(native_calls=0, packet_visits=0, bound_calls=prior.CAP, bound_steps=0))
              for case in prior.CASES for index in range(len(prior.STARTS)))


def qualification(root, *, check=False):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=REQUIRED,
            minimum_tests=len(REQUIRED))
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the frozen direction-correction study')
    sources, environment = qualification(root, check=True)
    prior_evidence(root)
    recovery, tests = checked(root, prior.RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = dict(design=PLAN, reference=prior.RESULT, qualification=REQUEST, tests=XML)
    for key, value in dict(recovery=recovery, recovery_tests=tests,
                           recovery_policy=encoded(prior.RECOVERY_RULE)).items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=list(TASKS), workers=1, threads=1, maximum_wall_s=60)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    from .ilvis0_solver_trust_v2 import fit_candidate

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('the frozen generated control is required')
    case, start = (task['payload'][key] for key in ('case', 'start'))
    problem = prior.Control(case, context.charge)
    fit = fit_candidate(problem, 'generated', start=prior.STARTS[start], maximum_evaluations=prior.CAP,
                        physical_step=lambda delta: delta.reshape((1, 3)), geodesic_retry=True)
    if problem.calls != fit['evaluations']:
        raise ValueError('generated corrections and final probes must be charged')
    optimum, cost = problem.exact_optimum()
    error = max(abs(a-b) for a, b in zip(fit['normalized_parameters'], optimum, strict=True))
    gap = abs(cost-fit['residual_sum_squares'])
    accepted = sum(row['accepted'] for row in fit['step_history'] if row.get('method') == 'geodesic_retry')
    baseline = json.loads(context.input_path('reference').read_bytes())['tasks']
    comparison = {row['arm']: row['passed'] for row in baseline if (row['case'], row['start']) == (case, start)}
    if set(comparison) != {'original', 'curvature'}:
        raise ValueError('previous results for the same case and start must remain available')
    context.save('fit.json', fit)
    return dict(case=case, start=start, previous_passed=comparison, evaluations=problem.calls,
                accepted_corrected_steps=accepted, parameter_error=error, cost_gap=gap,
                fresh_position_passed=fit['converged'], stop_reason=fit['stability_probe']['reason'],
                passed=bool(fit['converged'] and error <= 1e-4 and gap <= 1e-7), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if set(study.rows) != {task['identity'] for task in TASKS}:
            raise ValueError('all eight generated dispositions are required')
        rows = []
        for task in TASKS:
            identity = task['identity']
            row = study.envelope(identity)
            result = row['result']
            if row['charged']['bound_calls'] != result['evaluations'] or row['status'] != 'complete':
                raise ValueError('complete sealed generated evaluation charges are required')
            study.artifact(identity, 'fit.json', raw=True)
            rows.append(dict(identity=identity, **result))
        summary = dict(tasks=len(rows), passed=sum(row['passed'] for row in rows),
                       accepted_corrected_steps=sum(row['accepted_corrected_steps'] for row in rows),
                       evaluations=sum(row['evaluations'] for row in rows))
        result = dict(summary=summary, results=rows, completion=study.completion, observed_fits=0,
                      protected_reads=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = {'request': qualification, 'prepare': prepare, 'report': report}[parser.parse_args().action]
    print(json.dumps(action(Path.cwd()), sort_keys=True))
