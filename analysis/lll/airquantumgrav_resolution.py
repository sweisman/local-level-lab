# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only ESA adapter for fixed-point stopping-resolution probes."""
from lll.airquantumgrav_inventory import environment,METADATA,validate_context

PARENT='docs/esa-observed-height-pilot'
SCOPE='fixed-point training-only ESA stopping diagnostic; no fitting, forecast, original or protected reads'
MEASUREMENT_KEYS=('interval','training','layout','working-errors')


def recipe():
    from lll.airquantumgrav_observed_height import recipe as base
    from lll.stopping_resolution import FRACTIONS,MAXIMUM_SWEEPS
    r=base()
    return dict(version='esa-fixed-point-resolution-v1',models=r['models'],profiles=r['profiles'],policies=r['policies'],
        source_starts=2,packets=239867,epochs=800,maximum_sweeps=MAXIMUM_SWEEPS,fractions=list(FRACTIONS),
        workers=4,threads=1,maximum_wall_s=3600.,optimizer_starts=0,original_reads=0,protected_reads=0,retries=0)


def tasks():
    import itertools
    r=recipe();result=[]
    for model,profile,policy,start in itertools.product(r['models'],r['profiles'],r['policies'],range(r['source_starts'])):
        result.append(dict(identity=f'{model}-{int(profile)}-{policy}-{start}',input_key='interval',native_kind='tangent',
            payload=dict(model=model,profile=profile,policy_id=policy,start=start),
            limits=dict(native_calls=r['maximum_sweeps'],packet_visits=r['maximum_sweeps']*r['packets']*r['epochs'],bound_calls=0,bound_steps=0)))
    return result


def make_problem(arrays,training_rows,layout,source_recipe,*,model,profile,policy_id,kernel,tangent):
    import math
    import numpy as np
    from lll.airquantumgrav_error_policy import build
    from lll.ilvis0_training_forecast import training_problem
    times=np.asarray(layout['times_s'],float);dt=np.asarray(arrays['dt'],float)
    if (set(arrays)!= {'theta','dv','dt'} or times.ndim!=1 or len(times)<2 or not np.all(np.isfinite(times))
            or np.any(np.diff(times)<=0) or dt.ndim!=1 or not len(dt) or not np.all(np.isfinite(dt))
            or np.any(dt<=0) or np.any(dt>source_recipe['maximum_interval_s'])):
        raise ValueError('finite supported training prefix required')
    count=int(np.searchsorted(np.cumsum(dt),times[-1]+source_recipe['limits']['time_offset'],side='left'))+1
    if count!=len(dt):raise ValueError('exact required training prefix only; no post-training increments')
    if (len(training_rows)!=len(times) or np.asarray(arrays['theta']).shape!=(len(dt),3)
            or np.asarray(arrays['dv']).shape!=(len(dt),3)
            or not all(np.all(np.isfinite(arrays[k])) for k in ('theta','dv'))):
        raise ValueError('complete earlier-only observations and three-axis increments required')
    weight=build(training_rows,policy_id=policy_id)
    if not np.array_equal(weight.times-layout['time_origin_gps_sow_s'],times):raise ValueError('exact earlier receiver times required')
    gps=np.array([[math.radians(v['latitude_deg']),math.radians(v['longitude_deg']),v['height_m']] for v in training_rows])
    problem=training_problem(times,gps,**arrays,covariance=weight.dense(maximum_epochs=1024),
        model=model,limits=source_recipe['limits'],profile=profile,clock='header_elapsed',
        maximum_interval_s=source_recipe['maximum_interval_s'],kernel=kernel,tangent_kernel=tangent)
    return problem,weight


def calculate(spec,source_recipe,*,arrays,training_rows,layout,fit,kernel_factory,reserve,save,save_bytes,check_continue):
    import math
    import numpy as np
    from lll.stopping_resolution import probe
    from lll.ilvis0_solver_position import physical_residual_step
    from lll.studies.artifacts import digest,encoded
    if (set(spec)!={'model','profile','policy_id','start'} or spec['model'] not in recipe()['models']
            or type(spec['profile']) is not bool or spec['policy_id'] not in recipe()['policies']
            or type(spec['start']) is not int or spec['start'] not in (0,1)
            or fit.get('model')!=spec['model'] or not training_rows
            or source_recipe.get('gravity_model')!='inverse-square-height-v1'):
        raise ValueError('one unchanged saved identity and height-gravity hypothesis required')
    anchor=float(training_rows[0]['height_m'])
    if not math.isfinite(anchor) or anchor<=-6371000.:raise ValueError('finite earlier-only height anchor required')
    check_continue();kernel,tangent,compilation=kernel_factory(anchor);save('compilation.json',compilation)
    problem,weight=make_problem(arrays,training_rows,layout,source_recipe,**{k:spec[k] for k in ('model','profile','policy_id')},
        kernel=kernel,tangent=tangent)
    if list(problem.bounds.active)!=fit['active_parameters']:raise ValueError('saved point must retain every original parameter column')
    prefix={k:digest(np.asarray(arrays[k],dtype='<f8').tobytes()) for k in arrays}
    save('training-binding.json',dict(epochs=len(training_rows),packets=len(arrays['dt']),times_s=layout['times_s'],
        training_rows_sha256=digest(encoded(training_rows)),prefix_sha256=prefix,gravity_anchor_height_m=anchor,
        gravity_anchor_source='first_training_receiver_height',weight_configuration=weight.configuration,
        weight_descriptor=weight.descriptor,weight_source_sha256=weight.source_sha256,later_positions_used=False))
    result=probe(fit,evaluate=lambda u:problem.residual_tangent(u,spec['model']),
        physical_step=lambda delta:physical_residual_step(problem,delta),packet_count=len(arrays['dt']),epoch_count=len(training_rows),
        reserve=reserve,save=save,save_bytes=save_bytes,check_continue=check_continue)
    after={k:digest(np.asarray(arrays[k],dtype='<f8').tobytes()) for k in arrays}
    if prefix!=after:raise ValueError('immutable training increments changed')
    return dict(result,**spec,gravity_anchor_height_m=anchor,original_reads=0,protected_reads=0,later_receiver_reads=0,
        raw_arrays_unchanged=True)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_resolution.py','analysis/lll/airquantumgrav_resolution_report.py',
        'analysis/tests/test_airquantumgrav_resolution.py','analysis/tests/test_airquantumgrav_resolution_numeric.py',
        'analysis/tests/test_airquantumgrav_resolution_report.py','analysis/tests/test_stopping_resolution.py',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','docs/esa-stopping-resolution/PLAN.md'])


def required_tests():
    return ['test_resolution_matrix_has_24_fixed_points_and_separate_finite_allowance',
        'test_resolution_prepare_requires_tests_before_any_inputs',
        'test_resolution_prepare_rejects_unguarded_environment_before_source_reads',
        'test_resolution_interface_has_no_later_position_or_forecast_callback',
        'test_resolution_problem_rejects_unneeded_post_training_increments',
        'test_resolution_report_rejects_open_before_numerical_imports',
        'test_resolution_report_rejects_changed_saved_parameters_and_missing_columns']+[
        f'test_resolution_probe_preserves_fixed_point_labels_columns_and_exact_charge_order[{n}]' for n in (26,27)]+[
        f'test_resolution_adapter_preserves_training_prefix_and_every_native_column[{policy}-{profile}-{model}]'
        for policy in recipe()['policies'] for profile in (False,True) for model in recipe()['models']]


def prepare(root,*,qualification,identity='esa-stopping-resolution-20261024'):
    if qualification is None:raise ValueError('passing source-bound fixed-point qualification required')
    import gzip
    import io
    import json
    import re
    from pathlib import Path
    from lll.compute_budget import environment as thread_environment
    from lll.studies.artifacts import ArchiveStore,atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    r=recipe();env=environment()
    if env['numerical_environment']!=thread_environment(workers=r['workers'],threads=r['threads']):raise ValueError('declared thread environment required')
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh fixed-point scope required')
    sources=qualification_sources(root)
    request,test_report=checked(root,qualification,sources=sources,environment=env,required_tests=required_tests(),minimum_tests=len(required_tests()))
    import numpy as np
    parent=ClosedStudy(root,PARENT)
    try:
        receipt=parent.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
        report=parent.read(name,receipt['artifacts'][name])
        if (report.get('verified') is not True or report['total']!=24 or report['complete_predictions']!=24
                or report['manifest_sha256']!=parent.completion['manifest_sha256']
                or report['summary_sha256']!=parent.completion['summary_sha256']):raise ValueError('verified closed 24-point parent required')
        for name in set(sources)&parent.manifest['sources'].keys():
            if digest((root/name).read_bytes())!=parent.manifest['sources'][name]:raise ValueError('parent numerical dependency changed: '+name)
        required={'analysis/lll/'+name for name in ('ilvis0_native.c','ilvis0_tangent.cpp','ilvis0_training_forecast.py','ilvis0_solver_position.py')}
        if not required<=set(sources)&parent.manifest['sources'].keys():raise ValueError('complete shared numerical dependency closure required')
        if parent.input('qualification-environment')!=env:raise ValueError('parent numerical environment changed')
        if {v['identity'] for v in tasks()}!=set(parent.tasks):raise ValueError('same 24 source points required')
        source_recipe=parent.input('recipe');query=parent.input('query-layout');count=parent.input('layout')['training_prefix_packets']
        if count!=r['packets'] or query['training_epochs']!=r['epochs']:raise ValueError('unchanged earlier support required')
        with np.load(io.BytesIO(parent.input('interval',raw=True)),allow_pickle=False) as archive:
            arrays={k:archive[k][:count].copy() for k in ('theta','dv','dt')}
        stream=io.BytesIO();np.savez_compressed(stream,**arrays)
        training=parent.input('training',raw=True);rows=json.loads(gzip.decompress(training))
        layout=dict(times_s=query['times_s'][:r['epochs']],time_origin_gps_sow_s=query['time_origin_gps_sow_s'])
        materials=dict(interval=stream.getvalue(),training=training,layout=encoded(layout),
            **{'working-errors':parent.input('working-errors',raw=True),'source-recipe':parent.input('recipe',raw=True),
               'context':parent.input('context',raw=True)})
        point_hashes={};prefix={k:digest(np.asarray(v,dtype='<f8').tobytes()) for k,v in arrays.items()}
        if len(rows)!=r['epochs']:raise ValueError('complete earlier receiver rows required')
        for task in tasks():
            identity_=task['identity'];raw=parent.artifact(identity_,'fit.json',raw=True)
            if parent.tasks[identity_]['payload']!=task['payload']:raise ValueError('unchanged source identity required')
            if parent.artifact(identity_,'training-observations.json')['training_prefix_sha256']!=prefix:
                raise ValueError('parent training increments differ')
            materials['point-'+identity_]=raw;point_hashes[identity_]=digest(raw)
        proof=dict(parent_manifest_sha256=parent.completion['manifest_sha256'],parent_summary_sha256=parent.completion['summary_sha256'],
            verified_report_sha256=receipt['artifacts']['artifacts/publication/verified-report.json'],point_sha256=point_hashes,
            prefix_sha256=prefix,parent_training_sha256=parent.manifest['inputs']['training']['sha256'],
            parent_source_recipe_sha256=parent.manifest['inputs']['recipe']['sha256'],
            parent_working_errors_sha256=parent.manifest['inputs']['working-errors']['sha256'],
            parent_full_interval_sha256=parent.manifest['inputs']['interval']['sha256'])
    finally:parent.close()
    store=ArchiveStore(root)
    try:metadata={key:store.read(name) for key,name in METADATA.items()}
    finally:store.close()
    binding=validate_context(**{key:json.loads(raw) for key,raw in metadata.items()})
    if binding!=json.loads(materials['context']):raise ValueError('explicit development membership changed')
    materials.update(metadata);materials.update({key:encoded(v) for key,v in
        [('recipe',r),('source-proof',proof),('qualification-environment',env)]})
    materials.update({'qualification-request':request,'qualification-report':test_report})
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(materials.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_resolution.py',sources=sources,inputs=inputs,
        tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,total=24,limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import gzip
    import json
    import numpy as np
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    load=lambda key:json.loads(context.input_path(key).read_bytes())
    declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if ({v['identity']:v for v in tasks()}.get(task['identity'])!=declared or load('recipe')!=recipe()
            or load('qualification-environment')!=environment() or context.manifest['scope']!=SCOPE
            or {'scoring','later','forecast'}&context.manifest['inputs'].keys()):raise ValueError('unchanged training-only diagnostic scope required')
    binding=validate_context(**{key:load(key) for key in METADATA})
    if binding!=load('context'):raise ValueError('development membership changed')
    proof=load('source-proof');point_key='point-'+task['identity'];fit=load(point_key)
    if context.manifest['inputs'][point_key]['sha256']!=proof['point_sha256'][task['identity']]:raise ValueError('saved fitted point changed')
    for key,reference in [('training','parent_training_sha256'),('source-recipe','parent_source_recipe_sha256'),
            ('working-errors','parent_working_errors_sha256')]:
        if context.manifest['inputs'][key]['sha256']!=proof[reference]:raise ValueError('parent input binding changed: '+key)
    with np.load(context.input_path(),allow_pickle=False) as a:arrays={k:a[k] for k in ('theta','dv','dt')}
    prefix={k:digest(np.asarray(v,dtype='<f8').tobytes()) for k,v in arrays.items()}
    if prefix!=proof['prefix_sha256'] or len(arrays['dt'])!=recipe()['packets']:raise ValueError('original training prefix changed')
    rows=json.loads(gzip.decompress(context.input_path('training').read_bytes()));layout=load('layout')
    if (len(rows)!=recipe()['epochs'] or len(layout['times_s'])!=len(rows)
            or set(layout)!= {'times_s','time_origin_gps_sow_s'}):raise ValueError('earlier-only receiver support changed')
    context.save('input-binding.json',dict(group_id=binding['group_id'],point_sha256=proof['point_sha256'][task['identity']],
        input_sha256={k:v['sha256'] for k,v in context.manifest['inputs'].items()},prefix_sha256=prefix,
        original_reads=0,protected_reads=0,later_receiver_reads=0))
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';env=environment()
    def factory(anchor):
        kernel,km=load_kernel(directory,gravity_anchor_height_m=anchor);tangent,tm=load_tangent(directory,gravity_anchor_height_m=anchor)
        for filename,meta,compiler in [('ilvis0_native.c',km,'cc'),('ilvis0_tangent.cpp',tm,'c++')]:
            if (meta['source_sha256']!=context.manifest['sources']['analysis/lll/'+filename]
                    or meta['compiler']!=env['compilers'][compiler]):raise ValueError('compiled diagnostic source differs')
        return kernel,tangent,dict(value=km,tangent=tm)
    expected_weights=load('working-errors')[task['payload']['policy_id']]['configuration']
    def save(name,value):
        if name=='training-binding.json' and value['weight_configuration']!=expected_weights:
            raise ValueError('unchanged parent working weights required')
        context.save(name,value)
    result=calculate(task['payload'],load('source-recipe'),arrays=arrays,training_rows=rows,layout=layout,fit=fit,
        kernel_factory=factory,reserve=context.charge,save=save,save_bytes=context.save_bytes,
        check_continue=lambda:_check_continue(context.root,context.manifest))
    return dict(result,group_id=binding['group_id'])
