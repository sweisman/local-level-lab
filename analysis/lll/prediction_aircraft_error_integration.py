# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated-aircraft integration matrix with explicit abstention."""
import itertools
import json
from pathlib import Path


IDENTITY = 'prediction-aircraft-error-integration-20261111'
SCOPE = ('48 generated two-second pipeline controls; fixed oracle error law, '
         'two withheld targets; no observed/protected inputs or calibrated decision')


def recipe():
    from lll.structured_noisy_training import recipe as base
    from lll.airquantumgrav_noisy_inputs import noise_settings, rate_point_noise_settings
    return dict(base(), version='prediction-aircraft-error-integration-v1',
                duration_s=2., rate_hz=200, queries=9, query_start_s=.1,
                query_step_s=.2, maximum_evaluations=8,
                models=['sphere_rotating', 'sphere_still', 'flat_still'],
                profiles=[False, True], input_laws=['increment', 'point'],
                sensor_cases=['interior', 'z_gyro_boundary'],
                clock_cases=['nominal_200Hz', 'header_jitter'],
                noise_by_law=dict(increment=noise_settings(seed=71),
                                  point=rate_point_noise_settings(seed=71)),
                header_jitter_amplitude_s=.0004, header_jitter_cycles=19,
                workers=4, threads=1, maximum_wall_s=1800.,
                prediction_targets=['physical_position', 'receiver_measurement'],
                scientific_decision='abstain')


def construction_limits(r, law):
    from lll.airquantumgrav_noisy_inputs import construction_limits as base
    if law not in r['input_laws']:
        raise ValueError('declared IMU input-error law required')
    result = base(dict(r, noise=r['noise_by_law'][law]))
    result['generated_samples'] += r['queries']
    result['noise_normal_variates'] += 3*r['queries']*2+6
    return result


def tasks(r=None):
    r = recipe() if r is None else r
    if (r['rate_hz'] != 200 or r['duration_s'] != 2. or r['queries'] != 9 or
            r['maximum_evaluations'] != 8 or
            r['clock_cases'] != ['nominal_200Hz', 'header_jitter']):
        raise ValueError('exact finite integration matrix required')
    result = []
    for model, profile, law, sensor, clock in itertools.product(
            r['models'], r['profiles'], r['input_laws'],
            r['sensor_cases'], r['clock_cases']):
        identity = f'{model}-{int(profile)}-{law}-{sensor}-{clock}'
        result.append(dict(identity=identity, input_key='recipe',
                           native_kind='tangent',
                           payload=dict(model=model, latitude_deg=55.,
                                        profile=profile, start=0,
                                        policy_id='reported-short-v1', law=law,
                                        sensor_case=sensor, clock_case=clock),
                           limits=dict(native_calls=2000, packet_visits=20000,
                                       bound_calls=0, bound_steps=0)))
    if len(result) != 48 or len({item['identity'] for item in result}) != 48:
        raise ValueError('complete unique 48-case matrix required')
    return result


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_aircraft_error_integration.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/airquantumgrav_dual_target_prediction.py',
        'analysis/lll/airquantumgrav_clock_disturbance.py',
        'analysis/tests/test_prediction_aircraft_error_integration.py',
        'analysis/tests/test_airquantumgrav_dual_target_native.py',
        'analysis/tests/test_airquantumgrav_200hz_clock.py',
        'analysis/tests/test_airquantumgrav_clock_disturbance.py',
        'analysis/tests/test_airquantumgrav_calibration_cases.py',
        'analysis/tests/test_airquantumgrav_withheld_receiver.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'docs/prediction-aircraft-error-integration/PLAN.md'])


def required_tests():
    names = ['test_integration_matrix_has_48_finite_distinct_tasks',
            'test_fresh_integration_study_requires_source_and_recovery_qualification',
            'test_construction_limits_include_full_later_receiver_draw[increment-7308]',
            'test_construction_limits_include_full_later_receiver_draw[point-4914]',
            'test_worker_prepays_work_and_preserves_scientific_abstention',
            'test_worker_keeps_charges_and_failure_artifacts',
            'test_evaluate_rejects_changed_frozen_case_before_charging',
            'test_full_receiver_draw_charges_declared_variates_before_generation',
            'test_header_jitter_changes_only_logged_intervals_and_binds_new_hash',
            'test_boundary_case_changes_only_z_gyro_calibration_not_receiver_or_noise',
            'test_generated_packet_jitter_changes_forecast_without_changing_measurements',
            'test_real_native_training_receives_declared_200hz_clock[header_elapsed]',
            'test_real_native_training_receives_declared_200hz_clock[nominal_200Hz]']
    names.extend(
        f'test_native_forecast_saves_both_targets_before_later_truth[True-{profile}-{model}-{law}-dual-target-native-v1]'
        for profile in (False, True) for model in range(3)
        for law in ('increment', 'point'))
    return names


def request_qualification(root, *, recovery=False):
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.qualification import request
    from lll.studies.task_resume import qualification_sources as recovery_sources
    root = Path(root).resolve()
    base = 'docs/prediction-aircraft-error-integration/qualification/'
    return request(root,
                   sources=(recovery_sources(root) if recovery else
                            qualification_sources(root)),
                   environment=(runtime_environment() if recovery else
                                environment()),
                   output=base+('recovery-request.json' if recovery else
                                'request.json'),
                   report=base+('recovery-tests.xml' if recovery else
                                'tests.xml'))


def prepare(root, *, qualification, recovery_qualification):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source-bound software and task recovery qualification required')
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as thread_environment
    from lll.studies.artifacts import atomic, encoded
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.task_resume import (qualification_sources as recovery_sources,
                                         REQUIRED_TESTS as recovery_tests)
    root = Path(root).resolve()
    base = root/'data'/(IDENTITY+'-inputs')
    if base.exists() or (root/'data'/IDENTITY).exists():
        raise ValueError('fresh finite integration allowance required')
    r = recipe()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=4, threads=1):
        raise ValueError('guarded four-thread numerical allocation required')
    source_request, source_report = checked(
        root, qualification, sources=qualification_sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=runtime_environment(), required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    base.mkdir(parents=True)
    material = dict(recipe=encoded(r), qualification_request=source_request,
                    qualification_report=source_report,
                    recovery_request=recovery_request,
                    recovery_report=recovery_report,
                    numerical_environment=encoded(env))
    inputs = {}
    for name, raw in material.items():
        path = base/name
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=IDENTITY, scope=SCOPE,
                      adapter='analysis/lll/prediction_aircraft_error_integration.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(r), workers=4, threads=1,
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+IDENTITY, total=48,
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    from lll.airquantumgrav_inventory import environment
    r = recipe()
    if (context.manifest.get('scope') != SCOPE or
            {key:value for key,value in task.items() if key not in ('index', 'shard')}
            != {item['identity']:item for item in tasks(r)}.get(task['identity']) or
            json.loads(context.input_path('recipe').read_bytes()) != r or
            json.loads(context.input_path('numerical_environment').read_bytes()) != environment()):
        raise ValueError('unchanged qualified integration case and environment required')
    return run_case(task, context, r=r)


def run_case(task, context, *, r):
    from lll.airquantumgrav_inventory import environment
    from lll.structured_noisy_study import _kernels
    from lll.airquantumgrav_noisy_inputs import construct, error_law
    from lll.airquantumgrav_clock_disturbance import apply_header_timestamp_jitter
    from lll.airquantumgrav_dual_target_prediction import calculate
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.airquantumgrav_training_controls import _spec
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.ilvis0_native_error_training import ErrorTrainingFactory, ForecastErrorDiagnostic
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest

    payload = task['payload']
    identity = task['identity']
    law = payload['law']
    construction = construction_limits(r, law)
    if task['limits'] != dict(native_calls=2000, packet_visits=20000,
                              bound_calls=0, bound_steps=0):
        raise ValueError('finite native allowance changed')
    journal = Journal(context.directory/'construction.sqlite',
                      freeze=digest((context.root/'manifest.json').read_bytes()),
                      limits={identity:construction})
    journal.start(identity)
    budget = None

    def check():
        _check_continue(context.root, context.manifest)

    def reserve_construction(**work):
        check()
        for name, count in work.items():
            journal.reserve(identity, name, count)

    try:
        noise_kernel, kernel_factory = _kernels(context, environment())
        configured = dict(r, noise=r['noise_by_law'][law],
                          sensor_case=payload['sensor_case'])
        clock_case = payload['clock_case']
        configured['clock'] = ('nominal_200Hz' if clock_case == 'nominal_200Hz'
                               else 'header_elapsed')
        spec = {key:value for key,value in payload.items()
                if key not in ('law', 'sensor_case', 'clock_case')}
        with context.prepay_native(native_calls=2000, packet_visits=20000) as budget:
            material = construct(spec, configured, reserve=reserve_construction)
            if clock_case == 'header_jitter':
                material = apply_header_timestamp_jitter(
                    material, amplitude_s=r['header_jitter_amplitude_s'],
                    cycles=r['header_jitter_cycles'])
            anchor = material['training_rows'][0]['height_m']
            factory = ErrorTrainingFactory(
                noise=error_law(configured['noise']), noise_kernel=noise_kernel,
                gravity_anchor_height_m=anchor,
                maximum_packets=len(material['dt']),
                maximum_queries=len(material['times']),
                maximum_bytes=64*1024**2,
                anchor_policy=r['covariance_anchor_policy'])
            diagnostic_args = dict(
                receiver_transform_policy=r['receiver_transform_policy'],
                bound_margin=r['bound_margin'], rank_rtol=r['rank_rtol'],
                estimability_rtol=r['estimability_rtol'],
                estimability_atol=r['estimability_atol'])
            physical = ForecastErrorDiagnostic(
                factory, target='physical_position', **diagnostic_args)
            receiver = ForecastErrorDiagnostic(
                factory, target='receiver_measurement', **diagnostic_args)
            arguments, sign = _spec({key:value for key,value in spec.items()
                                     if key != 'policy_id'})

            def truth(times):
                return receiver_samples(
                    times=times, sign=sign, **arguments,
                    height_profile=r['height_profile'],
                    gravity_model=r['gravity_model'])

            result = calculate(
                spec, configured, material=material,
                train_and_forecast=train_and_forecast,
                kernel_factory=kernel_factory, reserve=budget.reserve,
                reserve_construction=reserve_construction,
                save=context.save, truth=truth, check_continue=check,
                training_error_factory=factory,
                physical_diagnostic=physical,
                receiver_diagnostic=receiver)
        journal.verify()
        if (any(journal.count(identity, name) != value
                for name,value in construction.items()) or
                result['native_calls'] != budget.snapshot()['attempted']['native_calls'] or
                result['dual_target']['scientific_decision'] != 'abstain' or
                not result['dual_target']['forecast_and_diagnostics_saved_before_later_truth'] or
                not result['dual_target']['training_receiver_prefix_exact']):
            raise ValueError('saved technical integration and charged work differ')
        return dict(result, passed=True,
                    generated_technical_integration_passed=True,
                    physical_prediction_passed=result['passed'],
                    constructed_intervals=construction['constructed_intervals'],
                    generated_samples=construction['generated_samples'],
                    noise_normal_variates=construction['noise_normal_variates'])
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('request', 'recovery-request', 'prepare'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request':
        result = request_qualification(args.root)
    elif args.action == 'recovery-request':
        result = request_qualification(args.root, recovery=True)
    else:
        result = prepare(args.root,
                         qualification='docs/prediction-aircraft-error-integration/qualification/request.json',
                         recovery_qualification='docs/prediction-aircraft-error-integration/qualification/recovery-request.json')
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
