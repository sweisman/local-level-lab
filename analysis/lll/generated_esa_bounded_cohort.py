# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite eight-case generated bound-aware full-path development cohort."""

import json
from pathlib import Path


ID = 'generated-esa-bounded-cohort-v1-20261117'
PREFLIGHT_ID = ID + '-preflight'
SCOPE = 'eight fresh known-answer generated bound-aware fits; no aircraft input'
PREFLIGHT_SCOPE = 'one short generated bound-aware cohort wiring check'
PLAN = 'docs/prediction-observed-development/GENERATED_BOUNDED_COHORT_PLAN.md'
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'
SEEDS = dict(increment=[630101, 630102, 630103, 630104],
             point=[630201, 630202, 630203, 630204])


def recipe():
    from .generated_esa_bounded_pilot_v2 import recipe as base

    return dict(version='generated-esa-bounded-cohort-v1', base=base(),
                seeds=SEEDS, workers=2, threads=1, maximum_wall_s=21600.)


def preflight_recipe():
    from .generated_esa_bounded_pilot_v2 import preflight_recipe as base

    return dict(version='generated-esa-bounded-cohort-preflight-v1',
                base=base(), seeds={'increment': [630000]}, workers=1,
                threads=1, maximum_wall_s=600.)


def case_recipe(law, seed, *, preflight):
    from .airquantumgrav_noisy_inputs import (noise_settings,
                                              rate_point_noise_settings)

    chosen = preflight_recipe() if preflight else recipe()
    if (law not in chosen['seeds'] or type(seed) is not int
            or seed not in chosen['seeds'][law]):
        raise ValueError('declared generated law and seed required')
    noise = dict(chosen['base']['noise_by_law'])
    noise[law] = (noise_settings if law == 'increment'
                  else rate_point_noise_settings)(seed=seed)
    return dict(chosen['base'], noise_by_law=noise)


def tasks(*, preflight=False):
    from .generated_esa_bounded_pilot_v2 import extra_limits
    from .structured_noisy_training import limits

    chosen = preflight_recipe() if preflight else recipe()
    result = []
    for law, seeds in chosen['seeds'].items():
        for seed in seeds:
            case = case_recipe(law, seed, preflight=preflight)
            base, _ = limits(case, law)
            native, packets = extra_limits(case['duration_s'], case['rate_hz'],
                                           case['queries'])
            allowance = dict(base, native_calls=base['native_calls'] + native,
                             packet_visits=base['packet_visits'] + packets)
            result.append(dict(identity=f'{law}-{seed}', input_key='recipe',
                               native_kind='tangent', seed=seed,
                               payload=dict(law=law, model='sphere_rotating',
                                            latitude_deg=55., profile=False,
                                            start=0, policy_id='reported-short-v1'),
                               limits=allowance))
    return result


def qualification_sources(root):
    from .studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_esa_bounded_cohort.py',
        'analysis/lll/generated_esa_bounded_pilot_v2.py',
        'analysis/lll/generated_esa_bounded_pilot.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/lll/bounded_forecast_wrapper.py',
        'analysis/lll/bounded_aircraft_tangent.py',
        'analysis/tests/test_generated_esa_bounded_cohort.py',
        'analysis/tests/test_generated_esa_bounded_pilot_v2.py',
        'analysis/tests/test_bounded_forecast_wrapper.py',
        'analysis/tests/test_bounded_aircraft_tangent.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_cohort_seeds_limits_and_threads_are_finite',
            'test_short_preflight_is_separate_and_finite',
            'test_changed_task_rejected_before_context_or_native_work',
            'test_extra_full_operator_pass_is_bounded',
            'test_wrapper_saves_complete_bound_before_returning_base_diagnostic',
            'test_wrapper_rejects_a_base_diagnostic_that_used_later_data',
            'test_boundary_tangent_returns_finite_earlier_only_intervals',
            'test_adapter_matches_independent_dense_conditional_calculation')


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
                   output=QUALIFICATION_DIR + stem + '-bounded-cohort-request.json',
                   report=QUALIFICATION_DIR + stem + '-bounded-cohort-tests.xml')


def definition(root, *, preflight, inputs):
    chosen = preflight_recipe() if preflight else recipe()
    return dict(id=PREFLIGHT_ID if preflight else ID,
                scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                adapter='analysis/lll/generated_esa_bounded_cohort.py',
                sources=qualification_sources(root), inputs=dict(inputs),
                tasks=tasks(preflight=preflight),
                workers=chosen['workers'], threads=chosen['threads'],
                maximum_wall_s=chosen['maximum_wall_s'])


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
    chosen = preflight_recipe() if preflight else recipe()
    if shutil.disk_usage(root).free < 2 * 1024**3:
        raise ValueError('2 GiB free space required for generated cohort')
    env = environment()
    if env['numerical_environment'] != thread_environment(
            workers=chosen['workers'], threads=1):
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
            raise ValueError('sealed generated cohort preflight required')
    name = PREFLIGHT_ID if preflight else ID
    base = root / 'data' / (name + '-inputs')
    if base.exists() or (root / 'data' / name).exists():
        raise ValueError('fresh finite generated cohort required')
    base.mkdir(parents=True)
    material = dict(recipe=encoded(chosen), environment=encoded(env),
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
    from .generated_esa_bounded_pilot_v2 import _run_case

    preflight = context.manifest.get('scope') == PREFLIGHT_SCOPE
    chosen = preflight_recipe() if preflight else recipe()
    expected = {item['identity']: item for item in tasks(preflight=preflight)}
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') not in (SCOPE, PREFLIGHT_SCOPE)
            or declared != expected.get(task['identity'])):
        raise ValueError('unchanged finite generated cohort task required')
    if (json.loads(context.input_path('recipe').read_bytes()) != chosen
            or json.loads(context.input_path('environment').read_bytes()) !=
                environment()):
        raise ValueError('changed generated recipe or numerical environment')
    law = task['payload']['law']
    case = case_recipe(law, task['seed'], preflight=preflight)
    result = _run_case(task, context, case)
    key = f'artifacts/{task["identity"]}/bounded-physical.json'
    if key not in context.artifacts:
        raise ValueError('complete bound artifact missing')
    bound = json.loads((context.root / key).read_bytes())
    if (bound.get('retained_calibration_columns') != 26
            or bound.get('training_epochs') != (6 if preflight else 600)
            or bound.get('prediction_epochs') != (3 if preflight else 300)
            or bound.get('later_observations_used') is not False
            or bound.get('scientific_decision') != 'abstain'):
        raise ValueError('generated cohort bound changed or incomplete')
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
                ('preflight-bounded-cohort-request.json' if short else
                 'full-bounded-cohort-request.json'),
            recovery_qualification=QUALIFICATION_DIR +
                'recovery-bounded-cohort-request.json')
    else:
        result = launch(args.root, preflight=args.action == 'run-preflight')
    print(result)


if __name__ == '__main__':
    main()
