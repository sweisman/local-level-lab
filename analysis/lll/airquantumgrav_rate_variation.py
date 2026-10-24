# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only ESA rate variation using shared diagnostics and study lifecycle."""
import math

SCOPE='saved earlier ESA logged-rate variation; no fitting or original/protected reads'


def recipe():
    return dict(version='esa-training-rate-variation-v1',workers=1,threads=1,maximum_wall_s=300.,
        maximum_input_samples=360100,maximum_input_bytes=128*1024*1024,strides=[1,3,30,300],
        maximum_gap_s=.005,training_epochs=800,prediction_epochs=400,
        native_calls=0,observed_starts=0,original_reads=0,protected_reads=0,retries=0)


def tasks():
    return [dict(identity='logged-rates',input_key='interval',payload=dict(recording='187'),native_kind='value',
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))]


def work_limits(r):
    n=r['maximum_input_samples']
    return dict(input_samples=n,training_samples=n,
        contrast_rows=sum(len(range(0,n-2*s,3*s)) for s in r['strides']))


def calculate(arrays,layout,r,*,reserve,save):
    if (r!=recipe() or layout.get('training_epochs')!=r['training_epochs']
            or layout.get('prediction_epochs')!=r['prediction_epochs']
            or len(layout.get('times_s',[]))!=r['training_epochs']+r['prediction_epochs']):
        raise ValueError('unchanged complete training layout required')
    import numpy as np
    from lll.rate_variation import training_prefix,summarize
    from lll.studies.artifacts import digest
    query=layout['times_s'];origin=layout['time_origin_gps_sow_s']
    if (not math.isfinite(origin) or not all(math.isfinite(x) for x in query)
            or any(b<=a for a,b in zip(query,query[1:]))):raise ValueError('ordered finite training layout required')
    times=arrays['raw_time_s'];reserve(input_samples=len(times))
    if (len(times)>r['maximum_input_samples'] or arrays['angular_rate_rads'].shape!=(len(times),3)
            or arrays['acceleration_mps2'].shape!=(len(times),3)):
        raise ValueError('bounded original six-channel sample arrays required')
    cutoff=origin+query[r['training_epochs']-1]
    times,values=training_prefix(times,np.column_stack([arrays['angular_rate_rads'],arrays['acceleration_mps2']]),
        last_training_time_s=cutoff,maximum_points=r['maximum_input_samples'])
    count=sum(len(range(0,len(times)-2*s,3*s)) for s in r['strides'])
    reserve(training_samples=len(times),contrast_rows=count)
    report=summarize(times,values,strides=r['strides'],maximum_points=r['maximum_input_samples'],maximum_gap_s=r['maximum_gap_s'])
    report.update(training_cutoff_gps_s=cutoff,first_used_time_gps_s=float(times[0]),last_used_time_gps_s=float(times[-1]),
        used_times_sha256=digest(times.astype('<f8').tobytes()),used_values_sha256=digest(values.astype('<f8').tobytes()))
    save('variation.json',report)
    return dict(passed=True,training_samples=len(times),input_samples=len(arrays['raw_time_s']),contrast_rows=count,
        native_calls=0,observed_starts=0,original_reads=0,protected_reads=0,
        isolated_sensor_noise_estimated=False,error_law_calibrated=False,scientific_decision='abstain')


def evaluate(task,context):
    import json
    from lll.airquantumgrav_inventory import validate_context,METADATA,environment,IMU_NAME
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll.ilvis0_control_shards import _check_continue
    read=lambda key:json.loads(context.input_path(key).read_bytes());r=recipe()
    if (read('recipe')!=r or context.manifest['scope']!=SCOPE or read('qualification-environment')!=environment()
            or {k:v for k,v in task.items() if k not in ('index','shard')}!=tasks()[0]):
        raise ValueError('unchanged qualified saved-data scope required')
    binding=validate_context(**{key:read(key) for key in METADATA})
    parent=read('verified-parent');source=read('source-validation')
    if (binding!=read('context') or not parent['verified'] or parent['group_id']!=binding['group_id']
            or source['group_id']!=binding['group_id'] or parent['source_references']!=source['references']
            or source['references']['imu']['filename']!=IMU_NAME
            or source['references']['imu']['sha256']!=binding['imu_source_sha256']
            or source['raw_points']!=parent['raw_points'] or parent['training_epochs']!=r['training_epochs']):
        raise ValueError('verified unchanged development preparation required')
    path=context.input_path('interval')
    if path.stat().st_size>r['maximum_input_bytes']:raise ValueError('bounded prepared artifact required')
    journal=Journal(context.directory/'variation.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:work_limits(r)});journal.start(task['identity'])
    try:
        def check():_check_continue(context.root,context.manifest)
        def reserve(**work):
            check()
            for key,count in work.items():journal.reserve(task['identity'],key,count)
        import numpy as np
        with np.load(path,allow_pickle=False) as archive:
            arrays={key:archive[key] for key in ('raw_time_s','angular_rate_rads','acceleration_mps2')}
        if len(arrays['raw_time_s'])!=source['raw_points']:raise ValueError('prepared sample count differs')
        result=calculate(arrays,read('query-layout'),r,reserve=reserve,save=context.save)
        check();journal.verify()
        if any(journal.count(task['identity'],key)!=result[key] for key in work_limits(r)):
            raise ValueError('saved-data work charges differ')
        return result
    finally:context.note_file(journal.path)


def inspect(root,prefix='data/esa-training-rate-variation-20261024'):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)
    try:
        from lll.studies.source_binding import verify
        from lll.airquantumgrav_inventory import environment
        from lll.airquantumgrav_geographic_report import construction_counts
        r=study.input('recipe');identity='logged-rates'
        if r!=recipe() or study.input('qualification-environment')!=environment() or study.manifest['scope']!=SCOPE:
            raise ValueError('unchanged qualified descriptive recipe required')
        verify(root,declared=study.input('qualification-request')['sources'],manifest=study.manifest['sources'])
        if set(study.rows)!={identity}:raise ValueError('one complete saved-rate outcome required')
        envelope=study.envelope(identity);result=envelope['result']
        for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
        report=study.artifact(identity,'variation.json')
        counts=construction_counts(study.artifact(identity,'variation.sqlite',raw=True),
            study.completion['manifest_sha256'],identity,work_limits(r),complete=False)
        if (not result['passed'] or report['points']!=result['training_samples']
                or report['total_contrasts']!=result['contrast_rows']
                or any(counts[key]!=result[key] for key in counts)
                or any(study.summary['charged'].values())
                or any(result[key] for key in ('native_calls','observed_starts','original_reads','protected_reads',
                    'isolated_sensor_noise_estimated','error_law_calibrated'))
                or report['last_used_time_gps_s']>report['training_cutoff_gps_s']
                or [row['stride'] for row in report['contrasts']]!=r['strides']
                or report['channel_units']!=['rad/s']*3+['m/s^2']*3
                or any(len(row['rms_native_units'])!=6 or not all(math.isfinite(x) and x>=0 for x in row['rms_native_units'])
                    for row in report['contrasts'])):
            raise ValueError('saved variation, units, boundary or charged work differs')
        return dict(verified=True,result=result,variation=report,elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            error_law_calibrated=False,isolated_sensor_noise_estimated=False,scientific_decision='abstain')
    finally:study.close()
