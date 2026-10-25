# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent generated controls for the common ESA weighted fitting path."""
from lll.airquantumgrav_inventory import environment

SCOPE='generated weighted training/forecast controls only; no observed or protected source reads'


def recipe():
    from lll.airquantumgrav_training_controls import recipe as previous
    return dict(previous(),version='esa-weighted-training-controls-v1',
        policies=['reported-short-v1','reported-persistent-v1'],workers=4,threads=1,protected_reads=0)


def tasks():
    from lll.airquantumgrav_training_controls import tasks as previous
    result=[]
    for task in previous():
        for policy in recipe()['policies']:
            result.append(dict(task,identity=task['identity']+'-'+policy,
                payload=dict(task['payload'],policy_id=policy)))
    return result


def fixture_rows(coordinates,times):
    import math
    return [dict(time_s=float(t),gps_week=2269,latitude_deg=math.degrees(c[0]),longitude_deg=math.degrees(c[1]),
        height_m=float(c[2]),position_variance_m2=[.04,.09,.25],position_cross_covariance_m2=[.01,.02,-.015])
        for c,t in zip(coordinates,times,strict=True)]


def calculate(spec,r,*,kernel,tangent,reserve,reserve_construction,save,save_bytes,check_continue):
    import io
    import numpy as np
    from lll.airquantumgrav_training_controls import generated_training,_spec
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.airquantumgrav_geographic_controls import position_errors,metrics
    base={k:v for k,v in spec.items() if k!='policy_id'};arguments,sign=_spec(base)
    if set(spec)!=set(base)|{'policy_id'} or spec['policy_id'] not in recipe()['policies']:
        raise ValueError('one declared weighted generated identity required')
    check_continue();material=generated_training(base,r,reserve=reserve_construction)
    buffer=io.BytesIO();np.savez_compressed(buffer,**{k:v for k,v in material.items() if k not in ('training_gps','training_epochs')})
    save_bytes('raw-inputs.npz',buffer.getvalue());times=material['times'];cut=material['training_epochs']
    training=fixture_rows(material['training_gps'],times[:cut])
    result=train_and_forecast(**{k:material[k] for k in ('theta','dv','dt')},times=times,
        training_rows=training,time_origin_s=0.,model=spec['model'],profile=spec['profile'],
        policy_id=spec['policy_id'],start=spec['start'],limits=r['limits'],maximum_evaluations=r['maximum_evaluations'],
        maximum_interval_s=1.5/r['rate_hz'],kernel=kernel,tangent_kernel=tangent,reserve=reserve,
        save=save,check_continue=check_continue)
    # The shared pipeline has saved the continuous forecast before this call.
    check_continue();reserve_construction(generated_samples=len(times));answer=receiver_samples(times=times,sign=sign,**arguments)
    if not np.array_equal(answer['coordinates'][:cut],material['training_gps']):
        raise ValueError('earlier independent scoring positions differ')
    save('scoring-observations.json',{k:v.tolist() for k,v in answer.items()})
    errors=position_errors(result['forecast']['coordinates'],answer,model=spec['model'])
    sections={name:metrics(errors[section]) for name,section in [('training',slice(0,cut)),('prediction',slice(cut,None))]}
    save('scores.json',dict(times_s=times.tolist(),errors_neu_m=errors.tolist(),**sections,training_positions_reproduced_for_scoring=True))
    fit=result['fit'];accuracy={name:{k:v[k]<=limit for k,limit in r['accuracy'].items()} for name,v in sections.items()}
    passed=fit['converged'] and result['all_columns_retained'] and all(v for values in accuracy.values() for v in values.values())
    return dict(passed=bool(passed),**spec,converged=fit['converged'],evaluations=fit['evaluations'],native_calls=fit['evaluations']+1,
        training_cost=fit['residual_sum_squares'],training_epochs=cut,prediction_epochs=len(times)-cut,**sections,accuracy=accuracy,
        all_columns_retained=result['all_columns_retained'],true_initial_state_supplied=False,true_calibration_supplied=False,
        forecast_saved_before_scoring=True,weight_configuration=result['weight_configuration'],
        constructed_intervals=len(material['dt']),generated_samples=len(material['dt'])+1+cut+len(times),
        original_reads=0,observed_starts=0,protected_reads=0,confidence_calibrated=False,scientific_decision='abstain')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_weighted_controls.py',
        'analysis/tests/test_airquantumgrav_weighted_controls.py','analysis/tests/test_airquantumgrav_prediction.py',
        'analysis/tests/test_airquantumgrav_error_policy.py','analysis/tests/test_airquantumgrav_training_controls.py',
        'analysis/tests/test_ilvis0_training_forecast.py','analysis/tests/test_study_binary_artifacts.py',
        'analysis/tests/test_ilvis0_control_shards.py','analysis/lll/studies/qualification.py',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','docs/esa-weighted-training-controls/PLAN.md'])


def required_tests():
    from lll.airquantumgrav_error_policy import required_tests as weight_tests
    return weight_tests()+['test_weighted_matrix_preserves_all_48_identities_and_separate_allowance',
        'test_weighted_fixture_is_independent_of_model_residuals',
        'test_weighted_control_preparation_rejects_absent_qualification_before_files',
        'test_weighted_prediction_interface_has_no_later_receiver_input']+[
        f'test_later_scoring_cannot_change_weighted_fit_or_saved_forecast[{p}]' for p in recipe()['policies']]+[
        f'test_weighted_prediction_uses_only_earlier_rows_and_preserves_all_columns[{profile}-{policy}]'
        for profile in (False,True) for policy in recipe()['policies']]+[
        f'test_weighted_prediction_rejects_unsupported_inputs_before_native_work[{v}]'
        for v in ('start','time','rows','cap','profile')]


def prepare(root,*,qualification,identity='esa-weighted-training-controls-20261023'):
    import re
    from pathlib import Path
    from lll.airquantumgrav_training_controls import qualified_parents
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if qualification is None:raise ValueError('passing source-bound weighted pipeline qualification required')
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('safe fresh qualification identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh weighted-control scope required')
    sources=qualification_sources(root);env=environment()
    request,report=checked(root,qualification,sources=sources,environment=env,required_tests=required_tests(),minimum_tests=len(required_tests()))
    parents=qualified_parents(root);parent=ClosedStudy(root,'docs/esa-training-forecast-controls')
    try:
        if not parent.summary['passed'] or parent.summary['completed']!=24:raise ValueError('complete preceding training qualification required')
        parents['training']=dict(manifest_sha256=parent.completion['manifest_sha256'],summary_sha256=parent.completion['summary_sha256'])
    finally:parent.close()
    base.mkdir(parents=True);inputs={};r=recipe()
    for key,name,raw in [('recipe','recipe.json',encoded(r)),('qualification-request','qualification-request.json',request),
        ('qualification-report','qualification-report.xml',report),('qualification-environment','qualification-environment.json',encoded(env)),
        ('qualified-parents','qualified-parents.json',encoded(parents))]:
        atomic(base/name,raw);inputs[key]=str((base/name).relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_weighted_controls.py',sources=sources,
        inputs=inputs,tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,total=len(tasks()),limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import json
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    r=recipe();declared={k:v for k,v in task.items() if k not in ('index','shard')};canonical={v['identity']:v for v in tasks()}
    if (canonical.get(task.get('identity'))!=declared or json.loads(context.input_path().read_bytes())!=r
            or context.manifest['scope']!=SCOPE or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()):
        raise ValueError('unchanged qualified generated scope, environment and finite task required')
    n=round(r['duration_s']*r['rate_hz']);counts=dict(constructed_intervals=n,generated_samples=n+1+2*r['queries']//3+r['queries'])
    journal=Journal(context.directory/'construction.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:counts});journal.start(task['identity'])
    try:
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';kernel,km=load_kernel(directory);tangent,tm=load_tangent(directory)
        for filename,meta in [('ilvis0_native.c',km),('ilvis0_tangent.cpp',tm)]:
            if meta['source_sha256']!=context.manifest['sources']['analysis/lll/'+filename]:raise ValueError('native source differs')
        context.save('compilation.json',dict(value=km,tangent=tm))
        def reserve(**values):
            for key,value in values.items():journal.reserve(task['identity'],key,value)
        result=calculate(task['payload'],r,kernel=kernel,tangent=tangent,reserve=context.charge,reserve_construction=reserve,
            save=context.save,save_bytes=context.save_bytes,check_continue=lambda:_check_continue(context.root,context.manifest))
        journal.verify()
        if any(journal.count(task['identity'],k)!=v for k,v in counts.items()):raise ValueError('complete construction charges differ')
        return result
    finally:context.note_file(journal.path)
