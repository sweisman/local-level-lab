# SPDX-License-Identifier: AGPL-3.0-or-later
"""Long generated training/forecast controls; no observed or protected inputs."""
import math

from lll.airquantumgrav_inventory import environment

SCOPE='generated training-only height-gravity forecast controls; no observed/protected reads'


def recipe():
    from lll.airquantumgrav_training_controls import recipe as base
    return dict(base(),version='esa-height-training-controls-v1',duration_s=1200.,queries=1200,
        latitudes_deg=[55.],height_profile='climb',gravity_model='inverse_square_height',
        policies=['reported-short-v1','reported-persistent-v1'],workers=4,threads=1,maximum_wall_s=28800.,
        accuracy=dict(horizontal_rms_m=.1,vertical_rms_m=.1,maximum_3d_m=.5),protected_reads=0)


def prefix_limit(r):
    cut=2*r['queries']//3;last=r['query_start_s']+(cut-1)*r['query_step_s']
    return math.ceil((last+r['limits']['time_offset'])*r['rate_hz'])+2


def construction_limits(r):
    n=round(r['duration_s']*r['rate_hz'])
    return dict(constructed_intervals=n,generated_samples=n+1+2*r['queries']//3+r['queries'])


def tasks():
    import itertools
    r=recipe();n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3;result=[]
    for model,profile,policy,start in itertools.product(r['models'],r['profiles'],r['policies'],range(r['starts'])):
        identity=f'{model}-{int(profile)}-{policy}-{start}'
        result.append(dict(identity=identity,input_key='recipe',native_kind='tangent',
            payload=dict(model=model,latitude_deg=55.,profile=profile,policy_id=policy,start=start),
            limits=dict(native_calls=r['maximum_evaluations']+1,
                packet_visits=r['maximum_evaluations']*prefix_limit(r)*cut+n*r['queries'],bound_calls=0,bound_steps=0)))
    return result


def calculate(spec,r,*,kernel_factory,reserve,reserve_construction,save,check_continue):
    import numpy as np
    from lll.airquantumgrav_training_controls import generated_training,_spec
    from lll.airquantumgrav_weighted_controls import fixture_rows
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.airquantumgrav_geographic_controls import position_errors,metrics
    from lll.studies.artifacts import digest,encoded
    base={k:v for k,v in spec.items() if k!='policy_id'};arguments,sign=_spec(base)
    if (set(spec)!=set(base)|{'policy_id'} or spec['latitude_deg']!=55. or spec['policy_id'] not in recipe()['policies']
            or r['height_profile']!='climb' or r['gravity_model']!='inverse_square_height' or r['stopping']!='near_zero'):
        raise ValueError('declared finite height-training identity and stopping method required')
    check_continue();material=generated_training(base,r,reserve=reserve_construction,
        height_profile=r['height_profile'],gravity_model=r['gravity_model'])
    times=material['times'];cut=material['training_epochs'];n=len(material['dt'])
    training=fixture_rows(material['training_gps'],times[:cut]);anchor=float(training[0]['height_m'])
    count=int(np.searchsorted(np.cumsum(material['dt']),times[cut-1]+r['limits']['time_offset'],side='left'))+1
    if count>prefix_limit(r):raise ValueError('training prefix exceeds independently frozen bound')
    names=('theta','dv','dt','rate_times','angular_rate_rads','specific_force_mps2','times')
    hashes=lambda:{key:digest(np.asarray(material[key],dtype='<f8').tobytes()) for key in names}
    raw_hashes=hashes();prefix_hashes={key:digest(np.asarray(material[key][:count],dtype='<f8').tobytes()) for key in ('theta','dv','dt')}
    save('training-receiver.json',training)
    save('input-binding.json',dict(full_array_sha256=raw_hashes,training_prefix_sha256=prefix_hashes,
        training_receiver_sha256=digest(encoded(training)),native_packets=n,training_prefix_packets=count,
        generated_rate_points=len(material['rate_times']),training_epochs=cut,prediction_epochs=len(times)-cut,
        gravity_anchor_height_m=anchor,gravity_anchor_source='first_training_receiver_height',
        raw_arrays_retained=False,raw_arrays_are_deterministic_generated_not_observed=True,
        raw_regeneration_requires_frozen_source_environment_recipe=True,original_reads=0,protected_reads=0))
    kernel,tangent,compilation=kernel_factory(anchor);save('compilation.json',compilation)
    result=train_and_forecast(**{key:material[key] for key in ('theta','dv','dt')},times=times,training_rows=training,
        time_origin_s=0.,model=spec['model'],profile=spec['profile'],policy_id=spec['policy_id'],start=spec['start'],
        limits=r['limits'],maximum_evaluations=r['maximum_evaluations'],maximum_interval_s=1.5/r['rate_hz'],
        kernel=kernel,tangent_kernel=tangent,reserve=reserve,save=save,check_continue=check_continue)
    check_continue();after=hashes();jac=result['forecast']['jacobian'];active=result['fit']['active_parameters']
    if after!=raw_hashes or jac.shape!=(len(times)*3,len(active)) or not np.all(np.isfinite(jac)):
        raise ValueError('raw input mutation or missing forecast derivative columns')
    save('forecast-binding.json',dict(full_array_sha256=after,jacobian_shape=list(jac.shape),
        jacobian_sha256=digest(np.asarray(jac,dtype='<f8').tobytes()),raw_arrays_unchanged=True))
    # This is the first request for any later receiver position.
    reserve_construction(generated_samples=len(times))
    answer=receiver_samples(times=times,sign=sign,**arguments,height_profile=r['height_profile'],gravity_model=r['gravity_model'])
    if not np.array_equal(answer['coordinates'][:cut],material['training_gps']):raise ValueError('earlier scoring positions changed')
    save('scoring-observations.json',{key:value.tolist() for key,value in answer.items()})
    errors=position_errors(result['forecast']['coordinates'],answer,model=spec['model'])
    sections={name:metrics(errors[section]) for name,section in [('training',slice(0,cut)),('prediction',slice(cut,None))]}
    save('scores.json',dict(times_s=times.tolist(),errors_neu_m=errors.tolist(),**sections,training_positions_reproduced_for_scoring=True))
    fit=result['fit'];accuracy={name:{key:value[key]<=limit for key,limit in r['accuracy'].items()} for name,value in sections.items()}
    passed=fit['converged'] and result['all_columns_retained'] and all(v for group in accuracy.values() for v in group.values())
    return dict(**spec,passed=bool(passed),converged=fit['converged'],evaluations=fit['evaluations'],native_calls=fit['evaluations']+1,
        training_cost=fit['residual_sum_squares'],training_epochs=cut,prediction_epochs=len(times)-cut,**sections,accuracy=accuracy,
        all_columns_retained=result['all_columns_retained'],forecast_saved_before_scoring=True,
        true_initial_state_supplied=False,true_calibration_supplied=False,gravity_anchor_height_m=anchor,
        gravity_anchor_source='first_training_receiver_height',raw_arrays_retained=False,
        constructed_intervals=n,generated_samples=construction_limits(r)['generated_samples'],
        original_reads=0,protected_reads=0,observed_starts=0,confidence_calibrated=False,scientific_decision='abstain')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_height_training.py','analysis/lll/airquantumgrav_height_report.py',
        'analysis/tests/test_airquantumgrav_height_training.py','analysis/tests/test_airquantumgrav_height_prediction.py',
        'analysis/tests/test_airquantumgrav_height_material.py','analysis/tests/test_airquantumgrav_height_report.py',
        'analysis/tests/test_airquantumgrav_prediction.py','analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp',
        'docs/esa-height-training-controls/PLAN.md'])


def required_tests():
    return ['test_height_training_freezes_separate_24_case_fit_allowance',
        'test_height_training_requires_qualification_before_any_files',
        'test_height_report_rejects_open_study_before_numerical_imports',
        'test_height_report_keeps_generated_scope_and_earlier_anchor_explicit',
        'test_default_material_does_not_silently_expand_legacy_duration_allowance',
        'test_weighted_prediction_interface_has_no_later_receiver_input']+[
        f'test_height_anchor_and_fit_cannot_use_later_positions[{policy}-{profile}]'
        for profile in (False,True) for policy in recipe()['policies']]+[
        f'{name}[{profile}]' for name in ('test_default_training_material_matches_archived_source_exactly',
        'test_height_material_exposes_only_earlier_positions_and_no_true_calibration') for profile in (False,True)]+[
        f'test_height_receiver_observations_use_independent_antenna_and_latency[{model}]' for model in recipe()['models']]


def qualified_parents(root):
    import ast
    from pathlib import Path
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    from lll.airquantumgrav_gravity_report import inspect
    from lll.airquantumgrav_observed_report import verify_audit_environment
    root=Path(root).resolve();gravity=inspect(root,'docs/esa-gravity-controls')
    if not gravity['qualified']:raise ValueError('complete known-correction gravity qualification required')
    proof=dict(gravity_manifest_sha256=gravity['manifest_sha256'],gravity_summary_sha256=gravity['summary_sha256'])
    parent=ClosedStudy(root,'docs/esa-gravity-controls')
    try:
        for filename in ('ilvis0_native.c','ilvis0_tangent.cpp','ilvis0_shape.py','ilvis0_exploratory.py','airquantumgrav_truth.py'):
            name='analysis/lll/'+filename
            if digest((root/name).read_bytes())!=parent.manifest['sources'][name]:raise ValueError('qualified gravity source changed')
        name='analysis/lll/airquantumgrav_observation_truth.py'
        functions=lambda raw:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
        old=functions(parent.read('source-freeze/'+name,parent.manifest['sources'][name],raw=True));new=functions((root/name).read_bytes())
        if any(old[k]!=new.get(k) for k in ('_check','_parameters','observe','antenna','start')):raise ValueError('known correction definitions changed')
    finally:parent.close()
    parent=ClosedStudy(root,'docs/esa-weighted-training-controls')
    try:
        if not parent.summary['passed']:raise ValueError('complete original weighted qualification required')
        verify_audit_environment(parent.input('qualification-environment'),environment())
        for filename in ('airquantumgrav_prediction.py','airquantumgrav_error_policy.py','ilvis0_training_forecast.py',
                'ilvis0_forecast.py','ilvis0_near_zero.py','ilvis0_estimator.py','ilvis0_forward.py',
                'ilvis0_solver_trust_v2.py','ilvis0_solver_position.py','ilvis0_solver_refinement.py','ilvis0_solver_boundary.py'):
            name='analysis/lll/'+filename
            if digest((root/name).read_bytes())!=parent.manifest['sources'].get(name):raise ValueError('qualified fitting source changed: '+filename)
        proof.update(weighted_manifest_sha256=parent.completion['manifest_sha256'],weighted_summary_sha256=parent.completion['summary_sha256'])
    finally:parent.close()
    return proof


def prepare(root,*,qualification,identity='esa-height-training-controls-20261023'):
    if qualification is None:raise ValueError('passing source-bound height-training qualification required')
    import re
    from pathlib import Path
    from lll.compute_budget import environment as thread_environment
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh height-training scope required')
    env=environment();r=recipe()
    if env['numerical_environment']!=thread_environment(workers=r['workers'],threads=r['threads']):raise ValueError('declared thread environment required')
    sources=qualification_sources(root)
    request,report=checked(root,qualification,sources=sources,environment=env,required_tests=required_tests(),minimum_tests=len(required_tests()))
    parents=qualified_parents(root);base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate([('recipe',encoded(r)),('qualification-request',request),('qualification-report',report),
            ('qualification-environment',encoded(env)),('qualified-parents',encoded(parents))]):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_height_training.py',sources=sources,inputs=inputs,
        tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,allocation=manifest['allocation'],limits=manifest['limits'],cases=len(tasks()))


def evaluate(task,context):
    import json
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    r=recipe();declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if ({v['identity']:v for v in tasks()}.get(task['identity'])!=declared or json.loads(context.input_path().read_bytes())!=r
            or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()
            or context.manifest['scope']!=SCOPE):raise ValueError('unchanged qualified height-training scope required')
    counts=construction_limits(r);journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:counts});journal.start(task['identity'])
    try:
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';env=environment()
        def factory(anchor):
            kernel,km=load_kernel(directory,gravity_anchor_height_m=anchor);tangent,tm=load_tangent(directory,gravity_anchor_height_m=anchor)
            for filename,metadata,compiler in [('ilvis0_native.c',km,'cc'),('ilvis0_tangent.cpp',tm,'c++')]:
                if (metadata['source_sha256']!=context.manifest['sources']['analysis/lll/'+filename]
                        or metadata['compiler']!=env['compilers'][compiler]):raise ValueError('compiled height-training source differs')
            return kernel,tangent,dict(value=km,tangent=tm)
        def reserve_construction(**work):
            _check_continue(context.root,context.manifest)
            for key,value in work.items():journal.reserve(task['identity'],key,value)
        result=calculate(task['payload'],r,kernel_factory=factory,reserve=context.charge,reserve_construction=reserve_construction,
            save=context.save,check_continue=lambda:_check_continue(context.root,context.manifest))
        journal.verify()
        if any(journal.count(task['identity'],key)!=value for key,value in counts.items()):raise ValueError('construction charges differ')
        return result
    finally:context.note_file(journal.path)
