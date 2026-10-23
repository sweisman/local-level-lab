# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-trajectory distances under supplied common receiver covariances."""
import json
from pathlib import Path


def recipe():
    return dict(correlation_s=[10,300],times_s=list(map(float,range(2,291))),
        sparse_s=[2.,10.,30.,180.,290.],scale=[6371000.,2692500.945549996,1.],
        independent_std_m=[.3,.3,.7],correlated_std_m=[1.,1.,3.],offset_std_m=[1.,1.,3.],
        drift_std_m=[1.,1.,3.],drift_origin_s=0.,drift_span_s=438.,identities=12,
        native_calls=0,optimizer_starts=0,future_epochs_used=False,receiver_component_only=True)


def receiver_spec(tau):
    import numpy as np
    from lll.ilvis0_error_model import Spec
    value=recipe()
    if tau not in value['correlation_s']:raise ValueError('one of the two predeclared correlation times required')
    diagonal=lambda key:np.diag(np.square(value[key]))
    return Spec(diagonal('independent_std_m'),components=((tau,diagonal('correlated_std_m')),),
        offset=diagonal('offset_std_m'),drift=diagonal('drift_std_m'),
        drift_origin_s=value['drift_origin_s'],drift_span_s=value['drift_span_s'])


def joint_recipe():
    return dict(recipe(),mode='joint-component',identities=24,gyro_psd_choices=[1e-12,1e-10],
        accel_psd=1e-8,coupling=[[0.,9.81,0.],[-9.81,0.,0.],[0.,0.,0.]],noise_origin_s=0.,
        noise_values_are_device_estimates=False,receiver_component_only=False)


def joint_operator(times,spec,gyro_psd):
    import numpy as np
    from lll.ilvis0_joint_error_operator import Operator
    settings=joint_recipe()
    if gyro_psd not in settings['gyro_psd_choices']:raise ValueError('one of two declared software gyro PSDs required')
    return Operator(times,spec,origin_s=settings['noise_origin_s'],
        accel_psd=np.eye(3)*settings['accel_psd'],gyro_psd=np.eye(3)*gyro_psd,coupling=settings['coupling'])


def trajectory_distances(times,predictions,scale,spec,*,operator=None):
    import numpy as np
    from lll.ilvis0_structured_covariance import Innovations
    t=np.asarray(times,float);values=np.asarray(predictions,float);units=np.asarray(scale,float)
    if (t.ndim!=1 or not len(t) or values.shape!=(3,len(t),3) or units.shape!=(3,)
            or not np.all(np.isfinite(t)) or not np.all(np.isfinite(values)) or not np.all(np.isfinite(units))
            or np.any(units<=0) or np.any(np.diff(t)<=0) or t[0]<2. or t[-1]>290.):
        raise ValueError('finite complete earlier predictions, positive scales and ordered training times required')
    combinations=[(0,1),(0,2),(1,2)];names=['origin','low','high']
    delta=np.stack([(values[a]-values[b])*units for a,b in combinations],axis=-1)
    if operator is not None and not np.array_equal(operator.times,t):
        raise ValueError('joint operator must use exactly the declared training epochs')
    white=(Innovations(t,spec) if operator is None else operator).whiten(delta.reshape(3*len(t),3))
    if not np.all(np.isfinite(white)):raise ValueError('finite common-law whitening required')
    squares=np.sum(white**2,axis=0);rms=np.sqrt(np.mean(delta**2,axis=0))
    return dict(epochs=len(t),pairs=[dict(roles=[names[a],names[b]],squared_distance=float(squares[j]),
        distance=float(np.sqrt(squares[j])),axis_rms_m=rms[:,j].tolist()) for j,(a,b) in enumerate(combinations)],
        receiver_component_only=operator is None,joint_fixture=operator is not None,
        future_epochs_used=False,uncertainty_qualified=False,
        observations_created=0,scientific_decision='abstain')


def prepare(root,identity='ilvis0-receiver-distance-20261022'):
    from lll.ilvis0_witness_density import inspect as inspect_density
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import safe_path,atomic,encoded
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();prefix='data/ilvis0-witness-density-20261022'
    previous=inspect_density(root,prefix)
    if not previous['assessment']['complete']:raise ValueError('all18fixed predictions must close successfully')
    base=safe_path(root,'data/ilvis0-source-point-development/receiver-distance-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh finite comparison required')
    adapter='analysis/lll/ilvis0_receiver_distance.py';plan='docs/ilvis0-witness-density/ERROR_LAW_COMPARISON_PLAN.md'
    sources=source_closure(root,[adapter,'analysis/tests/test_ilvis0_receiver_distance.py',plan])
    study=ClosedStudy(root,prefix);inputs={};tasks=[]
    def save(key,value):
        path=base/(key+'.json');atomic(path,encoded(value));inputs[key]=path.relative_to(root).as_posix()
    try:
        base.mkdir(parents=True);save('recipe',recipe())
        for m in range(3):
            for p in (False,True):
                selected={t['payload']['role']:t for t in study.tasks.values()
                    if (t['payload']['model'],t['payload']['profile'])==(m,p)}
                if set(selected)!= {'origin','low','high'}:raise ValueError('original calibration and selected pair required')
                values=[];refs={};scale=None
                for role in ('origin','low','high'):
                    task=selected[role];spec=task['payload'];bundle=study.input(spec['bundle_key'])
                    if bundle['problem']['coordinate_scale']!=recipe()['scale']:raise ValueError('common frozen metric required')
                    scale=bundle['problem']['coordinate_scale'];native=study.artifact(task['identity'],'native-output.json')
                    values.append(native['prediction'][:-1])
                    path='artifacts/'+task['identity']+'/native-output.json'
                    refs[role]=dict(path=prefix+'/'+path,sha256=study.envelope(task['identity'])['artifacts'][path])
                key=f'case-{m}-{int(p)}'
                save(key,dict(model=m,profile=p,times_s=recipe()['times_s'],scale=scale,predictions=values,
                    source_study=prefix,source_manifest_sha256=study.completion['manifest_sha256'],source_outputs=refs,
                    original_epoch_values_verified=True))
                for tau in recipe()['correlation_s']:
                    tasks.append(dict(identity=f'distance-{m}-{int(p)}-{tau}',input_key=key,
                        payload=dict(model=m,profile=p,correlation_s=tau),
                        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
        definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,
            workers=1,threads=1,maximum_wall_s=120.)
        atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,identities=12,sources=len(manifest['sources']),
            limits=manifest['limits'],allocation=manifest['allocation'])
    finally:study.close()


def evaluate(task,context):
    import numpy as np
    settings=json.loads(context.input_path('recipe').read_bytes())
    if settings.get('mode')=='joint-component':return evaluate_joint(task,context,settings)
    if settings!=recipe():raise ValueError('unchanged shared receiver-law comparison required')
    value=json.loads(context.input_path().read_bytes());spec=task['payload'];tau=spec['correlation_s']
    if (value['model'],value['profile'])!=(spec['model'],spec['profile']) or value['times_s']!=settings['times_s']:
        raise ValueError('matching fixed candidate and full training cadence required')
    if value['scale']!=settings['scale'] or value['original_epoch_values_verified'] is not True:
        raise ValueError('common metric and original epoch consistency required')
    times=value['times_s'];pred=np.asarray(value['predictions'],float);law=receiver_spec(tau)
    dense=trajectory_distances(times,pred,value['scale'],law)
    indices=[times.index(t) for t in settings['sparse_s']]
    sparse=trajectory_distances(settings['sparse_s'],pred[:,indices,:],value['scale'],law)
    result=dict(identity=task['identity'],passed=True,model=spec['model'],profile=spec['profile'],correlation_s=tau,
        dense=dense,sparse=sparse,receiver_component_only=True,uncertainty_qualified=False,
        future_epochs_used=False,native_evaluations=0,optimizer_starts=0,scientific_decision='abstain')
    context.save('receiver-distances.json',result);return result


def prepare_joint(root,identity='ilvis0-joint-distance-20261022'):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import safe_path,atomic,encoded
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();prefix='data/ilvis0-receiver-distance-20261022'
    prior=inspect(root,prefix)
    if not prior['complete']:raise ValueError('close all12receiver-only comparisons first')
    base=safe_path(root,'data/ilvis0-source-point-development/joint-distance-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('new finite sensitivity freeze required')
    adapter='analysis/lll/ilvis0_receiver_distance.py'
    sources=source_closure(root,[adapter,'analysis/tests/test_ilvis0_receiver_distance.py','docs/ilvis0-joint-distance/PLAN.md'])
    study=ClosedStudy(root,prefix);inputs={};tasks=[]
    def save(key,value):
        path=base/(key+'.json');atomic(path,encoded(value));inputs[key]=path.relative_to(root).as_posix()
    try:
        base.mkdir(parents=True);save('recipe',joint_recipe())
        baseline={f"{r['model']}-{int(r['profile'])}-{r['correlation_s']}":r for r in prior['rows']}
        save('receiver-baselines',dict(rows=baseline,source_manifest_sha256=study.completion['manifest_sha256']))
        for m in range(3):
            for p in (False,True):
                task=next(t for t in study.tasks.values() if (t['payload']['model'],t['payload']['profile'])==(m,p))
                key=f'case-{m}-{int(p)}';save(key,study.input(task['input_key']))
                for tau in recipe()['correlation_s']:
                    for index,q in enumerate(joint_recipe()['gyro_psd_choices']):
                        tasks.append(dict(identity=f'joint-{m}-{int(p)}-{tau}-{index}',input_key=key,
                            payload=dict(model=m,profile=p,correlation_s=tau,gyro_psd=q),
                            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
        definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,
            workers=1,threads=1,maximum_wall_s=120.)
        atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,identities=24,sources=len(manifest['sources']),
            limits=manifest['limits'],allocation=manifest['allocation'])
    finally:study.close()


def evaluate_joint(task,context,settings):
    import numpy as np
    if settings!=joint_recipe():raise ValueError('unchanged joint-component sensitivity required')
    value=json.loads(context.input_path().read_bytes());spec=task['payload'];tau=spec['correlation_s'];q=spec['gyro_psd']
    if ((value['model'],value['profile'])!=(spec['model'],spec['profile'])
            or value['times_s']!=settings['times_s'] or value['scale']!=settings['scale']
            or value['original_epoch_values_verified'] is not True):raise ValueError('unchanged saved means required')
    baselines=json.loads(context.input_path('receiver-baselines').read_bytes())
    baseline=baselines['rows'][f"{spec['model']}-{int(spec['profile'])}-{tau}"]
    times=value['times_s'];pred=np.asarray(value['predictions'],float);law=receiver_spec(tau)
    dense=trajectory_distances(times,pred,value['scale'],law,operator=joint_operator(times,law,q))
    indices=[times.index(t) for t in settings['sparse_s']]
    sparse=trajectory_distances(settings['sparse_s'],pred[:,indices,:],value['scale'],law,
        operator=joint_operator(settings['sparse_s'],law,q))
    for mode,result in (('dense',dense),('sparse',sparse)):
        for old,new in zip(baseline[mode]['pairs'],result['pairs'],strict=True):
            if (new['roles']!=old['roles'] or new['axis_rms_m']!=old['axis_rms_m']
                    or new['squared_distance']>old['squared_distance']+1e-9*max(1.,old['squared_distance'])):
                raise ValueError('independent added noise changed means or increased same-mean separation')
    result=dict(identity=task['identity'],passed=True,**spec,dense=dense,sparse=sparse,
        baseline_dense=baseline['dense'],baseline_sparse=baseline['sparse'],
        independent_added_noise_monotonic=True,noise_values_are_device_estimates=False,
        uncertainty_qualified=False,native_evaluations=0,optimizer_starts=0,scientific_decision='abstain')
    context.save('joint-distances.json',result);return result


def inspect_joint(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[];missing=[]
    try:
        if study.input('recipe')!=joint_recipe():raise ValueError('fixed joint recipe required')
        for identity,task in study.tasks.items():
            if identity not in study.rows or not study.rows[identity]['passed']:missing.append(identity);continue
            value=study.artifact(identity,'joint-distances.json')
            if value!=study.envelope(identity)['result'] or any(value[k]!=v for k,v in task['payload'].items()):
                raise ValueError('joint result differs from frozen identity')
            if not value['independent_added_noise_monotonic'] or value['noise_values_are_device_estimates']:
                raise ValueError('joint sensitivity scope changed')
            rows.append(value)
        expected={(m,p,t,q) for m in range(3) for p in (False,True)
            for t in recipe()['correlation_s'] for q in joint_recipe()['gyro_psd_choices']}
        actual={(r['model'],r['profile'],r['correlation_s'],r['gyro_psd']) for r in rows}
        if len(actual)!=len(rows) or not actual<=expected:raise ValueError('joint matrix changed')
        return dict(rows=rows,missing=missing,complete=actual==expected and not missing,numerical_work=0,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            noise_values_are_device_estimates=False,uncertainty_qualified=False)
    finally:study.close()


def render_joint(report):
    names=['Globe + field','Globe, zero field','Stationary disc']
    text=['# Adding accumulated IMU error to the same saved-trajectory comparison','',
        f"**{len(report['rows'])}/24 calculations completed.** The trajectories and receiver assumptions are "
        'unchanged. This adds two declared linear-noise examples, without refitting a parameter.',
        '', 'An IMU is an inertial measurement unit. Its random turning and acceleration errors can '
        'accumulate into position error. The examples below use isotropic acceleration power density '
        '1e-8 m²/s³ and gyro power densities 1e-12 or 1e-10 rad²/s. **These are software sensitivity '
        'settings, not measured instrument specifications.** The fixed coupling and zero-time noise '
        'origin are assumptions of this linear example.',
        '', '| Model | Processing | Receiver correlation (s) | Gyro PSD (rad²/s) | Receiver-only distance | '
        'Distance with added IMU noise |', '|---|---|---:|---:|---:|---:|']
    for r in report['rows']:
        a=r['baseline_dense']['pairs'][2]['distance'];b=r['dense']['pairs'][2]['distance']
        text.append('| '+' | '.join([names[r['model']],'Profiled removal' if r['profile'] else 'Zero removal',
            str(r['correlation_s']),f"{r['gyro_psd']:.0e}",f'{a:.3f}',f'{b:.3f}'])+' |')
    text+=['', 'Every comparison checks that adding an independent positive noise covariance cannot '
        'increase the noise-scaled separation of the same deterministic means. Raw position differences '
        'remain identical. The distances are not p-values, actual likelihood ratios or Earth-model votes.',
        '', 'This checks a supplied constant-coupling linear law. It does not establish the actual IMU '
        'noise, its independence, trajectory-dependent propagation, complete nonlinear calibration '
        'uncertainty or observational coverage. **V01 remains unqualified.** The 53-stretch findings '
        'and protected ESA data are unchanged.',
        '', '[Frozen scope](PLAN.md) · [Receiver-only comparison](../ilvis0-receiver-distance/README.md) · '
        '[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)']
    return '\n'.join(text)+'\n'


def publish_joint(root,prefix,output='docs/ilvis0-joint-distance'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import safe_path,atomic,encoded,digest
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect_joint(root,prefix);package(data,public,render_joint(report),plan='docs/ilvis0-joint-distance/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[];missing=[]
    try:
        if study.input('recipe')!=recipe():raise ValueError('frozen law recipe required')
        for identity,task in study.tasks.items():
            if identity not in study.rows or not study.rows[identity]['passed']:missing.append(identity);continue
            env=study.envelope(identity);value=study.artifact(identity,'receiver-distances.json')
            if value!=env['result'] or any(value[k]!=v for k,v in task['payload'].items()):
                raise ValueError('saved law comparison differs from its task or envelope')
            if (value['future_epochs_used'] or not value['receiver_component_only']
                    or value['uncertainty_qualified'] or value['dense']['epochs']!=289 or value['sparse']['epochs']!=5):
                raise ValueError('comparison scope differs from frozen training recipe')
            rows.append(value)
        matrix={(r['model'],r['profile'],r['correlation_s']) for r in rows}
        expected={(m,p,t) for m in range(3) for p in (False,True) for t in recipe()['correlation_s']}
        if len(matrix)!=len(rows) or not matrix<=expected:raise ValueError('duplicate or unknown law comparison')
        return dict(rows=rows,missing=missing,complete=matrix==expected and not missing,numerical_work=0,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            receiver_component_only=True,uncertainty_qualified=False)
    finally:study.close()


def render(report):
    labels=['Globe + field','Globe, zero field','Stationary disc']
    text=['# How the receiver-error assumptions change trajectory separation','',
        f"**{len(report['rows'])}/12 saved-data comparisons completed.** These calculations hold every "
        'calibration fixed and use earlier predictions only. They create no observations and perform no fits.',
        '', 'The distance below measures separation between two predicted training trajectories relative '
        'to a supplied receiver covariance. A larger value means greater separation under that assumption. '
        'It is not a p-value, observed likelihood ratio or Earth-model vote.',
        '', '| Model | Processing case | Correlation time (s) | Distance: 5 epochs | Distance: 289 epochs | '
        'Dense north/east/height RMS difference (m) |',
        '|---|---|---:|---:|---:|---|']
    for r in report['rows']:
        sparse=r['sparse']['pairs'][2];dense=r['dense']['pairs'][2]
        text.append('| '+' | '.join([labels[r['model']],'Profiled removal' if r['profile'] else 'Zero removal',
            str(r['correlation_s']),f"{sparse['distance']:.3f}",f"{dense['distance']:.3f}",
            ' / '.join(f'{v:.3f}' for v in dense['axis_rms_m'])])+' |')
    text+=['', 'The table compares the selected low/high pair within each candidate. The evidence also '
        'keeps both distances from the original calibration. All cases use the same coordinate conversion, '
        'noise scales, shared offset and full-record drift anchor; only correlation time changes.',
        '', '**This covers the receiver component only.** Accumulated IMU noise, covariance estimation, '
        'complete nonlinear calibration uncertainty and numerical/clock treatment remain unqualified. '
        'The 53-stretch findings are unchanged, and no new observed prediction fits are authorized.',
        '', '[Frozen calculation](PLAN.md) · [Saved trajectories](../ilvis0-witness-density/README.md) · '
        '[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)']
    return '\n'.join(text)+'\n'


def publish(root,prefix,output='docs/ilvis0-receiver-distance'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import safe_path,atomic,encoded,digest
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),
        plan='docs/ilvis0-witness-density/ERROR_LAW_COMPARISON_PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
