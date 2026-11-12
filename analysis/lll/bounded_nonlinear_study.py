# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated-aircraft check of bound-aware nonlinear forecast tangents."""
import itertools
import json
from pathlib import Path


IDENTITY = 'bounded-nonlinear-aircraft-v2-20261111'
SCOPE = ('corrected 24 generated two-minute aircraft tangent checks; two withheld targets, '
         'known candidate input law, interior/boundary calibration, no observed '
         'or protected inputs and no calibrated scientific decision')


def recipe():
    from lll.structured_noisy_training import recipe as base
    from lll.airquantumgrav_noisy_inputs import noise_settings, rate_point_noise_settings
    return dict(base(), version='bounded-nonlinear-aircraft-v1',
                duration_s=120., rate_hz=300, queries=119,
                maximum_evaluations=200, starts=1,
                models=['sphere_rotating', 'sphere_still', 'flat_still'],
                profiles=[False, True], input_laws=['increment', 'point'],
                sensor_cases=['interior', 'z_gyro_boundary'],
                noise_by_law=dict(increment=noise_settings(seed=271828),
                                  point=rate_point_noise_settings(seed=271828)),
                clock='header_elapsed', calibration_alpha=.025,
                future_alpha=.025, workers=4, threads=1,
                maximum_wall_s=7200.,
                scientific_decision='abstain')


def limits(r):
    from lll.structured_noisy_training import limits as one
    if (r['rate_hz'] != 300 or r['duration_s'] != 120. or
            r['queries'] != 119 or r['maximum_evaluations'] != 200 or
            r['input_laws'] != ['increment', 'point'] or
            r['sensor_cases'] != ['interior', 'z_gyro_boundary']):
        raise ValueError('exact finite bounded nonlinear recipe required')
    reference = max(one(r, law)[0]['native_calls'] for law in r['input_laws'])
    packet = max(one(r, law)[0]['packet_visits'] for law in r['input_laws'])
    return dict(native_calls=4*reference, packet_visits=4*packet,
                bound_calls=0, bound_steps=0)


def construction_limits(r, law):
    from lll.airquantumgrav_noisy_inputs import construction_limits as base
    if law not in r['input_laws']:
        raise ValueError('declared generating IMU error law required')
    out = base(dict(r, noise=r['noise_by_law'][law]))
    out['generated_samples'] += r['queries']
    out['noise_normal_variates'] += 6*r['queries']+6
    return out


def tasks(r=None):
    r = recipe() if r is None else r
    allowance = limits(r)
    result = []
    for model, profile, law, sensor in itertools.product(
            r['models'], r['profiles'], r['input_laws'], r['sensor_cases']):
        identity = f'{model}-{int(profile)}-{law}-{sensor}'
        result.append(dict(identity=identity, input_key='recipe',
                           native_kind='tangent',
                           payload=dict(model=model, latitude_deg=55.,
                                        profile=profile, start=0,
                                        policy_id='reported-short-v1',
                                        law=law, sensor_case=sensor),
                           limits=allowance))
    if len(result) != 24 or len({item['identity'] for item in result}) != 24:
        raise ValueError('complete distinct 24-case matrix required')
    return result


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/bounded_nonlinear_study.py',
        'analysis/lll/bounded_nonlinear_case.py',
        'analysis/lll/bounded_forecast_wrapper.py',
        'analysis/lll/bounded_aircraft_tangent.py',
        'analysis/lll/bounded_linear_prediction.py',
        'analysis/tests/test_bounded_nonlinear_study.py',
        'analysis/tests/test_bounded_nonlinear_native.py',
        'analysis/tests/test_bounded_nonlinear_case.py',
        'analysis/tests/test_bounded_forecast_wrapper.py',
        'analysis/tests/test_bounded_aircraft_tangent.py',
        'analysis/tests/test_bounded_linear_prediction.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'docs/bounded-calibration-prediction/NONLINEAR_V2_PLAN.md'])


def required_tests():
    return [
        'test_standalone_frozen_adapter_has_no_relative_imports',
        'test_bounded_nonlinear_matrix_has_24_cases_and_finite_limits',
        'test_bounded_study_requires_source_and_recovery_qualification',
        'test_bounded_worker_prepays_and_preserves_abstention',
        'test_bounded_worker_preserves_charged_failure',
        'test_bounded_evaluate_rejects_changed_case_before_charging',
        'test_native_bounded_case_seals_both_targets_before_truth[interior-increment]',
        'test_native_bounded_case_seals_both_targets_before_truth[interior-point]',
        'test_native_bounded_case_seals_both_targets_before_truth[z_gyro_boundary-increment]',
        'test_native_bounded_case_seals_both_targets_before_truth[z_gyro_boundary-point]',
        'test_rank_deficient_training_retains_full_box_null_direction',
        'test_adapter_matches_independent_dense_conditional_calculation',
        'test_wrapper_saves_complete_bound_before_returning_base_diagnostic',
        'test_marginal_score_uses_all_axes_and_wraps_longitude',
    ]


def request_qualification(root, *, recovery=False):
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.qualification import request
    from lll.studies.task_resume import qualification_sources as recovery_sources
    root = Path(root).resolve()
    base = 'docs/bounded-calibration-prediction/qualification/'
    return request(root,
                   sources=(recovery_sources(root) if recovery else
                            qualification_sources(root)),
                   environment=(runtime_environment() if recovery else
                                environment()),
                   output=base+('recovery-request.json' if recovery else
                               'request-v3.json'),
                   report=base+('recovery-tests.xml' if recovery else
                               'tests-v3.xml'))


def prepare(root, *, qualification, recovery_qualification):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source-bound software and recovery qualification required')
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
        raise ValueError('fresh bounded nonlinear allowance required')
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
    inputs = {}
    for name, raw in dict(recipe=encoded(r),
                          qualification_request=source_request,
                          qualification_report=source_report,
                          recovery_request=recovery_request,
                          recovery_report=recovery_report,
                          numerical_environment=encoded(env)).items():
        path = base/name
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=IDENTITY, scope=SCOPE,
                      adapter='analysis/lll/bounded_nonlinear_study.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(r), workers=4, threads=1,
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+IDENTITY, total=24,
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    from lll.airquantumgrav_inventory import environment
    r = recipe()
    expected = {item['identity']:item for item in tasks(r)}
    if (context.manifest.get('scope') != SCOPE or
            {key:value for key,value in task.items()
             if key not in ('index', 'shard')} != expected.get(task['identity']) or
            json.loads(context.input_path('recipe').read_bytes()) != r or
            json.loads(context.input_path('numerical_environment').read_bytes())
            != environment()):
        raise ValueError('unchanged qualified bounded nonlinear case required')
    return run_case(task, context, r=r)


def run_case(task, context, *, r):
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest

    if task['limits'] != limits(r):
        raise ValueError('finite bounded nonlinear allowance changed')
    identity = task['identity']
    law = task['payload']['law']
    construction = construction_limits(r, law)
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
        with context.prepay_native(**{key:task['limits'][key]
                                     for key in ('native_calls', 'packet_visits')}) as budget:
            result = run_generated_case(task, context, r,
                                        budget.reserve, reserve_construction,
                                        check)
        journal.verify()
        if (any(journal.count(identity, name) != count
                for name, count in construction.items()) or
                result['native_calls'] !=
                budget.snapshot()['attempted']['native_calls'] or
                result['bounded']['scientific_decision'] != 'abstain' or
                result['bounded']['both_bounds_saved_before_later_truth'] is not True):
            raise ValueError('bounded results and charged work differ')
        return dict(result, passed=True, scientific_decision='abstain',
                    bounded_technical_integration_passed=True,
                    physical_prediction_passed=result['passed'],
                    constructed_intervals=construction['constructed_intervals'],
                    generated_samples=construction['generated_samples'],
                    noise_normal_variates=construction['noise_normal_variates'])
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def run_generated_case(task, context, r, reserve_native,
                       reserve_construction, check):
    from lll.airquantumgrav_inventory import environment
    from lll.airquantumgrav_noisy_inputs import construct, error_law
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.airquantumgrav_training_controls import _spec
    from lll.bounded_nonlinear_case import calculate
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    from lll.structured_noisy_study import _kernels

    noise_kernel, kernel_factory = _kernels(context, environment())
    payload = task['payload']
    law = payload['law']
    spec = {key:value for key,value in payload.items()
            if key not in ('law', 'sensor_case')}
    configured = dict(r, noise=r['noise_by_law'][law],
                      sensor_case=payload['sensor_case'])
    material = construct(spec, configured, reserve=reserve_construction)
    anchor = material['training_rows'][0]['height_m']
    factory = ErrorTrainingFactory(
        noise=error_law(configured['noise']), noise_kernel=noise_kernel,
        gravity_anchor_height_m=anchor,
        maximum_packets=len(material['dt']),
        maximum_queries=len(material['times']),
        maximum_bytes=64*1024**2,
        anchor_policy=r['covariance_anchor_policy'])
    arguments, sign = _spec({key:value for key,value in spec.items()
                             if key != 'policy_id'})

    def truth(times):
        return receiver_samples(
            times=times, sign=sign, **arguments,
            height_profile=r['height_profile'],
            gravity_model=r['gravity_model'])

    return calculate(
        spec, configured, material=material, factory=factory,
        kernel_factory=kernel_factory, reserve=reserve_native,
        reserve_construction=reserve_construction,
        save=context.save, truth=truth, check_continue=check)


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
        result = prepare(
            args.root,
            qualification='docs/bounded-calibration-prediction/qualification/request-v3.json',
            recovery_qualification='docs/bounded-calibration-prediction/qualification/recovery-request.json')
    print(json.dumps(result, sort_keys=True, default=str))


if __name__ == '__main__':
    main()
