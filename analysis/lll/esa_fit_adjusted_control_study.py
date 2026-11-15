# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite long generated control of fit-adjusted ESA training-error scale."""

import io
import json
from pathlib import Path
import argparse


ID = 'esa-fit-adjusted-control-v1-20261115'
PREFLIGHT_ID = ID + '-preflight'
SCOPE = ('two 900-second generated same-input two-law training controls; '
         'no observed or protected flight inputs and no Earth-model decision')
PREFLIGHT_SCOPE = 'one short generated frozen-worker two-law wiring check'
LAWS = ('increment', 'point')
SEEDS = dict(increment=20261115001, point=20261115002)
LIMITS = dict(native_calls=1_400_000, packet_visits=90_000_000_000,
              bound_calls=0, bound_steps=0)
PREFLIGHT_LIMITS = dict(native_calls=100_000, packet_visits=100_000_000,
                        bound_calls=0, bound_steps=0)
DIRECTORY = 'docs/prediction-observed-development/qualification/'


def recipe():
    from .prediction_paired_law_study import recipe as base
    from .airquantumgrav_noisy_inputs import (noise_settings,
                                               rate_point_noise_settings)
    return dict(base(), version='esa-fit-adjusted-control-v1',
                duration_s=900., rate_hz=300, queries=900,
                query_start_s=.5, query_step_s=1., maximum_evaluations=200,
                models=['sphere_rotating'], profiles=[False],
                noise_by_law=dict(
                    increment=noise_settings(seed=SEEDS['increment']),
                    point=rate_point_noise_settings(seed=SEEDS['increment'])),
                workers=2, threads=1, maximum_wall_s=7200.,
                original_reads=0, observed_starts=0, retries=0)


def preflight_recipe():
    return dict(recipe(), duration_s=2., rate_hz=200, queries=9,
                query_start_s=.1, query_step_s=.2,
                maximum_evaluations=8, workers=1, maximum_wall_s=600.)


def tasks(r=None):
    r = recipe() if r is None else r
    if (r['version'] != 'esa-fit-adjusted-control-v1' or
            (r['duration_s'], r['rate_hz'], r['queries']) !=
            (900., 300, 900) or
            (r['query_start_s'], r['query_step_s']) != (.5, 1.) or
            r['maximum_evaluations'] != 200 or
            (r['workers'], r['threads'], r['maximum_wall_s']) !=
            (2, 1, 7200.)):
        raise ValueError('exact long known-answer recipe required')
    return [dict(identity=law, input_key='recipe', native_kind='tangent',
                 payload=dict(model='sphere_rotating', latitude_deg=55.,
                              profile=False, start=0,
                              policy_id='reported-short-v1', truth_law=law,
                              noise_seed=SEEDS[law]),
                 limits=dict(LIMITS)) for law in LAWS]


def preflight_task():
    return dict(tasks()[0], identity='preflight-increment',
                limits=dict(PREFLIGHT_LIMITS))


def case_recipe(r, task):
    from .airquantumgrav_noisy_inputs import (noise_settings,
                                               rate_point_noise_settings)
    payload = task['payload']
    law = payload['truth_law']
    if law not in LAWS or payload['noise_seed'] != SEEDS[law]:
        raise ValueError('predeclared distinct generated seed required')
    seed = payload['noise_seed']
    return dict(r, noise_by_law=dict(
        increment=noise_settings(seed=seed),
        point=rate_point_noise_settings(seed=seed)))


def construction_limits(r, truth_law):
    from .airquantumgrav_noisy_inputs import construction_limits as count
    settings = r['noise_by_law'][truth_law]
    return count(dict(r, noise=settings))


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_fit_adjusted_control_study.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/lll/airquantumgrav_prediction.py',
        'analysis/lll/ilvis0_native_error_training.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/tests/test_esa_fit_adjusted_control_study.py',
        'analysis/tests/test_esa_fit_adjusted_control_recovery.py',
        'docs/prediction-observed-development/FIT_ADJUSTED_CONTROL_PLAN.md'])


def required_tests():
    return (
        'test_two_known_answer_cases_have_exact_600_report_training_support',
        'test_known_answer_study_requires_qualification_before_staging',
        'test_known_answer_study_rejects_changed_task_before_input_read',
        'test_known_answer_worker_prepays_and_reuses_one_measured_stream',
        'test_known_answer_worker_preserves_charged_failure',
        'test_known_answer_recovery_requires_sealed_matching_source',
        'test_reboot_resume_skips_sealed_and_preserves_charges',
        'test_source_input_environment_mutation_blocks',
        'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    return request(Path(root).resolve(), sources=sources(root),
                   environment=environment(),
                   output=DIRECTORY+'fit-adjusted-request.json',
                   report=DIRECTORY+'fit-adjusted-tests.xml')


def _definition(root, *, preflight, inputs):
    return dict(id=PREFLIGHT_ID if preflight else ID,
                scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                adapter='analysis/lll/esa_fit_adjusted_control_study.py',
                sources=sources(root), inputs=inputs,
                tasks=[preflight_task()] if preflight else tasks(),
                workers=1 if preflight else 2, threads=1,
                maximum_wall_s=600. if preflight else 7200.)


def prepare_preflight(root):
    return _prepare(root, preflight=True)


def prepare(root, *, qualification=None, recovery_qualification=None):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source and recovery qualification required before staging')
    return _prepare(root, preflight=False, qualification=qualification,
                    recovery_qualification=recovery_qualification)


def _prepare(root, *, preflight, qualification=None,
             recovery_qualification=None):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .ilvis0_control_shards import verify_completion, runtime_environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import (qualification_sources as recovery_sources,
                                      REQUIRED_TESTS as recovery_tests)

    root = Path(root).resolve()
    identity = PREFLIGHT_ID if preflight else ID
    directory = safe_path(root, 'data/'+identity+'-inputs')
    if directory.exists() or safe_path(root, 'data/'+identity).exists():
        raise ValueError('fresh known-answer identity required')
    env = environment()
    workers = 1 if preflight else 2
    if env['numerical_environment'] != numerical_environment(
            workers=workers, threads=1):
        raise ValueError('guarded numerical allocation required')
    staged = dict(recipe=encoded(preflight_recipe() if preflight else recipe()),
                  numerical_environment=encoded(env))
    if not preflight:
        request, report = checked(root, qualification, sources=sources(root),
            environment=env, required_tests=required_tests(),
            minimum_tests=len(required_tests()))
        recovery_request, recovery_report = checked(root,
            recovery_qualification, sources=recovery_sources(root),
            environment=runtime_environment(),
            required_tests=recovery_tests,
            minimum_tests=len(recovery_tests))
        result = verify_completion(root/'data'/PREFLIGHT_ID)
        if (result['state'] != 'complete' or result['completed'] != 1 or
                result['passed'] is not True):
            raise ValueError('sealed short two-law preflight required')
        staged.update(qualification_request=request,
            qualification_report=report,
            recovery_request=recovery_request,
            recovery_report=recovery_report)
    directory.mkdir(parents=True)
    inputs = {}
    for key, value in staged.items():
        path = directory/key
        atomic(path, value)
        inputs[key] = path.relative_to(root).as_posix()
    definition = _definition(root, preflight=preflight, inputs=inputs)
    atomic(directory/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+identity, total=len(definition['tasks']),
                allocation=manifest['allocation'])


def evaluate(task, context):
    from .airquantumgrav_inventory import environment
    preflight = context.manifest.get('scope') == PREFLIGHT_SCOPE
    r = preflight_recipe() if preflight else recipe()
    expected = ({preflight_task()['identity']:preflight_task()}
                if preflight else {row['identity']:row for row in tasks(r)})
    declared = {key:value for key,value in task.items()
                if key not in ('index','shard')}
    if (context.manifest.get('scope') not in (SCOPE,PREFLIGHT_SCOPE) or
            declared != expected.get(task['identity'])):
        raise ValueError('unchanged known-answer task required')
    if (json.loads(context.input_path('recipe').read_bytes()) != r or
            json.loads(context.input_path(
                'numerical_environment').read_bytes()) != environment()):
        raise ValueError('unchanged known-answer recipe and environment required')
    return run_case(task, context, r=case_recipe(r, task))


def run_case(task, context, *, r):
    from .ilvis0_control_shards import _check_continue
    from .studies.artifacts import digest
    from .studies.journal import Journal

    preflight = task['identity'] == 'preflight-increment'
    if task['limits'] != (PREFLIGHT_LIMITS if preflight else LIMITS):
        raise ValueError('finite known-answer native allowance changed')
    identity = task['identity']
    construction = construction_limits(r, task['payload']['truth_law'])
    journal = Journal(context.directory/'construction.sqlite',
                      freeze=digest((context.root/'manifest.json').read_bytes()),
                      limits={identity:construction})
    journal.start(identity)
    budget = None

    def reserve_construction(**work):
        _check_continue(context.root, context.manifest)
        for name,count in work.items():
            journal.reserve(identity,name,count)

    try:
        with context.prepay_native(**{
                key:task['limits'][key]
                for key in ('native_calls','packet_visits')}) as budget:
            result = run_generated_case(task,context,r,
                                        budget.reserve,reserve_construction)
        journal.verify()
        if (any(journal.count(identity,name) != count
                for name,count in construction.items()) or
                result['native_calls'] != budget.snapshot()['attempted'][
                    'native_calls'] or
                result['scientific_decision'] != 'abstain'):
            raise ValueError('generated result and charged work differ')
        return dict(result, constructed_intervals=construction['constructed_intervals'],
                    generated_samples=construction['generated_samples'],
                    noise_normal_variates=construction['noise_normal_variates'])
    finally:
        if budget is not None:
            context.save('native-prepayment.json',budget.snapshot())
        context.note_file(journal.path)


def run_generated_case(task,context,r,reserve_native,reserve_construction):
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construct, error_law
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .structured_noisy_study import _kernels
    from .ilvis0_control_shards import _check_continue
    from .studies.artifacts import digest,encoded

    payload = task['payload']
    spec = {key:value for key,value in payload.items()
            if key not in ('truth_law','noise_seed')}
    configured = dict(r,noise=r['noise_by_law'][payload['truth_law']])
    charged = 0

    def check():
        _check_continue(context.root,context.manifest)

    def charge(**work):
        nonlocal charged
        check()
        reserve_native(**work)
        charged += work['native_calls']

    check()
    material = construct(spec,configured,reserve=reserve_construction)
    times = np.asarray(material['times'],dtype=float)
    cut = material['training_epochs']
    if (len(material['dt']) != round(r['duration_s']*r['rate_hz']) or
            len(times) != r['queries'] or cut != 2*r['queries']//3 or
            (not task['identity'].startswith('preflight') and cut != 600) or
            any(not np.all(np.isfinite(material[key]))
                for key in ('theta','dv','dt','times')) or
            times[0]-r['limits']['time_offset'] < 0 or
            times[-1]+r['limits']['time_offset'] >=
                float(np.sum(material['dt']))):
        raise ValueError('complete finite generated timing and measurements required')
    buffer = io.BytesIO()
    np.savez_compressed(buffer,**{key:material[key]
                                  for key in ('theta','dv','dt','times')})
    context.save_bytes('measured-inputs.npz',buffer.getvalue())
    context.save('training-receiver.json',material['training_rows'])
    binding = dict(training_receiver_sha256=digest(encoded(
        material['training_rows'])),
        measured_raw_array_sha256=material['binding'][
            'measured_raw_array_sha256'],
        training_epochs=cut,truth_law=payload['truth_law'],
        noise_seed=payload['noise_seed'],original_reads=0,protected_reads=0)
    context.save('input-binding.json',binding)
    noise_kernel,kernel_factory = _kernels(context,environment())
    kernel,tangent,compilation = kernel_factory(
        material['training_rows'][0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('frozen native tangent source required')
    context.save('compilation.json',compilation)
    fits = {}
    for law in LAWS:
        check()
        factory = ErrorTrainingFactory(
            noise=error_law(r['noise_by_law'][law]),
            noise_kernel=noise_kernel,
            gravity_anchor_height_m=material['training_rows'][0]['height_m'],
            maximum_packets=len(material['dt']),maximum_queries=len(times),
            maximum_bytes=64*1024**2,
            anchor_policy=r['covariance_anchor_policy'])
        result = train_and_forecast(
            **{key:material[key] for key in ('theta','dv','dt')},
            times=times,training_rows=material['training_rows'],
            time_origin_s=0.,model='sphere_rotating',profile=False,
            policy_id='reported-short-v1',start=0,limits=r['limits'],
            maximum_evaluations=r['maximum_evaluations'],
            maximum_interval_s=1.5/r['rate_hz'],
            kernel=kernel,tangent_kernel=tangent,reserve=charge,
            save=lambda name,value:context.save(law+'/'+name,value),
            check_continue=check,training_error_factory=factory,
            clock='header_elapsed')
        fit = result['fit']
        fits[law] = dict(converged=bool(fit['converged'] and
                                      fit['stopping_rule_verified']),
                         active_bounds=fit['active_bounds'],
                         training_cost=fit['residual_sum_squares'],
                         observation_count=3*cut,
                         input_binding_sha256=digest(encoded(binding)))
    context.save('matched-fit-summary.json',fits)
    return dict(passed=True,scientific_decision='abstain',
                native_calls=charged,truth_law=payload['truth_law'],
                noise_seed=payload['noise_seed'],training_epochs=cut,
                candidate_results=fits,original_reads=0,protected_reads=0,
                same_measured_input_for_both_laws=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','preflight','prepare'))
    parser.add_argument('--root',default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request':
        result = request_qualification(root)
    elif args.action == 'preflight':
        result = prepare_preflight(root)
    else:
        from .esa_fit_adjusted_control_recovery import SPEC
        result = prepare(root,qualification=DIRECTORY+'fit-adjusted-request.json',
                         recovery_qualification=SPEC.request)
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()
