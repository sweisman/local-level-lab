# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated pilot for matched physical and receiver forecast bounds."""

import json
from pathlib import Path


ID = 'generated-esa-dual-target-v1-20261117'
PREFLIGHT_ID = ID + '-preflight'
SCOPE = ('two fresh generated dual-target fits; technical artifacts only; '
         'no original or protected aircraft input')
PREFLIGHT_SCOPE = 'one short generated dual-target frozen-worker check'
PLAN = 'docs/prediction-observed-development/DUAL_TARGET_GENERATED_PILOT_PLAN.md'
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'


def recipe():
    from .generated_esa_bounded_pilot_v2 import recipe as base
    from .airquantumgrav_noisy_inputs import noise_settings, rate_point_noise_settings
    return dict(base(), version='generated-esa-dual-target-v1',
                noise_by_law=dict(increment=noise_settings(seed=650101),
                                  point=rate_point_noise_settings(seed=650102)))


def preflight_recipe():
    from .airquantumgrav_noisy_inputs import noise_settings
    r = recipe()
    return dict(r, version='generated-esa-dual-target-preflight-v1',
                duration_s=10., queries=9, maximum_evaluations=8,
                noise_by_law=dict(r['noise_by_law'], increment=noise_settings(seed=650000)),
                workers=1, threads=1, maximum_wall_s=600.)


def tasks(r=None):
    from .structured_noisy_study import extra_forecast_work
    from .structured_noisy_training import limits
    r = recipe() if r is None else r
    if r not in (recipe(), preflight_recipe()):
        raise ValueError('exact dual-target recipe required')
    preflight = r == preflight_recipe()
    result = []
    for law in (('increment',) if preflight else ('increment', 'point')):
        allowance = dict(limits(r, law)[0])
        for key, value in extra_forecast_work(r, 3).items():
            allowance[key] += value
        result.append(dict(identity='preflight-increment' if preflight else law,
                           input_key='recipe', native_kind='tangent',
                           payload=dict(law=law, model='sphere_rotating',
                                        latitude_deg=55., profile=False,
                                        start=0, policy_id='reported-short-v1'),
                           limits=allowance))
    return result


def dual_training(**kwargs):
    from .airquantumgrav_prediction import train_and_forecast
    from .dual_target_forecast_wrapper import evaluate as dual
    from .ilvis0_native_error_training import ForecastErrorDiagnostic
    physical = kwargs.get('forecast_error_diagnostic')
    save = kwargs.get('save')
    if (not isinstance(physical, ForecastErrorDiagnostic)
            or physical.target != 'physical_position' or not callable(save)):
        raise ValueError('complete physical forecast and saving callback required')
    receiver = ForecastErrorDiagnostic(
        physical.factory, target='receiver_measurement',
        receiver_transform_policy=physical.policy,
        bound_margin=physical.bound_margin, rank_rtol=physical.rank_rtol,
        estimability_rtol=physical.estimability_rtol,
        estimability_atol=physical.estimability_atol)

    def extended(problem, point, forecast, *, theta, dv, dt, times, reserve):
        return dual(physical, receiver, problem, point, forecast,
                    theta=theta, dv=dv, dt=dt, times=times,
                    reserve=reserve, save=save, calibration_alpha=.025,
                    future_alpha=.025, rank_rtol=1e-10)

    return train_and_forecast(**dict(kwargs, forecast_error_diagnostic=extended))


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_esa_dual_target_pilot.py',
        'analysis/lll/dual_target_forecast_wrapper.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/tests/test_generated_esa_dual_target_pilot.py',
        'analysis/tests/test_dual_target_forecast_wrapper.py',
        'analysis/tests/test_structured_noisy_study.py',
        'analysis/tests/test_bounded_forecast_wrapper.py',
        'analysis/tests/test_bounded_aircraft_tangent.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_dual_target_tasks_have_exact_four_operator_passes',
            'test_changed_task_rejected_before_work',
            'test_training_provider_uses_same_factory_for_both_targets',
            'test_artifact_gate_requires_both_targets',
            'test_shared_runner_prepays_exact_three_extra_forecast_passes',
            'test_extra_pass_reserve_rejects_changed_task_before_construction',
            'test_both_targets_are_saved_before_wrapper_returns',
            'test_receiver_failure_prevents_return_to_later_truth',
            'test_boundary_tangent_returns_finite_earlier_only_intervals',
            'test_adapter_matches_independent_dense_conditional_calculation')


def request_qualification(root, *, preflight=False, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources
    root = Path(root).resolve()
    stem = 'recovery' if recovery else 'preflight' if preflight else 'full'
    return request(root, sources=recovery_sources(root) if recovery else
                   qualification_sources(root),
                   environment=runtime_environment() if recovery else environment(),
                   output=QUALIFICATION_DIR + stem + '-dual-target-v2-request.json',
                   report=QUALIFICATION_DIR + stem + '-dual-target-v2-tests.xml')


def definition(root, *, preflight, inputs):
    r = preflight_recipe() if preflight else recipe()
    return dict(id=PREFLIGHT_ID if preflight else ID,
                scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                adapter='analysis/lll/generated_esa_dual_target_pilot.py',
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
        qualification_sources as recovery_sources, REQUIRED_TESTS as recovery_tests)
    root = Path(root).resolve()
    r = preflight_recipe() if preflight else recipe()
    if shutil.disk_usage(root).free < 2 * 1024**3:
        raise ValueError('2 GiB free space required for dual-target pilot')
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
            raise ValueError('sealed dual-target preflight required')
    name = PREFLIGHT_ID if preflight else ID
    base = root / 'data' / (name + '-inputs')
    if base.exists() or (root / 'data' / name).exists():
        raise ValueError('fresh finite dual-target pilot required')
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


def _run_case(task, context, r):
    from .structured_noisy_study import run_case
    return run_case(task, context, r=r, payload=task['payload'],
                    training_provider=dual_training, extra_forecast_passes=3)


def evaluate(task, context):
    from .airquantumgrav_inventory import environment
    preflight = context.manifest.get('scope') == PREFLIGHT_SCOPE
    r = preflight_recipe() if preflight else recipe()
    expected = {item['identity']: item for item in tasks(r)}
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') not in (SCOPE, PREFLIGHT_SCOPE)
            or declared != expected.get(task['identity'])):
        raise ValueError('unchanged finite dual-target task required')
    if (json.loads(context.input_path('recipe').read_bytes()) != r
            or json.loads(context.input_path('environment').read_bytes()) !=
                environment()):
        raise ValueError('changed generated input or numerical environment')
    result = _run_case(task, context, r)
    prefix = f'artifacts/{task["identity"]}/'
    needed = ('bounded-physical.json', 'bounded-receiver.json',
              'receiver-forecast-error-diagnostic.json')
    if not all(prefix + name in context.artifacts for name in needed):
        raise ValueError('both target bounds and receiver diagnostic required')
    physical, receiver, ordinary = (
        json.loads((context.root / (prefix + name)).read_bytes()) for name in needed)
    m, future = (6, 3) if preflight else (600, 300)
    for target, bounded in (('physical_position', physical),
                            ('receiver_measurement', receiver)):
        if (bounded.get('prediction_target') != target
                or bounded.get('retained_calibration_columns') != 26
                or bounded.get('training_epochs') != m
                or bounded.get('prediction_epochs') != future
                or bounded.get('later_observations_used') is not False
                or bounded.get('scientific_decision') != 'abstain'):
            raise ValueError('both target bounds must be complete and earlier-only')
    if (ordinary.get('prediction_target') != 'receiver_measurement'
            or ordinary.get('later_observations_used') is not False
            or ordinary.get('training_epochs') != m
            or ordinary.get('prediction_epochs') != future):
        raise ValueError('receiver target diagnostic incomplete')
    return dict(result, passed=True, dual_target_technical_passed=True,
                original_prediction_passed=result['passed'],
                technical_pilot_only=True)


def launch(root, *, preflight=False):
    from .ilvis0_control_shards import launch as run_study
    name = PREFLIGHT_ID if preflight else ID
    return run_study(Path(root).resolve() / 'data' / name, reserved_threads=0)


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
                ('preflight-dual-target-v2-request.json' if short else
                 'full-dual-target-v2-request.json'),
            recovery_qualification=QUALIFICATION_DIR +
                'recovery-dual-target-v2-request.json')
    else:
        result = launch(args.root, preflight=args.action == 'run-preflight')
    print(result)


if __name__ == '__main__':
    main()
