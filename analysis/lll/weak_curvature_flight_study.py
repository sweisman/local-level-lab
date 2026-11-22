# SPDX-License-Identifier: AGPL-3.0-or-later
"""One native generated flight comparison with a sealed matched reference."""
import argparse
from contextlib import ExitStack, closing
from functools import partial
import json
from pathlib import Path

from . import centered_flight_solver_study as ref
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_solver_matrix_core import make_tasks
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .weak_tangent_curvature_study import ID as CONTROL_ID, RESULT as CONTROL, TASKS as CONTROL_TASKS


ID = 'weak-curvature-flight-v1'
SCOPE = 'One earlier-only generated flight test of weak-direction residual curvature'
KEY = 'sphere_rotating-header_elapsed'
BASE = ref.FOLDER
PLAN = BASE+'WEAK_CURVATURE_FLIGHT_PLAN.md'
RESULT = BASE+'weak-curvature-flight-result.json'
REQUEST = BASE+'weak-curvature-flight-qualification.json'
XML = BASE+'weak-curvature-flight-tests.xml'
REF_SHA = '17be711b9259d8fc5276e9ffd4796404992dc913e20cf8a082aa9b8a7c664786'
CONTROL_SHA = '0a2b4564dc75cb37da9a3d0ce62213dfa0a8143b8b3af22268f5cc1471e0efe5'
REF_IDENTITY = KEY+'-trust_v2-0'
RECOVERY_RULE = RECOVER | dict(maximum_wall_s=210)
TESTS = ('test_weak_flight_retains_the_exact_matched_work_limit',
         'test_weak_flight_solver_uses_native_residuals_and_original_physical_step')


def tasks(solver='weak_curvature'):
    return [task for task in make_tasks({KEY: ref.recipes()[KEY]}, solvers=(solver,))
            if task['payload']['start'] == 0]


def solve_native(problem, model, *, start, maximum_evaluations):
    from .ilvis0_solver_position import physical_residual_step
    from .residual_curvature_solver import fit_candidate

    fit = fit_candidate(problem, model, start=start, maximum_evaluations=maximum_evaluations,
                        physical_step=partial(physical_residual_step, problem),
                        strong_restoration=True, weak_curvature=True)
    return dict(fit, active_parameters=list(problem.bounds.active),
                maximum_evaluations=maximum_evaluations)


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_weak_curvature_flight.py',
             'analysis/lll/ilvis0_tangent.cpp', 'analysis/lll/ilvis0_noise_bridge.cpp')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS,
            minimum_tests=len(TESTS))
    return sources, environment


def baseline(root, stack):
    from .ilvis0_solver_matrix_report_core import case_from_study

    raw = (root/ref.RESULT).read_bytes()
    if digest(raw) != REF_SHA:
        raise ValueError('exact prior generated flight dispositions required')
    report = json.loads(raw)
    source = stack.enter_context(closing(ClosedStudy(root, 'data/'+ref.ID)))
    original = next(task for task in ref.tasks() if task['identity'] == REF_IDENTITY)
    if (source.completion['manifest_sha256'] != report['manifest_sha256']
            or source.input(KEY) != ref.recipes()[KEY] or original['limits'] != tasks()[0]['limits']):
        raise ValueError('the matched sealed recipe and allowance are required')
    result = case_from_study(source, REF_IDENTITY, original, total_epochs=ref.QUERIES,
                             training_epochs=ref.TRAINING)
    reported = next(row for row in report['fit_results'] if row['identity'] == REF_IDENTITY)
    if (not result.get('converged') or not result.get('physical_accuracy_passed')
            or any(value != result.get(key) for key, value in reported.items() if key != 'disposition')):
        raise ValueError('a complete matched reference forecast is required')
    return source, result


def prepare(root):
    sources, environment = qualification(root, verify=True)
    return prepare_flight(root, identity=ID, scope=SCOPE, plan=PLAN,
                          adapter=Path(__file__).relative_to(root).as_posix(), declared_tasks=tasks(),
                          sources=sources, environment=environment, request=REQUEST, xml=XML,
                          control_path=CONTROL, control_id=CONTROL_ID, control_sha=CONTROL_SHA,
                          control_tasks=CONTROL_TASKS)


def prepare_flight(root, *, identity, scope, plan, adapter, declared_tasks, sources, environment,
                   request, xml, control_path, control_id, control_sha, control_tasks):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/identity/'manifest.json').is_file():
        raise ValueError('retain the original finite flight allowance')
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    raw = (root/control_path).read_bytes()
    if digest(raw) != control_sha:
        raise ValueError('exact small-control report required')
    report = json.loads(raw)
    with ExitStack() as stack:
        source = stack.enter_context(closing(ClosedStudy(root, 'data/'+control_id)))
        if (report['completion'] != source.completion or not report['summary']['qualified']
                or not source.summary['passed']
                or set(source.rows) != {task['identity'] for task in control_tasks}):
            raise ValueError('all declared numerical software controls must pass')
        for task in control_tasks:
            if not source.envelope(task['identity'])['result']['passed']:
                raise ValueError('small-control disposition differs')
        reference, _ = baseline(root, stack)
        values = {KEY: reference.input(KEY, raw=True)}
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_RULE))
    inputs = dict(plan=plan, prior=ref.RESULT, controls=control_path, qualification=request, qualification_tests=xml)
    for key, value in values.items():
        filename = f'data/{identity}-inputs/{key}'
        _write_equal(root/filename, value)
        inputs[key] = filename
    return Definition.from_dict(dict(id=identity, scope=scope, adapter=adapter,
                                     inputs=inputs, sources=sources, tasks=declared_tasks, workers=1, threads=1,
                                     maximum_wall_s=210), root).prepare(root)['limits']


def evaluate(task, context):
    return evaluate_flight(task, context, scope=SCOPE, declared_tasks=tasks(), solver_provider=solve_native)


def evaluate_flight(task, context, *, scope, declared_tasks, solver_provider):
    from .airquantumgrav_prediction import train_and_forecast
    from .structured_noisy_study import run_case

    if (context.manifest['scope'] != scope
            or {k: v for k, v in task.items() if k not in ('index', 'shard')} not in declared_tasks):
        raise ValueError('only the declared earlier-only generated flight may run')
    key = task['input_key']
    recipe = ref.recipes()[key]
    if json.loads(context.input_path(key).read_bytes()) != recipe:
        raise ValueError('the exact matched flight recipe is required')
    payload = {k: v for k, v in task['payload'].items() if k not in ('solver', 'sensor_case')}
    outcome = run_case(task, context, r=recipe, payload=payload,
                       training_provider=partial(train_and_forecast, solver_provider=solver_provider))
    if (outcome.get('forecast_saved_before_scoring') is not True or outcome.get('training_epochs') != ref.TRAINING
            or outcome.get('prediction_epochs') != ref.QUERIES-ref.TRAINING
            or outcome.get('original_reads') != 0 or outcome.get('protected_reads') != 0):
        raise ValueError('a complete earlier-only generated forecast is required')
    physical = bool(outcome['accuracy_all_sections'])
    return dict(outcome, passed=bool(physical and outcome['converged']), technical_completion_only=True,
                physical_accuracy_passed=physical, solver=task['payload']['solver'],
                sensor_case=task['payload']['sensor_case'], scientific_decision='abstain')


def recover(root):
    return recover_flight(root, study_id=ID, task=tasks()[0])


def recover_flight(root, *, study_id, task):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+study_id
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVERY_RULE:
                raise ValueError('unchanged recovery policy required')
            identity = task['identity']
            if identity in study.rows and study.envelope(identity)['status'] == 'complete':
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVERY_RULE)
    return resume_campaign(root, continuation)


def report(root):
    return report_flight(root, study_id=ID, task=tasks()[0], destination=RESULT,
                         fit_statistic='weak_curvature_estimates', result_statistic='completed_weak_estimates')


def report_flight(root, *, study_id, task, destination, fit_statistic, result_statistic,
                  require_statistic=False):
    import numpy as np

    from .ilvis0_solver_matrix_report_core import case_from_study
    from .ilvis0_solver_position import physical_metric

    prefix = 'data/'+study_id
    identity = task['identity']
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        reference, old = baseline(root, stack)
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        source = original
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
        trial = (case_from_study(source, identity, task, total_epochs=ref.QUERIES, training_epochs=ref.TRAINING)
                 if identity in source.rows else dict(identity=identity, technical_error='no sealed trial'))
        later_error, cost_gap, probes, attempted = None, None, None, None
        if 'forecast' in trial:
            if reference.artifact(REF_IDENTITY, 'input-binding.json') != source.artifact(identity, 'input-binding.json'):
                raise ValueError('only the solver may change in a matched flight pair')
            old_path, new_path = (np.asarray(row['forecast'], float) for row in (old, trial))
            a, b = old_path[ref.TRAINING:], new_path[ref.TRAINING:]
            later_error = float(np.max(np.linalg.norm((a-b)*physical_metric(a), axis=1)))
            cost_gap = abs(trial['training_cost']-old['training_cost'])
            probes = source.artifact(identity, 'fit.json')[fit_statistic]
            attempted = trial['evaluations']
        elif identity in source.rows:
            names = {name.rsplit('/', 1)[-1] for name in source.envelope(identity)['artifacts']}
            attempted = ref._interrupted_training_attempts(source, identity, names)
        passed = bool(later_error is not None and later_error <= .1 and cost_gap <= .01
                      and trial['converged'] and trial['physical_accuracy_passed']
                      and (not require_statistic or probes > 0))
        summary = dict(qualified=passed, maximum_later_spread_m=later_error, absolute_training_cost_gap=cost_gap,
                       attempted_training_tangents=attempted, **{result_statistic: probes},
                       original_reads=0, protected_reads=0, scientific_decision='abstain')
        compact = [{k: v for k, v in row.items() if k != 'forecast'} for row in (old, trial)]
        _write_equal(root/destination, encoded(dict(summary=summary, cases=compact, completion=source.completion,
                                               charged=source.summary['charged'], reference_sha256=REF_SHA)))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
