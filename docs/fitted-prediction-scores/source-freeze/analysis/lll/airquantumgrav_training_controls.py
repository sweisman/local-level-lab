# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite ESA-rate training/forecast controls without observed recordings."""
import math

from lll.airquantumgrav_truth import MODELS,A,E2,DISC_RADIUS
from lll.airquantumgrav_geographic_controls import environment


def parameter_limits():
    values=dict(attitude=.25,velocity=20.,position=100.,gyro_bias=math.radians(1)/3600,
        accel_bias=.1,gyro_gain=.01,accel_gain=.02,lever=5.)
    return dict({name+'_'+axis:v for name,v in values.items() for axis in 'xyz'},
        attitude_z=math.pi,gravity_delta=.1,time_offset=.01)


def recipe():
    return dict(version='esa-generated-training-forecast-v1',duration_s=120.,rate_hz=300,
        queries=119,query_start_s=.5,query_step_s=1.,pattern='fast',method='linear_points',
        models=list(MODELS),latitudes_deg=[-55.,55.],profiles=[False,True],starts=2,
        limits=parameter_limits(),training_sigma_m=.01,maximum_evaluations=200,stopping='near_zero',
        accuracy=dict(horizontal_rms_m=.1,vertical_rms_m=.1,maximum_3d_m=.5),
        workers=1,threads=4,maximum_wall_s=7200.,original_reads=0,observed_starts=0,retries=0)


def tasks():
    r=recipe();n=round(r['duration_s']*r['rate_hz']);calls=r['maximum_evaluations']+1;result=[]
    for model in MODELS:
        for latitude in r['latitudes_deg']:
            for profile in r['profiles']:
                for start in range(r['starts']):
                    result.append(dict(identity=f"{model}-{'south' if latitude<0 else 'north'}-{int(profile)}-{start}",
                        input_key='recipe',native_kind='tangent',payload=dict(model=model,latitude_deg=latitude,profile=profile,start=start),
                        limits=dict(native_calls=calls,packet_visits=calls*n*r['queries'],bound_calls=0,bound_steps=0)))
    return result


def _spec(spec):
    if (set(spec)!=set(('model','latitude_deg','profile','start')) or spec['model'] not in MODELS
            or spec['latitude_deg'] not in (-55.,55.) or type(spec['profile']) is not bool
            or type(spec['start']) is not int or spec['start'] not in (0,1)):
        raise ValueError('one declared generated training identity required')
    return dict(model=spec['model'],latitude_deg=spec['latitude_deg'],pattern='fast',
        removal=.35 if spec['profile'] else 0.),-1 if spec['profile'] else 1


def generated_training(spec,r,*,reserve,height_profile=None,gravity_model='constant'):
    """Expose raw generated channels and earlier positions; no true starting state."""
    import numpy as np
    from lll.airquantumgrav_truth import truth
    from lll.airquantumgrav_observation_truth import observe,receiver_samples
    from lll.airquantumgrav_geographic_controls import construct
    from lll.ilvis0_prediction import split
    arguments,sign=_spec(spec)
    if (height_profile not in (None,'climb','descend') or gravity_model not in ('constant','inverse_square_height')
            or (height_profile is None and gravity_model!='constant')):
        raise ValueError('explicit supported height and gravity construction required')
    maximum_duration,maximum_queries=(120.,119) if height_profile is None else (1200.,1200)
    if height_profile is not None:arguments.update(height_profile=height_profile,gravity_model=gravity_model)
    if (r['rate_hz']!=300 or not math.isfinite(r['duration_s']) or not 2<=r['duration_s']<=maximum_duration
            or type(r['queries']) is not int or not 9<=r['queries']<=maximum_queries
            or r['pattern']!='fast' or r['method']!='linear_points'):
        raise ValueError('declared finite training construction required')
    n=round(r['duration_s']*r['rate_hz']);times=r['query_start_s']+np.arange(r['queries'])*r['query_step_s']
    layout=split(times);cut=layout['training_epochs'];offset=r['limits']['time_offset']
    if n/r['rate_hz']!=r['duration_s'] or times[0]-offset<0 or times[-1]+offset>=r['duration_s']:
        raise ValueError('complete generated timing support required')
    reserve(generated_samples=n+1);rate_times=np.arange(n+1)/r['rate_hz']
    geometric=truth(times=rate_times,**arguments);raw=observe(geometric,sign=sign);del geometric
    raw['times']=rate_times
    increments=construct(raw,method=r['method'],rate_hz=r['rate_hz'],reserve=reserve)
    reserve(generated_samples=cut)
    training=receiver_samples(times=times[:cut],sign=sign,**arguments)['coordinates']
    return dict(**{k:increments[k] for k in ('theta','dv','dt')},rate_times=rate_times,
        angular_rate_rads=raw['angular_rate_rads'],specific_force_mps2=raw['specific_force_mps2'],
        times=times,training_gps=training,training_epochs=cut)


def training_covariance(gps,model,*,sigma_m):
    """Fixed software weight in the generating metric, from earlier coordinates only."""
    import numpy as np
    g=np.asarray(gps,float)
    if (model not in MODELS or g.ndim!=2 or g.shape[1:]!=(3,) or not len(g)
            or not np.all(np.isfinite(g)) or np.any(abs(g[:,0])>=math.pi/2)
            or not math.isfinite(sigma_m) or sigma_m<=0):
        raise ValueError('finite training coordinates and fixed positive software sigma required')
    phi,h=g[:,0],g[:,2]
    if model=='flat_still':mn=np.full(len(g),DISC_RADIUS);me=DISC_RADIUS*(math.pi/2-phi)
    else:
        q=1-E2*np.sin(phi)**2;mn=A*(1-E2)/q**1.5+h;me=(A/np.sqrt(q)+h)*np.cos(phi)
    scale=np.column_stack((mn,me,np.ones(len(g))))
    if np.any(scale<=0):raise ValueError('positive generating coordinate metric required')
    return np.diag(np.square(sigma_m/scale).ravel())


def calculate(spec,r,*,kernel,tangent,reserve,reserve_construction,save,save_bytes,check_continue):
    import io
    import numpy as np
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.airquantumgrav_geographic_controls import position_errors,metrics
    from lll.ilvis0_training_forecast import training_problem,fit_training
    from lll.ilvis0_forecast import native_forecast
    from lll.studies.artifacts import digest
    arguments,sign=_spec(spec)
    if r['stopping']!='near_zero' or type(r['maximum_evaluations']) is not int or not 8<=r['maximum_evaluations']<=200:
        raise ValueError('unchanged stopping policy and finite evaluation allowance required')
    check_continue();material=generated_training(spec,r,reserve=reserve_construction)
    buffer=io.BytesIO();np.savez_compressed(buffer,**{k:v for k,v in material.items() if k not in ('training_gps','training_epochs')})
    save_bytes('raw-inputs.npz',buffer.getvalue());times=material['times'];cut=material['training_epochs']
    train=material['training_gps'];count=int(np.searchsorted(np.cumsum(material['dt']),times[cut-1]+r['limits']['time_offset'],side='left'))+1
    save('training-observations.json',dict(times_s=times[:cut].tolist(),coordinates=train.tolist(),training_epochs=cut,
        native_prefix_packets=count,maximum_interval_s=1.5/r['rate_hz'],limits=r['limits'],
        training_sigma_m=r['training_sigma_m'],true_initial_state_supplied=False,true_calibration_supplied=False,
        raw_arrays_sha256={k:digest(np.asarray(material[k],dtype='<f8').tobytes())
            for k in ('theta','dv','dt','rate_times','angular_rate_rads','specific_force_mps2')},
        training_prefix_sha256={k:digest(np.asarray(material[k][:count],dtype='<f8').tobytes()) for k in ('theta','dv','dt')}))
    covariance=training_covariance(train,spec['model'],sigma_m=r['training_sigma_m'])
    problem=training_problem(times[:cut],train,theta=material['theta'][:count],dv=material['dv'][:count],dt=material['dt'][:count],
        covariance=covariance,model=spec['model'],limits=r['limits'],profile=spec['profile'],clock='header_elapsed',
        maximum_interval_s=1.5/r['rate_hz'],kernel=kernel,tangent_kernel=tangent)
    point=np.zeros(len(problem.bounds.active)) if spec['start']==0 else np.where(np.arange(len(problem.bounds.active))%2,.001,-.001)
    check_continue();fit=fit_training(problem,spec['model'],start=point,maximum_evaluations=r['maximum_evaluations'],
        reserve=reserve,stopping=r['stopping']);save('fit.json',fit)
    check_continue();forecast=native_forecast(problem,fit['normalized_parameters'],spec['model'],
        theta=material['theta'],dv=material['dv'],dt=material['dt'],times=times,maximum_interval_s=1.5/r['rate_hz'],reserve=reserve)
    save('forecast.json',dict(coordinates=forecast['coordinates'].tolist(),times_s=times.tolist(),
        active_parameters=forecast['active_parameters'],training_epochs=cut,prediction_epochs=len(times)-cut,
        continuous_propagation_without_gps_reset=True,prediction_receiver_positions_used=False))
    # Scoring geometry is generated only after the continuous forecast is saved.
    check_continue();reserve_construction(generated_samples=len(times))
    answer=receiver_samples(times=times,sign=sign,**arguments)
    save('scoring-observations.json',{k:v.tolist() for k,v in answer.items()})
    if not np.array_equal(answer['coordinates'][:cut],train):
        raise ValueError('earlier scoring positions differ from the unchanged training observations')
    errors=position_errors(forecast['coordinates'],answer,model=spec['model'])
    sections={name:metrics(errors[section]) for name,section in [('training',slice(0,cut)),('prediction',slice(cut,None))]}
    save('scores.json',dict(times_s=times.tolist(),errors_neu_m=errors.tolist(),**sections,
        training_positions_reproduced_for_scoring=bool(np.array_equal(answer['coordinates'][:cut],train))))
    retained=(forecast['active_parameters']==list(problem.bounds.active)==fit['active_parameters']
        and len(problem.bounds.active)==26+int(spec['profile']))
    accuracy={name:{key:value[key]<=limit for key,limit in r['accuracy'].items()} for name,value in sections.items()}
    passed=fit['converged'] and retained and all(v for values in accuracy.values() for v in values.values())
    return dict(passed=bool(passed),**spec,converged=fit['converged'],evaluations=fit['evaluations'],
        native_calls=fit['evaluations']+1,training_cost=fit['residual_sum_squares'],all_columns_retained=retained,
        training_epochs=cut,prediction_epochs=len(times)-cut,**sections,accuracy=accuracy,
        true_initial_state_supplied=False,true_calibration_supplied=False,
        forecast_saved_before_scoring=True,constructed_intervals=len(material['dt']),
        generated_samples=len(material['dt'])+1+cut+len(times),original_reads=0,observed_starts=0,
        actual_sampling_established=False,confidence_calibrated=False,scientific_decision='abstain')


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_training_controls.py',
        'analysis/tests/test_airquantumgrav_training_controls.py','analysis/tests/test_study_binary_artifacts.py',
        'analysis/tests/test_ilvis0_control_shards.py','analysis/tests/test_ilvis0_training_forecast.py',
        'analysis/lll/studies/qualification.py','analysis/lll/ilvis0_control_shards.py',
        'docs/esa-training-forecast-controls/PLAN.md','analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_shape.py'])


def required_tests():
    names=['test_training_matrix_preserves_the_declared_finite_fit_and_forecast_allowance',
        'test_generated_training_material_exposes_no_later_position_or_true_start',
        'test_training_weights_use_training_coordinate_metric_and_fixed_sigma_only',
        'test_training_preparation_requires_software_qualification_before_any_write',
        'test_training_bad_recipe_rejected_before_loading_or_charging',
        'test_changed_earlier_scoring_positions_are_rejected_after_forecast',
        'test_training_definition_and_isolated_dependencies_cover_native_inputs',
        'test_binary_artifact_is_saved_and_hash_bound_without_json_conversion',
        'test_binary_artifact_rejects_paths_and_sealed_context_before_writing']
    names += [f'test_later_positions_open_after_saved_forecast_and_cannot_change_training_fit[{p}]' for p in (False,True)]
    names += [f'test_generated_receiver_samples_include_latency_and_antenna_without_fused_navigation[{s}-{m}]'
        for s in (-1,1) for m in MODELS]
    names += [f'test_independent_receiver_coordinates_match_known_nonzero_antenna_geometry[{m}]' for m in MODELS]
    names += [f'test_independent_receiver_coordinate_failures_are_not_repaired[{v}]'
        for v in ('empty','shape','nonfinite','origin','disc_domain','model')]
    names += [f'test_independent_receiver_coordinates_recover_oblique_ellipsoid_point[{s}]' for s in (-1,1)]
    names += [f'test_independent_receiver_coordinates_recover_equator_without_fitted_height[{m}]' for m in MODELS[:2]]
    return names


def qualified_parents(root):
    """Check closed parents and unchanged numerical code, never refit them."""
    import ast
    from pathlib import Path
    from lll.airquantumgrav_observation_report import inspect
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    root=Path(root).resolve();report=inspect(root)
    if not report['qualified']:raise ValueError('known-correction calculation must qualify before training fits')
    proof={};core=('ilvis0_native.c','ilvis0_tangent.cpp','ilvis0_shape.py','ilvis0_exploratory.py',
        'ilvis0_estimator.py','ilvis0_forward.py','ilvis0_forecast.py')
    for prefix,files in [('docs/esa-observation-controls',core+('airquantumgrav_truth.py','airquantumgrav_geographic_controls.py')),
        ('docs/ilvis0-near-zero-forecast-controls',core+('ilvis0_near_zero.py','ilvis0_training_forecast.py',
            'ilvis0_corpus_modeling.py','ilvis0_solver_trust_v2.py','ilvis0_solver_position.py',
            'ilvis0_solver_refinement.py','ilvis0_solver_boundary.py'))]:
        parent=ClosedStudy(root,prefix)
        try:
            if not parent.summary['passed']:raise ValueError('complete qualified numerical parent required')
            for filename in files:
                name='analysis/lll/'+filename
                if digest((root/name).read_bytes())!=parent.manifest['sources'].get(name):
                    raise ValueError('qualified parent numerical source changed: '+filename)
            proof[prefix]=dict(manifest_sha256=parent.completion['manifest_sha256'],summary_sha256=parent.completion['summary_sha256'])
            if prefix=='docs/esa-observation-controls':
                name='analysis/lll/airquantumgrav_observation_truth.py'
                old=ast.parse(parent.read('source-freeze/'+name,parent.manifest['sources'][name],raw=True));new=ast.parse((root/name).read_bytes())
                functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
                before,after=functions(old),functions(new)
                if any(before[k]!=after.get(k) for k in ('_check','_parameters','observe','antenna','start')):
                    raise ValueError('qualified synthetic sensor/antenna definition changed')
        finally:parent.close()
    return proof


def prepare(root,*,qualification,identity='esa-training-forecast-controls-20261023'):
    import re
    from pathlib import Path
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if qualification is None:raise ValueError('passing source-bound software qualification required')
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('safe fresh training control identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh training study required')
    source=sources(root);env=environment()
    request,report=checked(root,qualification,sources=source,environment=env,required_tests=required_tests(),minimum_tests=len(required_tests()))
    parents=qualified_parents(root);r=recipe();base.mkdir(parents=True);inputs={}
    for key,name,raw in [('recipe','recipe.json',encoded(r)),('qualification-request','qualification-request.json',request),
                         ('qualification-report','qualification-report.xml',report),('qualification-environment','qualification-environment.json',encoded(env)),
                         ('qualified-parents','qualified-parents.json',encoded(parents))]:
        atomic(base/name,raw);inputs[key]=str((base/name).relative_to(root))
    definition=dict(id=identity,adapter='analysis/lll/airquantumgrav_training_controls.py',sources=source,
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
    r=recipe();canonical={v['identity']:v for v in tasks()};declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if json.loads(context.input_path().read_bytes())!=r or canonical.get(task['identity'])!=declared:
        raise ValueError('unchanged frozen training recipe, identity and allowance required')
    if json.loads(context.input_path('qualification-environment').read_bytes())!=environment():
        raise ValueError('qualified training environment differs')
    n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3
    counts=dict(constructed_intervals=n,generated_samples=n+1+cut+r['queries'])
    journal=Journal(context.directory/'construction.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:counts});journal.start(task['identity'])
    try:
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';kernel,km=load_kernel(directory);tangent,tm=load_tangent(directory)
        for filename,metadata in [('ilvis0_native.c',km),('ilvis0_tangent.cpp',tm)]:
            if metadata['source_sha256']!=context.manifest['sources']['analysis/lll/'+filename]:
                raise ValueError('compiled training source differs from freeze')
        context.save('compilation.json',dict(value=km,tangent=tm))
        def reserve(**values):
            for key,value in values.items():journal.reserve(task['identity'],key,value)
        result=calculate(task['payload'],r,kernel=kernel,tangent=tangent,reserve=context.charge,reserve_construction=reserve,
            save=context.save,save_bytes=context.save_bytes,check_continue=lambda:_check_continue(context.root,context.manifest))
        journal.verify()
        if any(journal.count(task['identity'],k)!=v for k,v in counts.items()):raise ValueError('training construction accounting differs')
        return result
    finally:context.note_file(journal.path)
