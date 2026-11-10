# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded receiver-only ESA development inventory using the shared lifecycle."""
import math
import re

IMU_NAME='187_rqh01.txt'
RECEIVER_NAME='187_air1_ppp_2Hz_final.txt'
RECEIVER_PATH='data/external-imu-survey-20261018/esa-sample/'+RECEIVER_NAME
SCOPE='receiver-only development inventory; no raw IMU reads or model fitting'
METADATA=dict(groups='docs/analysis-provenance/ledger.json',
    reservation='docs/external-imu-data/ESA_CONFIRMATION_POLICY.json',
    inspection='data/external-imu-survey-20261018/esa-sample/inspection.json',
    receipt='data/external-imu-survey-20261018/esa-sample/download-completion.json',
    receiver_report='docs/external-imu-data/esa-gnss-report.json')


def recipe():
    return dict(version='esa-full-motion-development-inventory-v2',maximum_receiver_epochs=100000,
        maximum_decoder_calls=100001,decoder_block_size=1024,maximum_receiver_file_passes=1,
        maximum_selection_passes=1,workers=1,threads=1,maximum_wall_s=300.,
        raw_imu_reads=0,observed_optimizer_starts=0,protected_reads=0,native_calls=0,retries=0)


def tasks():
    return [dict(identity='receiver-inventory-187-v2',input_key='source-reference',payload=dict(recording='187'),
        native_kind='value',limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))]


def environment():
    import os
    from lll.airquantumgrav_geographic_controls import environment as base
    from lll.compute_budget import THREAD_KEYS
    keys=(*THREAD_KEYS,'OMP_THREAD_LIMIT','OMP_MAX_ACTIVE_LEVELS')
    return dict(base(),numerical_environment={k:os.environ.get(k) for k in keys})


def validate_context(*,groups,reservation,inspection,receipt,receiver_report):
    from lll.evidence_groups import require_development
    matches=[g for g in groups['groups'] if 'esa:'+IMU_NAME in g['record_ids']]
    if (len(matches)!=1 or matches[0]['role']!='development'
            or IMU_NAME not in reservation['development_files'] or IMU_NAME in reservation['confirmation_files']):
        raise ValueError('explicit unique recording-187 development membership required')
    group=matches[0]['group_id'];require_development(groups,[group])
    if (inspection['source_file']!=IMU_NAME or inspection['source_sha256']!=receipt['sha256']
            or inspection['byte_size']!=receipt['size_bytes'] or inspection['byte_size']<=0
            or inspection['records']<=0 or inspection['gaps_above_1p5_nominal_periods']!=0):
        raise ValueError('matching complete IMU acquisition and uninterrupted inspection required')
    first,last=inspection['first_gps_sow_s'],inspection['last_gps_sow_s']
    if not all(math.isfinite(v) for v in (first,last)) or not 0<=first<last<604800:
        raise ValueError('finite ordered single-week IMU support required')
    if (receiver_report['source_file']!=RECEIVER_NAME or type(receiver_report['epochs']) is not int
            or not 2<=receiver_report['epochs']<=recipe()['maximum_receiver_epochs']
            or any(not isinstance(v,str) or not re.fullmatch('[0-9a-f]{64}',v)
                for v in (inspection['source_sha256'],receiver_report['sha256']))):
        raise ValueError('established receiver identity and bounded complete epoch count required')
    return dict(group_id=group,imu_support_s=[first,last],imu_source_sha256=inspection['source_sha256'],
        receiver_sha256=receiver_report['sha256'],expected_receiver_epochs=receiver_report['epochs'])


def decode(lines,*,expected_sha256,maximum_epochs,block_size,reserve,check_continue):
    import hashlib
    from lll.airquantumgrav_receiver import records
    if (not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_sha256)
            or type(maximum_epochs) is not int or not 1<=maximum_epochs<=100000
            or type(block_size) is not int or not 1<=block_size<=1024):
        raise ValueError('known complete-source hash and finite decoder allowance required')
    digest=hashlib.sha256();byte_count=0
    def hashed():
        nonlocal byte_count
        for line in lines:
            if not isinstance(line,bytes):raise ValueError('binary original receiver stream required')
            digest.update(line);byte_count+=len(line);yield line
    iterator=iter(records(hashed()));rows=[];reserved=0;calls=0
    while reserved<maximum_epochs+1:
        check_continue();slots=min(block_size,maximum_epochs+1-reserved)
        reserve(decoder_calls=slots);reserved+=slots
        for _ in range(slots):
            calls+=1
            try:row=next(iterator)
            except StopIteration:
                if digest.hexdigest()!=expected_sha256:raise ValueError('complete original receiver hash differs')
                return dict(rows=rows,decoder_calls=calls,reserved_decoder_calls=reserved,
                    source_sha256=digest.hexdigest(),source_bytes=byte_count)
            if len(rows)>=maximum_epochs:raise ValueError('receiver epoch allowance exceeded; source is not truncated')
            rows.append(row)
    raise ValueError('decoder allowance exhausted without complete source')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_inventory.py',
        'analysis/tests/test_airquantumgrav_inventory.py','analysis/tests/test_airquantumgrav_selection_v2.py',
        'analysis/tests/test_airquantumgrav_selection.py','analysis/tests/test_airquantumgrav_error_policy.py',
        'analysis/tests/test_study_scope.py','analysis/tests/test_study_runtime.py',
        'analysis/lll/studies/qualification.py','docs/esa-development-selection-v2/PLAN.md',
        'docs/external-imu-data/ESA_SELECTION_V2.md'])


def required_tests():
    from lll.airquantumgrav_error_policy import required_tests as error_tests
    names=['test_inventory_context_enforces_explicit_development_and_matching_support',
        'test_bounded_decoder_charges_before_parsing_and_verifies_complete_hash',
        'test_inventory_definition_has_no_model_or_native_allowance',
        'test_inventory_prepare_rejects_absent_qualification_before_inputs',
        'test_full_motion_retains_turns_and_climbs_without_claiming_quiet_flight',
        'test_full_motion_exact_duration_distance_and_quality_thresholds_pass',
        'test_full_motion_uses_actual_timestamps_and_wrapped_heading_differences',
        'test_full_motion_ignores_outcomes_and_does_not_mutate_receiver_rows',
        'test_inventory_evaluator_preserves_outputs_and_exact_accounting[10-0]',
        'test_inventory_evaluator_preserves_outputs_and_exact_accounting[2401-1]',
        'test_inventory_evaluator_rejects_protected_group_before_opening_source',
        'test_explicit_receiver_inventory_scope_is_frozen_and_authorized']
    names += [f'test_inventory_rejects_protected_or_unsupported_context_before_reading[{v}]'
        for v in ('protected','unknown','overlap','hash','size','gap','time','receiver_name')]
    names += [f'test_bounded_decoder_rejects_incomplete_or_changed_sources[{v}]' for v in ('excess','hash','truncated_row','order')]
    names += [f'test_version_one_is_identical_to_its_frozen_implementation[{v}]' for v in ('plain','turn','climb','gap','quality','wrap','support')]
    names += [f'test_full_motion_failures_are_preserved_without_maneuver_margin[{v}-{reason}]' for v,reason in
        [('covariance','receiver_covariance'),('pole','receiver_chart_support'),('pdop','receiver_quality'),
         ('satellites','receiver_quality'),('speed','speed'),('support','imu_support')]]
    names += [f'test_full_motion_splits_discontinuities_without_joining_short_runs[{v}]' for v in ('time_gap','sequence_gap')]
    names += [f'test_full_motion_rejects_bad_schema_or_unverified_sources[{v}]' for v in ('cross_shape','missing_cross','duplicate','week','integrity')]
    return names+error_tests()


def prepare(root,*,qualification,identity='esa-development-selection-v2-20261023'):
    import json
    from pathlib import Path
    from lll.studies.artifacts import ArchiveStore,atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if qualification is None:raise ValueError('passing source-bound selection qualification required')
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('safe fresh inventory identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh inventory scope required')
    sources=qualification_sources(root);env=environment()
    request,report=checked(root,qualification,sources=sources,environment=env,
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    store=ArchiveStore(root)
    try:
        raw={key:store.read(name) for key,name in METADATA.items()};values={k:json.loads(v) for k,v in raw.items()}
        context=validate_context(**values)
        legacy=store.read('docs/esa-development-selection/manifest.json');legacy_manifest=json.loads(legacy)
        if legacy_manifest['inputs'][RECEIVER_PATH]!=context['receiver_sha256']:
            raise ValueError('receiver version differs from the preserved first inventory')
        legacy_name='analysis/lll/airquantumgrav_selection.py'
        legacy_source=store.read('docs/esa-development-selection/source-freeze/'+legacy_name)
        if digest(legacy_source)!=legacy_manifest['sources'][legacy_name]:raise ValueError('legacy selection reference differs')
    finally:store.close()
    parent=ClosedStudy(root,'docs/esa-training-forecast-controls')
    try:
        if not parent.summary['passed'] or parent.summary['total']!=24 or parent.summary['completed']!=24:
            raise ValueError('qualified complete training-only parent required')
        proof=dict(training_manifest_sha256=parent.completion['manifest_sha256'],training_summary_sha256=parent.completion['summary_sha256'],
            legacy_manifest_sha256=digest(legacy),legacy_selector_sha256=digest(legacy_source))
    finally:parent.close()
    original=safe_path(root,RECEIVER_PATH)
    reference=dict(path=RECEIVER_PATH,filename=RECEIVER_NAME,sha256=context['receiver_sha256'],size_bytes=original.stat().st_size)
    base.mkdir(parents=True);inputs={};r=recipe()
    materials=[(key,key+'.json',value) for key,value in raw.items()]
    materials += [('source-reference','source-reference.json',encoded(reference)),('recipe','recipe.json',encoded(r)),
        ('qualification-request','qualification-request.json',request),('qualification-report','qualification-report.xml',report),
        ('qualification-environment','qualification-environment.json',encoded(env)),('context','context.json',encoded(context)),
        ('qualified-parents','qualified-parents.json',encoded(proof)),('legacy-manifest','legacy-manifest.json',legacy),
        ('legacy-selector','legacy-selector.py',legacy_source)]
    for key,name,payload in materials:
        atomic(base/name,payload);inputs[key]=str((base/name).relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_inventory.py',sources=sources,
        inputs=inputs,tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=1,scope=manifest['scope'],allocation=manifest['allocation'],limits=r)


def _csv(rows,fields):
    import csv
    import io
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    return stream.getvalue().encode()


def evaluate(task,context):
    import gzip
    import json
    from collections import Counter
    from lll.airquantumgrav_selection import select_full_motion,FULL_MOTION_VERSION
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest,encoded,safe_path
    from lll.studies.journal import Journal
    r=recipe();declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if declared!=tasks()[0] or json.loads(context.input_path('recipe').read_bytes())!=r or context.manifest['scope']!=SCOPE:
        raise ValueError('unchanged frozen receiver-only scope, task and limits required')
    if json.loads(context.input_path('qualification-environment').read_bytes())!=environment():
        raise ValueError('qualified single-thread inventory environment differs')
    values={k:json.loads(context.input_path(k).read_bytes()) for k in METADATA};binding=validate_context(**values)
    if binding!=json.loads(context.input_path('context').read_bytes()):raise ValueError('frozen development context differs')
    reference=json.loads(context.input_path().read_bytes())
    if reference['path']!=RECEIVER_PATH or reference['filename']!=RECEIVER_NAME or reference['sha256']!=binding['receiver_sha256']:
        raise ValueError('explicit established development source reference required')
    if context.root.parent.name!='data':raise ValueError('registered data-namespace runtime required')
    original=safe_path(context.root.parent.parent,reference['path'])
    if original.stat().st_size!=reference['size_bytes']:raise ValueError('original receiver size differs from freeze')
    limits=dict(receiver_file_passes=1,decoder_calls=r['maximum_decoder_calls'],selection_passes=1)
    journal=Journal(context.directory/'inventory-work.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:limits});journal.start(task['identity'])
    try:
        def reserve(**counts):
            for key,value in counts.items():journal.reserve(task['identity'],key,value)
        reserve(receiver_file_passes=1)
        with original.open('rb') as stream:
            decoded=decode(stream,expected_sha256=reference['sha256'],maximum_epochs=r['maximum_receiver_epochs'],
                block_size=r['decoder_block_size'],reserve=reserve,check_continue=lambda:_check_continue(context.root,context.manifest))
        rows=decoded['rows']
        if len(rows)!=binding['expected_receiver_epochs'] or decoded['source_bytes']!=reference['size_bytes']:
            raise ValueError('complete receiver population differs from its established inspection')
        _check_continue(context.root,context.manifest);reserve(selection_passes=1)
        selected=select_full_motion(rows,imu_support=binding['imu_support_s'],source_integrity_verified=True)
        context.save_bytes('selection.json.gz',gzip.compress(encoded(selected),mtime=0))
        fields=('interval_id','group_id','source_file','source_sha256','policy_version','first_index','last_index','epochs',
            'gps_week','first_time_s','last_time_s','duration_s','distance_m','first_utc_date','first_utc_time',
            'last_utc_date','last_utc_time','minimum_speed_kmh','mean_speed_kmh','maximum_speed_kmh',
            'mean_north_mps','mean_east_mps','mean_course_deg','mean_latitude_deg','minimum_height_m',
            'maximum_height_m','mean_up_mps','maximum_absolute_up_mps','maximum_sampled_course_rate_deg_s',
            'height_range_m','rejection_reasons')
        for label in ('eligible','rejected_runs'):
            formatted=[dict(row,interval_id=f'187-v2-{label}-{i:04d}',group_id=binding['group_id'],source_file=RECEIVER_NAME,
                source_sha256=reference['sha256'],policy_version=FULL_MOTION_VERSION,rejection_reasons='|'.join(row['rejection_reasons']))
                for i,row in enumerate(selected[label])]
            context.save_bytes(label+'.csv',_csv(formatted,fields))
        epoch_rows=[dict(index=i,sequence=row['sequence'],gps_week=row['gps_week'],time_s=row['time_s'],
            rejection_reasons='|'.join(selected['epoch_reasons'][i])) for i,row in enumerate(rows)]
        context.save_bytes('epoch-reasons.csv.gz',gzip.compress(_csv(epoch_rows,('index','sequence','gps_week','time_s','rejection_reasons')),mtime=0))
        journal.verify();charged={key:journal.count(task['identity'],key) for key in limits}
        _check_continue(context.root,context.manifest)
        return dict(passed=True,policy_version=FULL_MOTION_VERSION,group_id=binding['group_id'],receiver_epochs=len(rows),
            receiver_source_sha256=decoded['source_sha256'],receiver_source_bytes=decoded['source_bytes'],
            decoder_calls=decoded['decoder_calls'],charged_work=charged,eligible_count=len(selected['eligible']),
            eligible_minutes=sum(row['duration_s'] for row in selected['eligible'])/60.,rejected_runs=len(selected['rejected_runs']),
            excluded_epochs=selected['excluded_epochs'],rejection_counts=dict(Counter(reason for values in selected['epoch_reasons'] for reason in values)),
            raw_imu_reads=0,native_calls=0,observed_optimizer_starts=0,protected_reads=0,scientific_decision='abstain')
    finally:context.note_file(journal.path)
