# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated 600-report nonlinear fitted-innovation pilot."""

import json
from pathlib import Path

from .structured_noisy_study import run_case


ID = 'generated-esa-600-innovation-null-v1-20261117'
PREFLIGHT_ID = ID + '-preflight'
SCOPE = ('two independent known-answer 600-report complete fits; '
         'no original or protected aircraft input')
PREFLIGHT_SCOPE = 'one short frozen-worker generated innovation wiring check'
PLAN = 'docs/prediction-observed-development/FULL_FIT_INNOVATION_NULL_PLAN.md'
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'


def recipe():
    from .airquantumgrav_noisy_inputs import (noise_settings,
                                              rate_point_noise_settings)
    from .structured_noisy_training import recipe as shared

    return dict(shared(), version='generated-esa-full-fit-innovation-v1',
                duration_s=900., rate_hz=300, queries=900,
                query_start_s=.5, query_step_s=1.,
                models=['sphere_rotating'], latitudes_deg=[55.],
                profiles=[False], starts=1, maximum_evaluations=200,
                noise_by_law=dict(increment=noise_settings(seed=600101),
                                  point=rate_point_noise_settings(seed=600102)),
                sensor_case='interior', clock='header_elapsed',
                workers=2, threads=1, maximum_wall_s=21600.,
                scientific_decision='abstain')


def preflight_recipe():
    return dict(recipe(), version='generated-esa-full-fit-innovation-preflight-v1',
                duration_s=10., queries=9, maximum_evaluations=8,
                workers=1, threads=1, maximum_wall_s=600.)


def tasks(r=None):
    from .structured_noisy_training import limits

    r = recipe() if r is None else r
    if (r not in (recipe(), preflight_recipe())
            or r['duration_s'] * r['rate_hz'] != round(
                r['duration_s'] * r['rate_hz'])):
        raise ValueError('exact bounded full or preflight recipe required')
    laws = ('increment',) if r == preflight_recipe() else ('increment', 'point')
    return [dict(identity='preflight-increment' if r == preflight_recipe()
                 else law, input_key='recipe', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating',
                              latitude_deg=55., profile=False, start=0,
                              policy_id='reported-short-v1'),
                 limits=limits(r, law)[0]) for law in laws]


def preflight_task():
    return tasks(preflight_recipe())[0]


def qualification_sources(root):
    from .studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_esa_full_fit_innovation.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/tests/test_generated_esa_full_fit_innovation.py',
        'analysis/tests/test_structured_noisy_study.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_full_pilot_has_two_600_report_tasks_and_finite_limits',
            'test_evaluator_refuses_changed_task_before_shared_worker',
            'test_frozen_definition_counts_preflight_and_full',
            'test_preflight_pass_means_artifacts_even_if_short_fit_does_not_converge',
            'test_cli_passes_project_relative_qualification_paths',
            'test_worker_prepays_native_work_and_keeps_construction_separate',
            'test_worker_preserves_prepayment_and_artifacts_after_failure')


def request_qualification(root, *, preflight=False, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources

    root = Path(root).resolve()
    stem = ('recovery' if recovery else
            'preflight-v2' if preflight else 'full')
    return request(root,
                   sources=recovery_sources(root) if recovery else
                           qualification_sources(root),
                   environment=runtime_environment() if recovery else
                               environment(),
                   output=QUALIFICATION_DIR + stem + '-innovation-request.json',
                   report=QUALIFICATION_DIR + stem + '-innovation-tests.xml')


def definition(root, *, preflight, inputs):
    r = preflight_recipe() if preflight else recipe()
    return dict(id=PREFLIGHT_ID if preflight else ID,
                scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                adapter='analysis/lll/generated_esa_full_fit_innovation.py',
                sources=qualification_sources(root), inputs=dict(inputs),
                tasks=tasks(r), workers=r['workers'], threads=r['threads'],
                maximum_wall_s=r['maximum_wall_s'])


def prepare(root, *, preflight, qualification, recovery_qualification):
    if qualification is None or recovery_qualification is None:
        raise ValueError('software and recovery qualification required')
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment, verify_completion
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import (
        qualification_sources as recovery_sources,
        REQUIRED_TESTS as recovery_tests)

    root = Path(root).resolve()
    r = preflight_recipe() if preflight else recipe()
    if shutil.disk_usage(root).free < 2 * 1024**3:
        raise ValueError('2 GiB free space required for generated pilot')
    env = environment()
    if env['numerical_environment'] != thread_environment(
            workers=r['workers'], threads=1):
        raise ValueError('guarded declared numerical allocation required')
    source_request, source_report = checked(
        root, qualification, sources=qualification_sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=runtime_environment(), required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    if not preflight:
        preflight_result = verify_completion(root / 'data' / PREFLIGHT_ID)
        if (preflight_result['state'] != 'complete'
                or preflight_result['completed'] != 1
                or preflight_result['passed'] is not True):
            raise ValueError('sealed frozen-worker preflight required')
    name = PREFLIGHT_ID if preflight else ID
    base = root / 'data' / (name + '-inputs')
    if base.exists() or (root / 'data' / name).exists():
        raise ValueError('fresh finite generated pilot required')
    base.mkdir(parents=True)
    material = dict(recipe=encoded(r), environment=encoded(env),
                    qualification_request=source_request,
                    qualification_report=source_report,
                    recovery_request=recovery_request,
                    recovery_report=recovery_report)
    inputs = {}
    for key, raw in material.items():
        path = base / key
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    frozen = definition(root, preflight=preflight, inputs=inputs)
    atomic(base / 'definition.json', encoded(frozen))
    manifest = Definition.from_dict(frozen, root).prepare(root)
    return dict(path='data/' + name, tasks=len(frozen['tasks']),
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    from .airquantumgrav_inventory import environment

    preflight = context.manifest.get('scope') == PREFLIGHT_SCOPE
    r = preflight_recipe() if preflight else recipe()
    expected = {item['identity']: item for item in tasks(r)}
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') not in (SCOPE, PREFLIGHT_SCOPE)
            or declared != expected.get(task['identity'])):
        raise ValueError('unchanged finite generated task required')
    if (json.loads(context.input_path('recipe').read_bytes()) != r
            or json.loads(context.input_path('environment').read_bytes()) !=
                environment()):
        raise ValueError('changed generated input or numerical environment')
    result = run_case(task, context, r=r, payload=task['payload'])
    if preflight:
        if (result.get('forecast_saved_before_scoring') is not True
                or result.get('training_epochs') != 6
                or result.get('prediction_epochs') != 3
                or result.get('scientific_decision') != 'abstain'):
            raise ValueError('short frozen worker did not complete artifacts')
        return dict(result, passed=True, preflight_only=True,
                    original_prediction_passed=result['passed'])
    return result


def launch(root, *, preflight=False):
    from .ilvis0_control_shards import launch as run_study

    name = PREFLIGHT_ID if preflight else ID
    return run_study(Path(root).resolve() / 'data' / name,
                     reserved_threads=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request-preflight', 'request-full',
                        'request-recovery', 'prepare-preflight', 'prepare-full',
                        'run-preflight', 'run-full'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request-preflight':
        result = request_qualification(args.root, preflight=True)
    elif args.action == 'request-full':
        result = request_qualification(args.root)
    elif args.action == 'request-recovery':
        result = request_qualification(args.root, recovery=True)
    elif args.action in ('prepare-preflight', 'prepare-full'):
        preflight = args.action == 'prepare-preflight'
        result = prepare(args.root, preflight=preflight,
            qualification=QUALIFICATION_DIR + (
                'preflight-v2-innovation-request.json' if preflight else
                'full-innovation-request.json'),
            recovery_qualification=QUALIFICATION_DIR +
                'recovery-innovation-request.json')
    else:
        result = launch(args.root, preflight=args.action == 'run-preflight')
    print(result)


if __name__ == '__main__':
    main()
