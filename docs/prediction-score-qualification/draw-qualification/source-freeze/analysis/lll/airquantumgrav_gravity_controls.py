# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated gravity controls using shared motion and study components."""
import itertools
import math

from lll.airquantumgrav_inventory import environment
from lll.airquantumgrav_truth import MODELS

SCOPE='generated known-correction gravity controls only; no fits or original/protected reads'


def recipe():
    return dict(version='esa-height-gravity-controls-v1',duration_s=1200.,rates_hz=[300,600],
        query_start_s=30.001,query_step_s=30.,queries=39,models=list(MODELS),latitudes_deg=[-55.,55.],
        removals=[0.,.35],gravity_models=['constant','inverse_square_height'],height_profiles=['climb','descend'],
        pattern='fast',method='linear_points',calibration_sign='latitude_sign',
        accuracy=dict(horizontal_rms_m=1.,vertical_rms_m=1.,maximum_3d_m=5.),
        refinement_factor=.4,refinement_allowance_m=.001,value_agreement_m=.001,
        workers=4,threads=1,maximum_wall_s=3600.,original_reads=0,protected_reads=0,observed_starts=0,retries=0)


def construction_limits(r):
    intervals=sum(round(r['duration_s']*hz) for hz in r['rates_hz'])
    return dict(constructed_intervals=intervals,generated_samples=intervals+len(r['rates_hz'])+r['queries'])


def tasks():
    r=recipe();result=[];packets=round(r['duration_s']*(2*r['rates_hz'][0]+r['rates_hz'][1]))
    keys=('model','latitude_deg','removal','gravity_model','height_profile')
    for values in itertools.product(r['models'],r['latitudes_deg'],r['removals'],r['gravity_models'],r['height_profiles']):
        spec=dict(zip(keys,values,strict=True));model,lat,removal,gravity,profile=values
        identity=f"{model}-{'south' if lat<0 else 'north'}-{int(removal*100)}-{gravity}-{profile}"
        result.append(dict(identity=identity,input_key='recipe',native_kind='mixed',payload=spec,
            limits=dict(native_calls=3,packet_visits=packets*r['queries'],bound_calls=0,bound_steps=0)))
    return result


def checks(phases,*,value_disagreement_m,all_columns_retained,r):
    if len(phases)!=2:raise ValueError('both fixed rate summaries required')
    accuracy=[{k:math.isfinite(phase[k]) and 0<=phase[k]<=limit for k,limit in r['accuracy'].items()} for phase in phases]
    refinement=phases[1]['maximum_3d_m']<=r['refinement_factor']*phases[0]['maximum_3d_m']+r['refinement_allowance_m']
    agreement=math.isfinite(value_disagreement_m) and 0<=value_disagreement_m<=r['value_agreement_m']
    passed=all(all(v.values()) for v in accuracy) and refinement and agreement and all_columns_retained
    return dict(passed=bool(passed),accuracy=accuracy,refinement=bool(refinement),value_agreement=bool(agreement),
        all_columns_retained=bool(all_columns_retained))


def calculate(spec,r,*,kernel,tangent,reserve,reserve_construction,save,check_continue):
    import copy
    import numpy as np
    from lll.airquantumgrav_truth import truth
    from lll.airquantumgrav_observation_truth import observe,antenna,start
    from lll.airquantumgrav_geographic_controls import construct,position_errors,metrics
    from lll.airquantumgrav_observation_controls import parameter_limits,value_prediction
    from lll.ilvis0_estimator import Bounds
    from lll.ilvis0_shape import TangentProblem,PARAMETERS
    from lll.ilvis0_forecast import native_forecast
    from lll.studies.artifacts import digest,encoded
    canonical=recipe();keys=('model','latitude_deg','removal','gravity_model','height_profile')
    if (set(spec)!=set(keys) or any(spec[k] not in canonical[v] for k,v in zip(keys,
            ('models','latitudes_deg','removals','gravity_models','height_profiles'),strict=True))
            or r['rates_hz']!=[300,600] or r['pattern']!='fast' or r['method']!='linear_points'
            or not 2<=r['duration_s']<=1200 or type(r['queries']) is not int or not 3<=r['queries']<=39):
        raise ValueError('one declared finite generated gravity identity required')
    queries=r['query_start_s']+np.arange(r['queries'])*r['query_step_s'];limits=parameter_limits()
    if (not np.all(np.isfinite(queries)) or np.any(np.diff(queries)<=0) or queries[0]<=.01
            or queries[-1]+.01>=r['duration_s']):raise ValueError('whole fixed timing-bound query support required')
    sign=1 if spec['latitude_deg']>0 else -1;arguments=dict(spec,pattern=r['pattern'])
    phases=[];answer=None;first_initial=None;disagreement=None;retained=False
    for hz in r['rates_hz']:
        check_continue();n=round(r['duration_s']*hz)
        if n/hz!=r['duration_s']:raise ValueError('complete generated-rate support required')
        reserve_construction(generated_samples=n+1)
        times=np.arange(n+1)/hz;geometric=truth(times=times,**arguments)
        initial=start(geometric,model=spec['model'],sign=sign);raw=observe(geometric,sign=sign);raw['times']=times
        signature=dict(initial={k:v.tolist() if hasattr(v,'tolist') else v for k,v in initial['initial'].items()},
            parameters=initial['parameters'],gravity_mps2=initial['gravity_mps2'])
        if first_initial is None:
            first_initial=signature;reserve_construction(generated_samples=len(queries))
            answer=antenna(truth(times=queries+initial['parameters']['time_offset'],**arguments),sign=sign)
            save('answer.json',dict(times_s=queries.tolist(),known_not_fitted=True,
                **{k:answer[k].tolist() for k in ('position_world_m','body_axes_world','attitude_body_to_local')}))
            save('corrections.json',dict(**signature,limits=limits,known_corrections_supplied_not_estimated=True,
                anchor_height_m=1500. if spec['height_profile']=='climb' else 3500.))
        elif encoded(signature)!=encoded(first_initial):raise ValueError('sample rates changed the known physical start')
        increments=construct(raw,method=r['method'],rate_hz=hz,reserve=reserve_construction)
        count=int(math.ceil((queries[1]+limits['time_offset'])*hz))+1
        # Shape placeholders are never fitted and provide no initial state.
        problem=TangentProblem(increments['theta'][:count],increments['dv'][:count],increments['dt'][:count],
            queries[:2],np.zeros((2,3)),np.eye(6),initial['initial'],Bounds(limits),
            fit_earth_removal=True,kernel=kernel,tangent_kernel=tangent,clock_hypothesis='header_elapsed',
            processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=1.5/hz,
            gravity_mps2=initial['gravity_mps2'],disc_radius_m=6371000.)
        point=np.array([2*spec['removal']-1 if key=='earth_removal' else initial['parameters'][key]/limits[key]
            for key in problem.bounds.active]);problem.bounds.decode(point)
        complete=copy.copy(problem)
        for key in ('theta','dv','dt'):setattr(complete,key,increments[key])
        check_continue();value=value_prediction(complete,point,spec['model'],queries,
            reserve=lambda **v:reserve(native_kind='value',**v))
        errors=position_errors(value,answer,model=spec['model']);summary=metrics(errors);phases.append(summary)
        save(f'rate-{hz}.json',dict(rate_hz=hz,packets=n,times_s=queries.tolist(),coordinates=value.tolist(),
            errors_neu_m=errors.tolist(),metrics=summary,generated_not_observed=True,
            original_rate_samples_sha256={k:digest(np.asarray(raw[k],dtype='<f8').tobytes()) for k in
                ('times','angular_rate_rads','specific_force_mps2')},
            constructed_arrays_sha256={k:digest(np.asarray(increments[k],dtype='<f8').tobytes()) for k in ('theta','dv','dt')}))
        if hz==r['rates_hz'][0]:
            check_continue();prediction=native_forecast(problem,point,spec['model'],times=queries,
                **{k:increments[k] for k in ('theta','dv','dt')},maximum_interval_s=1.5/hz,
                reserve=lambda **v:reserve(native_kind='tangent',**v))
            scale=np.array([6378137.,6378137.,1.]);disagreement=float(np.max(abs((prediction['coordinates']-value)*scale)))
            retained=prediction['active_parameters']==list(PARAMETERS) and prediction['jacobian'].shape==(3*len(queries),27)
            save('tangent.json',dict(coordinates=prediction['coordinates'].tolist(),jacobian=prediction['jacobian'].tolist(),
                active_parameters=prediction['active_parameters'],normalized_parameters=point.tolist(),value_disagreement_m=disagreement))
        del geometric,raw,increments,problem,complete
    result=checks(phases,value_disagreement_m=disagreement,all_columns_retained=retained,r=r)
    return dict(**spec,passed=result['passed'],checks=result,coarse=phases[0],fine=phases[1],
        all_columns_retained=retained,value_disagreement_m=disagreement,
        known_corrections_supplied_not_estimated=True,constructed_intervals=construction_limits(r)['constructed_intervals'],
        generated_samples=construction_limits(r)['generated_samples'],native_calls=3,
        original_reads=0,observed_starts=0,protected_reads=0,confidence_calibrated=False,scientific_decision='abstain')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_gravity_controls.py',
        'analysis/lll/airquantumgrav_gravity_report.py','analysis/tests/test_airquantumgrav_gravity_controls.py',
        'analysis/tests/test_airquantumgrav_gravity_calculation.py','analysis/tests/test_airquantumgrav_gravity_report.py',
        'analysis/tests/test_ilvis0_height_gravity.py','analysis/tests/test_airquantumgrav_gravity_truth.py',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','docs/esa-gravity-controls/PLAN.md',
        'docs/esa-gravity-controls/IMPLEMENTATION.md'])


def required_tests():
    names=['test_gravity_matrix_has_separate_finite_48_case_allowance',
        'test_gravity_study_requires_qualification_before_any_files',
        'test_gravity_comparison_cannot_pass_missing_accuracy_or_columns',
        'test_gravity_calculation_rejects_unknown_identity_before_native_work',
        'test_gravity_reporting_rejects_open_study_before_numerical_imports',
        'test_known_correction_controls_cannot_claim_observed_or_training_qualification',
        'test_truth_rejects_undeclared_gravity_or_height_profiles']+[
        f'test_short_known_correction_calculation_counts_all_work_and_preserves_columns[{g}-{m}]'
        for g in recipe()['gravity_models'] for m in MODELS]
    names += [f'{name}[{p}-{m}]' for name in ('test_constant_mode_preserves_archived_values_and_all_derivatives',
        'test_height_gravity_values_and_every_active_column_match') for p in (False,True) for m in MODELS]
    names += [f'test_known_vertical_motion_uses_predicted_midpoint_height[{v}]' for v in ('0.0','50.0','-50.0')]
    names += [f'test_invalid_gravity_anchor_rejected_before_compilation[{v}]' for v in ('nan','inf','-6371000.0','-6371001.0')]
    names += [f'test_default_truth_is_exactly_the_frozen_constant_gravity_truth[{m}]' for m in MODELS]
    names += [f'test_generated_height_profiles_have_declared_endpoints_and_zero_endpoint_climb[{p}-heights{i}]'
        for i,p in enumerate(recipe()['height_profiles'])]
    names += [f'test_height_gravity_changes_only_specific_force_with_independent_sign_and_scale[{p}-{m}]'
        for p in recipe()['height_profiles'] for m in MODELS]
    names += [f'test_climbing_cartesian_acceleration_matches_independent_position_differences[{m}]' for m in MODELS]
    return names


def prepare(root,*,qualification,identity='esa-height-gravity-controls-20261023'):
    if qualification is None:raise ValueError('source-bound generated gravity qualification required')
    import re
    from pathlib import Path
    from lll.compute_budget import environment as thread_environment
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.studies.closed import ClosedStudy
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh generated scope required')
    env=environment();r=recipe()
    if env['numerical_environment']!=thread_environment(workers=r['workers'],threads=r['threads']):
        raise ValueError('prepare under the declared thread environment')
    sources=qualification_sources(root)
    request,report=checked(root,qualification,sources=sources,environment=env,required_tests=required_tests(),minimum_tests=len(required_tests()))
    previous=ClosedStudy(root,'docs/esa-development-pilot')
    try:reference=dict(manifest_sha256=previous.completion['manifest_sha256'],sources={key:previous.manifest['sources']['analysis/lll/'+key]
        for key in ('ilvis0_native.c','ilvis0_tangent.cpp','airquantumgrav_truth.py')},purpose='historical constant compatibility only')
    finally:previous.close()
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate([('recipe',encoded(r)),('qualification-request',request),('qualification-report',report),
            ('qualification-environment',encoded(env)),('compatibility-reference',encoded(reference))]):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_gravity_controls.py',sources=sources,inputs=inputs,
        tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,allocation=manifest['allocation'],limits=manifest['limits'],cases=len(tasks()))


def evaluate(task,context):
    import json
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    r=recipe();declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if ({v['identity']:v for v in tasks()}.get(task['identity'])!=declared
            or json.loads(context.input_path().read_bytes())!=r
            or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()
            or context.manifest['scope']!=SCOPE):raise ValueError('unchanged qualified gravity scope and environment required')
    counts=construction_limits(r);journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:counts});journal.start(task['identity'])
    try:
        spec=task['payload'];anchor=None if spec['gravity_model']=='constant' else (1500. if spec['height_profile']=='climb' else 3500.)
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
        kernel,km=load_kernel(directory,gravity_anchor_height_m=anchor);tangent,tm=load_tangent(directory,gravity_anchor_height_m=anchor)
        env=environment()
        for filename,metadata,compiler in [('ilvis0_native.c',km,'cc'),('ilvis0_tangent.cpp',tm,'c++')]:
            if (metadata['source_sha256']!=context.manifest['sources']['analysis/lll/'+filename]
                    or metadata['compiler']!=env['compilers'][compiler]):raise ValueError('compiled gravity source/environment differs')
        context.save('compilation.json',dict(value=km,tangent=tm))
        def reserve_construction(**work):
            _check_continue(context.root,context.manifest)
            for key,value in work.items():journal.reserve(task['identity'],key,value)
        result=calculate(spec,r,kernel=kernel,tangent=tangent,reserve=context.charge,
            reserve_construction=reserve_construction,save=context.save,
            check_continue=lambda:_check_continue(context.root,context.manifest))
        journal.verify()
        if any(journal.count(task['identity'],k)!=v for k,v in counts.items()):raise ValueError('complete generated construction charges required')
        return result
    finally:context.note_file(journal.path)
