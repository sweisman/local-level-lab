# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded saved-data diagnosis; no motion kernel, fitting or original-source API."""
import json
import math

SCOPE='saved ESA development prediction diagnosis only; no fitting, propagation or original/protected reads'


def recipe():
    return dict(version='esa-saved-prediction-diagnosis-v1',workers=1,threads=1,maximum_wall_s=600.,
        maximum_settings=12,maximum_saved_records=24,maximum_saved_error_epochs=28800,
        maximum_raw_points=360100,receiver_epochs=1200,training_epochs=800,block_s=60.,
        normalized_boundary_threshold=.999,reference_gravity_mps2=9.81,reference_radius_m=6371000.,
        temperature_display_stride=120,native_calls=0,observed_starts=0,new_propagations=0,
        original_reads=0,protected_reads=0,retries=0)


def tasks():
    return [dict(identity='saved-prediction-diagnosis',input_key='pilot-report',payload=dict(recording='187'),
        native_kind='value',limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))]


def closed_parent(root,prefix='docs/esa-development-pilot'):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)
    try:
        receipt=study.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
        report=study.read(name,receipt['artifacts'][name])
        if (not report.get('verified') or report['total']!=24 or report['expected_primaries']!=12
                or report['manifest_sha256']!=study.completion['manifest_sha256']
                or report['summary_sha256']!=study.completion['summary_sha256']):
            raise ValueError('closed, fully audited development pilot required')
        return study,report
    except Exception:study.close();raise


def environment():
    import importlib.metadata
    from lll.airquantumgrav_inventory import environment as base
    return dict(base(),diagnostic_packages=dict(matplotlib=importlib.metadata.version('matplotlib')))


def gravity_reference(times,heights,training_epochs):
    import numpy as np
    t,h=(np.asarray(v,float) for v in (times,heights));cut=training_epochs;r=recipe()
    if (t.ndim!=1 or len(t)<2 or h.shape!=t.shape or not np.all(np.isfinite(t)) or not np.all(np.isfinite(h))
            or np.any(np.diff(t)<=0) or type(cut) is not int or not 0<cut<len(t)
            or np.any(r['reference_radius_m']+h<=0)):
        raise ValueError('finite ordered receiver times, supported heights and training boundary required')
    g=r['reference_gravity_mps2']*((r['reference_radius_m']+h[0])/(r['reference_radius_m']+h))**2
    training_mean=float(np.mean(g[:cut]));difference=float(np.max(abs(g[cut:]-training_mean)))
    duration=float(t[-1]-t[cut]);scale=.5*difference*duration**2
    if not np.all(np.isfinite(g)) or not math.isfinite(scale):raise ValueError('unrepresentable reference sensitivity')
    return dict(reference_gravity_mps2=g.tolist(),minimum_mps2=float(np.min(g)),maximum_mps2=float(np.max(g)),
        range_mps2=float(np.max(g)-np.min(g)),training_mean_mps2=training_mean,
        maximum_later_difference_mps2=difference,prediction_span_s=duration,constant_acceleration_position_scale_m=scale,
        reference_law='illustrative inverse-square radial field, anchored at first receiver height',
        gravity_measured=False,scale_is_forecast=False,scale_is_error_bound=False,causation_established=False)


def fixed_blocks(times,errors,training_epochs):
    import numpy as np
    from lll.airquantumgrav_geographic_report import error_metrics
    t,e=(np.asarray(v,float) for v in (times,errors));cut=training_epochs
    if (t.ndim!=1 or e.shape!=(len(t),3) or not np.all(np.isfinite(t)) or not np.all(np.isfinite(e))
            or np.any(np.diff(t)<=0) or type(cut) is not int or not 0<cut<len(t)):
        raise ValueError('complete fixed receiver times, errors and training boundary required')
    blocks=[]
    for label,first,last in [('training',0,cut),('prediction',cut,len(t))]:
        bins={}
        for i in range(first,last):bins.setdefault(math.floor((t[i]-t[first])/recipe()['block_s']),[]).append(i)
        for number,indices in bins.items():
            blocks.append(dict(section=label,block=number,first_epoch=indices[0],last_epoch=indices[-1],epochs=len(indices),
                first_time_s=float(t[indices[0]]),last_time_s=float(t[indices[-1]]),**error_metrics(e[indices].tolist())))
    return dict(blocks=blocks,epochs=len(t),blocks_are_independent_trials=False,forecasts_changed=False)


def calibration(normalized,limits,force_reference_mps2):
    if (not isinstance(normalized,dict) or not normalized or not math.isfinite(force_reference_mps2) or force_reference_mps2<=0
            or any(not math.isfinite(v) or abs(v)>1 for v in normalized.values())
            or any(k not in limits and k!='earth_removal' for k in normalized)
            or any(not math.isfinite(v) or v<0 for v in limits.values())):
        raise ValueError('finite feasible normalized calibration and declared limits required')
    physical={key:value*limits[key] for key,value in normalized.items() if key in limits}
    return dict(normalized=normalized,physical_linear_parameters=physical,
        near_boundary=[key for key,value in normalized.items() if abs(value)>=recipe()['normalized_boundary_threshold']],
        boundary_threshold=recipe()['normalized_boundary_threshold'],
        force_based_initial_reference_mps2=force_reference_mps2,
        fitted_constant_gravity_mps2=force_reference_mps2+physical.get('gravity_delta',0.),
        force_reference_is_independent_gravity=False,calibration_uniquely_identified=False)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_diagnosis.py','analysis/tests/test_airquantumgrav_diagnosis.py',
        'analysis/tests/test_airquantumgrav_diagnosis_numeric.py',
        'analysis/lll/airquantumgrav_diagnosis_report.py','analysis/tests/test_airquantumgrav_diagnosis_report.py',
        'analysis/lll/studies/qualification.py','docs/esa-development-diagnosis/PLAN.md'])


def required_tests():
    return ['test_diagnosis_has_finite_read_only_scope','test_diagnosis_requires_qualification_before_reading_inputs',
        'test_diagnosis_rejects_open_parent_before_numerical_imports',
        'test_preparation_rejects_unguarded_threads_before_reading_inputs','test_constant_height_has_no_reference_variation',
        'test_increasing_height_has_independently_expected_gravity_change',
        'test_fixed_blocks_never_cross_training_boundary_or_change_errors',
        'test_normalization_and_boundaries_do_not_claim_calibration_identification',
        'test_reference_failure_does_not_clip_or_repair_inputs',
        'test_saved_diagnosis_preserves_missing_predictions_and_has_no_native_work']


def prepare(root,*,qualification,identity='esa-development-diagnosis-20261023'):
    if qualification is None:raise ValueError('source-bound diagnosis qualification required')
    import gzip
    import re
    from pathlib import Path
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh diagnosis identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh diagnosis scope required')
    from lll.compute_budget import environment as thread_environment
    env=environment()
    if env['numerical_environment']!=thread_environment(workers=recipe()['workers'],threads=recipe()['threads']):
        raise ValueError('prepare under the declared thread environment before reading inputs')
    sources=qualification_sources(root)
    request,report=checked(root,qualification,sources=sources,environment=env,required_tests=required_tests(),minimum_tests=len(required_tests()))
    parent,verified=closed_parent(root)
    try:
        curves={}
        for row in verified['rows']:
            if not row['complete']:continue
            scores=parent.artifact(row['identity'],'scores.json')
            curves[row['identity']]=dict(times_s=scores['times_s'],errors_neu_m=scores['errors_neu_m'],
                source_sha256=parent.envelope(row['identity'])['artifacts']['artifacts/'+row['identity']+'/scores.json'])
        r=recipe()
        if len(curves)>r['maximum_saved_records'] or sum(len(v['times_s']) for v in curves.values())>r['maximum_saved_error_epochs']:
            raise ValueError('parent exceeds finite diagnosis scope')
        materials={key:parent.input(key,raw=True) for key in ('interval','scoring','query-layout')}
        materials.update({'pilot-report':encoded(verified),'pilot-manifest':parent.read('manifest.json',parent.completion['manifest_sha256'],raw=True),
            'curves':gzip.compress(encoded(curves),mtime=0),'recipe':encoded(r),'qualification-request':request,
            'qualification-report':report,'qualification-environment':encoded(env)})
    finally:parent.close()
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(materials.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_diagnosis.py',sources=sources,
        inputs=inputs,tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,scope=manifest['scope'],allocation=manifest['allocation'],native_calls=0)


def _plots(save_bytes,context,cases,curves,training_epochs):
    import io
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    times=np.asarray(context['times_s']);minutes=(times-times[0])/60;boundary=minutes[training_epochs]
    fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True)
    axes[0].plot(minutes,context['height_m']);axes[0].set_ylabel('Receiver height (m)')
    axes[1].plot(minutes,context['ground_speed_kmh']);axes[1].set_ylabel('Ground speed (km/h)')
    axes[2].plot((np.asarray(context['temperature_time_s'])-times[0])/60,context['temperature_c']);axes[2].set_ylabel('IMU temperature (°C)')
    axes[2].set_xlabel('Minutes from first receiver query')
    for ax in axes:ax.axvline(boundary,color='black',linestyle='--',label='Prediction begins');ax.grid(alpha=.2)
    axes[0].legend();fig.suptitle('Recorded context; temperature uses recorded samples without interpolation')
    fig.tight_layout();buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=160);plt.close(fig);save_bytes('context.png',buffer.getvalue())
    fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True)
    colors=dict(sphere_rotating='#176aa8',sphere_still='#bd6d00',flat_still='#a52958');available=False
    labels=dict(sphere_rotating='Globe + field',sphere_still='Globe, zero field',flat_still='Tested disc')
    for case in cases:
        if not case['available']:continue
        spec=case['spec'];values=np.asarray(curves[case['identity']]['errors_neu_m']);available=True
        label=f"{labels[spec['model']]}, {'profiled' if spec['profile'] else 'zero'} removal, {'short' if spec['policy_id']=='reported-short-v1' else 'persistent'} errors"
        for j,ax in enumerate(axes):
            ax.plot(minutes,values[:,j],color=colors[spec['model']],linestyle='--' if spec['profile'] else '-',
                alpha=.9 if spec['policy_id']=='reported-short-v1' else .45,label=label if j==0 else None)
    for ax,axis in zip(axes,('North','East','Height'),strict=True):
        ax.set_yscale('symlog',linthresh=1.);ax.set_ylabel(axis+' error (m)');ax.axvline(boundary,color='black',linestyle=':');ax.grid(alpha=.2)
    if available:axes[0].legend(fontsize=6,ncol=2)
    axes[-1].set_xlabel('Minutes from first receiver query')
    fig.suptitle('Unchanged saved errors; symmetric log scale beyond ±1 m; dotted line begins prediction')
    fig.tight_layout();buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=160);plt.close(fig);save_bytes('saved-errors.png',buffer.getvalue())


def evaluate(task,context):
    import gzip
    import io
    import numpy as np
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    declared={key:value for key,value in task.items() if key not in ('index','shard')}
    if declared!=tasks()[0]:raise ValueError('one unchanged frozen diagnosis identity required')
    load=lambda key:json.loads(context.input_path(key).read_bytes());r=recipe()
    if load('recipe')!=r or context.manifest['scope']!=SCOPE or load('qualification-environment')!=environment():
        raise ValueError('unchanged qualified saved-data scope, environment and limits required')
    report=load('pilot-report');manifest=load('pilot-manifest');query=load('query-layout')
    if (not report['verified'] or report['total']!=24 or report['expected_primaries']!=12
            or digest(context.input_path('pilot-manifest').read_bytes())!=report['manifest_sha256']
            or report['original_reads'] or report['protected_reads'] or report['native_calls_during_audit']):
        raise ValueError('verified closed development pilot required')
    limits=dict(raw_points=r['maximum_raw_points'],receiver_epochs=r['receiver_epochs'],saved_records=r['maximum_saved_records'],
        saved_error_epochs=r['maximum_saved_error_epochs'],settings=r['maximum_settings'])
    journal=Journal(context.directory/'diagnosis-work.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:limits});journal.start(task['identity'])
    try:
        def check():_check_continue(context.root,context.manifest)
        def reserve(resource):check();journal.reserve(task['identity'],resource,limits[resource])
        reserve('raw_points')
        with np.load(io.BytesIO(context.input_path('interval').read_bytes()),allow_pickle=False) as archive:
            raw={key:archive[key] for key in ('raw_time_s','temperature_c','dv','dt')}
        n=len(raw['raw_time_s'])
        if (not 2001<=n<=r['maximum_raw_points'] or n!=report['source']['raw_points']
                or raw['temperature_c'].shape!=(n,) or raw['dv'].shape!=(n-1,3) or raw['dt'].shape!=(n-1,)
                or any(not np.all(np.isfinite(value)) for value in raw.values())
                or not np.array_equal(raw['dt'],np.diff(raw['raw_time_s'])) or np.any(raw['dt']<=0)):
            raise ValueError('unchanged complete retained raw support required')
        force_reference=float(np.linalg.norm(np.sum(raw['dv'][:2000],axis=0)/np.sum(raw['dt'][:2000])))
        reserve('receiver_epochs');receiver=json.loads(gzip.decompress(context.input_path('scoring').read_bytes()))
        times=np.array([row['time_s'] for row in receiver]);height=np.array([row['height_m'] for row in receiver]);cut=r['training_epochs']
        if (len(receiver)!=r['receiver_epochs'] or query['training_epochs']!=cut or query['prediction_epochs']!=400
                or not np.array_equal(times-query['time_origin_gps_sow_s'],np.array(query['times_s']))):
            raise ValueError('exact unchanged receiver queries and boundary required')
        reference=gravity_reference(times,height,cut)
        speed=np.array([math.hypot(row['north_mps'],row['east_mps'])*3.6 for row in receiver])
        indices=np.unique(np.append(np.arange(0,n,r['temperature_display_stride']),n-1))
        data=dict(times_s=times.tolist(),height_m=height.tolist(),ground_speed_kmh=speed.tolist(),
            latitude_deg=[row['latitude_deg'] for row in receiver],
            course_deg=[math.degrees(math.atan2(row['east_mps'],row['north_mps']))%360 for row in receiver],
            temperature_time_s=raw['raw_time_s'][indices].tolist(),temperature_c=raw['temperature_c'][indices].tolist(),
            minimum_temperature_c=float(np.min(raw['temperature_c'])),maximum_temperature_c=float(np.max(raw['temperature_c'])),
            temperature_display_uses_recorded_samples=True,force_based_reference_mps2=force_reference,gravity_reference=reference)
        context.save('recorded-context.json',data)
        reserve('saved_records');reserve('saved_error_epochs')
        curves=json.loads(gzip.decompress(context.input_path('curves').read_bytes()))
        if (len(curves)>r['maximum_saved_records'] or sum(len(value['times_s']) for value in curves.values())>r['maximum_saved_error_epochs']
                or any(value['times_s']!=query['times_s'] for value in curves.values())):
            raise ValueError('complete bounded saved curves required')
        expected={(t['payload']['model'],t['payload']['profile'],t['payload']['policy_id']) for t in manifest['tasks']}
        groups=report['primaries'];keys=[(v['model'],v['profile'],v['policy_id']) for v in groups]
        if len(keys)!=r['maximum_settings'] or len(set(keys))!=len(keys) or set(keys)!=expected:
            raise ValueError('all twelve original settings must remain present')
        reserve('settings');cases=[];actual_epochs=0
        for group in groups:
            check();primary=group['primary'];spec={key:group[key] for key in ('model','profile','policy_id')}
            case=dict(spec=spec,available=primary is not None,selected_training_start=group['selected_training_start'])
            if primary is not None:
                identity=primary['identity']
                if identity not in curves:raise ValueError('selected primary lacks its unchanged saved curve')
                curve=curves[identity];summary=fixed_blocks(curve['times_s'],curve['errors_neu_m'],cut)
                actual_epochs+=summary['epochs']
                case.update(identity=identity,**summary,calibration=calibration(primary['normalized_parameters'],report['calibration_limits'],force_reference),
                    training=primary['training'],prediction=primary['prediction'],source_scores_sha256=curve['source_sha256'])
            else:case['reason']='original training-selected primary has no qualified prediction; no replacement'
            cases.append(case)
        context.save('cases.json',cases);context.save('start-sensitivity.json',report['start_sensitivity'])
        _plots(context.save_bytes,data,cases,curves,cut);journal.verify();check()
        return dict(passed=True,settings=len(cases),available_settings=sum(case['available'] for case in cases),
            raw_points=n,receiver_epochs=len(receiver),available_saved_records=len(curves),processed_primary_error_epochs=actual_epochs,
            gravity_reference=reference,force_based_initial_reference_mps2=force_reference,
            charged_work={key:journal.count(task['identity'],key) for key in limits},
            original_reads=0,protected_reads=0,native_calls=0,observed_starts=0,new_propagations=0,
            forecasts_changed=False,causation_established=False,scientific_decision='abstain')
    finally:context.note_file(journal.path)
