# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh bound-aware pilot with an explicit second full operator reserve."""

import json
from pathlib import Path


ID = 'generated-esa-bounded-full-fit-v2-20261117'
PREFLIGHT_ID = ID + '-preflight'
SCOPE = ('two fresh bound-aware generated fits with extra operator reserve; '
         'technical artifacts only; no original or protected aircraft input')
PREFLIGHT_SCOPE = 'one short bound-aware extra-reserve frozen-worker check'
PLAN = 'docs/prediction-observed-development/BOUND_AWARE_GENERATED_PILOT_V2_PLAN.md'
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'


def recipe():
    from .generated_esa_bounded_pilot import recipe as base
    from .airquantumgrav_noisy_inputs import (noise_settings,
                                              rate_point_noise_settings)

    return dict(base(), version='generated-esa-bounded-full-fit-v2',
                noise_by_law=dict(increment=noise_settings(seed=620101),
                                  point=rate_point_noise_settings(seed=620102)))


def preflight_recipe():
    return dict(recipe(), version='generated-esa-bounded-preflight-v2',
                duration_s=10., queries=9, maximum_evaluations=8,
                workers=1, threads=1, maximum_wall_s=600.)


def extra_limits(duration_s, rate_hz, queries):
    if (not isinstance(duration_s, (int, float)) or duration_s <= 0
            or type(rate_hz) is not int or rate_hz <= 0
            or type(queries) is not int or queries <= 0
            or duration_s * rate_hz != round(duration_s * rate_hz)):
        raise ValueError('exact positive packet and query counts required')
    count = round(duration_s * rate_hz) + queries
    return count, count


def tasks(r=None):
    from .structured_noisy_training import limits

    r = recipe() if r is None else r
    if r not in (recipe(), preflight_recipe()):
        raise ValueError('exact revised bounded recipe required')
    preflight = r == preflight_recipe()
    native, packets = extra_limits(r['duration_s'], r['rate_hz'], r['queries'])
    laws = ('increment',) if preflight else ('increment', 'point')
    result = []
    for law in laws:
        allowance = dict(limits(r, law)[0])
        allowance['native_calls'] += native
        allowance['packet_visits'] += packets
        result.append(dict(identity='preflight-increment' if preflight else law,
                           input_key='recipe', native_kind='tangent',
                           payload=dict(law=law, model='sphere_rotating',
                                        latitude_deg=55., profile=False,
                                        start=0, policy_id='reported-short-v1'),
                           limits=allowance))
    return result


def qualification_sources(root):
    from .studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_esa_bounded_pilot_v2.py',
        'analysis/lll/generated_esa_bounded_pilot.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/lll/bounded_forecast_wrapper.py',
        'analysis/lll/bounded_aircraft_tangent.py',
        'analysis/tests/test_generated_esa_bounded_pilot_v2.py',
        'analysis/tests/test_generated_esa_bounded_pilot.py',
        'analysis/tests/test_bounded_forecast_wrapper.py',
        'analysis/tests/test_bounded_aircraft_tangent.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_fresh_seeds_and_explicit_preflight_reserve',
            'test_extra_full_operator_pass_is_bounded',
            'test_changed_task_is_rejected_before_native_work',
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
                   output=QUALIFICATION_DIR + stem + '-bounded-v2-request.json',
                   report=QUALIFICATION_DIR + stem + '-bounded-v2-tests.xml')


def definition(root, *, preflight, inputs):
    r = preflight_recipe() if preflight else recipe()
    return dict(id=PREFLIGHT_ID if preflight else ID,
                scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                adapter='analysis/lll/generated_esa_bounded_pilot_v2.py',
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
        raise ValueError('2 GiB free space required for revised bounded pilot')
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
            raise ValueError('sealed revised bound-aware preflight required')
    name = PREFLIGHT_ID if preflight else ID
    base = root / 'data' / (name + '-inputs')
    if base.exists() or (root / 'data' / name).exists():
        raise ValueError('fresh revised bound-aware pilot required')
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
    from .structured_noisy_study import _kernels
    from .structured_noisy_training import calculate, limits
    from .generated_esa_bounded_pilot import bounded_training
    from .ilvis0_control_shards import _check_continue
    from .studies.artifacts import digest
    from .studies.journal import Journal
    from .airquantumgrav_inventory import environment

    identity = task['identity']
    native, packets = extra_limits(r['duration_s'], r['rate_hz'], r['queries'])
    base, construction = limits(r, task['payload']['law'])
    if (task['limits']['native_calls'] != base['native_calls'] + native
            or task['limits']['packet_visits'] != base['packet_visits'] + packets
            or any(task['limits'][key] != base[key]
                   for key in ('bound_calls', 'bound_steps'))):
        raise ValueError('revised bound-aware task allowance differs')
    journal = Journal(context.directory / 'construction.sqlite',
                      freeze=digest((context.root / 'manifest.json').read_bytes()),
                      limits={identity: construction})
    journal.start(identity)
    budget = None

    def reserve_construction(**work):
        _check_continue(context.root, context.manifest)
        for key, value in work.items():
            journal.reserve(identity, key, value)

    try:
        noise, factory = _kernels(context, environment())
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                                   packet_visits=task['limits']['packet_visits']) as budget:
            result = calculate(task['payload'], r, kernel_factory=factory,
                               noise_kernel=noise, reserve=budget.reserve,
                               reserve_construction=reserve_construction,
                               save=context.save,
                               check_continue=lambda: _check_continue(
                                   context.root, context.manifest),
                               training_provider=bounded_training)
        journal.verify()
        if (any(journal.count(identity, key) != value
                for key, value in construction.items())
                or result['native_calls'] !=
                    budget.snapshot()['attempted']['native_calls']):
            raise ValueError('revised native and construction charges differ')
        return dict(result, **construction)
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def evaluate(task, context):
    from .airquantumgrav_inventory import environment

    preflight = context.manifest.get('scope') == PREFLIGHT_SCOPE
    r = preflight_recipe() if preflight else recipe()
    expected = {item['identity']: item for item in tasks(r)}
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') not in (SCOPE, PREFLIGHT_SCOPE)
            or declared != expected.get(task['identity'])):
        raise ValueError('unchanged finite revised bound-aware task required')
    if (json.loads(context.input_path('recipe').read_bytes()) != r
            or json.loads(context.input_path('environment').read_bytes()) !=
                environment()):
        raise ValueError('changed generated input or numerical environment')
    result = _run_case(task, context, r)
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
                ('preflight-bounded-v2-request.json' if short else
                 'full-bounded-v2-request.json'),
            recovery_qualification=QUALIFICATION_DIR +
                'recovery-bounded-v2-request.json')
    else:
        result = launch(args.root, preflight=args.action == 'run-preflight')
    print(result)


if __name__ == '__main__':
    main()
