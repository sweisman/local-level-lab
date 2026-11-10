# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched retrospective prediction tasks using shared training and forecast code."""
import math

VERSION='ilvis0-retrospective-prediction-pilot-v1'


def recipe():
    return dict(version=VERSION,maximum_evaluations=200,starts=2,
        clocks=['header_elapsed','nominal_200Hz'],models=3,processing_cases=2,
        stopping='near_zero',maximum_interval_s=.0075,gyro_offset_dph=1.,
        training_weight='h1_v3_tau60',independent_neu_m=[.3,.3,.7],
        accuracy_limits=dict(horizontal_rms_m=10.,vertical_rms_m=30.,
            maximum_horizontal_m=50.,maximum_absolute_up_m=150.),
        workers=1,threads=4,maximum_wall_s=86400.,retries=0,
        prospective_validation=False,confidence_calibrated=False)


def tasks(layouts):
    if len(layouts)!=3 or len({v['segment_id'] for v in layouts})!=3:
        raise ValueError('exactly three distinct preselected stretches required')
    result=[];r=recipe()
    for row in layouts:
        n,nt,nq=(row[k] for k in ('native_packets','training_epochs','receiver_epochs'))
        if (any(type(v) is not int or v<=0 for v in (n,nt,nq)) or nt!=2*nq//3 or nq<9):
            raise ValueError('complete packet counts and unchanged receiver split required')
        for model in range(3):
            for profile in (False,True):
                for clock in r['clocks']:
                    for start in range(2):
                        result.append(dict(identity=f"{row['segment_id']}-{model}-{int(profile)}-{clock}-{start}",
                            input_key=row['segment_id']+'-measurements',
                            payload=dict(segment_id=row['segment_id'],model=model,profile=profile,clock=clock,start=start),
                            limits=dict(native_calls=201,packet_visits=n*(200*nt+nq),bound_calls=0,bound_steps=0)))
    return result


def accuracy_screen(prediction):
    limits=recipe()['accuracy_limits']
    values={k:prediction[k] for k in limits}
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in values.values()):
        raise ValueError('finite nonnegative prediction errors required')
    checks={k:values[k]<=bound for k,bound in limits.items()}
    return dict(passed=all(checks.values()),checks=checks,limits=limits,
        calibrated_goodness_of_fit=False,scientific_decision='abstain')


def sources(root):
    from lll.studies.dependencies import source_closure
    # The value loader names a .c file dynamically; Python import traversal
    # alone does not discover it. Declare both compiled entry points explicitly.
    return source_closure(root,['analysis/lll/ilvis0_prediction_observed.py',
        'analysis/lll/ilvis0_prediction_pilot.py','analysis/tests/test_ilvis0_prediction_observed.py',
        'analysis/tests/test_ilvis0_prediction_pilot.py','docs/ilvis0-prediction-pilot-preparation/PLAN.md',
        'docs/ilvis0-prediction-pilot-preparation/LOADER_REPAIR.md',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp'])


def prepare(root,*,software_report,identity='ilvis0-retrospective-prediction-pilot-20261023',prepared_from=None):
    """Check qualification before decoding the three exact saved selections.

    No fit runs here. Converted/raw inputs are shared by tasks; later positions
    have a separate scoring artifact which the evaluator opens after forecasting.
    """
    import csv
    import gzip
    import io
    import json
    import xml.etree.ElementTree as ET
    from pathlib import Path
    from lll.studies.artifacts import ArchiveStore,atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.runtime import Definition
    from lll.ilvis0_forecast_report import inspect
    root=Path(root).resolve()
    parent='docs/ilvis0-near-zero-forecast-controls'
    qualified=ClosedStudy(root,parent)
    try:
        for name,sha in qualified.manifest['sources'].items():
            if digest(safe_path(root,name).read_bytes())!=sha:raise ValueError('qualified forecast source changed')
        if qualified.input('recipe').get('stopping')!='near_zero':raise ValueError('qualified stopping composition required')
        gate=inspect(root,parent)
        if not gate['complete']:raise ValueError('all 24 complete prediction controls must qualify')
    finally:qualified.close()
    # Parse software evidence before numerical imports or any original read.
    report=safe_path(root,software_report).read_bytes();tree=ET.fromstring(report)
    required=('test_fixed_pilot_has_all_models_processing_clocks_and_starts',
        'test_accuracy_screen_requires_height_and_does_not_claim_calibration',
        'test_preparation_cannot_read_originals_before_complete_qualification',
        'test_exact_split_uses_receiver_times_without_model_or_gyro_outcomes',
        'test_evaluator_saves_forecast_before_opening_later_positions',
        'test_source_freeze_includes_both_native_translation_units',
        'test_frozen_loader_compiles_without_access_to_live_library')
    names=[v.attrib['name'] for v in tree.iter('testcase')]
    if (not all(n in names for n in required) or any(list(v) for v in tree.iter('testcase'))
            or any(int(s.attrib.get(k,0)) for s in tree.iter('testsuite') for k in ('errors','failures','skipped'))):
        raise ValueError('complete passing pilot software checks required')
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh observed study identity required')
    frozen_sources=sources(root)
    if prepared_from is not None:
        parent=ClosedStudy(root,prepared_from)
        try:
            if (parent.summary['completed']!=72 or parent.summary['charged']['native_calls']!=0
                    or parent.input('recipe')!=recipe()
                    or any(parent.envelope(i)['result'].get('error_type')!='FileNotFoundError' for i in parent.tasks)):
                raise ValueError('unchanged zero-native loader failure required for prepared-input reuse')
            copies={k:parent.input(k,raw=True) for k in parent.manifest['inputs']}
            layouts=json.loads(copies['layouts.json'])
        finally:parent.close()
        base.mkdir(parents=True);inputs={}
        copies['software-report.xml']=report
        copies['qualification.json']=encoded(gate)
        copies['loader-parent.json']=encoded(dict(prefix=prepared_from,charged_identities=72,
            native_calls=0,originals_reread=0,prior_allowance_reused=False))
        for index,(key,raw) in enumerate(copies.items()):
            name=f'input-{index:03d}';atomic(base/name,raw);inputs[key]=str((base/name).relative_to(root))
        r=recipe();definition=dict(id=identity,adapter='analysis/lll/ilvis0_prediction_observed.py',
            sources=frozen_sources,inputs=inputs,tasks=tasks(layouts),workers=r['workers'],threads=r['threads'],
            maximum_wall_s=r['maximum_wall_s'])
        atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,identities=72,allocation=manifest['allocation'],limits=manifest['limits'],originals_reread=0)
    store=ArchiveStore(root)
    try:
        selection_name='docs/ilvis0-prediction-pilot-preparation/selection.csv'
        receipt_name='docs/ilvis0-prediction-pilot-preparation/split-receipt.json'
        selection=store.read(selection_name);receipt=store.read(receipt_name);split=json.loads(receipt)
        if digest(selection)!=split['input_sha256'][selection_name]:raise ValueError('unchanged selected inventory required')
        population_name='data/ilvis0-highspeed-segments-v2-20261008/selection.json.gz'
        context_name='data/ilvis0-followup-20261007/summary.json'
        population_raw=store.read(population_name);context_raw=store.read(context_name)
        if any(digest(raw)!=split['input_sha256'][name] for raw,name in ((population_raw,population_name),(context_raw,context_name))):
            raise ValueError('original saved selection or timing context differs')
        population=json.loads(gzip.decompress(population_raw))
        chosen={v['segment']['segment_id']:v for v in population['selected']}
        contexts={v['task_id']:v for v in json.loads(context_raw)['results']}
        rows=list(csv.DictReader(io.StringIO(selection.decode())))
    finally:store.close()
    from lll.ilvis0_segments import extract_segment
    from lll.ilvis0_prediction_layout import prediction_layout
    from lll.ilvis0_prediction import split as numerical_split
    base.mkdir(parents=True);inputs={};layouts=[]
    for name,raw in [('recipe.json',encoded(recipe())),('software-report.xml',report),
                     ('qualification.json',encoded(gate)),('selection.csv',selection),('split-receipt.json',receipt)]:
        atomic(base/name,raw);inputs['recipe' if name=='recipe.json' else name]=str((base/name).relative_to(root))
    for row in rows:
        sid=row['segment_id'];source=chosen[sid];context=contexts[source['task']]
        layout=prediction_layout(row,source,context)
        if layout!=next(v for v in split['layouts'] if v['segment_id']==sid):raise ValueError('preselected split differs')
        original=Path(source['source_path'])
        relative=original.relative_to(root)
        if relative.parts[:2]!=('data','ilvis0-ready'):raise ValueError('documented retained original required')
        original=safe_path(root,relative.as_posix())
        values,times,gps,provenance=extract_segment(original,context,source['segment'])
        actual=numerical_split(times);cut=layout['training_epochs']
        if (actual['training_epochs']!=cut or actual['prediction_epochs']!=layout['prediction_epochs']
                or provenance['source_sha256']!=row['source_sha256']):raise ValueError('decoded selection differs')
        layout=dict(layout,native_packets=len(values),first_interval_start_utc_s=provenance['first_interval_start_utc_s'])
        layouts.append(layout)
        material=dict(segment_id=sid,layout=layout,values=values.tolist(),times=times.tolist(),training_gps=gps[:cut].tolist())
        name=sid+'-measurements.json.gz';atomic(base/name,gzip.compress(encoded(material),mtime=0))
        inputs[sid+'-measurements']=str((base/name).relative_to(root))
        name=sid+'-scoring.json';atomic(base/name,encoded(dict(segment_id=sid,prediction_gps=gps[cut:].tolist())))
        inputs[sid+'-scoring']=str((base/name).relative_to(root))
        name=sid+'-provenance.json';atomic(base/name,encoded(provenance));inputs[sid+'-provenance']=str((base/name).relative_to(root))
    name='layouts.json';atomic(base/name,encoded(layouts));inputs[name]=str((base/name).relative_to(root))
    r=recipe();definition=dict(id=identity,adapter='analysis/lll/ilvis0_prediction_observed.py',sources=frozen_sources,
        inputs=inputs,tasks=tasks(layouts),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=len(definition['tasks']),allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    import gzip
    import json
    import numpy as np
    from lll.ilvis0_exploratory import MODELS,load_kernel
    from lll.ilvis0_shape import instrument_limits,load_tangent
    from lll.ilvis0_prediction import training_inputs
    from lll.ilvis0_training_forecast import training_problem,fit_training
    from lll.ilvis0_forecast import native_forecast
    from lll.ilvis0_gps_sensitivity import assumptions,coordinate_covariance
    from lll.ilvis0_saved_prediction import summarize
    from lll.ilvis0_residuals import autocorrelation
    spec=task['payload'];r=recipe()
    if json.loads(context.input_path('recipe').read_bytes())!=r:raise ValueError('frozen pilot recipe differs')
    material=json.loads(gzip.decompress(context.input_path().read_bytes()))
    if material['segment_id']!=spec['segment_id']:raise ValueError('measurement identity differs')
    values=np.asarray(material['values'],float);times=np.asarray(material['times'],float)
    training_gps=np.asarray(material['training_gps'],float);layout=material['layout'];cut=layout['training_epochs']
    if len(training_gps)!=cut or len(times)!=layout['receiver_epochs'] or len(values)!=layout['native_packets']:
        raise ValueError('complete frozen training-only observations required')
    # The input holds no later receiver positions. Only a shape placeholder is
    # passed to the shared prefix selector, which returns the training block.
    placeholder=np.zeros((len(times),3));placeholder[:cut]=training_gps
    clock_values=values.copy()
    if spec['clock']=='nominal_200Hz':clock_values[:,2]=.005
    limits=instrument_limits(r['gyro_offset_dph'])
    t,g,v=training_inputs(times,placeholder,clock_values,limits['time_offset'])
    if not np.array_equal(g,training_gps):raise ValueError('training-only position boundary differs')
    assumption=next(a for a in assumptions() if a.name==r['training_weight'])
    blocks=np.tile(np.diag(np.square(r['independent_neu_m'])),(len(t),1,1))
    covariance=coordinate_covariance(t,g[:,0],g[:,2],blocks,assumption)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel,kmeta=load_kernel(directory);tangent,tmeta=load_tangent(directory)
    for filename,meta in [('ilvis0_native.c',kmeta),('ilvis0_tangent.cpp',tmeta)]:
        if context.manifest['sources']['analysis/lll/'+filename]!=meta['source_sha256']:
            raise ValueError('compiled native source differs from freeze')
    context.save('compilation.json',dict(value=kmeta,tangent=tmeta))
    model=MODELS[spec['model']]
    problem=training_problem(t,g,theta=v[:,9:12],dv=v[:,12:15],dt=v[:,2],covariance=covariance,
        model=model,limits=limits,profile=spec['profile'],clock=spec['clock'],
        maximum_interval_s=r['maximum_interval_s'],kernel=kernel,tangent_kernel=tangent)
    n=len(problem.bounds.active);start=np.zeros(n) if spec['start']==0 else np.where(np.arange(n)%2,-.001,.001)
    fit=fit_training(problem,model,start=start,maximum_evaluations=r['maximum_evaluations'],
        reserve=context.charge,stopping=r['stopping'])
    context.save('fit.json',fit)
    forecast=native_forecast(problem,fit['normalized_parameters'],model,theta=values[:,9:12],dv=values[:,12:15],
        dt=clock_values[:,2],times=times,maximum_interval_s=r['maximum_interval_s'],reserve=context.charge)
    context.save('forecast.json',dict(coordinates=forecast['coordinates'].tolist(),times=times.tolist(),
        active_parameters=forecast['active_parameters'],training_epochs=cut,
        continuous_propagation_without_gps_reset=True,prediction_receiver_positions_used=False))
    # Open scoring positions only after the continuous forecast is saved.
    truth=json.loads(context.input_path(spec['segment_id']+'-scoring').read_bytes())
    if truth['segment_id']!=spec['segment_id']:raise ValueError('scoring identity differs')
    later=np.asarray(truth['prediction_gps'],float)
    if later.shape!=(len(times)-cut,3):raise ValueError('complete later scoring positions required')
    gps=np.concatenate((training_gps,later))
    metric=np.column_stack((6378137.+gps[:,2],(6378137.+gps[:,2])*np.cos(gps[:,0]),np.ones(len(times))))
    errors=(forecast['coordinates']-gps)*metric
    rows=[dict(epoch=i,time_s=float(time),role='training' if i<cut else 'prediction',
        **{axis+'_direct_error_m':float(errors[i,j]) for j,axis in enumerate(('north','east','up'))})
        for i,time in enumerate(times)]
    report=summarize(rows,training_epochs=cut,prediction_epochs=len(times)-cut)
    for name,section in [('training',slice(0,cut)),('prediction',slice(cut,None))]:
        e=errors[section];rms=np.sqrt(np.mean(e*e,axis=0))
        report[name].update(rms_neu_m=rms.tolist(),total_rms_m=float(np.linalg.norm(rms)),
            autocorrelation=[dict(lag_epochs=lag,neu=[autocorrelation(e[:,j],lag) for j in range(3)])
                for lag in (1,5,10,30,60) if lag<len(e)])
    context.save('epochs.json',rows);context.save('scores.json',report)
    active_ok=len(forecast['active_parameters'])==26+int(spec['profile'])
    return dict(passed=bool(fit['converged'] and active_ok),segment_id=spec['segment_id'],
        model=model,profile=spec['profile'],clock=spec['clock'],start=spec['start'],
        converged=fit['converged'],training_cost=fit['residual_sum_squares'],evaluations=fit['evaluations'],
        active_columns=len(forecast['active_parameters']),all_active_columns_retained=active_ok,
        training=report['training'],prediction=report['prediction'],
        accuracy_screen=accuracy_screen(report['prediction']),confidence_calibrated=False,
        scientific_decision='abstain')
