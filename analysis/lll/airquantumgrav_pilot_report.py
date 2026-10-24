# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-data verification of preparation; no original reads or model fitting."""
import gzip
import io
import json


def validate_interval(raw,layout,result):
    import numpy as np
    names=('raw_time_s','acceleration_mps2','angular_rate_rads','temperature_c','line_number','theta','dv','dt')
    n=result['raw_points'];m=n-1
    if type(n) is not int or not 2<=n<=360100:raise ValueError('finite retained point count required')
    with np.load(io.BytesIO(raw),allow_pickle=False) as archive:
        if set(archive.files)!=set(names):raise ValueError('complete original and constructed channels required')
        values={k:archive[k] for k in names}
    shapes=dict(raw_time_s=(n,),acceleration_mps2=(n,3),angular_rate_rads=(n,3),temperature_c=(n,),
        line_number=(n,),theta=(m,3),dv=(m,3),dt=(m,))
    if any(a.shape!=shapes[k] or a.dtype!=np.dtype('int64' if k=='line_number' else 'float64')
            or not np.all(np.isfinite(a)) for k,a in values.items()):
        raise ValueError('complete finite raw/constructed shapes and original line numbers required')
    t=values['raw_time_s'];dt=values['dt'];times=np.asarray(layout['times_s'],float);cut=layout['training_epochs']
    if (np.any((t<0)|(t>=604800)) or not np.array_equal(dt,np.diff(t)) or np.any(dt<=0) or np.any(dt>.005)
            or np.any(np.diff(values['line_number'])!=1) or values['line_number'][0]<2
            or result['constructed_intervals']!=m or layout['time_origin_gps_sow_s']!=t[0]
            or times.shape!=(result['query_epochs'],) or not np.all(np.isfinite(times)) or np.any(np.diff(times)<=0)
            or not 0<cut<len(times) or cut!=result['training_epochs'] or len(times)-cut!=result['prediction_epochs']
            or layout['prediction_epochs']!=len(times)-cut
            or layout['sampling_hypothesis']!='linear_points' or not layout['constructed_not_logged_increments']
            or layout['maximum_interval_s']!=.005 or layout['maximum_latency_s']!=.01
            or times[0]-.01<0 or times[-1]+.01>np.sum(dt)):
        raise ValueError('actual complete timing, original support or declared quadrature differs')
    for name,channel in [('theta','angular_rate_rads'),('dv','acceleration_mps2')]:
        expected=(values[channel][:-1]+values[channel][1:])/2*dt[:,None]
        if not np.array_equal(values[name],expected):raise ValueError('constructed increments differ from original rates and actual dt')
    return dict(raw_points=n,constructed_intervals=m,minimum_dt_s=float(np.min(dt)),
        median_dt_s=float(np.median(dt)),maximum_dt_s=float(np.max(dt)),
        first_raw_time_s=float(t[0]),last_raw_time_s=float(t[-1]),constructed_not_logged_increments=True)


def inspect(root,prefix='data/esa-development-pilot-preparation-20261023'):
    import sqlite3
    from pathlib import Path
    import numpy as np
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    from lll.studies.journal import inspect_snapshot
    from lll.airquantumgrav_error_policy import build,policies
    study=ClosedStudy(root,prefix)
    try:
        if not study.summary['passed'] or len(study.tasks)!=1:raise ValueError('complete passing preparation required')
        identity=next(iter(study.tasks));envelope=study.envelope(identity);result=envelope['result'];r=study.input('recipe')
        artifact=lambda name:study.artifact(identity,name)
        layout=artifact('query-layout.json');source=artifact('source-validation.json');weights=artifact('working-errors.json')
        training=json.loads(gzip.decompress(study.artifact(identity,'training-receiver.json.gz',raw=True)))
        scoring=json.loads(gzip.decompress(study.artifact(identity,'scoring-receiver.json.gz',raw=True)))
        cut=layout['training_epochs'];chosen=study.input('chosen');binding=study.input('context');refs=study.input('references')
        checked=validate_interval(study.artifact(identity,'interval.npz',raw=True),layout,result)
        if (cut!=800 or layout['prediction_epochs']!=400 or len(scoring)!=1200 or len(training)!=cut
                or encoded(training)!=encoded(scoring[:cut]) or result['chosen']!=chosen
                or source['selection']!=chosen or source['references']!=refs or source['sources']!=result['sources']
                or source['group_id']!=binding['group_id'] or result['group_id']!=binding['group_id']
                or layout['query_source_indices']!=list(range(chosen['first_index']+1,chosen['last_index'],2))
                or layout['later_positions_used_for_training']
                or not np.array_equal(np.array(layout['times_s']),np.array([v['time_s'] for v in scoring])-layout['time_origin_gps_sow_s'])
                or source['raw_points']!=checked['raw_points'] or source['intervals']!=checked['constructed_intervals']
                or source['first_raw_time_s']!=checked['first_raw_time_s'] or source['last_raw_time_s']!=checked['last_raw_time_s']):
            raise ValueError('unchanged selection, source or exact earlier/later binding required')
        for name,block in [('imu',r['imu_decoder_block']),('receiver',r['receiver_decoder_block'])]:
            stat=result['sources'][name];ref=refs[name]
            if (stat['records']!=ref['records'] or stat['source_sha256']!=ref['sha256'] or stat['source_bytes']!=ref['size_bytes']
                    or stat['decoder_calls']!=stat['records']+1
                    or stat['reserved_calls']!=min(((stat['decoder_calls']+block-1)//block)*block,r['maximum_'+name+'_records']+1)):
                raise ValueError('complete original integrity and decoder accounting differ')
        expected=dict(imu_passes=1,receiver_passes=1,imu_decoder_calls=result['sources']['imu']['reserved_calls'],
            receiver_decoder_calls=result['sources']['receiver']['reserved_calls'],retained_points=r['maximum_retained_points'],
            constructed_intervals=checked['constructed_intervals'],working_error_descriptions=2)
        raw=study.artifact(identity,'preparation-work.sqlite',raw=True)
        snapshot=inspect_snapshot(raw,study.completion['manifest_sha256']);connection=sqlite3.connect(':memory:')
        try:
            connection.deserialize(raw);connection.execute('PRAGMA query_only=ON')
            counts=dict(connection.execute('SELECT resource,SUM(total) FROM counts GROUP BY resource'))
            if counts!=expected or counts!=result['charged_work'] or snapshot['starts']!=1:
                raise ValueError('saved preparation work differs')
        finally:connection.close()
        # Reconstruct weights from saved earlier rows only, with checked numerical sources.
        for filename in ('airquantumgrav_error_policy.py','ilvis0_error_model.py','models.py'):
            name='analysis/lll/'+filename
            if digest((Path(root)/name).read_bytes())!=study.manifest['sources'][name]:
                raise ValueError('restore the qualified weight dependencies before reporting')
        if set(weights)!=set(policies()) or set(result['working_error_cases'])!=set(weights):
            raise ValueError('both frozen working error cases required')
        for name in weights:
            w=build(training,policy_id=name)
            if weights[name]!=dict(descriptor=w.descriptor,configuration=w.configuration,training_source_sha256=w.source_sha256):
                raise ValueError('weights depend on different observations or policy')
        if any(result[k]!=0 for k in ('native_calls','observed_starts','protected_reads')):
            raise ValueError('preparation cannot contain model fitting or protected data')
        for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
        speed=np.array([np.hypot(v['north_mps'],v['east_mps'])*3.6 for v in scoring])
        return dict(verified=True,**checked,duration_s=result['duration_s'],training_epochs=800,prediction_epochs=400,
            query_epochs=1200,chosen=chosen,group_id=binding['group_id'],source_references=refs,
            minimum_query_speed_kmh=float(np.min(speed)),mean_query_speed_kmh=float(np.mean(speed)),
            maximum_query_speed_kmh=float(np.max(speed)),mean_query_latitude_deg=float(np.mean([v['latitude_deg'] for v in scoring])),
            minimum_query_height_m=min(v['height_m'] for v in scoring),maximum_query_height_m=max(v['height_m'] for v in scoring),
            charged_work=expected,working_error_cases=list(weights),elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            original_reads=0,native_calls=0,observed_starts=0,protected_reads=0,scientific_decision='abstain')
    finally:study.close()


def render(report):
    return f'''# One ESA interval ready for the prediction pilot

**The first twenty-minute development interval is prepared and verified.**
It contains {report['raw_points']:,} original IMU samples and
{report['constructed_intervals']:,} constructed intervals, using actual timestamps.
The IMU is an inertial measurement unit containing gyroscopes and accelerometers.

The interval is the earliest eligible window in recording 187. It was chosen
before any ESA model fit. At the fixed query epochs, mean speed is
{report['mean_query_speed_kmh']:.1f} km/h, mean latitude is
{report['mean_query_latitude_deg']:.2f}° N and height spans
{report['minimum_query_height_m']:.0f}–{report['maximum_query_height_m']:.0f} m.
Turns and climbs remain in the data for explicit motion reconstruction.

The earlier **800 receiver positions** are stored for training. The later
**400 positions** are kept separately for scoring only after a continuous forecast
has been saved. Both working receiver-error cases use earlier observations only.
They are sensitivity assumptions, not calibrated receiver accuracy.

Preparation verified all 9,168,819 IMU rows and 64,080 receiver rows in one complete
pass through each source. The retained samples preserve original rate, acceleration,
temperature, timestamps and line numbers. Constructed angle and velocity increments
use the linear-point sampling hypothesis; they are not logged instrument increments.
Actual sampling, filtering and compensation remain distinct processing assumptions.

The saved-data audit checks every artifact hash, rate-to-increment conversion,
timing support, exact query indices, training/scoring separation, working weights
and charge journal. It does not reopen original sources or fit a model.

**No ESA globe/disc or background-field result exists yet.** The next gate is a
matched software check and a separately frozen 24-fit development comparison.
Seven confirmation groups remain protected. The original NASA findings are unchanged.

[Frozen preparation plan](PLAN.md) · [Pilot plan](../esa-development-pilot/PLAN.md) ·
[Source interval inventory](../esa-development-selection-v2/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
'''


def publish(root,prefix='data/esa-development-pilot-preparation-20261023',output='docs/esa-development-pilot-preparation'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('preparation publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-development-pilot-preparation/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0)
