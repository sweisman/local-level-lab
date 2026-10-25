# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite known-correction controls using shared forecast and study machinery."""
import math

from lll.airquantumgrav_truth import MODELS
from lll.airquantumgrav_geographic_controls import environment


def recipe():
    return dict(version='esa-known-observation-corrections-v1',duration_s=1200.,rate_hz=300,
        queries=1200,query_start_s=.5,query_step_s=1.,models=list(MODELS),
        latitudes_deg=[-55.,55.],removals=[0.,.35],signs=[-1,1],pattern='fast',method='linear_points',
        accuracy=dict(horizontal_rms_m=1.,vertical_rms_m=1.,maximum_3d_m=5.),
        value_agreement_m=.0001,difference_step=.000001,derivative_absolute_m=.5,derivative_relative=.002,
        workers=1,threads=4,maximum_wall_s=7200.,original_reads=0,observed_starts=0,retries=0)


def tasks():
    r=recipe();n=round(r['duration_s']*r['rate_hz']);result=[]
    for model in MODELS:
        for latitude in r['latitudes_deg']:
            for removal in r['removals']:
                for sign in r['signs']:
                    result.append(dict(identity=f"{model}-{'south' if latitude<0 else 'north'}-{int(removal*100)}-{sign}",
                        input_key='recipe',native_kind='mixed',payload=dict(model=model,latitude_deg=latitude,removal=removal,sign=sign),
                        limits=dict(native_calls=4,packet_visits=4*n*r['queries'],bound_calls=0,bound_steps=0)))
    return result


def parameter_limits():
    """Numerical fixture domain, deliberately unrelated to per-device claims."""
    values=dict(attitude=.05,velocity=2.,position=20.,gyro_bias=math.radians(1)/3600,
        accel_bias=.1,gyro_gain=.01,accel_gain=.02,lever=5.)
    return dict({name+'_'+axis:v for name,v in values.items() for axis in 'xyz'},gravity_delta=.05,time_offset=.01)


def value_prediction(problem,point,model,times,*,reserve):
    """Reuse the value predictor with new query epochs and no new observations.

    Only its output shape uses the placeholder GPS array. No residual, whitening
    or fit is called; the original training object remains unchanged.
    """
    import copy
    import numpy as np
    t=np.array(times,float,copy=True);p=problem.bounds.decode(point)
    if (t.ndim!=1 or not len(t) or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0)
            or t[0]+p['time_offset']<0 or t[-1]+p['time_offset']>np.cumsum(problem.dt)[-1]):
        raise ValueError('complete supported value-only forecast queries required')
    query=copy.copy(problem);query.gps_times=t;query.gps=np.zeros((len(t),3))
    reserve(native_calls=1,packet_visits=len(problem.dt)*len(t))
    return query.predict(point,model)


def calculate(spec,r,*,kernel,tangent,reserve,reserve_construction,save,check_continue):
    import numpy as np
    from lll.airquantumgrav_truth import truth
    from lll.airquantumgrav_observation_truth import observe,antenna,start
    from lll.airquantumgrav_geographic_controls import construct,position_errors,metrics
    from lll.ilvis0_shape import TangentProblem
    from lll.ilvis0_estimator import Bounds
    from lll.ilvis0_forecast import native_forecast
    from lll.studies.artifacts import digest
    if (set(spec)!=set(('model','latitude_deg','removal','sign')) or spec['model'] not in MODELS
            or spec['latitude_deg'] not in (-55.,55.) or spec['removal'] not in (0.,.35)
            or type(spec['sign']) is not int or spec['sign'] not in (-1,1)
            or r['rate_hz']!=300 or r['pattern']!='fast' or r['method']!='linear_points'
            or not math.isfinite(r['duration_s']) or not 2<=r['duration_s']<=1200
            or type(r['queries']) is not int or not 3<=r['queries']<=1200):
        raise ValueError('declared finite generated observation case required')
    hz=r['rate_hz'];n=round(r['duration_s']*hz)
    if n/hz!=r['duration_s']:raise ValueError('complete generated sampling support required')
    queries=r['query_start_s']+np.arange(r['queries'])*r['query_step_s']
    if (not np.all(np.isfinite(queries)) or np.any(np.diff(queries)<=0)
            or queries[0]<=.01 or queries[-1]+.01>=r['duration_s']):
        raise ValueError('queries require full timing-bound support')
    arguments={k:spec[k] for k in ('model','latitude_deg','removal')};arguments['pattern']=r['pattern']
    check_continue();reserve_construction(generated_samples=n+1)
    times=np.arange(n+1)/hz;geometric=truth(times=times,**arguments)
    raw=observe(geometric,sign=spec['sign']);raw['times']=times
    initial=start(geometric,model=spec['model'],sign=spec['sign'])
    increments=construct(raw,method=r['method'],rate_hz=hz,reserve=reserve_construction)
    reserve_construction(generated_samples=len(queries))
    answer=antenna(truth(times=queries+initial['parameters']['time_offset'],**arguments),sign=spec['sign'])
    limits=parameter_limits();count=int(math.ceil((queries[1]+limits['time_offset'])*hz))+1
    # Two analytic shape placeholders suffice: no receiver data are fitted here.
    problem=TangentProblem(increments['theta'][:count],increments['dv'][:count],increments['dt'][:count],
        queries[:2],answer['coordinates'][:2],np.eye(6),initial['initial'],Bounds(limits),
        tangent_kernel=tangent,kernel=kernel,fit_earth_removal=True,
        clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=1.5/hz,gravity_mps2=initial['gravity_mps2'],disc_radius_m=6371000.)
    parameters=initial['parameters'];point=np.array([2*spec['removal']-1 if name=='earth_removal'
        else parameters[name]/limits[name] for name in problem.bounds.active])
    problem.bounds.decode(point)
    save('corrections.json',dict(initial={k:v.tolist() if hasattr(v,'tolist') else v for k,v in initial['initial'].items()},
        parameters=parameters,limits=limits,normalized_parameters=point.tolist(),active_parameters=list(problem.bounds.active),
        gravity_mps2=initial['gravity_mps2'],removal=spec['removal'],known_corrections_supplied_not_estimated=True,
        original_rate_samples_sha256={k:digest(np.asarray(raw[k],dtype='<f8').tobytes())
            for k in ('times','angular_rate_rads','specific_force_mps2')},
        constructed_arrays_sha256={k:digest(np.asarray(increments[k],dtype='<f8').tobytes()) for k in ('theta','dv','dt')}))
    check_continue()
    forecast=native_forecast(problem,point,spec['model'],theta=increments['theta'],dv=increments['dv'],dt=increments['dt'],
        times=queries,maximum_interval_s=1.5/hz,reserve=lambda **v:reserve(native_kind='tangent',**v))
    # Value forecasts share the same raw history and starting state, without
    # allocating a dense covariance or fitting any placeholder observations.
    from copy import copy
    complete=copy(problem)
    for key in ('theta','dv','dt'):setattr(complete,key,increments[key])
    scale=np.array([6378137.,6378137.,1.]);output=forecast['coordinates']
    value_reserve=lambda **v:reserve(native_kind='value',**v)
    check_continue();value=value_prediction(complete,point,spec['model'],queries,reserve=value_reserve)
    direction=np.where(np.arange(len(point))%2,.25,-.25);direction[-1]=.25
    shifted=point+r['difference_step']*direction;problem.bounds.decode(shifted)
    check_continue();near=value_prediction(complete,shifted,spec['model'],queries,reserve=value_reserve)
    zero=np.zeros_like(point);zero[-1]=point[-1]
    check_continue();uncorrected=value_prediction(complete,zero,spec['model'],queries,reserve=value_reserve)
    derivative=(forecast['jacobian']@direction).reshape(-1,3)*scale
    finite=(near-value)*scale/r['difference_step']
    derivative_error=float(np.max(abs(derivative-finite)));derivative_size=float(np.max(abs(derivative)))
    disagreement=float(np.max(abs((output-value)*scale)))
    errors=position_errors(output,answer,model=spec['model']);corrected=metrics(errors)
    uncorrected_errors=position_errors(uncorrected,answer,model=spec['model']);unadjusted=metrics(uncorrected_errors)
    retained=forecast['active_parameters']==list(problem.bounds.active) and forecast['jacobian'].shape==(3*len(queries),27)
    checks={k:corrected[k]<=limit for k,limit in r['accuracy'].items()}
    checks.update(value_agreement=disagreement<=r['value_agreement_m'],all_columns_retained=retained,
        mixed_derivative=derivative_error<=r['derivative_absolute_m']+r['derivative_relative']*derivative_size)
    save('forecast.json',dict(times_s=queries.tolist(),coordinates=output.tolist(),errors_neu_m=errors.tolist(),
        corrected=corrected,uncorrected_errors_neu_m=uncorrected_errors.tolist(),uncorrected=unadjusted,
        jacobian_sha256=digest(np.asarray(forecast['jacobian'],dtype='<f8').tobytes()),
        continuous_propagation_without_gps_reset=True,generated_not_observed=True))
    save('comparison.json',dict(value_coordinates=value.tolist(),shifted_coordinates=near.tolist(),
        uncorrected_coordinates=uncorrected.tolist(),direction=direction.tolist(),step=r['difference_step'],
        analytic_direction_scaled_m=derivative.tolist(),value_disagreement_m=disagreement,
        derivative_disagreement_m=derivative_error,derivative_size_m=derivative_size,checks=checks))
    return dict(passed=bool(all(checks.values())),**spec,corrected=corrected,uncorrected=unadjusted,checks=checks,
        value_disagreement_m=disagreement,derivative_disagreement_m=derivative_error,
        all_columns_retained=retained,known_corrections_supplied_not_estimated=True,
        initialization_estimator_qualified=False,native_calls=4,constructed_intervals=n,generated_samples=n+1+len(queries),
        original_reads=0,observed_starts=0,actual_sampling_established=False,confidence_calibrated=False,
        scientific_decision='abstain')


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_observation_controls.py',
        'analysis/tests/test_airquantumgrav_observation_controls.py','analysis/tests/test_study_mixed_native_charges.py',
        'analysis/lll/studies/qualification.py','analysis/lll/ilvis0_control_shards.py',
        'docs/esa-observation-controls/PLAN.md','analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_shape.py'])


def required_tests():
    names=['test_observation_matrix_has_finite_charges_for_every_identity',
        'test_observation_truth_does_not_import_navigation_or_calibration_implementation',
        'test_observation_prepare_rejects_missing_source_qualification_before_writing',
        'test_observation_bad_recipe_rejected_before_native_execution',
        'test_observation_definition_accepts_actual_runner_assignment_fields',
        'test_observation_evaluator_preserves_construction_journal_and_actual_native_kinds',
        'test_fixed_native_kind_and_bound_reservations_cannot_be_reclassified']
    names += [f'test_mixed_native_calls_keep_each_actual_kind_and_one_combined_allowance[{v}]' for v in ('receipts-v1','sqlite-v1')]
    names += [f'test_mixed_context_rejects_missing_or_invalid_operation_kind_before_charging[{v}]' for v in ('None','mixed','undeclared')]
    names += [f'test_observation_channels_apply_bias_and_gain_in_measurement_direction[{s}]' for s in (-1,1)]
    for name in ('test_antenna_truth_is_independent_cartesian_body_displacement',
                 'test_generated_start_corrections_return_true_state_without_navigation_helpers'):
        names += [f'{name}[{s}-{m}]' for s in (-1,1) for m in MODELS]
    names += [f'test_observation_truth_rejects_unsupported_inputs[{v}]' for v in ('sign','shape','nonfinite','model')]
    names += [f'test_known_observation_corrections_match_cartesian_truth_with_all_columns[{s}-{lat}-{m}]'
        for s in (-1,1) for lat in (-55.,55.) for m in MODELS]
    return names


def prepare(root,*,qualification,identity='esa-observation-controls-20261023'):
    import re
    from pathlib import Path
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if qualification is None:raise ValueError('passing source-bound software qualification required')
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('fresh safe observation control identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh observation study required')
    source=sources(root);env=environment()
    request,report=checked(root,qualification,sources=source,environment=env,
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    base.mkdir(parents=True);r=recipe();inputs={}
    for key,name,raw in [('recipe','recipe.json',encoded(r)),('qualification-request','qualification-request.json',request),
                         ('qualification-report','qualification-report.xml',report),
                         ('qualification-environment','qualification-environment.json',encoded(env))]:
        atomic(base/name,raw);inputs[key]=str((base/name).relative_to(root))
    definition=dict(id=identity,adapter='analysis/lll/airquantumgrav_observation_controls.py',sources=source,
        inputs=inputs,tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=len(tasks()),limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import json
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    r=recipe();canonical={v['identity']:v for v in tasks()}
    declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if json.loads(context.input_path().read_bytes())!=r or canonical.get(task['identity'])!=declared:
        raise ValueError('unchanged frozen observation recipe, identity and limits required')
    if json.loads(context.input_path('qualification-environment').read_bytes())!=environment():
        raise ValueError('qualified observation environment differs')
    n=round(r['duration_s']*r['rate_hz']);counts=dict(constructed_intervals=n,generated_samples=n+1+r['queries'])
    journal=Journal(context.directory/'construction.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:counts});journal.start(task['identity'])
    try:
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
        kernel,km=load_kernel(directory);tangent,tm=load_tangent(directory)
        for filename,metadata in [('ilvis0_native.c',km),('ilvis0_tangent.cpp',tm)]:
            if metadata['source_sha256']!=context.manifest['sources']['analysis/lll/'+filename]:
                raise ValueError('compiled observation control source differs')
        context.save('compilation.json',dict(value=km,tangent=tm))
        def reserve(**values):
            for key,value in values.items():journal.reserve(task['identity'],key,value)
        result=calculate(task['payload'],r,kernel=kernel,tangent=tangent,reserve=context.charge,
            reserve_construction=reserve,save=context.save,check_continue=lambda:_check_continue(context.root,context.manifest))
        journal.verify()
        if any(journal.count(task['identity'],k)!=v for k,v in counts.items()):
            raise ValueError('observation construction charges differ from finite recipe')
        return result
    finally:context.note_file(journal.path)
