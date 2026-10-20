# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen receiver-only ESA development selection; no model fitting."""
import argparse
from collections import Counter
import csv
import fcntl
import gzip
import io
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_channel_envelope_worker import sha,load,write,environment
from lll.ilvis0_receipt_journal import durable_write

NAME='esa-development-selection-v1-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/esa-development-selection'
SOURCE=ROOT/'data/external-imu-survey-20261018/esa-sample'
INPUTS=['docs/analysis-provenance/ledger.json','docs/external-imu-data/ESA_CONFIRMATION_POLICY.json',
    'docs/external-imu-data/esa-gnss-report.json',
    'data/external-imu-survey-20261018/esa-sample/187_air1_ppp_2Hz_final.txt',
    'data/external-imu-survey-20261018/esa-sample/inspection.json',
    'data/external-imu-survey-20261018/esa-sample/download-completion.json']
TASK=dict(identity='receiver-inventory-187')
LIMITS=dict(maximum_identities=1,maximum_receiver_epochs=100000,maximum_wall_s=300,numerical_threads=4,
    receiver_files=1,raw_imu_reads=0,optimizer_starts=0,native_evaluations=0,retries=0,deadline_policy='cooperative-no-signals')


def development_group(ledger,filename):
    from lll.evidence_groups import require_development
    matches=[g['group_id'] for g in ledger['groups'] if 'esa:'+filename in g['record_ids']]
    if len(matches)!=1:raise ValueError('exactly one assigned development group required')
    require_development(ledger,matches);return matches[0]


def checked_support(inspection,receipt):
    if (inspection['source_file']!='187_rqh01.txt' or inspection['source_sha256']!=receipt['sha256']
            or inspection['byte_size']!=receipt['size_bytes'] or inspection['gaps_above_1p5_nominal_periods']!=0):
        raise ValueError('matching complete acquisition/inspection with no IMU gaps required')
    first=inspection['first_gps_sow_s'];last=inspection['last_gps_sow_s']
    if not 0<=first<last<604800:raise ValueError('supported single-week IMU timing required')
    return first,last


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import airquantumgrav_selection,airquantumgrav_receiver,airquantumgrav_intervals,evidence_groups
    files={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    files.update('analysis/tests/'+name for name in ('airquantumgrav_selection_worker.py','ilvis0_channel_envelope_worker.py',
        'run_numerical.py','test_airquantumgrav_receiver.py','test_airquantumgrav_selection.py',
        'test_airquantumgrav_intervals.py','test_airquantumgrav_selection_worker.py'))
    files.add('docs/external-imu-data/ESA_SELECTION_V1.md')
    sources={name:sha(ROOT/name) for name in sorted(files)};inputs={name:sha(ROOT/name) for name in INPUTS}
    ledger=load(ROOT/INPUTS[0]);group=development_group(ledger,'187_rqh01.txt')
    policy=load(ROOT/INPUTS[1])
    if '187_rqh01.txt' not in policy['development_files'] or '187_rqh01.txt' in policy['confirmation_files']:
        raise ValueError('explicit development reservation required')
    support=checked_support(load(SOURCE/'inspection.json'),load(SOURCE/'download-completion.json'))
    gps_report=load(ROOT/INPUTS[2])
    if inputs[INPUTS[3]]!=gps_report['sha256']:raise ValueError('receiver source differs from inspected original')
    for name in sources:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    for name in INPUTS:
        if name.endswith('.json'):
            target=DATA/'input-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version=airquantumgrav_selection.VERSION,sources=sources,inputs=inputs,
        environment=environment(),limits=LIMITS,plan=dict(tasks=[TASK],numerical_threads=4),
        group_id=group,imu_source_file='187_rqh01.txt',receiver_source_file=Path(INPUTS[3]).name,
        imu_support_s=support,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS:raise ValueError('environment or finite scope changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('frozen source changed: '+name)
    for name,digest in manifest['inputs'].items():
        if sha(ROOT/name)!=digest:raise ValueError('frozen input changed: '+name)
    return manifest


def csv_artifact(name,rows,fields):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader();writer.writerows(rows);payload=stream.getvalue().encode()
    if name.endswith('.gz'):payload=gzip.compress(payload,mtime=0)
    path=DATA/name;path.parent.mkdir(parents=True,exist_ok=True);durable_write(path,payload)
    return dict(artifact=name,sha256=sha(path))


def calculate(manifest,deadline):
    from lll.airquantumgrav_receiver import records
    from lll.airquantumgrav_selection import select
    rows=[]
    with (ROOT/INPUTS[3]).open('rb') as stream:
        for row in records(stream):
            if len(rows)>=LIMITS['maximum_receiver_epochs']:raise ValueError('receiver epoch allowance exhausted')
            if time.monotonic()>=deadline:raise RuntimeError('cooperative wall allowance exhausted')
            rows.append(row)
    result=select(rows,imu_support=manifest['imu_support_s'],source_integrity_verified=True)
    if time.monotonic()>=deadline:raise RuntimeError('cooperative wall allowance exhausted')
    artifacts=[]
    for label in ('eligible','rejected_runs'):
        formatted=[]
        for i,row in enumerate(result[label]):
            row=dict(row);row['rejection_reasons']='|'.join(row['rejection_reasons'])
            row.update(interval_id=f'187--{label}--{i:04d}',group_id=manifest['group_id'],source_file=manifest['receiver_source_file'],
                source_sha256=manifest['inputs'][INPUTS[3]],policy_version=manifest['version'])
            formatted.append(row)
        fields=list(formatted[0]) if formatted else ['interval_id','group_id','source_file','source_sha256','policy_version','rejection_reasons']
        artifacts.append(csv_artifact('inventory/'+label+'.csv',formatted,fields))
    epoch_rows=[dict(index=i,sequence=row['sequence'],gps_week=row['gps_week'],time_s=row['time_s'],
        rejection_reasons='|'.join(result['epoch_reasons'][i])) for i,row in enumerate(rows)]
    artifacts.append(csv_artifact('inventory/epoch-reasons.csv.gz',epoch_rows,['index','sequence','gps_week','time_s','rejection_reasons']))
    reasons=Counter(reason for value in result['epoch_reasons'] for reason in value)
    path='inventory/selection.json.gz';write(DATA/path,result);artifacts.append(dict(artifact=path,sha256=sha(DATA/path)))
    return dict(passed=True,receiver_epochs=len(rows),eligible_count=len(result['eligible']),
        eligible_minutes=sum(row['duration_s'] for row in result['eligible'])/60.,
        rejected_runs=len(result['rejected_runs']),excluded_epochs=result['excluded_epochs'],
        rejection_counts=dict(reasons),artifacts=artifacts,eligible=result['eligible'],
        raw_imu_reads=0,native_evaluations=0,optimizer_starts=0,scientific_decision='abstain',
        completeness_basis='previous full-source acquisition hash and streaming IMU inspection; no new raw-IMU pass')


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged selection inventory cannot restart')
        manifest=verify();started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s']
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        write(DATA/'charges/receiver-inventory-187.json',dict(TASK,manifest_sha256=sha(DATA/'manifest.json')))
        write(DATA/'status.json',dict(state='running',identity=TASK['identity'],total=1,numerical_threads=4,pid=os.getpid()),replace=True)
        try:result=calculate(manifest,deadline)
        except Exception as error:result=dict(passed=False,error=type(error).__name__+': '+str(error))
        artifact='results/receiver-inventory-187.json';write(DATA/artifact,result)
        row=dict(TASK,passed=result['passed'],artifact=artifact,artifact_sha256=sha(DATA/artifact))
        elapsed=time.time()-started
        write(DATA/'summary.json',dict(state='complete',passed=result['passed'],results=[row],elapsed_s=elapsed,
            wall_overrun_s=max(0.,elapsed-LIMITS['maximum_wall_s']),native_evaluations=0,optimizer_starts=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state='complete',total=1,numerical_threads=0),replace=True)
    publish()


def publish():
    manifest=load(DATA/'manifest.json');summary=load(DATA/'summary.json');completion=load(DATA/'completion.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):
        raise ValueError('completed inventory changed')
    row=summary['results'][0]
    if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('inventory result changed')
    result=load(DATA/row['artifact'])
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json',row['artifact'],'charges/receiver-inventory-187.json']
    for item in result.get('artifacts',[]):
        if sha(DATA/item['artifact'])!=item['sha256']:raise ValueError('selection artifact changed')
        names.append(item['artifact'])
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    shutil.copytree(DATA/'input-freeze',PUBLIC/'input-freeze',dirs_exist_ok=True)
    lines=['# ESA development interval inventory','']
    if result['passed']:
        lines+=[f"**{result['eligible_count']} eligible stretches, {result['eligible_minutes']:.1f} minutes**, from {result['receiver_epochs']:,} receiver epochs in recording 187.",'',
            'Selection used receiver trajectory, reported quality and the preserved completeness inspection. No gyroscope values, model costs, raw-IMU rereads or native fits were used. Protected confirmation groups were not evaluated.','',
            '| Interval | Duration | Distance | Mean speed | Mean latitude | Mean course |','|---|---:|---:|---:|---:|---:|']
        for i,interval in enumerate(result['eligible']):
            lines.append(f"| {i+1} | {interval['duration_s']/60:.2f} min | {interval['distance_m']/1000:.2f} km | "
                f"{interval['mean_speed_kmh']:.1f} km/h | {interval['mean_latitude_deg']:.3f}° | {interval['mean_course_deg']:.1f}° |")
        lines+=['',f"{result['excluded_epochs']:,} epochs were excluded; {result['rejected_runs']} retained runs failed duration or distance. Reasons can overlap.",'',
            '[Eligible intervals](inventory/eligible.csv) · [Rejected runs](inventory/rejected_runs.csv) · [Every epoch and reason](inventory/epoch-reasons.csv.gz).']
    else:lines+=[f"Inventory failed: `{result['error']}`. Preserve the charged outcome; no automatic retry."]
    lines+=['','This is a frozen selection inventory, not an Earth-model result. Engineering-rate quadrature, sampling phase, native integration, lever arms, mounting and observational uncertainty remain separately qualified requirements.',
        '', '[Selection rules](../external-imu-data/ESA_SELECTION_V1.md) · [Confirmation reservation](../analysis-provenance/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names.append('README.md')
    names+=['source-freeze/'+name for name in manifest['sources']]
    names+=['input-freeze/'+name for name in INPUTS if name.endswith('.json')]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen one receiver-only development inventory.')
    elif args.run:run();print('Finite receiver inventory complete; see saved results.')
    else:publish();print('Published saved selection; no recalculation.')


if __name__=='__main__':main()
