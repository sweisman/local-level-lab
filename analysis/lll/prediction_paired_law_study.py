# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite same-measurement comparison of two fixed aircraft error laws."""
import itertools
import json
from pathlib import Path


IDENTITY = 'prediction-paired-law-20261111'
SCOPE = ('12 generated two-minute same-input candidate-law comparisons; '
         'training score only, no observed/protected inputs or calibrated decision')


def recipe():
    from lll.structured_noisy_training import recipe as base
    from lll.airquantumgrav_noisy_inputs import noise_settings, rate_point_noise_settings
    return dict(base(), version='prediction-paired-law-pilot-v1',
                models=['sphere_rotating', 'sphere_still', 'flat_still'],
                profiles=[False, True], starts=1, rate_hz=300,
                duration_s=120., queries=119, maximum_evaluations=200,
                input_laws=['increment', 'point'],
                noise_by_law=dict(increment=noise_settings(seed=71),
                                  point=rate_point_noise_settings(seed=71)),
                sensor_case='interior', clock='header_elapsed',
                workers=4, threads=1, maximum_wall_s=7200.,
                scientific_decision='abstain')


def limits(r):
    from lll.structured_noisy_training import limits as one
    if (r['rate_hz'] != 300 or r['duration_s'] != 120. or
            r['queries'] != 119 or r['maximum_evaluations'] != 200 or
            r['input_laws'] != ['increment', 'point']):
        raise ValueError('exact finite paired-law recipe required')
    work = [one(r, law)[0] for law in r['input_laws']]
    return dict(native_calls=4*max(item['native_calls'] for item in work),
                packet_visits=4*max(item['packet_visits'] for item in work),
                bound_calls=0, bound_steps=0)


def construction_limits(r, truth_law):
    from lll.airquantumgrav_noisy_inputs import construction_limits as one
    if truth_law not in r['input_laws']:
        raise ValueError('declared generating input law required')
    result = one(dict(r, noise=r['noise_by_law'][truth_law]))
    result['generated_samples'] += r['queries']
    result['noise_normal_variates'] += 6*r['queries']+6
    return result


def tasks(r=None):
    r = recipe() if r is None else r
    budget = limits(r)
    out = []
    for model, profile, law in itertools.product(
            r['models'], r['profiles'], r['input_laws']):
        identity = f'{model}-{int(profile)}-{law}'
        out.append(dict(identity=identity, input_key='recipe',
                        native_kind='tangent',
                        payload=dict(model=model, latitude_deg=55.,
                                     profile=profile, start=0,
                                     policy_id='reported-short-v1',
                                     truth_law=law), limits=budget))
    if len(out) != 12 or len({item['identity'] for item in out}) != 12:
        raise ValueError('complete unique twelve-case pilot required')
    return out


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_paired_law_study.py',
        'analysis/lll/prediction_paired_law.py',
        'analysis/lll/prediction_training_law_comparison.py',
        'analysis/tests/test_prediction_paired_law_study.py',
        'analysis/tests/test_prediction_paired_law.py',
        'analysis/tests/test_prediction_training_law_comparison.py',
        'analysis/tests/test_airquantumgrav_dual_target_native.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'docs/prediction-paired-law/PLAN.md'])


def required_tests():
    return [
        'test_ranks_matched_training_laws_without_selecting_or_claiming_coverage',
        'test_rejects_mismatched_measurements_or_later_outcomes',
        'test_failed_fit_abstains_without_rank_or_future_spread',
        'test_active_bound_keeps_training_ranking_but_blocks_calibration_claim',
        'test_paired_fits_and_training_comparison_precede_withheld_truth',
        'test_paired_run_refuses_missing_saved_forecast_before_truth',
        'test_paired_law_matrix_has_twelve_shared_input_tasks_and_finite_limits',
        'test_paired_law_study_requires_source_and_recovery_qualification',
        'test_paired_worker_prepays_and_preserves_abstention',
        'test_paired_worker_preserves_charged_failure',
        'test_paired_evaluate_rejects_changed_frozen_case_before_charging',
        'test_short_native_paired_case_uses_one_kernel_and_one_measured_stream']


def request_qualification(root, *, recovery=False):
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.qualification import request
    from lll.studies.task_resume import qualification_sources as recovery_sources
    root = Path(root).resolve()
    base = 'docs/prediction-paired-law/qualification/'
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
        raise ValueError('fresh finite paired-law allowance required')
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
                      adapter='analysis/lll/prediction_paired_law_study.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(r), workers=4, threads=1,
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+IDENTITY, total=12,
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    from lll.airquantumgrav_inventory import environment
    r = recipe()
    if (context.manifest.get('scope') != SCOPE or
            {key:value for key,value in task.items() if key not in ('index', 'shard')}
            != {item['identity']:item for item in tasks(r)}.get(task['identity']) or
            json.loads(context.input_path('recipe').read_bytes()) != r or
            json.loads(context.input_path('numerical_environment').read_bytes()) != environment()):
        raise ValueError('unchanged qualified paired-law case and environment required')
    return run_case(task, context, r=r)


def run_case(task, context, *, r):
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    if task['limits'] != limits(r):
        raise ValueError('finite paired-law native allowance changed')
    identity = task['identity']
    construction = construction_limits(r, task['payload']['truth_law'])
    journal = Journal(context.directory/'construction.sqlite',
                      freeze=digest((context.root/'manifest.json').read_bytes()),
                      limits={identity:construction})
    journal.start(identity)
    budget = None

    def reserve_construction(**work):
        _check_continue(context.root, context.manifest)
        for name, count in work.items():
            journal.reserve(identity, name, count)

    try:
        with context.prepay_native(**{key:task['limits'][key]
                                     for key in ('native_calls','packet_visits')}) as budget:
            result = run_generated_pair(task, context, r,
                                        budget.reserve, reserve_construction)
        journal.verify()
        if (any(journal.count(identity, name) != count
                for name, count in construction.items()) or
                result['native_calls'] != budget.snapshot()['attempted']['native_calls'] or
                result['scientific_decision'] != 'abstain'):
            raise ValueError('paired-law results and charged work differ')
        return dict(result, constructed_intervals=construction['constructed_intervals'],
                    generated_samples=construction['generated_samples'],
                    noise_normal_variates=construction['noise_normal_variates'])
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def run_generated_pair(task, context, r, reserve_native, reserve_construction):
    import io
    import numpy as np
    from lll.airquantumgrav_inventory import environment
    from lll.airquantumgrav_noisy_inputs import construct, error_law
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.airquantumgrav_training_controls import _spec
    from lll.airquantumgrav_withheld_receiver import generate_full_report
    from lll.airquantumgrav_dual_target_prediction import _marginal_score
    from lll.airquantumgrav_geographic_controls import position_errors
    from lll.airquantumgrav_scoring import sections
    from lll.ilvis0_native_error_training import ErrorTrainingFactory, ForecastErrorDiagnostic
    from lll.structured_noisy_study import _kernels
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest, encoded
    from lll.prediction_paired_law import run

    payload = task['payload']
    truth_law = payload['truth_law']
    spec = {key:value for key,value in payload.items() if key != 'truth_law'}
    configured_truth = dict(r, noise=r['noise_by_law'][truth_law])
    noise_kernel, kernel_factory = _kernels(context, environment())
    charged_native = 0

    def check():
        _check_continue(context.root, context.manifest)

    def charge(**work):
        nonlocal charged_native
        check()
        reserve_native(**work)
        charged_native += work['native_calls']

    material = construct(spec, configured_truth, reserve=reserve_construction)
    times = np.asarray(material['times'], float)
    cut = material['training_epochs']
    if (len(material['dt']) != round(r['duration_s']*r['rate_hz']) or
            len(times) != r['queries'] or cut != 2*r['queries']//3):
        raise ValueError('unchanged complete measured pilot inputs required')
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **{key:material[key]
                                  for key in ('theta','dv','dt','times')})
    context.save_bytes('measured-inputs.npz', buffer.getvalue())
    context.save('training-receiver.json', material['training_rows'])
    prefix = int(np.searchsorted(np.cumsum(material['dt']),
                                 times[cut-1]+r['limits']['time_offset'],
                                 side='left'))+1
    binding = dict(training_receiver_sha256=digest(encoded(material['training_rows'])),
                   training_prefix_sha256={key:digest(
                       np.asarray(material[key][:prefix], dtype='<f8').tobytes())
                       for key in ('theta','dv','dt')},
                   training_epochs=cut, prediction_epochs=len(times)-cut,
                   original_reads=0, protected_reads=0,
                   generating_law=truth_law,
                   measured_input_sha256=material['binding']['measured_raw_array_sha256'])
    context.save('input-binding.json', binding)
    anchor = material['training_rows'][0]['height_m']
    kernel, tangent, compilation = kernel_factory(anchor)
    context.save('compilation.json', compilation)
    diagnostic_args = dict(receiver_transform_policy=r['receiver_transform_policy'],
                           bound_margin=r['bound_margin'], rank_rtol=r['rank_rtol'],
                           estimability_rtol=r['estimability_rtol'],
                           estimability_atol=r['estimability_atol'])

    def fit_candidate(law, save_candidate):
        configured = dict(r, noise=r['noise_by_law'][law])
        factory = ErrorTrainingFactory(
            noise=error_law(configured['noise']), noise_kernel=noise_kernel,
            gravity_anchor_height_m=anchor,
            maximum_packets=len(material['dt']), maximum_queries=len(times),
            maximum_bytes=64*1024**2,
            anchor_policy=r['covariance_anchor_policy'])
        physical = ForecastErrorDiagnostic(factory, target='physical_position',
                                           **diagnostic_args)
        receiver = ForecastErrorDiagnostic(factory, target='receiver_measurement',
                                           **diagnostic_args)
        diagnostics = {}

        def both(*args, **kwargs):
            physical_result = physical(*args, **kwargs)
            receiver_result = receiver(*args, **kwargs)
            diagnostics.update(physical=physical_result,
                               receiver=receiver_result)
            save_candidate('receiver-error-diagnostic.json',
                           json.loads(json.dumps(receiver_result,
                               default=lambda value:value.tolist(),
                               allow_nan=False)))
            return physical_result

        result = train_and_forecast(
            **{key:material[key] for key in ('theta','dv','dt')},
            times=times, training_rows=material['training_rows'],
            time_origin_s=0., model=spec['model'], profile=spec['profile'],
            policy_id=spec['policy_id'], start=spec['start'],
            limits=r['limits'], maximum_evaluations=r['maximum_evaluations'],
            maximum_interval_s=1.5/r['rate_hz'],
            kernel=kernel, tangent_kernel=tangent,
            reserve=charge, save=save_candidate, check_continue=check,
            training_error_factory=factory,
            forecast_error_diagnostic=both, clock=r['clock'])
        return dict(fit=result['fit'], binding=binding,
                    diagnostic=diagnostics['receiver'],
                    physical_diagnostic=diagnostics['physical'],
                    forecast=result['forecast'])

    arguments, sign = _spec({key:value for key,value in spec.items()
                             if key != 'policy_id'})

    def truth():
        check()
        reserve_construction(generated_samples=len(times))
        answer = receiver_samples(times=times, sign=sign, **arguments,
                                  height_profile=r['height_profile'],
                                  gravity_model=r['gravity_model'])
        context.save('withheld-physical-truth.json',
                     {key:np.asarray(value).tolist() for key,value in answer.items()})
        return answer

    pair = run(tuple(r['input_laws']), fit_candidate=fit_candidate,
               save=context.save, withheld_truth=truth)
    answer = pair['withheld_truth']
    report = generate_full_report(answer['coordinates'], times,
                                  material['training_rows'],
                                  policy_id=spec['policy_id'],
                                  seed=r['noise_by_law'][truth_law]['seed'],
                                  reserve=reserve_construction)
    context.save('later-receiver-report.json',
                 dict(rows=report['rows'],
                      training_prefix_exact=True,
                      later_observations_used_for_training=False))
    receiver_coordinates = np.array([[np.radians(row['latitude_deg']),
                                      np.radians(row['longitude_deg']),
                                      row['height_m']] for row in report['rows']])
    case_results = {}
    for law, candidate in pair['candidates'].items():
        forecast = candidate['forecast']
        errors = position_errors(forecast['coordinates'], answer,
                                 model=spec['model'])
        physical = sections(errors, cut)
        coverage = dict(physical_position=_marginal_score(
                          candidate['physical_diagnostic'],
                          answer['coordinates'], cut),
                        receiver_measurement=_marginal_score(
                          candidate['diagnostic'], receiver_coordinates, cut))
        case_results[law] = dict(converged=bool(candidate['fit']['converged']),
                                 training_cost=candidate['fit']['residual_sum_squares'],
                                 physical_prediction_passed=bool(
                                     candidate['fit']['converged'] and
                                     all(section['accuracy']['passed']
                                         for section in physical.values())),
                                 training=physical['training'],
                                 prediction=physical['prediction'],
                                 marginal_coverage=coverage,
                                 scientific_decision='abstain')
        context.save(law+'/scores.json',case_results[law])
    return dict(passed=True, technical_pair_complete=True,
                scientific_decision='abstain', truth_law=truth_law,
                comparison_status=pair['comparison']['status'],
                numerical_passing_fits=sum(value['converged']
                                           for value in case_results.values()),
                physical_passing_fits=sum(value['physical_prediction_passed']
                                          for value in case_results.values()),
                candidate_results=case_results, native_calls=charged_native,
                original_reads=0, protected_reads=0,
                coverage_calibrated=False)


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
                         qualification='docs/prediction-paired-law/qualification/request.json',
                         recovery_qualification='docs/prediction-paired-law/qualification/recovery-request.json')
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
