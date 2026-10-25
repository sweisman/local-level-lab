# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated geographic qualification using the existing rate and motion code."""
import math

from lll.airquantumgrav_truth import MODELS,A,E2,DISC_RADIUS,GRAVITY
from lll.airquantumgrav_increments import METHODS

VERSION='esa-geographic-rate-controls-v1'


def recipe():
    return dict(version=VERSION,duration_s=1200.,rates_hz=[300,600],query_start_s=.5,
        query_step_s=1.,queries=1200,latitudes_deg=[-55.,55.],removals=[0.,.35],
        patterns=['slow','fast'],methods=list(METHODS),models=list(MODELS),
        refinement_factor=dict(left_hold=.6,right_hold=.6,linear_points=.4),
        refinement_allowance_m=.001,linear_accuracy=dict(horizontal_rms_m=1.,vertical_rms_m=1.,maximum_3d_m=5.),
        maximum_constructed_intervals=1080000,maximum_generated_samples=1081202,
        workers=1,threads=4,maximum_wall_s=14400.,
        original_reads=0,observed_starts=0,retries=0)


def tasks():
    r=recipe();result=[]
    intervals=sum(round(r['duration_s']*hz) for hz in r['rates_hz'])
    if (intervals!=r['maximum_constructed_intervals']
            or intervals+len(r['rates_hz'])+r['queries']!=r['maximum_generated_samples']):
        raise ValueError('declared construction and generated-sample limits differ')
    for model in MODELS:
        for latitude in r['latitudes_deg']:
            for removal in r['removals']:
                for pattern in r['patterns']:
                    for method in METHODS:
                        identity=f"{model}-{'south' if latitude<0 else 'north'}-{int(removal*100)}-{pattern}-{method}"
                        result.append(dict(identity=identity,input_key='recipe',native_kind='value',payload=dict(model=model,
                            latitude_deg=latitude,removal=removal,pattern=pattern,method=method,
                            maximum_constructed_intervals=r['maximum_constructed_intervals'],
                            maximum_generated_samples=r['maximum_generated_samples']),
                            limits=dict(native_calls=2,packet_visits=intervals*r['queries'],bound_calls=0,bound_steps=0)))
    return result


def construct(case,*,method,rate_hz,reserve,chunk_size=4096):
    import numpy as np
    from lll.airquantumgrav_increments import IntervalStream
    if (method not in METHODS or type(rate_hz) is not int or rate_hz not in (300,600)
            or not callable(reserve) or type(chunk_size) is not int or not 1<=chunk_size<=65536):
        raise ValueError('declared sampling, rate, charge callback and chunk size required')
    t=np.asarray(case['times'],float);w=np.asarray(case['angular_rate_rads'],float)
    f=np.asarray(case['specific_force_mps2'],float);n=len(t)
    if (t.ndim!=1 or n<2 or w.shape!=(n,3) or f.shape!=(n,3)
            or any(not np.all(np.isfinite(v)) for v in (t,w,f))):
        raise ValueError('complete finite original generated time/rate/force samples required')
    reserve(constructed_intervals=n-1)
    stream=IntervalStream(method=method);theta=np.empty((n-1,3));dv=np.empty_like(theta);dt=np.empty(n-1);index=0
    for start in range(0,n,chunk_size):
        rows=(dict(gps_time_s=float(t[i]),angular_rate_rads=w[i].tolist(),acceleration_mps2=f[i].tolist())
              for i in range(start,min(n,start+chunk_size)))
        for row in stream.push(rows):
            theta[index]=row['dtheta_rad'];dv[index]=row['dv_mps'];dt[index]=row['dt_s'];index+=1
    if index!=n-1:raise ValueError('constructed interval count differs from complete support')
    return dict(theta=theta,dv=dv,dt=dt,constructed_not_logged_increments=True,sampling_hypothesis=method)


def propagate(increments,times,initial,*,model,removal,kernel,reserve):
    import numpy as np
    if model not in MODELS or not math.isfinite(removal) or not 0<=removal<=1 or not callable(reserve):
        raise ValueError('declared model, removal and charge callback required')
    theta,dv,dt=(np.ascontiguousarray(increments[k],dtype=float) for k in ('theta','dv','dt'))
    t=np.ascontiguousarray(times,dtype=float);c=np.ascontiguousarray(initial['coordinates'],dtype=float)
    v=np.ascontiguousarray(initial['velocity'],dtype=float);r=np.ascontiguousarray(initial['rotation'],dtype=float)
    n=len(dt)
    if (dt.shape!=(n,) or not n or theta.shape!=(n,3) or dv.shape!=(n,3) or t.ndim!=1 or not len(t)
            or c.shape!=(3,) or v.shape!=(3,) or r.shape!=(3,3)
            or any(not np.all(np.isfinite(x)) for x in (theta,dv,dt,t,c,v,r))
            or np.any(dt<=0) or np.any(dt>1.5/300.) or np.any(np.diff(t)<=0)
            or t[0]<0 or t[-1]>np.cumsum(dt)[-1]
            or not np.allclose(r.T@r,np.eye(3),atol=1e-10,rtol=0) or abs(np.linalg.det(r)-1)>1e-10):
        raise ValueError('supported complete increments, queries and proper initial state required')
    output=np.empty((len(t),3));reserve(native_calls=1,packet_visits=n*len(t))
    code=kernel(n,theta,dv,dt,len(t),t,c,v,r,np.zeros(3),MODELS.index(model),GRAVITY,DISC_RADIUS,removal,output)
    if code or not np.all(np.isfinite(output)):raise ValueError('native geographic propagation outside support')
    return output


def position_errors(predicted,answer,*,model):
    """Actual candidate-space metres, projected on the known true local axes."""
    import numpy as np
    p=np.asarray(predicted,float);truth=np.asarray(answer['position_world_m'],float)
    if model not in MODELS or p.ndim!=2 or p.shape[1]!=3 or p.shape!=truth.shape or not len(p):
        raise ValueError('declared geometry and aligned three-coordinate predictions required')
    if not np.all(np.isfinite(p)) or np.any(abs(p[:,0])>=math.pi/2):raise ValueError('finite nonpolar coordinates required')
    phi,longitude,h=p.T
    if model.startswith('sphere'):
        rn=A/np.sqrt(1-E2*np.sin(phi)**2);radius=(rn+h)*np.cos(phi);height=(rn*(1-E2)+h)*np.sin(phi)
    else:radius=DISC_RADIUS*(math.pi/2-phi);height=h
    world=np.column_stack((radius*np.cos(longitude),radius*np.sin(longitude),height))
    local=np.asarray(answer['body_axes_world'])@np.asarray(answer['attitude_body_to_local']).swapaxes(1,2)
    error=np.einsum('nji,nj->ni',local,world-truth);error[:,2]*=-1
    if not np.all(np.isfinite(error)):raise ValueError('finite physical errors required')
    return error


def metrics(errors):
    import numpy as np
    e=np.asarray(errors,float)
    if e.ndim!=2 or e.shape[1]!=3 or not len(e) or not np.all(np.isfinite(e)):
        raise ValueError('finite nonempty physical error series required')
    rms=np.sqrt(np.mean(e*e,axis=0));norm=np.linalg.norm(e,axis=1)
    return dict(rms_neu_m=rms.tolist(),horizontal_rms_m=float(np.linalg.norm(rms[:2])),
        vertical_rms_m=float(rms[2]),maximum_3d_m=float(norm.max()),total_rms_m=float(np.linalg.norm(rms)))


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_geographic_controls.py',
        'analysis/tests/test_airquantumgrav_geographic_study.py','analysis/tests/test_airquantumgrav_geographic_controls.py',
        'analysis/lll/studies/qualification.py','docs/esa-geographic-rate-controls/PLAN.md',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_shape.py'])


def environment():
    import subprocess
    from lll.ilvis0_control_shards import runtime_environment
    return dict(runtime_environment(),compilers={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0]
        for c in ('cc','c++')})


def required_tests():
    names=['test_generator_import_contract_keeps_navigation_code_separate',
        'test_geographic_definition_preserves_complete_matrix_and_finite_work',
        'test_construct_keeps_original_channels_and_stream_chunk_equivalence',
        'test_definition_explicitly_includes_both_native_sources',
        'test_disc_error_metric_uses_disc_distance_not_globe_longitude_scale',
        'test_finite_evaluator_reconciles_all_charges_and_persists_its_journal',
        'test_bad_frozen_recipe_is_rejected_before_compilation_or_charges',
        'test_geographic_loaders_compile_from_the_declared_isolated_snapshot',
        'test_preparation_requires_passing_source_bound_qualification_before_files']
    names += [f'test_construct_rejects_unsupported_inputs_without_repair[{v}]' for v in ('method','gap','reversal','nonfinite')]
    names += [f'test_stationary_limit_preserves_signed_background_and_specific_force[{latitude}-{model}]'
              for latitude in (-55.,55.) for model in MODELS]
    names += [f'test_analytic_derivatives_match_independent_five_point_samples[{pattern}-{model}]'
              for pattern in ('slow','fast') for model in MODELS]
    names += [f'test_common_removal_changes_only_the_logged_angular_channels[{model}]' for model in MODELS]
    names += [f'test_native_adapter_matches_independent_short_geometry_and_exact_charges[{removal}-{latitude}-{model}]'
              for removal in (0.,.35) for latitude in (-55.,55.) for model in MODELS]
    return names


def prepare(root,*,qualification,identity='esa-geographic-rate-controls-20261023'):
    import re
    from pathlib import Path
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if qualification is None:raise ValueError('passing source-bound software qualification required')
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('safe fresh study identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh geographic study identity required')
    source=sources(root);env=environment();required=required_tests()
    request,report=checked(root,qualification,sources=source,environment=env,
        required_tests=required,minimum_tests=len(required))
    base.mkdir(parents=True);inputs={}
    for key,name,raw in [('recipe','recipe.json',encoded(recipe())),
                         ('qualification-request','qualification-request.json',request),
                         ('qualification-report','qualification-report.xml',report),
                         ('qualification-environment','qualification-environment.json',encoded(env))]:
        atomic(base/name,raw);inputs[key]=str((base/name).relative_to(root))
    r=recipe();definition=dict(id=identity,adapter='analysis/lll/airquantumgrav_geographic_controls.py',
        sources=source,inputs=inputs,tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=72,allocation=manifest['allocation'],limits=manifest['limits'],
        maximum_constructed_intervals=72*r['maximum_constructed_intervals'],
        maximum_generated_samples=72*r['maximum_generated_samples'])


def evaluate(task,context):
    import json
    import numpy as np
    from lll.airquantumgrav_truth import truth
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    r=recipe();spec=task['payload'];canonical={v['identity']:v for v in tasks()}
    if (json.loads(context.input_path().read_bytes())!=r or task['identity'] not in canonical
            or spec!=canonical[task['identity']]['payload'] or task['limits']!=canonical[task['identity']]['limits']):
        raise ValueError('unchanged frozen geographic recipe, identity and limits required')
    if json.loads(context.input_path('qualification-environment').read_bytes())!=environment():
        raise ValueError('qualified compiler or numerical environment differs')
    journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:dict(constructed_intervals=r['maximum_constructed_intervals'],
            generated_samples=r['maximum_generated_samples'])})
    journal.start(task['identity'])
    try:
        kernel,metadata=load_kernel(context.root/'shards'/f'{context.shard:03d}'/'kernels')
        if metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_native.c']:
            raise ValueError('native geographic source differs from freeze')
        context.save('compilation.json',metadata)
        queries=r['query_start_s']+np.arange(r['queries'])*r['query_step_s']
        arguments={key:spec[key] for key in ('model','latitude_deg','pattern','removal')}
        _check_continue(context.root,context.manifest)
        journal.reserve(task['identity'],'generated_samples',len(queries))
        answer=truth(times=queries,**arguments);summaries=[]
        for hz in r['rates_hz']:
            _check_continue(context.root,context.manifest)
            n=round(r['duration_s']*hz)
            journal.reserve(task['identity'],'constructed_intervals',n)
            journal.reserve(task['identity'],'generated_samples',n+1)
            times=np.arange(n+1)/hz;case=truth(times=times,**arguments);case['times']=times
            def already_reserved(**value):
                if value!=dict(constructed_intervals=n):raise ValueError('construction differs from its precharged size')
            increments=construct(case,method=spec['method'],rate_hz=hz,reserve=already_reserved)
            initial=dict(coordinates=case['coordinates'][0],velocity=case['velocity_local_mps'][0],
                rotation=case['attitude_body_to_local'][0])
            prediction=propagate(increments,queries,initial,model=spec['model'],removal=spec['removal'],
                kernel=kernel,reserve=context.charge)
            error=position_errors(prediction,answer,model=spec['model']);summary=metrics(error)
            context.save(f'rate-{hz}.json',dict(rate_hz=hz,packets=n,times=queries.tolist(),
                coordinates=prediction.tolist(),errors_neu_m=error.tolist(),metrics=summary,
                original_rate_samples_sha256={k:digest(np.asarray(case[k],dtype='<f8').tobytes())
                    for k in ('times','angular_rate_rads','specific_force_mps2')},
                constructed_arrays_sha256={k:digest(np.asarray(increments[k],dtype='<f8').tobytes()) for k in ('theta','dv','dt')},
                constructed_not_logged_increments=True))
            summaries.append(summary)
        coarse,fine=summaries;factor=r['refinement_factor'][spec['method']]
        refinement=fine['maximum_3d_m']<=factor*coarse['maximum_3d_m']+r['refinement_allowance_m']
        accuracy={k:coarse[k]<=limit for k,limit in r['linear_accuracy'].items()}
        accuracy_required=spec['method']=='linear_points'
        journal.verify()
        if any(journal.count(task['identity'],k)!=r['maximum_'+k] for k in ('constructed_intervals','generated_samples')):
            raise ValueError('construction accounting differs from exact frozen scope')
        return dict(passed=bool(refinement and (not accuracy_required or all(accuracy.values()))),
            **spec,coarse=coarse,fine=fine,refinement_passed=bool(refinement),accuracy_required=accuracy_required,
            accuracy_checks=accuracy,native_calls=2,constructed_intervals=r['maximum_constructed_intervals'],
            generated_samples=r['maximum_generated_samples'],original_reads=0,observed_starts=0,
            actual_sampling_established=False,confidence_calibrated=False,scientific_decision='abstain')
    finally:context.note_file(journal.path)
