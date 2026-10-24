# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen one-pass preparation of a reusable ESA development interval."""
from lll.airquantumgrav_inventory import IMU_NAME,RECEIVER_NAME,RECEIVER_PATH,METADATA,environment,validate_context

IMU_PATH='data/external-imu-survey-20261018/esa-sample/'+IMU_NAME
SCOPE='observed ESA development interval preparation only; no model fitting or protected reads'


def recipe():
    return dict(version='esa-development-pilot-preparation-v1',workers=1,threads=1,maximum_wall_s=1200.,
        receiver_passes=1,imu_passes=1,maximum_receiver_records=100000,maximum_imu_records=10000000,
        receiver_decoder_block=1024,imu_decoder_block=65536,maximum_retained_points=360100,
        maximum_constructed_intervals=360099,working_error_descriptions=2,support_padding_s=.05,
        maximum_latency_s=.01,rate_hz=300,sampling_hypothesis='linear_points',observed_starts=0,
        native_calls=0,protected_reads=0,retries=0)


def tasks():
    return [dict(identity='prepare-earliest-187-v2',input_key='references',payload=dict(recording='187'),
        native_kind='value',limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))]


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_pilot_preparation.py',
        'analysis/tests/test_airquantumgrav_pilot_preparation.py','analysis/tests/test_airquantumgrav_pilot_data.py',
        'analysis/tests/test_study_streams.py','analysis/tests/test_airquantumgrav.py',
        'analysis/tests/test_airquantumgrav_receiver.py','analysis/tests/test_airquantumgrav_increments.py',
        'analysis/tests/test_airquantumgrav_error_policy.py','analysis/tests/test_airquantumgrav_inventory.py',
        'analysis/tests/test_study_scope.py','analysis/lll/studies/qualification.py',
        'docs/esa-development-pilot/PLAN.md','docs/esa-development-pilot-preparation/PLAN.md'])


def required_tests():
    from lll.airquantumgrav_error_policy import required_tests as weights
    return weights()+['test_pilot_preparation_has_separate_finite_no_fit_allowance',
        'test_pilot_preparation_requires_source_bound_qualification_before_writes',
        'test_pilot_preparation_rejects_changed_task_before_reading_any_source',
        'test_bounded_stream_charges_before_decode_and_checks_complete_bytes',
        'test_bounded_stream_cannot_silently_accept_an_early_stopping_decoder',
        'test_first_interval_layout_is_chronological_fixed_and_training_only',
        'test_imu_window_preserves_original_samples_and_brackets_timing_allowance',
        'test_existing_imu_decoder_stream_and_interval_constructor_preserve_units',
        'test_explicit_receiver_inventory_scope_is_frozen_and_authorized']+[
        f'test_bounded_stream_rejects_changed_incomplete_or_unbounded_sources[{x}]' for x in ('hash','bytes','excess','text','cap','block')]+[
        f'test_pilot_receiver_layout_rejects_unsupported_selection_without_repair[{x}]'
        for x in ('empty','version','short','gap','sequence','week','reordered','nonfinite')]+[
        f'test_imu_window_fails_instead_of_repairing_or_trimming[{x}]' for x in ('gap','capacity','left','right')]


def prepare(root,*,qualification,identity='esa-development-pilot-preparation-20261023'):
    import json
    import re
    from pathlib import Path
    from lll.airquantumgrav_pilot_data import choose
    from lll.airquantumgrav_inventory_report import inspect
    from lll.studies.artifacts import ArchiveStore,atomic,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if qualification is None:raise ValueError('source-bound preparation qualification required')
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('safe fresh preparation identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh preparation scope required')
    sources=qualification_sources(root);env=environment()
    request,report=checked(root,qualification,sources=sources,environment=env,
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    store=ArchiveStore(root)
    try:raw={key:store.read(name) for key,name in METADATA.items()}
    finally:store.close()
    values={k:json.loads(v) for k,v in raw.items()};binding=validate_context(**values);r=recipe()
    if values['inspection']['records']>r['maximum_imu_records']:raise ValueError('established IMU count exceeds finite scope')
    parent=ClosedStudy(root,'docs/esa-development-selection-v2')
    try:
        proof=inspect(root,'docs/esa-development-selection-v2')
        if not proof['verified'] or parent.input('context')!=binding:raise ValueError('matching verified inventory required')
        import gzip
        selected=json.loads(gzip.decompress(parent.artifact('receiver-inventory-187-v2','selection.json.gz',raw=True)))
        chosen=choose(selected);receiver_reference=parent.input('source-reference')
    finally:parent.close()
    imu=safe_path(root,IMU_PATH);receiver=safe_path(root,RECEIVER_PATH)
    if imu.stat().st_size!=values['inspection']['byte_size'] or receiver.stat().st_size!=receiver_reference['size_bytes']:
        raise ValueError('original source size changed before preparation')
    references=dict(imu=dict(path=IMU_PATH,filename=IMU_NAME,sha256=binding['imu_source_sha256'],
        size_bytes=values['inspection']['byte_size'],records=values['inspection']['records']),
        receiver=dict(receiver_reference,records=binding['expected_receiver_epochs']))
    base.mkdir(parents=True);inputs={}
    materials=[(key,key+'.json',value) for key,value in raw.items()]
    materials += [(key,key+'.json',encoded(value)) for key,value in
        [('references',references),('context',binding),('selection',selected),('chosen',chosen),('recipe',r),
         ('qualified-inventory',proof),('qualification-environment',env)]]
    materials += [('qualification-request','qualification-request.json',request),('qualification-report','qualification-report.xml',report)]
    for key,name,payload in materials:
        atomic(base/name,payload);inputs[key]=str((base/name).relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_pilot_preparation.py',
        sources=sources,inputs=inputs,tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,scope=manifest['scope'],limits=r,chosen=chosen)


def evaluate(task,context):
    import gzip
    import io
    import json
    import numpy as np
    from lll.airquantumgrav import records as imu_records
    from lll.airquantumgrav_receiver import records as receiver_records
    from lll.airquantumgrav_pilot_data import choose,receiver_layout,RawWindow
    from lll.airquantumgrav_geographic_controls import construct
    from lll.airquantumgrav_error_policy import build,policies
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest,encoded,safe_path
    from lll.studies.streams import consume
    from lll.studies.journal import Journal
    if {k:v for k,v in task.items() if k not in ('index','shard')}!=tasks()[0]:
        raise ValueError('one unchanged frozen preparation identity required')
    load=lambda key:json.loads(context.input_path(key).read_bytes())
    r=recipe()
    if load('recipe')!=r or context.manifest['scope']!=SCOPE or load('qualification-environment')!=environment():
        raise ValueError('qualified unchanged preparation scope and environment required')
    values={key:load(key) for key in METADATA};binding=validate_context(**values)
    chosen=choose(load('selection'));references=load('references')
    if binding!=load('context') or chosen!=load('chosen') or context.root.parent.name!='data':
        raise ValueError('unchanged explicit development interval required')
    for label,path,name,sha,count in [('imu',IMU_PATH,IMU_NAME,binding['imu_source_sha256'],values['inspection']['records']),
        ('receiver',RECEIVER_PATH,RECEIVER_NAME,binding['receiver_sha256'],binding['expected_receiver_epochs'])]:
        ref=references[label]
        if (ref['path']!=path or ref['filename']!=name or ref['sha256']!=sha or ref['records']!=count
                or type(count) is not int or not 0<count<=r['maximum_'+label+'_records']):
            raise ValueError('established original development source reference required')
    limits=dict(receiver_passes=1,imu_passes=1,receiver_decoder_calls=r['maximum_receiver_records']+1,
        imu_decoder_calls=r['maximum_imu_records']+1,retained_points=r['maximum_retained_points'],
        constructed_intervals=r['maximum_constructed_intervals'],working_error_descriptions=r['working_error_descriptions'])
    journal=Journal(context.directory/'preparation-work.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:limits});journal.start(task['identity'])
    try:
        def reserve(**counts):
            for key,value in counts.items():journal.reserve(task['identity'],key,value)
        check=lambda:_check_continue(context.root,context.manifest)
        def original(label):
            path=safe_path(context.root.parent.parent,references[label]['path'])
            if path.stat().st_size!=references[label]['size_bytes']:raise ValueError('frozen original byte size differs')
            return path
        stats={};rows=[];index=0
        def receiver_row(row):
            nonlocal index
            if chosen['first_index']<=index<=chosen['last_index']:rows.append(row)
            index+=1
        def read(label,decoder,accept):
            ref=references[label];path=original(label);reserve(**{label+'_passes':1})
            with path.open('rb') as stream:
                result=consume(stream,decoder=decoder,expected_sha256=ref['sha256'],expected_bytes=ref['size_bytes'],
                    maximum_records=r['maximum_'+label+'_records'],block_size=r[label+'_decoder_block'],
                    reserve=lambda amount:reserve(**{label+'_decoder_calls':amount}),check_continue=check,accept=accept)
            if result['records']!=ref['records']:raise ValueError('complete original record count differs')
            stats[label]=result
        read('receiver',receiver_records,receiver_row);layout=receiver_layout(rows,chosen)
        reserve(retained_points=r['maximum_retained_points'])
        window=RawWindow(layout['first_time_s']-r['support_padding_s'],layout['last_time_s']+r['support_padding_s'],
            maximum_points=r['maximum_retained_points'])
        read('imu',imu_records,window.accept);raw=window.finish();check()
        material=construct(dict(times=raw['raw_time_s'],angular_rate_rads=raw['angular_rate_rads'],
            specific_force_mps2=raw['acceleration_mps2']),method=r['sampling_hypothesis'],rate_hz=r['rate_hz'],reserve=reserve)
        origin=float(raw['raw_time_s'][0]);query=np.array([row['time_s']-origin for row in layout['scoring_rows']])
        if query[0]-r['maximum_latency_s']<0 or query[-1]+r['maximum_latency_s']>np.sum(material['dt']):
            raise ValueError('constructed support must contain complete latency allowance')
        buffer=io.BytesIO();np.savez_compressed(buffer,**raw,**{k:material[k] for k in ('theta','dv','dt')})
        context.save_bytes('interval.npz',buffer.getvalue());check()
        for name,key in [('training-receiver.json.gz','training_rows'),('scoring-receiver.json.gz','scoring_rows')]:
            context.save_bytes(name,gzip.compress(encoded(layout[key]),mtime=0))
        context.save('query-layout.json',dict(**{k:v for k,v in layout.items() if k not in ('training_rows','scoring_rows')},
            times_s=query.tolist(),time_origin_gps_sow_s=origin,sampling_hypothesis=r['sampling_hypothesis'],
            constructed_not_logged_increments=True,maximum_interval_s=1.5/r['rate_hz'],maximum_latency_s=r['maximum_latency_s']))
        weights={}
        for name in policies():
            check();reserve(working_error_descriptions=1);weight=build(layout['training_rows'],policy_id=name)
            weights[name]=dict(descriptor=weight.descriptor,configuration=weight.configuration,training_source_sha256=weight.source_sha256)
        context.save('working-errors.json',weights);context.save('source-validation.json',dict(sources=stats,references=references,
            group_id=binding['group_id'],selection=chosen,raw_points=len(raw['raw_time_s']),
            intervals=len(material['dt']),first_raw_time_s=float(raw['raw_time_s'][0]),last_raw_time_s=float(raw['raw_time_s'][-1])))
        journal.verify();check()
        return dict(passed=True,group_id=binding['group_id'],chosen=chosen,training_epochs=layout['training_epochs'],
            prediction_epochs=layout['prediction_epochs'],query_epochs=len(query),raw_points=len(raw['raw_time_s']),
            constructed_intervals=len(material['dt']),duration_s=layout['duration_s'],working_error_cases=list(weights),
            charged_work={key:journal.count(task['identity'],key) for key in limits},sources=stats,
            observed_starts=0,native_calls=0,protected_reads=0,scientific_decision='abstain')
    finally:context.note_file(journal.path)
