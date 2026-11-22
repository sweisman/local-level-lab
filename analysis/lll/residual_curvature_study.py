# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated comparison of analytic and differenced residual curvature."""
import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

from .curvature_retry_study import CAP, CASES, FOLDER, RECOVERY, RECOVERY_RULE, STARTS, Control
from .curvature_retry_study import ID as PRIOR_ID, RESULT as PRIOR
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'residual-curvature-controls-v1'
SCOPE = 'Analytic and finite-difference curvature on the sealed generated box controls'
PLAN = FOLDER+'RESIDUAL_CURVATURE_CONTROLS_PLAN.md'
RESULT = FOLDER+'residual-curvature-controls-result.json'
REQUEST = FOLDER+'residual-curvature-controls-qualification.json'
XML = FOLDER+'residual-curvature-controls-tests.xml'
PRIOR_SHA = 'dc773f51ec820aaf767c9227d2c5211b1dc950ab48e3c8a0d00976e152177b16'
METHODS = ('analytic', 'differences')
TESTS = ('test_feasible_hessian_differences_match_coupled_quadratic',
         'test_bounded_hessian_step_obeys_face_and_radius')
TASKS = [dict(identity=f'{case}-{i}-{method}', input_key='design',
              payload=dict(case=case, start=i, method=method),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=CAP, bound_steps=0))
         for case in CASES for i in range(len(STARTS)) for method in METHODS]


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_residual_curvature_solver.py')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS,
            minimum_tests=4)
    return sources, environment


def prior_evidence(root):
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('the original generated outcomes are required')
    report = json.loads(raw)
    with closing(ClosedStudy(root, 'data/'+PRIOR_ID)) as study:
        if (report['completion'] != study.completion or len(report['tasks']) != 16
                or any(any(task[key] != value for key, value in study.envelope(task['identity'])['result'].items())
                       for task in report['tasks'])):
            raise ValueError('the sealed original outcomes must match')
    return report


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite curvature allowance')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    prior_evidence(root)
    inputs = dict(design=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=XML)
    for key, value in dict(recovery=recovery, recovery_tests=tests,
                           recovery_policy=encoded(RECOVERY_RULE)).items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=TASKS, workers=1, threads=1,
                                     maximum_wall_s=60), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .residual_curvature_solver import fit_candidate

    if (context.manifest['scope'] != SCOPE
            or {k: v for k, v in task.items() if k not in ('index', 'shard')} not in TASKS):
        raise ValueError('frozen residual curvature control required')
    context.input_path('design')
    case, start, method = (task['payload'][key] for key in ('case', 'start', 'method'))
    problem = Control(case, context.charge)

    def curvature(point, residual):
        return np.diag([2*problem.q*residual[0]-50*problem.bend*residual[1], 0.])

    fit = fit_candidate(problem, 'generated', start=STARTS[start], maximum_evaluations=CAP,
                        physical_step=lambda delta: delta.reshape((1, 3)),
                        analytic_curvature=curvature if method == 'analytic' else None)
    if fit['evaluations'] != problem.calls:
        raise ValueError('charged curvature evaluations differ')
    exact, cost = problem.exact_optimum()
    error = max(abs(a-b) for a, b in zip(fit['normalized_parameters'], exact, strict=True))
    gap = abs(fit['residual_sum_squares']-cost)
    verdict = dict(case=case, start=start, method=method, evaluations=problem.calls,
                   parameter_error=error, cost_gap=gap, fresh_position_passed=fit['converged'],
                   stop_reason=fit['stability_probe']['reason'],
                   passed=bool(fit['converged'] and error <= 1e-4 and gap <= 1e-7),
                   scientific_decision='abstain')
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
            study = original
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            envelope = study.envelope(identity)
            outcome = envelope['result']
            if envelope['status'] != 'complete' or outcome['evaluations'] != envelope['charged']['bound_calls']:
                raise ValueError('all declared curvature fit charges are required')
            study.artifact(identity, 'fit.json', raw=True)
            rows.append(dict(identity=identity, origin=origin, **outcome))
        counts = {method: sum(row['passed'] for row in rows if row['method'] == method)
                  for method in METHODS}
        summary = dict(passed=counts, qualified={method: count == 8 for method, count in counts.items()},
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
