# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated recordings fitted under all three physical candidates."""

import json
from pathlib import Path


ID='generated-matched-candidates-v1-20261117'
PREFLIGHT_ID=ID+'-preflight'
SCOPE=('twelve fresh generated recordings, three matched candidate fits each; '
       'development only; no observed or protected aircraft input')
PREFLIGHT_SCOPE='one short generated three-candidate shared-input preflight'
PLAN='docs/prediction-observed-development/MATCHED_CANDIDATE_GENERATED_PLAN.md'
QUALIFICATION_DIR='docs/prediction-observed-development/qualification/'


def recipe():
    from .generated_esa_dual_target_pilot import recipe as base
    from .airquantumgrav_noisy_inputs import noise_settings,rate_point_noise_settings
    return dict(base(),version='generated-matched-candidates-v1',
                duration_s=120.,queries=119,
                noise_by_law=dict(increment=noise_settings(seed=670101),
                                  point=rate_point_noise_settings(seed=670102)),
                workers=2,threads=1,maximum_wall_s=10800.)


def preflight_recipe():
    return dict(recipe(),version='generated-matched-candidates-preflight-v1',
                duration_s=10.,queries=9,maximum_evaluations=8,
                workers=1,threads=1,maximum_wall_s=900.)


def tasks(r=None):
    from .matched_candidate_case import MODELS
    from .structured_noisy_training import limits
    from .structured_noisy_study import extra_forecast_work
    r=recipe() if r is None else r
    if r not in (recipe(),preflight_recipe()):
        raise ValueError('exact matched-candidate recipe required')
    preflight=r==preflight_recipe()
    cases=([('sphere_rotating',55.,'increment',670000)] if preflight else
           [(model,latitude,law,670101+i)
            for i,(model,latitude,law) in enumerate(
                (m,lat,law) for m in MODELS for lat in (55.,-55.)
                for law in ('increment','point'))])
    rows=[]
    for model,latitude,law,seed in cases:
        base=limits(r,law)[0]
        extra=extra_forecast_work(r,3)
        allowance=dict(base)
        for key,value in extra.items():allowance[key]+=value
        for key in allowance:allowance[key]*=3
        identity=('preflight-increment' if preflight else
                  model+'-'+('north' if latitude>0 else 'south')+'-'+law)
        rows.append(dict(identity=identity,input_key='recipe',native_kind='tangent',
                         payload=dict(truth_model=model,latitude_deg=latitude,
                                      law=law,seed=seed,
                                      height_profile='climb' if latitude>0 else 'descend',
                                      profile=False,start=0,
                                      policy_id='reported-short-v1'),
                         limits=allowance))
    return rows


def evaluate(task,context):
    from .airquantumgrav_inventory import environment
    preflight=context.manifest.get('scope')==PREFLIGHT_SCOPE
    r=preflight_recipe() if preflight else recipe()
    expected={row['identity']:row for row in tasks(r)}
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    if (context.manifest.get('scope') not in (SCOPE,PREFLIGHT_SCOPE)
            or declared!=expected.get(task['identity'])):
        raise ValueError('unchanged finite matched-candidate task required')
    if (json.loads(context.input_path('recipe').read_bytes())!=r
            or json.loads(context.input_path('environment').read_bytes())!=environment()):
        raise ValueError('changed generated input or numerical environment')
    return _run_case(task,context,r)


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/matched_candidate_generated_study.py',
        'analysis/lll/matched_candidate_case.py',
        'analysis/lll/matched_candidate_scoring.py',
        'analysis/lll/simultaneous_dual_target_wrapper.py',
        'analysis/lll/dual_target_forecast_wrapper.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/tests/test_matched_candidate_generated_study.py',
        'analysis/tests/test_matched_candidate_case.py',
        'analysis/tests/test_matched_candidate_scoring.py',
        'analysis/tests/test_simultaneous_dual_target_wrapper.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',PLAN])


def required_tests():
    return ('test_full_matrix_has_twelve_recordings_and_thirty_six_fits',
            'test_preflight_is_one_short_three_candidate_recording',
            'test_changed_task_is_rejected_before_any_native_work',
            'test_shape_first_requires_complete_candidates_and_shape_before_rotation',
            'test_three_candidates_use_one_saved_input_before_later_truth',
            'test_candidate_mutation_blocks_later_truth',
            'test_joint_allowance_is_split_across_all_future_coordinates')


def request_qualification(root,*,preflight=False,recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources
    root=Path(root).resolve()
    stem='recovery' if recovery else 'preflight' if preflight else 'full'
    return request(root,sources=recovery_sources(root) if recovery else
                   qualification_sources(root),
                   environment=runtime_environment() if recovery else environment(),
                   output=QUALIFICATION_DIR+stem+'-matched-candidates-v1-request.json',
                   report=QUALIFICATION_DIR+stem+'-matched-candidates-v1-tests.xml')


def definition(root,*,preflight,inputs):
    r=preflight_recipe() if preflight else recipe()
    return dict(id=PREFLIGHT_ID if preflight else ID,
                scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                adapter='analysis/lll/matched_candidate_generated_study.py',
                sources=qualification_sources(root),inputs=dict(inputs),
                tasks=tasks(r),workers=r['workers'],threads=r['threads'],
                maximum_wall_s=r['maximum_wall_s'])


def prepare(root,*,preflight,qualification,recovery_qualification):
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment,verify_completion
    from .studies.artifacts import atomic,encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import (
        qualification_sources as recovery_sources,REQUIRED_TESTS as recovery_tests)
    root=Path(root).resolve();r=preflight_recipe() if preflight else recipe()
    if shutil.disk_usage(root).free<2*1024**3:
        raise ValueError('2 GiB free space required for matched-candidate development')
    env=environment()
    if env['numerical_environment']!=thread_environment(
            workers=r['workers'],threads=1):
        raise ValueError('guarded declared numerical allocation required')
    source_request,source_report=checked(
        root,qualification,sources=qualification_sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_request,recovery_report=checked(
        root,recovery_qualification,sources=recovery_sources(root),
        environment=runtime_environment(),required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    if not preflight:
        prior=verify_completion(root/'data'/PREFLIGHT_ID)
        if (prior['state']!='complete' or prior['completed']!=1
                or prior['passed'] is not True):
            raise ValueError('sealed matched-candidate preflight required')
    name=PREFLIGHT_ID if preflight else ID
    base=root/'data'/(name+'-inputs')
    if base.exists() or (root/'data'/name).exists():
        raise ValueError('fresh finite matched-candidate study required')
    base.mkdir(parents=True)
    payload=dict(recipe=encoded(r),environment=encoded(env),
                 qualification_request=source_request,
                 qualification_report=source_report,
                 recovery_request=recovery_request,
                 recovery_report=recovery_report)
    inputs={}
    for key,raw in payload.items():
        path=base/key
        atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    frozen=definition(root,preflight=preflight,inputs=inputs)
    atomic(base/'definition.json',encoded(frozen))
    manifest=Definition.from_dict(frozen,root).prepare(root)
    return dict(path='data/'+name,tasks=len(frozen['tasks']),
                allocation=manifest['allocation'],limits=manifest['limits'])


def launch(root,*,preflight=False):
    from .ilvis0_control_shards import launch as run_study
    name=PREFLIGHT_ID if preflight else ID
    return run_study(Path(root).resolve()/'data'/name,reserved_threads=0)


def generated_case(payload,r):
    from .structured_noisy_training import case_recipe
    law=payload['law']
    configured=case_recipe(r,law)
    configured['noise']=dict(r['noise_by_law'][law],seed=payload['seed'])
    if 'route' in payload:configured['route']=payload['route']
    specification={key:payload[key] for key in
                   ('truth_model','latitude_deg','profile','start','policy_id')}
    specification['model']=specification.pop('truth_model')
    return specification,configured


def _run_case(task,context,r,*,solver_provider=None):
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construct,error_law
    from .airquantumgrav_observation_truth import receiver_samples
    from .airquantumgrav_training_controls import _spec
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_native_error_training import ErrorTrainingFactory,ForecastErrorDiagnostic
    from .matched_candidate_case import run,MODELS
    from .matched_candidate_scoring import shape_first
    from .generated_receiver_target_check import score as receiver_score
    from .forecast_envelope_contrast import diagnose as contrast
    from .simultaneous_dual_target_wrapper import evaluate as simultaneous
    from .structured_noisy_study import _kernels
    from .structured_noisy_training import limits
    from .ilvis0_control_shards import _check_continue
    from .studies.artifacts import digest
    from .studies.journal import Journal

    payload=task['payload'];identity=task['identity'];law=payload['law']
    specification,configured=generated_case(payload,r)
    construction=limits(r,law)[1]
    journal=Journal(context.directory/'construction.sqlite',
                    freeze=digest((context.root/'manifest.json').read_bytes()),
                    limits={identity:construction})
    journal.start(identity)
    def check():
        _check_continue(context.root,context.manifest)
    def reserve_construction(**work):
        check()
        for key,value in work.items():
            journal.reserve(identity,key,value)
    budget=None
    try:
        noise,kernel_factory=_kernels(context,environment())
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                                   packet_visits=task['limits']['packet_visits']) as budget:
            material=construct(specification,configured,reserve=reserve_construction,
                               height_profile=payload['height_profile'])
            save=context.save
            save('training-receiver.json',material['training_rows'])
            save('noise-binding.json',material['binding'])
            anchor=material['training_rows'][0]['height_m']
            kernel,tangent,compilation=kernel_factory(anchor)
            save('compilation.json',compilation)
            factory=ErrorTrainingFactory(
                noise=error_law(configured['noise']),noise_kernel=noise,
                gravity_anchor_height_m=anchor,
                maximum_packets=len(material['dt']),
                maximum_queries=len(material['times']),maximum_bytes=64*1024**2,
                anchor_policy=r['covariance_anchor_policy'])
            physical=ForecastErrorDiagnostic(
                factory,target='physical_position',
                receiver_transform_policy=r['receiver_transform_policy'],
                bound_margin=r['bound_margin'],rank_rtol=r['rank_rtol'],
                estimability_rtol=r['estimability_rtol'],
                estimability_atol=r['estimability_atol'])
            receiver=ForecastErrorDiagnostic(
                factory,target='receiver_measurement',
                receiver_transform_policy=r['receiver_transform_policy'],
                bound_margin=r['bound_margin'],rank_rtol=r['rank_rtol'],
                estimability_rtol=r['estimability_rtol'],
                estimability_atol=r['estimability_atol'])
            artifacts={};native_calls=0
            def counted(**work):
                nonlocal native_calls
                check();budget.reserve(**work)
                native_calls+=work['native_calls']
            def fit_candidate(model,frozen,candidate_save):
                check();specific={}
                def record(name,value):
                    candidate_save(name,value)
                    if name in ('fit.json','bounded-physical.json',
                                'bounded-receiver.json',
                                'receiver-forecast-error-diagnostic.json'):
                        specific[name]=value
                def forecast_bound(problem,point,forecast,*,theta,dv,dt,times,reserve):
                    return simultaneous(physical,receiver,problem,point,forecast,
                                        theta=theta,dv=dv,dt=dt,times=times,
                                        reserve=reserve,save=record)
                result=train_and_forecast(
                    **{key:frozen[key] for key in ('theta','dv','dt','times')},
                    training_rows=frozen['training_rows'],time_origin_s=0.,
                    model=model,profile=False,policy_id=payload['policy_id'],
                    start=payload['start'],limits=r['limits'],
                    maximum_evaluations=r['maximum_evaluations'],
                    maximum_interval_s=1.5/r['rate_hz'],kernel=kernel,
                    tangent_kernel=tangent,reserve=counted,save=record,
                    check_continue=check,training_error_factory=factory,
                    forecast_error_diagnostic=forecast_bound,
                    clock=r['clock'],solver_provider=solver_provider)
                fit=result['fit']
                if (len(fit['active_parameters'])!=26
                        or result['training_epochs']!=len(frozen['training_rows'])):
                    raise ValueError('matched complete calibration columns required')
                artifacts[model]=specific
                return dict(converged=bool(fit['converged']),
                            evaluations=fit['evaluations'],
                            training_cost=fit['residual_sum_squares'])
            truth_args,sign=_spec({key:specification[key] for key in
                                  ('model','latitude_deg','profile','start')})
            if 'route' in payload:truth_args['route']=payload['route']
            def open_later():
                check();reserve_construction(generated_samples=len(material['times']))
                answer=receiver_samples(times=material['times'],sign=sign,
                                        **truth_args,
                                        height_profile=payload['height_profile'],
                                        gravity_model=r['gravity_model'])
                save('scoring-observations.json',
                     {key:value.tolist() for key,value in answer.items()})
                return answer
            outcome=run(material,MODELS,fit_candidate=fit_candidate,
                        save=save,open_later=open_later)
        journal.verify()
        if any(journal.count(identity,key)!=value
               for key,value in construction.items()):
            raise ValueError('matched construction differs from frozen accounting')
        future=outcome['truth']['coordinates'][len(material['training_rows']):]
        receiver_binding={'noise':material['binding']}
        score_rows={};envelopes={}
        for model in MODELS:
            item=artifacts[model]
            score_rows[model]=receiver_score(
                material['times'],outcome['truth']['coordinates'],
                material['training_rows'],receiver_binding,
                item['receiver-forecast-error-diagnostic.json'],
                item['bounded-receiver.json'])
            envelopes[model]=item['bounded-receiver.json']
        comparison=contrast(envelopes,future,target='receiver_measurement')
        if comparison['covered']!={model:score_rows[model]['all_later_coordinates_contained']
                                   for model in MODELS}:
            raise ValueError('receiver scoring and matched contrast disagree')
        convergence={model:outcome['candidates'][model]['converged'] for model in MODELS}
        staged=shape_first(comparison['covered'],convergence)
        save('matched-comparison.json',dict(
            input_binding=outcome['binding'],receiver_target=score_rows,
            contrast=comparison,convergence=convergence,shape_first=staged,
            later_observations_opened_after_all_bounds=True,
            empirical_coverage_calibrated=False,scientific_decision='abstain'))
        return dict(passed=True,technical_passed=True,
                    all_candidates_converged=all(convergence.values()),
                    candidate_fits=3,native_calls=native_calls,
                    training_epochs=len(material['training_rows']),
                    prediction_epochs=len(future),
                    shape=staged['shape'],background_field=staged['background_field'],
                    original_reads=0,protected_reads=0,
                    empirical_coverage_calibrated=False,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json',budget.snapshot())
        context.note_file(journal.path)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request-preflight','request-full',
                        'request-recovery','prepare-preflight','prepare-full',
                        'run-preflight','run-full'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    if args.action=='request-preflight':
        result=request_qualification(args.root,preflight=True)
    elif args.action=='request-full':
        result=request_qualification(args.root)
    elif args.action=='request-recovery':
        result=request_qualification(args.root,recovery=True)
    elif args.action in ('prepare-preflight','prepare-full'):
        short=args.action=='prepare-preflight'
        result=prepare(args.root,preflight=short,
                       qualification=QUALIFICATION_DIR+
                           ('preflight' if short else 'full')+
                           '-matched-candidates-v1-request.json',
                       recovery_qualification=QUALIFICATION_DIR+
                           'recovery-matched-candidates-v1-request.json')
    else:
        result=launch(args.root,preflight=args.action=='run-preflight')
    print(result)


if __name__=='__main__':
    main()
