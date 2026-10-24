# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite closed-form training/forecast controls, without aircraft observations."""
import math
from pathlib import Path


def recipe(stopping='ordinary'):
    if stopping not in ('ordinary','near_zero'):raise ValueError('supported stopping policy required')
    value=dict(packets=4800,period_s=.005,times_s=list(map(float,range(1,24))),
        models=3,processing_cases=2,clocks=['header_elapsed','nominal_200Hz'],starts=2,
        maximum_evaluations=600,maximum_interval_s=.0075,position_rms_m=.001,
        position_max_m=.01,maximum_training_cost=.01,receiver_sigma_m=.01,
        workers=1,threads=4,maximum_wall_s=3600.,original_reads=0,observed_starts=0)
    if stopping!='ordinary':value['stopping']=stopping
    return value


def case_arrays(model,profile,clock):
    """Analytic equatorial motion, independent of native forward equations.

    Local NED velocity is constant eastward. The body X axis points east.
    Circle geometry fixes the local-frame rate; force balances that rotation,
    the candidate background term and gravity. No numerical predictor supplies
    the receiver truth, gyro increments or force increments.
    """
    import numpy as np
    if type(model) is not int or model not in range(3) or type(profile) is not bool or clock not in recipe()['clocks']:
        raise ValueError('declared model, processing case and clock required')
    r=recipe();dt=np.full(r['packets'],r['period_s'])
    if clock=='header_elapsed':dt[::2]=.0049;dt[1::2]=.0051
    times=np.array(r['times_s']);speed=220.;height=20.
    radius=6378137.+height if model<2 else 6371000.*math.pi/2
    longitude_rate=speed/radius
    earth=np.array([7.292115e-5 if model==0 else 0.,0.,0.])
    transport=np.array([longitude_rate,0.,0.]) if model<2 else np.array([0.,0.,-longitude_rate])
    removed=np.array([.35*7.292115e-5 if profile else 0.,0.,0.])
    body_to_ned=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    omega=body_to_ned.T@(earth+transport-removed)
    force=body_to_ned.T@(np.cross(2*earth+transport,[0.,speed,0.])-[0.,0.,9.81])
    return dict(theta=dt[:,None]*omega,dv=dt[:,None]*force,dt=dt,times=times,
        gps=np.c_[times*0,longitude_rate*times,np.full(len(times),height)])


def control_tasks(stopping='ordinary'):
    from lll.ilvis0_control_shards import _tasks
    r=recipe(stopping);tasks=[]
    for model in range(3):
        for profile in (False,True):
            for clock in r['clocks']:
                for start in range(2):
                    # Full history/query counts bound every training and forecast call.
                    calls=r['maximum_evaluations']+1
                    payload=dict(model=model,profile=profile,clock=clock,start=start)
                    if stopping!='ordinary':payload['stopping']=stopping
                    tasks.append(dict(identity=f'forecast-{model}-{int(profile)}-{clock}-{start}',input_key='recipe',
                        payload=payload,
                        limits=dict(native_calls=calls,packet_visits=calls*r['packets']*len(r['times_s']),
                            bound_calls=0,bound_steps=0)))
    _tasks(tasks,r['workers'])
    return tasks


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/ilvis0_forecast_controls.py',
        'analysis/tests/test_ilvis0_training_forecast.py','analysis/tests/test_ilvis0_near_zero.py',
        'docs/ilvis0-near-zero-forecast-controls/PLAN.md',
        'analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_native.c'])


def qualification_request(root,output,report):
    """Bind the code/environment before a local software test, without running it."""
    import subprocess
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.ilvis0_control_shards import runtime_environment
    root=Path(root).resolve();path=safe_path(root,output);safe_path(root,report)
    if path.exists():raise ValueError('fresh software qualification request required')
    value=dict(sources={n:digest((root/n).read_bytes()) for n in qualification_sources(root)},
        environment=runtime_environment(),report=report,
        compilers={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('cc','c++')})
    atomic(path,encoded(value));return dict(request=output,report=report,sources=len(value['sources']))


def _software_checked(root,qualification):
    import json
    import subprocess
    import xml.etree.ElementTree as ET
    from lll.studies.artifacts import digest,safe_path
    from lll.ilvis0_control_shards import runtime_environment
    if qualification is None:raise ValueError('passing software qualification required before preparation')
    raw=safe_path(root,qualification).read_bytes();q=json.loads(raw)
    expected={n:digest((root/n).read_bytes()) for n in qualification_sources(root)}
    if (q['sources']!=expected or q['environment']!=runtime_environment()
            or q['compilers']!={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('cc','c++')}):
        raise ValueError('software qualification source or environment differs')
    report=safe_path(root,q['report']).read_bytes();tree=ET.fromstring(report)
    tests=list(tree.iter('testcase'));names=[v.attrib['name'] for v in tests]
    required=('test_new_composition_checks_near_zero_without_relabeling_the_ordinary_solver',
        'test_near_zero_repeat_failure_and_nonzero_budget_exhaustion_remain_failures',
        'test_repeat_cannot_change_the_observation_vector_length',
        'test_near_zero_control_definition_preserves_geometry_and_allowances')
    if (not all(name in names for name in required)
            or sum(n.startswith('test_nonzero_known_optima_and_bounds_keep_the_original_gate[') for n in names)!=40
            or any(list(v) for v in tests)
            or any(int(s.attrib.get(k,0)) for s in tree.iter('testsuite') for k in ('failures','errors','skipped'))):
        raise ValueError('complete passing near-zero/nonzero software qualification required')
    return raw,report


def _matched_physics(root):
    import ast
    from lll.studies.artifacts import digest
    from lll.studies.closed import ClosedStudy
    baseline=ClosedStudy(root,'docs/ilvis0-training-forecast-controls')
    names=['analysis/lll/'+n for n in ('ilvis0_tangent.cpp','ilvis0_native.c','ilvis0_shape.py',
        'ilvis0_exploratory.py','ilvis0_estimator.py','ilvis0_forward.py','ilvis0_corpus_modeling.py',
        'models.py','ilvis0_forecast.py','ilvis0_solver_trust_v2.py','ilvis0_solver_position.py',
        'ilvis0_solver_refinement.py','ilvis0_solver_boundary.py')]
    try:
        unchanged={n:digest((root/n).read_bytes()) for n in names}
        if any(baseline.manifest['sources'].get(n)!=sha for n,sha in unchanged.items()):
            raise ValueError('matched physical/native/ordinary-solver source differs')
        name='analysis/lll/ilvis0_forecast_controls.py'
        old=ast.parse(baseline.read('source-freeze/'+name,baseline.manifest['sources'][name],raw=True))
        new=ast.parse((root/name).read_bytes())
        function=lambda tree:next(v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name=='case_arrays')
        if ast.dump(function(old),include_attributes=False)!=ast.dump(function(new),include_attributes=False):
            raise ValueError('independent generated track function changed')
        if baseline.input('recipe')!=recipe():raise ValueError('matched geometry or numerical limits changed')
        return dict(parent=baseline.prefix,manifest_sha256=baseline.completion['manifest_sha256'],
            unchanged_sources=unchanged,generated_track_ast_unchanged=True)
    finally:baseline.close()


def prepare(root,identity='ilvis0-training-forecast-controls-v3-20261023',*,stopping='ordinary',qualification=None):
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh qualification identity required')
    checked=_software_checked(root,qualification) if stopping=='near_zero' else None
    matched=_matched_physics(root) if stopping=='near_zero' else None
    r=recipe(stopping);tasks=control_tasks(stopping)
    plan=('docs/ilvis0-near-zero-forecast-controls/PLAN.md' if stopping=='near_zero'
          else 'docs/ilvis0-training-forecast-controls/PLAN.md')
    sources=source_closure(root,['analysis/lll/ilvis0_forecast_controls.py',
        plan,'analysis/tests/test_ilvis0_training_forecast.py','analysis/tests/test_ilvis0_near_zero.py',
        'analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_native.c'])
    base.mkdir(parents=True);path=base/'recipe.json';atomic(path,encoded(r));inputs=dict(recipe=path.relative_to(root).as_posix())
    if checked is not None:
        for name,raw in [('software-request.json',checked[0]),('software-report.xml',checked[1]),('matched-physics.json',encoded(matched))]:
            atomic(base/name,raw);inputs[name]=str((base/name).relative_to(root))
    definition=dict(id=identity,adapter='analysis/lll/ilvis0_forecast_controls.py',sources=sources,
        inputs=inputs,tasks=tasks,workers=r['workers'],
        threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=len(tasks),allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    import json
    import numpy as np
    from lll.ilvis0_exploratory import MODELS,load_kernel
    from lll.ilvis0_shape import instrument_limits,load_tangent
    from lll.ilvis0_prediction import split
    from lll.ilvis0_training_forecast import training_problem,fit_training
    from lll.ilvis0_forecast import native_forecast
    from lll.studies.artifacts import digest
    stopping=task.get('payload',{}).get('stopping','ordinary');r=recipe(stopping)
    if json.loads(context.input_path().read_bytes())!=r:raise ValueError('frozen control recipe differs')
    spec=task['payload'];case=case_arrays(spec['model'],spec['profile'],spec['clock'])
    cut=split(case['times'])['training_epochs'];limits=instrument_limits(1.)
    count=int(np.searchsorted(np.cumsum(case['dt']),case['times'][cut-1]+limits['time_offset']))+1
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel,kmeta=load_kernel(directory);tangent,tmeta=load_tangent(directory)
    for filename,meta in [('ilvis0_native.c',kmeta),('ilvis0_tangent.cpp',tmeta)]:
        if context.manifest['sources']['analysis/lll/'+filename]!=meta['source_sha256']:
            raise ValueError('compiled native source differs from freeze')
    context.save('compilation.json',dict(value=kmeta,tangent=tmeta))
    model=MODELS[spec['model']];scale=np.array([6371000.,6371000.,1.])
    sigma=np.tile(r['receiver_sigma_m']/scale,cut)
    problem=training_problem(case['times'][:cut],case['gps'][:cut],
        theta=case['theta'][:count],dv=case['dv'][:count],dt=case['dt'][:count],
        covariance=np.diag(sigma*sigma),model=model,limits=limits,profile=spec['profile'],clock=spec['clock'],
        maximum_interval_s=r['maximum_interval_s'],kernel=kernel,tangent_kernel=tangent)
    n=len(problem.bounds.active);start=np.zeros(n) if spec['start']==0 else np.where(np.arange(n)%2,-.001,.001)
    fit=fit_training(problem,model,start=start,maximum_evaluations=r['maximum_evaluations'],reserve=context.charge,stopping=stopping)
    context.save('fit.json',fit)
    forecast=native_forecast(problem,fit['normalized_parameters'],model,theta=case['theta'],dv=case['dv'],dt=case['dt'],
        times=case['times'],maximum_interval_s=r['maximum_interval_s'],reserve=context.charge)
    error=(forecast['coordinates']-case['gps'])*scale;sections={}
    for name,slice_ in [('training',slice(0,cut)),('prediction',slice(cut,None))]:
        e=error[slice_];rms=np.sqrt(np.mean(e*e,axis=0));maximum=np.max(abs(e),axis=0)
        sections[name]=dict(rms_neu_m=rms.tolist(),maximum_abs_neu_m=maximum.tolist())
    active_ok=(forecast['active_parameters']==list(problem.bounds.active) and len(problem.bounds.active)==26+int(spec['profile']))
    passed=bool(fit['converged'] and active_ok and fit['residual_sum_squares']<=r['maximum_training_cost']
        and all(max(v['rms_neu_m'])<=r['position_rms_m'] and max(v['maximum_abs_neu_m'])<=r['position_max_m']
            for v in sections.values()))
    context.save('forecast.json',dict(coordinates=forecast['coordinates'].tolist(),coordinate_errors=error.tolist(),
        active_parameters=forecast['active_parameters'],training_epochs=cut,prediction_epochs=len(error)-cut,
        continuous_propagation_without_gps_reset=True,confidence_calibrated=False))
    return dict(passed=passed,model=model,profile=spec['profile'],clock=spec['clock'],start=spec['start'],
        converged=fit['converged'],training_cost=fit['residual_sum_squares'],evaluations=fit['evaluations'],
        active_columns=len(problem.bounds.active),all_active_columns_retained=active_ok,**sections,
        training_prefix_sha256=digest(case['theta'][:count].tobytes()+case['dv'][:count].tobytes()+case['dt'][:count].tobytes()),
        original_reads=0,observed_starts=0,scientific_decision='abstain')
