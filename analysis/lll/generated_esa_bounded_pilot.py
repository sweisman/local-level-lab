# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated technical pilot for bound-aware complete-fit forecasts."""

import json
from pathlib import Path


ID = 'generated-esa-bounded-full-fit-v1-20261117'
PREFLIGHT_ID = ID + '-preflight'
SCOPE = ('two independent bound-aware generated complete fits; '
         'technical artifacts only; no original or protected aircraft input')
PREFLIGHT_SCOPE = 'one short bound-aware frozen-worker wiring check'
PLAN = 'docs/prediction-observed-development/BOUND_AWARE_GENERATED_PILOT_PLAN.md'
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'


def recipe():
    from .generated_esa_full_fit_innovation import recipe as base
    from .airquantumgrav_noisy_inputs import (noise_settings,
                                              rate_point_noise_settings)

    return dict(base(), version='generated-esa-bounded-full-fit-v1',
                noise_by_law=dict(increment=noise_settings(seed=610101),
                                  point=rate_point_noise_settings(seed=610102)),
                calibration_alpha=.025, future_alpha=.025)


def preflight_recipe():
    return dict(recipe(), version='generated-esa-bounded-preflight-v1',
                duration_s=10., queries=9, maximum_evaluations=8,
                workers=1, threads=1, maximum_wall_s=600.)


def tasks(r=None):
    from .structured_noisy_training import limits

    r = recipe() if r is None else r
    if (r not in (recipe(), preflight_recipe())
            or r['duration_s'] * r['rate_hz'] != round(
                r['duration_s'] * r['rate_hz'])):
        raise ValueError('exact bounded generated recipe required')
    preflight = r == preflight_recipe()
    laws = ('increment',) if preflight else ('increment', 'point')
    return [dict(identity='preflight-increment' if preflight else law,
                 input_key='recipe', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating',
                              latitude_deg=55., profile=False, start=0,
                              policy_id='reported-short-v1'),
                 limits=limits(r, law)[0]) for law in laws]


def bounded_training(**kwargs):
    from .airquantumgrav_prediction import train_and_forecast
    from .bounded_forecast_wrapper import evaluate as bounded

    ordinary = kwargs.get('forecast_error_diagnostic')
    save = kwargs.get('save')
    if not callable(ordinary) or not callable(save):
        raise ValueError('complete earlier-only forecast callback required')

    def extended(problem, point, forecast, *, theta, dv, dt, times, reserve):
        return bounded(ordinary, problem, point, forecast,
                       theta=theta, dv=dv, dt=dt, times=times,
                       reserve=reserve, save=save,
                       calibration_alpha=.025, future_alpha=.025,
                       rank_rtol=1e-10)

    return train_and_forecast(**dict(kwargs, forecast_error_diagnostic=extended))


def qualification_sources(root):
    from .studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_esa_bounded_pilot.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/lll/bounded_forecast_wrapper.py',
        'analysis/lll/bounded_aircraft_tangent.py',
        'analysis/tests/test_generated_esa_bounded_pilot.py',
        'analysis/tests/test_bounded_forecast_wrapper.py',
        'analysis/tests/test_bounded_aircraft_tangent.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_new_seeds_and_two_600_report_tasks_are_finite',
            'test_frozen_adapter_rejects_changed_task_before_work',
            'test_preflight_has_one_short_task_and_separate_identity',
            'test_wrapper_saves_complete_bound_before_returning_base_diagnostic',
            'test_wrapper_rejects_a_base_diagnostic_that_used_later_data',
            'test_boundary_tangent_returns_finite_earlier_only_intervals',
            'test_adapter_matches_independent_dense_conditional_calculation',
            'test_rejects_missing_calibration_column_or_outside_box')


def request_qualification(root, *, preflight=False, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources

    root = Path(root).resolve()
    stem = 'recovery' if recovery else 'preflight' if preflight else 'full'
    return request(root,
                   sources=recovery_sources(root) if recovery else
                           qualification_sources(root),
                   environment=runtime_environment() if recovery else
                               environment(),
                   output=QUALIFICATION_DIR + stem + '-bounded-request.json',
                   report=QUALIFICATION_DIR + stem + '-bounded-tests.xml')


def definition(root, *, preflight, inputs):
    r = preflight_recipe() if preflight else recipe()
    return dict(id=PREFLIGHT_ID if preflight else ID,
                scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                adapter='analysis/lll/generated_esa_bounded_pilot.py',
                sources=qualification_sources(root), inputs=dict(inputs),
                tasks=tasks(r), workers=r['workers'], threads=r['threads'],
                maximum_wall_s=r['maximum_wall_s'])


def prepare(root, *, preflight, qualification, recovery_qualification):
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
        raise ValueError('2 GiB free space required for bound-aware pilot')
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
        prior = verify_completion(root / 'data' / PREFLIGHT_ID)
        if (prior['state'] != 'complete' or prior['completed'] != 1
                or prior['passed'] is not True):
            raise ValueError('sealed bound-aware preflight required')
    name = PREFLIGHT_ID if preflight else ID
    base = root / 'data' / (name + '-inputs')
    if base.exists() or (root / 'data' / name).exists():
        raise ValueError('fresh finite bound-aware pilot required')
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
    from .structured_noisy_study import run_case

    preflight = context.manifest.get('scope') == PREFLIGHT_SCOPE
    r = preflight_recipe() if preflight else recipe()
    expected = {item['identity']: item for item in tasks(r)}
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') not in (SCOPE, PREFLIGHT_SCOPE)
            or declared != expected.get(task['identity'])):
        raise ValueError('unchanged finite bound-aware task required')
    if (json.loads(context.input_path('recipe').read_bytes()) != r
            or json.loads(context.input_path('environment').read_bytes()) !=
                environment()):
        raise ValueError('changed generated input or numerical environment')
    result = run_case(task, context, r=r, payload=task['payload'],
                      training_provider=bounded_training)
    key = f'artifacts/{task["identity"]}/bounded-physical.json'
    if key not in context.artifacts:
        raise ValueError('bound-aware artifact missing after complete fit')
    bounded = json.loads((context.root / key).read_bytes())
    if (bounded.get('retained_calibration_columns') != 26
            or bounded.get('training_epochs') != (6 if preflight else 600)
            or bounded.get('prediction_epochs') != (3 if preflight else 300)
            or bounded.get('later_observations_used') is not False
            or bounded.get('scientific_decision') != 'abstain'):
        raise ValueError('bound-aware artifact changed or incomplete')
    return dict(result, passed=True, bounded_technical_passed=True,
                original_prediction_passed=result['passed'],
                technical_pilot_only=True)


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
        short = args.action == 'prepare-preflight'
        result = prepare(args.root, preflight=short,
            qualification=QUALIFICATION_DIR +
                ('preflight-bounded-request.json' if short else
                 'full-bounded-request.json'),
            recovery_qualification=QUALIFICATION_DIR +
                'recovery-bounded-request.json')
    else:
        result = launch(args.root, preflight=args.action == 'run-preflight')
    print(result)


if __name__ == '__main__':
    main()
