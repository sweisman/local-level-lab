# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare direct residual changes with sealed generated curvature controls."""
import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

from .ilvis0_matched_observed_inputs import _write_equal
from .residual_curvature_study import (
    CAP, FOLDER, METHODS, RECOVERY, RECOVERY_RULE, STARTS, TASKS, Control,
)
from .residual_curvature_study import ID as PRIOR_ID, RESULT as PRIOR
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'direct-residual-change-v1'
SCOPE = 'Direct residual increments on the unchanged generated curvature controls'
PLAN = FOLDER+'DIRECT_RESIDUAL_CHANGE_PLAN.md'
RESULT = FOLDER+'direct-residual-change-result.json'
REQUEST = FOLDER+'direct-residual-change-qualification.json'
XML = FOLDER+'direct-residual-change-tests.xml'
PRIOR_SHA = 'fd62f0880a673ef4200644312dda23ebd695578d18326abdc50b28b2db5960fb'
TESTS = ('test_direct_increment_preserves_an_improvement_below_rounding',
         'test_direct_generated_residual_change_matches_exact_formula')


def control_increment(problem, before, after):
    x, y = before
    u, v = after
    dx = u-x
    return (problem.q*dx*((x-problem.tx)+(u-problem.tx)),
            25*((v-y)-problem.bend*dx*((x-problem.x_opt)+(u-problem.x_opt))),
            problem.slope*dx)


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_direct_residual_change.py')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS,
            minimum_tests=len(TESTS))
    return sources, environment


def matched_outcomes(root, path, sha, study_id, *, tasks=TASKS):
    raw = (root/path).read_bytes()
    if digest(raw) != sha:
        raise ValueError('unchanged curvature report required')
    report = json.loads(raw)
    with closing(ClosedStudy(root, 'data/'+study_id)) as study:
        identities = {task['identity'] for task in tasks}
        if (report['completion'] != study.completion or len(report['tasks']) != len(identities)
                or {row['identity'] for row in report['tasks']} != identities):
            raise ValueError('unchanged complete curvature evidence required')
        for row in report['tasks']:
            immutable = study.envelope(row['identity'])['result']
            if any(row[key] != value for key, value in immutable.items()):
                raise ValueError('prior generated disposition differs')
    return {row['identity']: row for row in report['tasks']}


def original_outcomes(root):
    return matched_outcomes(root, PRIOR, PRIOR_SHA, PRIOR_ID)


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the finite direct-residual allowance')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    original_outcomes(root)
    inputs = dict(design=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=XML)
    for key, value in dict(recovery=recovery, recovery_tests=tests,
                           recovery_policy=encoded(RECOVERY_RULE)).items():
        filename = f'data/{ID}-inputs/{key}'
        _write_equal(root/filename, value)
        inputs[key] = filename
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=TASKS, workers=1, threads=1,
                                     maximum_wall_s=60), root).prepare(root)['limits']


def evaluate(task, context):
    if (context.manifest['scope'] != SCOPE
            or {k: v for k, v in task.items() if k not in ('index', 'shard')} not in TASKS):
        raise ValueError('frozen direct-residual control required')
    return fit_control(task, context)


def fit_control(task, context, *, strong_restoration=False, weak_curvature=False, secant_curvature=False):
    import numpy as np

    from .residual_curvature_solver import fit_candidate

    context.input_path('design')
    case, start, method = (task['payload'][key] for key in ('case', 'start', 'method'))
    problem = Control(case, context.charge)

    def curvature(_, residual):
        return np.diag([2*problem.q*residual[0]-50*problem.bend*residual[1], 0.])

    fit = fit_candidate(problem, 'generated', start=STARTS[start], maximum_evaluations=CAP,
                        physical_step=lambda delta: delta.reshape((1, 3)),
                        analytic_curvature=curvature if method == 'analytic' else None,
                        residual_change=lambda old, new: control_increment(problem, old, new),
                        strong_restoration=strong_restoration, weak_curvature=weak_curvature,
                        secant_curvature=secant_curvature)
    if fit['evaluations'] != problem.calls:
        raise ValueError('charged direct-change evaluations differ')
    expected, cost = problem.exact_optimum()
    error = max(abs(a-b) for a, b in zip(fit['normalized_parameters'], expected, strict=True))
    gap = abs(fit['residual_sum_squares']-cost)
    recovered = sum(row['accepted'] and row['rounded_residual_reduction'] <= 0 for row in fit['step_history'])
    verdict = dict(case=case, start=start, method=method, evaluations=problem.calls,
                   parameter_error=error, cost_gap=gap, fresh_position_passed=fit['converged'],
                   accepted_at_rounded_plateau=recovered, stop_reason=fit['stability_probe']['reason'],
                   passed=bool(fit['converged'] and error <= 1e-4 and gap <= 1e-7),
                   scientific_decision='abstain')
    if strong_restoration:
        rows = [row for row in fit['step_history'] if row.get('strong_restoration')]
        verdict.update(restoration_trials=len(rows), restoration_accepts=sum(row['accepted'] for row in rows))
    if weak_curvature:
        verdict['weak_curvature_estimates'] = fit['weak_curvature_estimates']
    if secant_curvature:
        fresh = 1+int('actual_cost_change' in fit['stability_probe'])
        if fit['evaluations'] != 1+len(fit['step_history'])+fresh:
            raise ValueError('secant curvature must use only initial, trial and fresh evaluations')
        verdict.update(secant_curvature_updates=fit['secant_curvature_updates'],
                       separate_derivative_probes=0)
    context.save('fit.json', fit)
    return verdict


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVERY_RULE:
                raise ValueError('unchanged recovery policy required')
            if all(key in study.rows and study.envelope(key)['status'] == 'complete' for key in study.tasks):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVERY_RULE)
    return resume_campaign(root, continuation)


def report(root):
    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    prior = original_outcomes(root)
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        selected = {}
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            selected = inspect(root, continuation)['selected']
        rows = []
        for task in TASKS:
            identity = task['identity']
            origin = selected.get(identity, {}).get('origin', prefix)
            source = original
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            envelope = source.envelope(identity)
            outcome = envelope['result']
            if envelope['status'] != 'complete' or outcome['evaluations'] != envelope['charged']['bound_calls']:
                raise ValueError('all direct-change fit charges are required')
            source.artifact(identity, 'fit.json', raw=True)
            rows.append(dict(identity=identity, origin=origin, prior_passed=prior[identity]['passed'], **outcome))
        counts = {method: sum(row['passed'] for row in rows if row['method'] == method)
                  for method in METHODS}
        summary = dict(passed=counts, qualified={method: count == 8 for method, count in counts.items()},
                       accepted_at_rounded_plateau=sum(row['accepted_at_rounded_plateau'] for row in rows),
                       observed_fits=0, protected_reads=0)
        _write_equal(root/RESULT, encoded(dict(summary=summary, tasks=rows, completion=original.completion,
                                               original_outcome_sha256=PRIOR_SHA)))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
