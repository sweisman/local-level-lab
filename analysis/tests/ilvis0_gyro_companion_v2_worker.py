# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen descriptive gyro companion: independent controls, then saved intervals."""
import argparse
import csv
import fcntl
import gzip
import io
import itertools
import math
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_channel_envelope_worker import sha,load,write,environment

NAME='ilvis0-gyro-companion-v2-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-gyro-companion-v2'
MODELS=('sphere_rotating','sphere_still','flat_still')
CONTROLS=[dict(identity=f'control-{i:02d}',kind='control',model=model,latitude_deg=latitude,course_deg=course,removal=removal,
    roll_deg=(-3.,0.,3.)[i%3],pitch_deg=(-3.,0.,3.)[(i//3)%3],crab_deg=(-10.,0.,10.)[(i//9)%3],course_rate=.001*math.sin(i))
    for i,(model,latitude,course,removal) in enumerate(itertools.product(MODELS,(-65.,65.),(0.,90.,180.,270.),(0.,1.)))]
SCENARIOS=[dict(model=model,removal=removal,crab_deg=crab,roll_deg=roll,pitch_deg=pitch)
    for model,removal,crab,roll,pitch in itertools.product(MODELS,(0.,.5,1.),(-10.,0.,10.),(-3.,0.,3.),(-3.,0.,3.))]
LIMITS=dict(maximum_controls=48,maximum_observed_summaries=53,maximum_scenarios=12879,maximum_bin_scenario_projections=12879000,
    maximum_bins_per_stretch=1000,maximum_receiver_fixes_per_stretch=1500,maximum_wall_s=180,numerical_threads=4,
    original_reads=0,native_evaluations=0,optimizer_starts=0,retries=0,deadline_policy='cooperative-no-signals')
FINDINGS=ROOT/'docs/ilvis0-current-findings-20261015';BASE=ROOT/'docs/ilvis0-highspeed-segments-20261008'
CACHE=ROOT/'data/ilvis0-stretch-analytics-20261013';CACHE_RECEIPT=ROOT/'docs/ilvis0-position-stability-trial-20261013/analytics-receipt.json'
GROUPS=ROOT/'docs/analysis-provenance';RAW=ROOT/'docs/ilvis0-gyro-overview'


class AllowanceExhausted(BaseException):pass


def check_time(deadline):
    if time.monotonic()>=deadline:raise AllowanceExhausted('cooperative gyro-companion wall allowance exhausted')


def control(task):
    """Independent ECEF/plane-basis derivative plus physical-axis projection."""
    import numpy as np
    from scipy.linalg import expm
    from lll import ilvis0_gyro_prediction as g
    phi,lam=math.radians(task['latitude_deg']),1.1
    course=math.radians(task['course_deg']);heading=course+math.radians(task['crab_deg'])
    roll,pitch=math.radians(task['roll_deg']),math.radians(task['pitch_deg'])
    pd=1e-5*math.cos(course);ld=2e-5*math.sin(course)
    def basis(latitude,longitude,flat=False):
        s,c=np.sin(longitude),np.cos(longitude)
        if flat:return np.array([[-c,-s,0.],[-s,c,0.],[0.,0.,-1.]])
        sp,cp=np.sin(latitude),np.cos(latitude)
        return np.array([[-sp*c,-s,-cp*c],[-sp*s,c,-cp*s],[cp,0.,-sp]])
    def skew(v):
        x,y,z=v;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    def attitude(tau):
        return expm(skew([0.,0.,heading+task['course_rate']*tau]))@expm(skew([0.,pitch,0.]))@expm(skew([roll,0.,0.]))
    def body(tau):return basis(phi+pd*tau,lam+ld*tau,task['model']=='flat_still')@attitude(tau)
    b0=body(0.);derivative=body(1e-25j).imag/1e-25;spin=b0.T@derivative
    relative=np.array([spin[2,1]-spin[1,2],spin[0,2]-spin[2,0],spin[1,0]-spin[0,1]])/2.
    standard=basis(phi,lam).T@np.array([0.,0.,7.2921150e-5])
    physical=b0.T@np.array([0.,0.,7.2921150e-5]) if task['model']=='sphere_rotating' else np.zeros(3)
    expected=relative+physical-task['removal']*(attitude(0.).T@standard)
    vector=g.geographic_vector(task['model'],phi,pd,ld,removal=task['removal'])
    actual=float(vector@g.right_axis(heading,roll=roll,pitch=pitch)+g.course_pitch_rate(task['course_rate'],roll=roll,pitch=pitch))
    error=abs(actual-float(expected[1]))
    return dict(identity=task['identity'],kind='control',passed=error<=1e-12,expected_right_rads=float(expected[1]),
        actual_right_rads=actual,absolute_error_rads=error,input=task,reference='independent geographic basis and body derivative',
        scientific_decision='abstain')


def require_controls(rows):
    if len(rows)!=48 or {r['identity'] for r in rows}!={t['identity'] for t in CONTROLS} or not all(r['passed'] for r in rows):
        raise ValueError('all independent gyro controls must pass before observed evaluation')


def observed(meta,selected,saved,deadline=None):
    from lll import ilvis0_gyro_prediction as g
    if saved['provenance']['source_sha256']!=meta['source_sha256']:raise ValueError('gyro source identity mismatch')
    if len(saved['seconds'])>LIMITS['maximum_bins_per_stretch'] or len(selected['receiver_fixes'])>LIMITS['maximum_receiver_fixes_per_stretch']:
        raise ValueError('frozen gyro-companion input allowance exceeded')
    geometry=g.receiver_geometry(selected['receiver_fixes'])
    support=g.matched_bins(saved['seconds'],geometry,recorded_mount_available=saved['summary']['recorded_mount_available'])
    if not support['supported']:return dict(supported=False,reason=support['reason'],metadata=meta,scenarios_evaluated=0,scientific_decision='abstain')
    rows=[]
    for scenario in SCENARIOS:
        if deadline is not None:check_time(deadline)
        rows.append(g.summarize(geometry,support,**scenario))
    baseline=[r for r in rows if all(r[k]==0. for k in ('removal','crab_deg','roll_deg','pitch_deg'))]
    spans={}
    for model in MODELS:
        candidates=[r for r in rows if r['model']==model]
        spans[model]={key:dict(minimum=min(r[key] for r in candidates),maximum=max(r[key] for r in candidates))
            for key in ('predicted_nose_down_dph','predicted_nose_down_deg','observed_minus_scenario_dph')}
    return dict(supported=True,metadata=meta,scenarios_evaluated=len(rows),baseline=baseline,scenario_results=rows,finite_scenario_spans=spans,
        matched_support=dict(utc_seconds=support['utc_seconds'],durations_s=support['durations_s'],raw_aircraft=support['raw_aircraft'],
            receiver_indices=support['receiver_indices'],association_errors_s=support['association_errors_s'],excluded=support['excluded']),
        recorded_mount_interpretation='preserved legacy message transformation; not independently measured mounting',
        field_magnitude_fitted=False,fused_attitude_used=False,original_reads=0,optimizer_starts=0,scientific_decision='abstain')


def csv_rows(path):
    with Path(path).open(newline='') as stream:return list(csv.DictReader(stream))


def prepare_inputs():
    inventory=FINDINGS/'current-stretches.csv';findings_receipt=FINDINGS/'findings-receipt.json'
    if sha(inventory)!=load(findings_receipt)['artifacts']['current-stretches.csv']:raise ValueError('current stretch inventory changed')
    selection=BASE/'selection.json.gz';base_receipt=BASE/'evidence-receipt.json'
    if sha(selection)!=load(base_receipt)['artifacts']['selection.json.gz']:raise ValueError('selected receiver population changed')
    selections={r['segment']['segment_id']:r['segment'] for r in load(selection)['selected']}
    group_file=GROUPS/'recording-groups.csv';group_receipt=GROUPS/'provenance-receipt.json'
    if sha(group_file)!=load(group_receipt)['artifacts']['recording-groups.csv']:raise ValueError('conservative grouping changed')
    groups={r['record_id'].split(':',1)[1]:r for r in csv_rows(group_file) if r['archive']=='ilvis0'}
    receipt=load(CACHE_RECEIPT);cache_manifest=CACHE/'manifest.json'
    if sha(cache_manifest)!=receipt['cache_manifest_sha256']:raise ValueError('gyro-cache source freeze changed')
    raw_receipt=RAW/'provenance.json';raw_metadata=load(raw_receipt)
    for name in ('raw-pitch.png','raw-pitch.svg'):
        if sha(RAW/name)!=raw_metadata['artifacts'][name]:raise ValueError('existing raw gyro plot changed')
    paths=[inventory,findings_receipt,selection,base_receipt,group_file,group_receipt,CACHE_RECEIPT,cache_manifest,raw_receipt,RAW/'raw-pitch.png',RAW/'raw-pitch.svg']
    rows=csv_rows(inventory)
    if len(rows)!=53 or len({r['segment_id'] for r in rows})!=53 or {r['segment_id'] for r in rows}!=set(selections):raise ValueError('fixed population mismatch')
    records=[]
    for row in rows:
        sid=row['segment_id'];selected=selections[sid];path=CACHE/(sid+'.json.gz');digest=sha(path)
        if digest!=receipt['cache_artifacts'][str(path)]:raise ValueError('preserved raw gyro bins changed')
        saved=load(path)
        if saved['cache_manifest_sha256']!=sha(cache_manifest) or saved['provenance']['source_sha256']!=row['source_sha256']:
            raise ValueError('gyro-cache provenance changed')
        if len(saved['seconds'])>1000 or len(selected['receiver_fixes'])>1500:raise ValueError('gyro-companion population exceeds finite scope')
        group=groups[sid]
        if group['source_sha256']!=row['source_sha256']:raise ValueError('grouping source mismatch')
        meta={k:row[k] for k in ('segment_id','filename','source_sha256','imu_type','duration_s','start_utc','end_utc')}
        meta.update(group_id=group['group_id'],shared_leg_id=group['shared_leg_id'],mounting_epoch=selected['signature'],
            physical_instrument_id=group['physical_instrument_id'],installation_id=group['installation_id'])
        records.append(dict(identity=sid,kind='observed',metadata=meta,cache_path=str(path.relative_to(ROOT))));paths.append(path)
    return records,{str(path.relative_to(ROOT)):sha(path) for path in paths}


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import ilvis0_gyro_prediction
    records,inputs=prepare_inputs()
    sources={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    sources.update('analysis/tests/'+name for name in ('ilvis0_gyro_companion_v2_worker.py','test_ilvis0_gyro_companion_v2_worker.py',
        'test_ilvis0_gyro_prediction.py','ilvis0_channel_envelope_worker.py','run_numerical.py'))
    sources.update(['docs/ilvis0-gyro-companion-v2/PLAN.md','docs/GYRO_PREDICTION.md'])
    hashes={name:sha(ROOT/name) for name in sorted(sources)}
    for name in hashes:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version='raw-gyro-companion-v1',sources=hashes,inputs=inputs,environment=environment(),limits=LIMITS,
        tasks=CONTROLS+records,scenarios=SCENARIOS,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS));return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['scenarios']!=SCENARIOS:
        raise ValueError('gyro-companion scope/environment changed')
    if manifest['tasks'][:48]!=CONTROLS or len(manifest['tasks'])!=101:raise ValueError('frozen gyro tasks changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('gyro authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('gyro source changed: '+name)
    for name,digest in manifest['inputs'].items():
        if sha(ROOT/name)!=digest:raise ValueError('gyro descriptive input changed: '+name)
    return manifest


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged gyro companion cannot restart')
        manifest=verify();started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s'];rows=[];controls=[];terminal=None
        selections={r['segment']['segment_id']:r['segment'] for r in load(BASE/'selection.json.gz')['selected']}
        charged=dict(controls=0,observed=0,scenarios=0,bin_scenario_projections=0)
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        try:
            for task in manifest['tasks']:
                check_time(deadline);identity=task['identity'];kind=task['kind']
                if kind=='observed':
                    require_controls(controls)
                    if charged['observed']>=53 or charged['scenarios']+243>12879:raise ValueError('gyro observed allowance exhausted')
                write(DATA/'charges'/(identity+'.json'),dict(identity=identity,kind=kind,maximum_controls=1 if kind=='control' else 0,
                    maximum_scenarios=243 if kind=='observed' else 0,maximum_bin_scenario_projections=243000 if kind=='observed' else 0,
                    manifest_sha256=sha(DATA/'manifest.json')))
                charged['controls' if kind=='control' else 'observed']+=1
                if kind=='observed':charged['scenarios']+=243;charged['bin_scenario_projections']+=243000
                write(DATA/'status.json',dict(state='running',identity=identity,total=101,numerical_threads=4,pid=os.getpid()),replace=True)
                try:
                    result=control(task) if kind=='control' else observed(task['metadata'],selections[identity],load(ROOT/task['cache_path']),deadline)
                    if kind=='control':controls.append(result)
                    passed=result['passed'] if kind=='control' else result['supported']
                except AllowanceExhausted as error:result=dict(error=str(error),scientific_decision='abstain');passed=False;terminal=str(error)
                except Exception as error:result=dict(error=type(error).__name__+': '+str(error),scientific_decision='abstain');passed=False
                artifact='results/'+identity+('.json' if kind=='control' else '.json.gz');write(DATA/artifact,dict(result,identity=identity,kind=kind))
                rows.append(dict(identity=identity,kind=kind,passed=passed,artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)),replace=True)
                if terminal:break
                if kind=='control' and not passed:terminal='independent control failed; observed stage blocked';break
        except AllowanceExhausted as error:terminal=str(error)
        state='terminal' if terminal else 'complete'
        write(DATA/'summary.json',dict(state=state,passed=len(rows)==101 and all(r['passed'] for r in rows) and not terminal,
            results=rows,elapsed_s=time.time()-started,terminal_reason=terminal,charged=charged,native_evaluations=0,
            original_reads=0,optimizer_starts=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=101,numerical_threads=0),replace=True)
    publish()


def _csv_bytes(rows):
    if not rows:return b''
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for row in rows for k in row)))
    writer.writeheader();writer.writerows(rows);return stream.getvalue().encode()


def plot(baselines):
    os.environ.setdefault('MPLCONFIGDIR','/tmp/local-level-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels=dict(sphere_rotating='Globe + specified field',sphere_still='Globe, zero field',flat_still='Flat, zero field')
    colors=dict(sphere_rotating='#186e7b',sphere_still='#bd7921',flat_still='#776b9c')
    fig,ax=plt.subplots(figsize=(10,8));fig.patch.set_facecolor('#fcfcfa');ax.set_facecolor('#fcfcfa')
    values=[r[k] for r in baselines for k in ('predicted_nose_down_dph','observed_nose_down_dph')]
    lo=min(0.,min(values));hi=max(values);padding=max(1.,.08*(hi-lo));lo-=padding;hi+=padding
    ax.plot([lo,hi],[lo,hi],color='#65717b',linewidth=1.,linestyle='--',label='Equal predicted and observed rates')
    for model in MODELS:
        rows=[r for r in baselines if r['model']==model]
        for imu,marker in (('8','o'),('21','^')):
            selected=[r for r in rows if r['imu_type']==imu]
            ax.scatter([r['predicted_nose_down_dph'] for r in selected],[r['observed_nose_down_dph'] for r in selected],
                s=37,alpha=.7,color=colors[model],marker=marker,label=labels[model] if imu=='8' else None)
    ax.set(xlim=(lo,hi),ylim=(lo,hi),xlabel='Scenario prediction (nose-down degrees/hour)',ylabel='Recorded raw pitch-axis mean (nose-down degrees/hour)')
    ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='upper left',frameon=False,fontsize=9)
    fig.suptitle('Raw gyro rates beside geographic predictions',fontsize=19,fontweight='bold',x=.12,ha='left')
    fig.text(.12,.925,'Level, heading follows candidate course, no upstream removal. No fitted correction.',fontsize=10)
    fig.text(.12,.055,'Same 53 observations shown against three predictions; overlapping records are not independent votes.',fontsize=9)
    fig.text(.12,.03,'Circles: IMU8. Triangles: IMU21. Aircraft pitching and instrument/processing differences remain in the observations.',fontsize=8)
    fig.subplots_adjust(left=.12,right=.96,bottom=.14,top=.89)
    for extension in ('png','svg'):
        fig.savefig(PUBLIC/('gyro-prediction.'+extension),dpi=170,metadata={'Date':None} if extension=='svg' else None)
    plt.close(fig)


def publish():
    manifest=load(DATA/'manifest.json');summary=load(DATA/'summary.json');completion=load(DATA/'completion.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('gyro completion changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];baselines=[];scenarios=[];records=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('gyro saved result changed')
        result=load(DATA/row['artifact']);names.extend([row['artifact'],'charges/'+row['identity']+'.json'])
        if row['kind']=='observed':
            records.append(result)
            for target,key in ((baselines,'baseline'),(scenarios,'scenario_results')):
                target.extend(dict(result['metadata'],**r) for r in result.get(key,[]))
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    (PUBLIC/'baseline-comparisons.csv').write_bytes(_csv_bytes(baselines))
    (PUBLIC/'scenario-comparisons.csv.gz').write_bytes(gzip.compress(_csv_bytes(scenarios),mtime=0))
    if baselines:plot(baselines);names+=['gyro-prediction.png','gyro-prediction.svg']
    lines=['# Raw gyroscope rates and geographic predictions','',
        f"Completed {sum(r['kind']=='control' and r['passed'] for r in summary['results'])}/48 independent controls and "
        f"{sum(r.get('supported',False) for r in records)}/53 saved-stretch comparisons. No fits or original-file reads.",'',
        '![Raw observed rates beside level/course predictions](gyro-prediction.png)' if baselines else 'No qualified comparison plot is available.','',
        'The plot uses a declared level attitude, heading equal to each candidate’s receiver-derived course, and no upstream removal. '
        'All three predictions use the same raw gyro observations. Differences include unresolved aircraft motion, mounting and instrument processing. '
        'They are not independent estimates of those effects or a new scientific decision.','',
        '| Candidate | Stretches | Median absolute observed − scenario difference |','|---|---:|---:|']
    import statistics
    for model in MODELS:
        rows=[r for r in baselines if r['model']==model]
        difference=statistics.median(abs(r['observed_minus_scenario_dph']) for r in rows) if rows else None
        lines.append(f"| {model} | {len(rows)} | {difference:.3f} degrees/hour |" if difference is not None else f'| {model} | 0 | unavailable |')
    lines+=['','[Every baseline comparison and source/group metadata](baseline-comparisons.csv) · [All fixed scenarios](scenario-comparisons.csv.gz) · '
        '[Frozen method and limits](PLAN.md) · [Original raw gyro plot](../ilvis0-gyro-overview/README.md).','',
        'The 243 scenarios per stretch vary declared crab, roll, pitch and processing. Their span is not a confidence interval '
        'or an exhaustive aircraft-motion envelope. No gyro bias/gain, field magnitude or aircraft attitude is fitted. '
        'Group-1 fused navigation is not used for prediction or motion subtraction. The preserved mounting transformation remains a legacy interpretation.','',
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names+=['README.md','PLAN.md','baseline-comparisons.csv','scenario-comparisons.csv.gz']
    names+=['source-freeze/'+n for n in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen 48 controls and all 53 descriptive comparisons; no evaluation.')
    elif args.run:run();print('Finite gyro-prediction companion finished; inspect saved results.')
    else:publish();print('Published saved gyro comparisons; no prediction evaluations or fits.')


if __name__=='__main__':main()
