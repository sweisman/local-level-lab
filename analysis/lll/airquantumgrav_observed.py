# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite observed ESA development pilot on immutable prepared inputs."""
from lll.airquantumgrav_inventory import environment,METADATA,validate_context

SCOPE='observed ESA recording-187 development prediction pilot; no original or protected source reads'


def recipe():
    from lll.airquantumgrav_training_controls import parameter_limits
    return dict(version='esa-observed-development-pilot-v1',models=['sphere_rotating','sphere_still','flat_still'],
        profiles=[False,True],policies=['reported-short-v1','reported-persistent-v1'],starts=2,
        maximum_evaluations=200,limits=parameter_limits(),maximum_interval_s=.005,stopping='near_zero',
        workers=4,threads=1,maximum_wall_s=28800.,original_reads=0,protected_reads=0,retries=0,
        training_epochs=800,prediction_epochs=400,query_epochs=1200,
        descriptive_ranking='later common receiver-chart total three-dimensional RMS',confidence_calibrated=False)


def tasks(layout):
    n,prefix,nt,nq=(layout[k] for k in ('native_packets','training_prefix_packets','training_epochs','receiver_epochs'))
    if (any(type(v) is not int for v in (n,prefix,nt,nq)) or not 0<prefix<=n or n!=360028 or nt!=800 or nq!=1200):
        raise ValueError('exact prepared twenty-minute interval and training prefix required')
    r=recipe();result=[]
    for model in r['models']:
        for profile in r['profiles']:
            for policy in r['policies']:
                for start in range(r['starts']):
                    result.append(dict(identity=f'{model}-{int(profile)}-{policy}-{start}',input_key='interval',native_kind='tangent',
                        payload=dict(model=model,profile=profile,policy_id=policy,start=start),
                        limits=dict(native_calls=201,packet_visits=200*prefix*nt+n*nq,bound_calls=0,bound_steps=0)))
    return result


def calculate(spec,r,*,arrays,training_rows,layout,open_scoring,kernel,tangent,reserve,save,check_continue):
    import math
    import numpy as np
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.airquantumgrav_scoring import receiver_errors,sections
    from lll.studies.artifacts import encoded
    if (set(spec)!={'model','profile','policy_id','start'} or spec['model'] not in r['models']
            or type(spec['profile']) is not bool or spec['policy_id'] not in r['policies']
            or type(spec['start']) is not int or spec['start'] not in (0,1)):
        raise ValueError('one unchanged declared observed fit identity required')
    times=np.array(layout['times_s']);cut=layout['training_epochs']
    if len(training_rows)!=cut or layout['prediction_epochs']!=len(times)-cut:raise ValueError('complete earlier/later split required')
    fitted=train_and_forecast(**{k:arrays[k] for k in ('theta','dv','dt')},times=times,training_rows=training_rows,
        time_origin_s=layout['time_origin_gps_sow_s'],model=spec['model'],profile=spec['profile'],policy_id=spec['policy_id'],
        start=spec['start'],limits=r['limits'],maximum_evaluations=r['maximum_evaluations'],maximum_interval_s=r['maximum_interval_s'],
        kernel=kernel,tangent_kernel=tangent,reserve=reserve,save=save,check_continue=check_continue)
    # This is the first access to the caller's separate scoring artifact.
    check_continue();scoring=open_scoring()
    if (len(scoring)!=len(times) or encoded(scoring[:cut])!=encoded(training_rows)
            or not np.array_equal(np.array([row['time_s'] for row in scoring])-layout['time_origin_gps_sow_s'],times)):
        raise ValueError('scoring must preserve complete fixed queries and exact earlier observations')
    gps=np.array([[math.radians(row['latitude_deg']),math.radians(row['longitude_deg']),row['height_m']] for row in scoring])
    errors=receiver_errors(fitted['forecast']['coordinates'],gps);scores=sections(errors,cut)
    save('scores.json',dict(times_s=times.tolist(),receiver_coordinates=gps.tolist(),errors_neu_m=errors.tolist(),**scores,
        coordinate_metric='common receiver ellipsoidal radii plus height; NEU; wrapped longitude',
        prediction_receiver_positions_used_in_training=False))
    fit=fitted['fit'];complete=bool(fit['converged'] and fitted['all_columns_retained'])
    return dict(passed=complete,**spec,converged=fit['converged'],training_cost=fit['residual_sum_squares'],
        evaluations=fit['evaluations'],native_calls=fit['evaluations']+1,training_epochs=cut,prediction_epochs=len(times)-cut,
        all_columns_retained=fitted['all_columns_retained'],weight_configuration=fitted['weight_configuration'],
        forecast_saved_before_scoring=True,**scores,accuracy_all_sections=all(v['accuracy']['passed'] for v in scores.values()),
        original_reads=0,protected_reads=0,observed_starts=1,confidence_calibrated=False,scientific_decision='abstain')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_observed.py',
        'analysis/tests/test_airquantumgrav_observed.py','analysis/tests/test_airquantumgrav_scoring.py',
        'analysis/tests/test_airquantumgrav_prediction.py','analysis/tests/test_airquantumgrav_error_policy.py',
        'analysis/tests/test_airquantumgrav_inventory.py','analysis/tests/test_study_scope.py',
        'analysis/tests/test_ilvis0_training_forecast.py','analysis/lll/studies/qualification.py',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','docs/esa-development-pilot/FIT_PLAN.md'])


def required_tests():
    from lll.airquantumgrav_error_policy import required_tests as weight_tests
    return weight_tests()+['test_observed_esa_matrix_and_allowance_are_fixed_before_fitting',
        'test_observed_esa_prepare_cannot_read_measurements_before_qualification',
        'test_observed_esa_opens_scoring_after_forecast_and_selects_no_start_from_it',
        'test_common_receiver_chart_preserves_height_and_wraps_longitude',
        'test_prediction_accuracy_requires_height_and_preserves_inadequacy',
        'test_weighted_prediction_interface_has_no_later_receiver_input',
        'test_inventory_context_enforces_explicit_development_and_matching_support',
        'test_explicit_receiver_inventory_scope_is_frozen_and_authorized']+[
        f'test_unsupported_scoring_fails_without_discarding_bad_epochs[{v}]' for v in ('shape','nonfinite','pole','height','split')]+[
        f'test_weighted_prediction_uses_only_earlier_rows_and_preserves_all_columns[{profile}-{policy}]'
        for profile in (False,True) for policy in recipe()['policies']]


def _verified_report(study):
    receipt=study.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
    report=study.read(name,receipt['artifacts'][name])
    if (not study.summary['passed'] or not report.get('qualified',report.get('verified',False))
            or report['manifest_sha256']!=study.completion['manifest_sha256']
            or report['summary_sha256']!=study.completion['summary_sha256']):
        raise ValueError('closed hash-bound successful qualification report required')
    return report


def prepare(root,*,qualification,identity='esa-observed-development-pilot-20261023'):
    import io
    import json
    import re
    from pathlib import Path
    import numpy as np
    from lll.studies.artifacts import ArchiveStore,atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if qualification is None:raise ValueError('passing source-bound observed pilot qualification required')
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh pilot identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh observed allowance required')
    sources=qualification_sources(root);env=environment()
    request,report=checked(root,qualification,sources=sources,environment=env,required_tests=required_tests(),minimum_tests=len(required_tests()))
    parent=ClosedStudy(root,'docs/esa-weighted-training-controls');prepared=ClosedStudy(root,'docs/esa-development-pilot-preparation')
    try:
        qualification_report=_verified_report(parent);preparation_report=_verified_report(prepared)
        if qualification_report['passing']!=48 or qualification_report['total']!=48:raise ValueError('complete 48-case matched qualification required')
        core=('airquantumgrav_prediction.py','airquantumgrav_error_policy.py','ilvis0_training_forecast.py','ilvis0_forecast.py',
            'ilvis0_near_zero.py','ilvis0_shape.py','ilvis0_estimator.py','ilvis0_exploratory.py','ilvis0_forward.py',
            'ilvis0_solver_trust_v2.py','ilvis0_solver_position.py','ilvis0_solver_refinement.py','ilvis0_solver_boundary.py',
            'ilvis0_native.c','ilvis0_tangent.cpp','ilvis0_error_model.py','models.py')
        for filename in core:
            name='analysis/lll/'+filename
            if digest((root/name).read_bytes())!=parent.manifest['sources'][name]:raise ValueError('qualified numerical dependency changed: '+filename)
        if parent.input('qualification-environment')!=env:raise ValueError('qualified numerical environment changed')
        store=ArchiveStore(root)
        try:metadata={key:store.read(name) for key,name in METADATA.items()}
        finally:store.close()
        binding=validate_context(**{k:json.loads(v) for k,v in metadata.items()})
        if binding!=prepared.input('context'):raise ValueError('prepared development membership changed')
        materials=dict(interval=prepared.artifact('prepare-earliest-187-v2','interval.npz',raw=True),
            training=prepared.artifact('prepare-earliest-187-v2','training-receiver.json.gz',raw=True),
            scoring=prepared.artifact('prepare-earliest-187-v2','scoring-receiver.json.gz',raw=True),
            **{'query-layout':prepared.artifact('prepare-earliest-187-v2','query-layout.json',raw=True),
               'working-errors':prepared.artifact('prepare-earliest-187-v2','working-errors.json',raw=True),
               'source-validation':prepared.artifact('prepare-earliest-187-v2','source-validation.json',raw=True)})
        query=json.loads(materials['query-layout']);r=recipe()
        with np.load(io.BytesIO(materials['interval']),allow_pickle=False) as archive:dt=archive['dt']
        count=int(np.searchsorted(np.cumsum(dt),query['times_s'][799]+r['limits']['time_offset'],side='left'))+1
        layout=dict(native_packets=len(dt),training_prefix_packets=count,training_epochs=query['training_epochs'],receiver_epochs=len(query['times_s']))
        task_list=tasks(layout)
        if preparation_report['raw_points']!=len(dt)+1 or query['prediction_epochs']!=400:raise ValueError('unchanged prepared layout required')
    finally:parent.close();prepared.close()
    materials.update(metadata);materials.update({key:encoded(value) for key,value in
        [('context',binding),('layout',layout),('recipe',r),('qualified-controls',qualification_report),
         ('verified-preparation',preparation_report),('qualification-environment',env)]})
    materials.update({'qualification-request':request,'qualification-report':report})
    base.mkdir(parents=True);inputs={}
    for index,(key,raw) in enumerate(materials.items()):
        name=f'input-{index:03d}';atomic(base/name,raw);inputs[key]=str((base/name).relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_observed.py',sources=sources,inputs=inputs,
        tasks=task_list,workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,total=len(task_list),layout=layout,limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import gzip
    import json
    import numpy as np
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_control_shards import _check_continue
    load=lambda key:json.loads(context.input_path(key).read_bytes())
    r=recipe();layout=load('layout');canonical={v['identity']:v for v in tasks(layout)}
    declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if (canonical.get(task.get('identity'))!=declared or load('recipe')!=r or context.manifest['scope']!=SCOPE
            or load('qualification-environment')!=environment()):raise ValueError('unchanged qualified observed task and environment required')
    binding=validate_context(**{key:load(key) for key in METADATA})
    if binding!=load('context'):raise ValueError('explicit unchanged development membership required')
    with np.load(context.input_path(),allow_pickle=False) as archive:arrays={k:archive[k] for k in ('theta','dv','dt')}
    query=load('query-layout');training=json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    count=int(np.searchsorted(np.cumsum(arrays['dt']),query['times_s'][799]+r['limits']['time_offset'],side='left'))+1
    if (len(arrays['dt'])!=layout['native_packets'] or count!=layout['training_prefix_packets']
            or len(training)!=800 or len(query['times_s'])!=1200):raise ValueError('unchanged complete raw input and prefix required')
    context.save('input-binding.json',dict(group_id=binding['group_id'],layout=layout,
        input_sha256={key:record['sha256'] for key,record in context.manifest['inputs'].items()},original_reads=0,protected_reads=0))
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';kernel,km=load_kernel(directory);tangent,tm=load_tangent(directory)
    for filename,meta in [('ilvis0_native.c',km),('ilvis0_tangent.cpp',tm)]:
        if meta['source_sha256']!=context.manifest['sources']['analysis/lll/'+filename]:raise ValueError('native source differs from freeze')
    context.save('compilation.json',dict(value=km,tangent=tm))
    result=calculate(task['payload'],r,arrays=arrays,training_rows=training,layout=query,
        open_scoring=lambda:json.loads(gzip.decompress(context.input_path('scoring').read_bytes())),kernel=kernel,tangent=tangent,
        reserve=context.charge,save=context.save,check_continue=lambda:_check_continue(context.root,context.manifest))
    expected=load('working-errors')[task['payload']['policy_id']]['configuration']
    if result['weight_configuration']!=expected:raise ValueError('training weights differ from prepared source')
    return dict(result,group_id=binding['group_id'])
