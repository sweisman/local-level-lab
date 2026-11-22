# SPDX-License-Identifier: AGPL-3.0-or-later
"""Three charged, receiver-blind forecasts from saved correction candidates."""

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

ID='ilvis0-correction-forecast-development-v2-20261118'
PARENT='data/ilvis0-remaining-prediction-transfer-20261118'
PARENT_MANIFEST='3cc9a72f3c3f3fa10c3f867fe31443fecfb7ee320dcb3567692d0af678c2863e'
SCOPE=('three saved numerical-correction forecast paths; no withheld '
       'receiver positions, fitting, model decision or failure reclassification')
PLAN='docs/prediction-group-transfer/CORRECTION_FORECAST_REPAIR_PLAN.md'
REQUEST='docs/prediction-group-transfer/correction-forecast-v2-qualification-request.json'
REPORT='docs/prediction-group-transfer/correction-forecast-v2-qualification-tests.xml'
CASES=(
    'bb8061a43b4f14b6262ceda1-outer-0-header_elapsed-1',
    'a6e658d1550299e4eb9f00a3-outer-0-header_elapsed-1',
    'fad74da3a09951b31e882472-outer-0-header_elapsed-0',
)
SCIENCE_SOURCES=(
    'analysis/lll/ilvis0_rolling_origin_study.py',
    'analysis/lll/ilvis0_training_forecast.py',
    'analysis/lll/ilvis0_forecast.py',
    'analysis/lll/ilvis0_gps_sensitivity.py',
    'analysis/lll/ilvis0_shape.py',
    'analysis/lll/ilvis0_native.c',
    'analysis/lll/ilvis0_tangent.cpp',
)


def tasks(layouts):
    if not isinstance(layouts,dict) or set(layouts)!=set(CASES):
        raise ValueError('exact three frozen correction cases required')
    result=[]
    for identity in CASES:
        row=layouts[identity]
        packets=row.get('native_packets')
        queries=row.get('queries')
        if (row.get('segment_id')!=identity.split('-')[0] or
                type(packets) is not int or packets<=0 or
                type(queries) is not int or queries<=1):
            raise ValueError('exact positive packet/query allowance required')
        result.append(dict(identity=identity,input_key=identity+'-common',
            payload=dict(original_identity=identity,segment_id=row['segment_id'],
                         origin='outer',clock='header_elapsed',profile=False,
                         model='sphere_rotating'),
            limits=dict(native_calls=1,packet_visits=packets*queries,
                        bound_calls=0,bound_steps=0)))
    return result


def path_difference(reference,candidate,*,training_epochs):
    from .ilvis0_solver_position import physical_metric
    a=np.asarray(reference,float)
    b=np.asarray(candidate,float)
    if (a.ndim!=2 or a.shape[1]!=3 or b.shape!=a.shape or
            not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or
            type(training_epochs) is not int or not 1<=training_epochs<len(a)):
        raise ValueError('complete aligned predicted trajectories required')
    delta=b[training_epochs:]-a[training_epochs:]
    delta[:,1]=(delta[:,1]+np.pi)%(2*np.pi)-np.pi
    neu=delta*physical_metric(a[training_epochs:])
    return dict(version='ilvis0-saved-correction-forecast-difference-v1',
        later_epochs=len(neu),
        rms_neu_m=np.sqrt(np.mean(neu**2,axis=0)).tolist(),
        max_absolute_neu_m=np.max(abs(neu),axis=0).tolist(),
        maximum_horizontal_m=float(np.max(np.linalg.norm(neu[:,:2],axis=1))),
        withheld_positions_read=False,physical_adequacy_established=False,
        scientific_decision='abstain')


def sources(root):
    from .studies.dependencies import source_closure
    root=Path(root).resolve()
    return source_closure(root,[
        'analysis/lll/ilvis0_correction_forecast_study.py',
        'analysis/tests/test_ilvis0_correction_forecast_study.py',
        'analysis/tests/test_task_resume.py',
        'analysis/tests/test_task_continuation.py',PLAN,*SCIENCE_SOURCES])


def required_tests():
    return ('test_three_fixed_cases_have_one_charged_forecast_each',
            'test_path_difference_uses_predictions_only_and_checks_shape',
            'test_case_staging_never_reads_scoring_positions',
            'test_source_closure_includes_both_native_translation_units',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=runtime_environment(),
                   output=REQUEST,report=REPORT)


def stage_case(prior,identity,candidate):
    """Copy only the sealed training inputs and two predicted paths."""
    from .studies.artifacts import encoded
    segment=identity.split('-')[0]
    payload=prior.tasks[identity]['payload']
    if payload!=dict(segment_id=segment,origin='outer',profile=False,
                     clock='header_elapsed',start=int(identity.rsplit('-',1)[1])):
        raise ValueError('unchanged selected outer task required')
    common=prior.input(segment+'-common',raw=True)
    training=prior.input(segment+'-outer-training',raw=True)
    fit=prior.artifact(identity,'fit.json',raw=True)
    forecast=prior.artifact(identity,'forecast.json',raw=True)
    raw=json.loads(gzip.decompress(common))
    predicted=json.loads(forecast)
    if (len(predicted['times'])<=predicted['training_epochs'] or
            len(raw['values'])!=raw['layout']['native_packets']):
        raise ValueError('exact saved outer forecast layout required')
    layout=dict(segment_id=segment,native_packets=len(raw['values']),
                queries=len(predicted['times']))
    material={identity+'-common':common,identity+'-training':training,
              identity+'-fit':fit,identity+'-forecast':forecast,
              identity+'-candidate':encoded(candidate)}
    return layout,material


def prepare(root,*,qualification=None):
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic,digest,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    root=Path(root).resolve()
    base=safe_path(root,'data/'+ID+'-inputs')
    if qualification is None or base.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh qualified finite correction study required')
    request,tests=checked(root,qualification,sources=sources(root),
        environment=runtime_environment(),required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    saved=json.loads((root/'docs/prediction-group-transfer/'
                      'remaining-correction-candidates.json').read_bytes())
    stopping=json.loads((root/'docs/prediction-group-transfer/'
                         'remaining-stopping-audit.json').read_bytes())
    ordered=sorted((row for row in stopping['rows'] if row['probe_reason']==
                    'fresh_position_probe_not_stable'),
                   key=lambda row:(row['actual_cost_change'],row['identity']))
    if (len(ordered)!=49 or tuple(ordered[i]['identity'] for i in (0,24,48))!=CASES
            or saved['manifest_sha256']!=PARENT_MANIFEST
            or saved['reconstructed_candidates']!=49
            or saved['forecast_computed'] is not False
            or saved['native_calls']!=0):
        raise ValueError('exact saved numerical selection required')
    candidates={row['identity']:row for row in saved['candidates']}
    if len(candidates)!=49 or not set(CASES)<=set(candidates):
        raise ValueError('complete distinct saved correction candidates required')
    prior=ClosedStudy(root,PARENT)
    try:
        if (prior.completion['manifest_sha256']!=PARENT_MANIFEST or
                len(prior.tasks)!=80 or prior.completion['state'] not in
                ('complete','terminal') or saved['completion_summary_sha256']!=
                prior.completion['summary_sha256']):
            raise ValueError('unchanged closed parent required')
        for name in SCIENCE_SOURCES:
            if prior.manifest['sources'].get(name)!=digest((root/name).read_bytes()):
                raise ValueError('frozen scientific source changed: '+name)
        material=dict(recipe=prior.input('recipe',raw=True),
            **{'qualification-request':request,'qualification-report':tests,
               'selection':encoded(dict(cases=CASES,
                    parent_manifest_sha256=PARENT_MANIFEST,
                    correction_sha256=digest(encoded(saved)),
                    stopping_sha256=digest(encoded(stopping))))})
        layouts={}
        for identity in CASES:
            layout,case_material=stage_case(prior,identity,candidates[identity])
            layouts[identity]=layout
            material.update(case_material)
    finally:
        prior.close()
    material['layouts']=encoded(layouts)
    base.mkdir(parents=True)
    inputs={}
    for index,(key,raw) in enumerate(material.items()):
        target=base/f'input-{index:03d}'
        atomic(target,raw)
        inputs[key]=target.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/ilvis0_correction_forecast_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(layouts),
        workers=3,threads=1,maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition))
    return Definition.from_dict(definition,root).prepare(root)


def evaluate(task,context):
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_shape import instrument_limits,load_tangent
    from .ilvis0_prediction import training_inputs
    from .ilvis0_training_forecast import training_problem
    from .ilvis0_forecast import native_forecast
    from .ilvis0_gps_sensitivity import assumptions,coordinate_covariance
    from .ilvis0_rolling_origin_study import recipe
    layouts=json.loads(context.input_path('layouts').read_bytes())
    identity=task['identity']
    declared={key:value for key,value in task.items() if key not in ('index','shard')}
    if (context.manifest['scope']!=SCOPE or
            declared!={row['identity']:row for row in tasks(layouts)}.get(identity)
            or json.loads(context.input_path('recipe').read_bytes())!=recipe()):
        raise ValueError('unchanged source-bound correction task required')
    common=json.loads(gzip.decompress(context.input_path().read_bytes()))
    prefix=json.loads(context.input_path(identity+'-training').read_bytes())
    fit=json.loads(context.input_path(identity+'-fit').read_bytes())
    original=json.loads(context.input_path(identity+'-forecast').read_bytes())
    correction=json.loads(context.input_path(identity+'-candidate').read_bytes())
    policy=recipe()
    times=np.asarray(common['times'],float)
    values=np.asarray(common['values'],float)
    training_gps=np.asarray(prefix['training_gps'],float)
    cut=prefix['cut_epoch']
    query=np.asarray(original['times'],float)
    if (common['segment_id']!=task['payload']['segment_id'] or
            prefix['segment_id']!=common['segment_id'] or
            correction['identity']!=identity or cut!=len(training_gps) or
            len(query)!=layouts[identity]['queries'] or
            query.tobytes()!=times[:len(query)].tobytes() or
            original['training_epochs']!=cut or
            len(values)!=layouts[identity]['native_packets'] or
            values.shape[1]!=15 or
            len(correction['candidate_parameters'])!=len(fit['normalized_parameters'])):
        raise ValueError('unchanged saved forecast inputs required')
    limits=instrument_limits(policy['gyro_offset_dph'])
    placeholder=np.zeros((len(times),3));placeholder[:cut]=training_gps
    t,gps,v=training_inputs(times,placeholder,values,
                            limits['time_offset'],cut=cut)
    assumption=next(row for row in assumptions()
                    if row.name==policy['training_weight'])
    blocks=np.tile(np.diag(np.square(policy['independent_neu_m'])),
                   (len(t),1,1))
    covariance=coordinate_covariance(t,gps[:,0],gps[:,2],blocks,assumption)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel,kmeta=load_kernel(directory)
    tangent,tmeta=load_tangent(directory)
    for name,meta in (('ilvis0_native.c',kmeta),
                      ('ilvis0_tangent.cpp',tmeta)):
        if context.manifest['sources']['analysis/lll/'+name]!=meta['source_sha256']:
            raise ValueError('compiled native source differs from freeze')
    problem=training_problem(t,gps,theta=v[:,9:12],dv=v[:,12:15],dt=v[:,2],
        covariance=covariance,model='sphere_rotating',limits=limits,
        profile=False,clock='header_elapsed',
        maximum_interval_s=policy['maximum_interval_s'],
        kernel=kernel,tangent_kernel=tangent)
    if list(problem.bounds.active)!=fit['active_parameters']:
        raise ValueError('frozen parameter order differs')
    forecast=native_forecast(problem,
        np.asarray(correction['candidate_parameters'],float),'sphere_rotating',
        theta=values[:,9:12],dv=values[:,12:15],dt=values[:,2],
        times=query,maximum_interval_s=policy['maximum_interval_s'],
        reserve=context.charge)
    context.save('candidate-forecast.json',dict(
        coordinates=forecast['coordinates'].tolist(),times=query.tolist(),
        original_identity=identity,training_epochs=cut,
        prediction_receiver_positions_used=False))
    difference=path_difference(original['coordinates'],forecast['coordinates'],
                               training_epochs=cut)
    context.save('path-difference.json',difference)
    return dict(passed=True,original_identity=identity,
                later_epochs=difference['later_epochs'],
                rms_neu_m=difference['rms_neu_m'],
                max_absolute_neu_m=difference['max_absolute_neu_m'],
                maximum_horizontal_m=difference['maximum_horizontal_m'],
                native_calls=1,withheld_positions_read=False,
                original_reads=0,refits=0,scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    parser.add_argument('--root',default='.')
    parser.add_argument('--qualification',default=None)
    args=parser.parse_args(argv)
    root=Path(args.root).resolve()
    if args.action=='request':
        result=request_qualification(root)
    elif args.action=='prepare':
        result=prepare(root,qualification=args.qualification)
    else:
        from .ilvis0_control_shards import launch
        result=launch(root/'data'/ID,reserved_threads=0)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
