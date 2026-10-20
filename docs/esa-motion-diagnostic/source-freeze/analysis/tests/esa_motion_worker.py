# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite known-motion qualification and receiver-only development diagnostic."""
import argparse
import csv
import fcntl
import gzip
import io
import math
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_channel_envelope_worker import sha,load,write,environment
from lll.ilvis0_receipt_journal import durable_write

NAME='esa-motion-diagnostic-v1-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/esa-motion-diagnostic'
PARENT=ROOT/'docs/esa-development-selection'
SOURCE=ROOT/'data/external-imu-survey-20261018/esa-sample/187_air1_ppp_2Hz_final.txt'
SEED=2026101911
TASKS=[dict(identity='exact-motion',kind='exact')]+[
    dict(identity=f'sd-{sigma:g}-rho-{rho:g}',kind='coverage',sigma=sigma,rho=rho,realizations=256)
    for sigma in (.01,.05,.2) for rho in (0.,.8,.98)]+[dict(identity='receiver-windows-187',kind='observed')]
LIMITS=dict(maximum_identities=11,maximum_exact_paths=24,maximum_realizations=2304,maximum_observed_windows=2048,
    maximum_receiver_epochs=100000,maximum_wall_s=300,numerical_threads=4,receiver_files=1,raw_imu_reads=0,
    optimizer_starts=0,native_evaluations=0,retries=0,deadline_policy='cooperative-no-signals')
INPUTS=['docs/esa-development-selection/manifest.json','docs/esa-development-selection/evidence-receipt.json',
    'docs/esa-development-selection/inventory/selection.json.gz','docs/analysis-provenance/ledger.json',
    'docs/external-imu-data/ESA_CONFIRMATION_POLICY.json',str(SOURCE.relative_to(ROOT))]


class AllowanceExhausted(BaseException):pass


def check_time(deadline):
    if time.monotonic()>=deadline:raise AllowanceExhausted('cooperative wall allowance exhausted')


def reference_coefficients(times,velocity):
    """Separate centered sums, not the estimator's normal-equation solve."""
    import numpy as np
    t=np.asarray(times,float);v=np.asarray(velocity,float);mean=math.fsum(t)/len(t)
    denominator=math.fsum((x-mean)**2 for x in t);result=[]
    for axis in (0,1):
        average=math.fsum(v[:,axis])/len(t)
        slope=math.fsum((x-mean)*(y-average) for x,y in zip(t,v[:,axis]))/denominator
        result.append((average-slope*mean,slope))
    return np.array([[r[0] for r in result],[r[1] for r in result]])


def analytic_path(heading,turn,climb=0.,nonuniform=False):
    import numpy as np
    t=np.linspace(-5.,5.,21)
    if nonuniform:t+=.02*np.sin(np.linspace(0.,np.pi,21))*np.sin(np.arange(21)*.8)
    angles=[math.radians(heading+turn*x) for x in t]
    velocity=np.array([[60.*math.cos(a),60.*math.sin(a)] for a in angles])
    return t,velocity,np.full(len(t),climb)


def exact_controls():
    import numpy as np
    from lll.airquantumgrav_motion import assess
    results=[]
    for heading in (0.,90.,359.9):
        for turn in (-.06,0.,.02,.06):
            for climb in (-2.,2.):
                t,v,up=analytic_path(heading,turn,climb,nonuniform=True)
                covariance=np.tile(np.eye(3)*.01**2,(len(t),1,1))
                result=assess(t,v,up,covariance,center_s=0.)
                reference=reference_coefficients(t,v)
                error=float(np.max(abs(np.array([result['intercept_ne_mps'],result['slope_ne_mps2']])-reference)))
                results.append(dict(heading_deg=heading,turn_deg_s=turn,climb_mps=climb,coefficient_error=error,
                    instantaneous_discrepancy_deg_s=abs(result['course_rate_deg_s']-turn),
                    passed=error<1e-10 and result['median_abs_vertical_speed_mps']==abs(climb)))
    return dict(passed=len(results)==24 and all(r['passed'] for r in results),exact_paths=len(results),
        maximum_coefficient_error=max(r['coefficient_error'] for r in results),results=results)


def coverage_fixture(sigma,rho):
    import numpy as np
    if sigma not in (.01,.05,.2) or rho not in (0.,.8,.98):raise ValueError('predeclared control family required')
    t=np.linspace(-5.,5.,21);tau=None if rho==0. else -.5/math.log(rho)
    corr=np.eye(len(t)) if tau is None else np.exp(-abs(t[:,None]-t[None,:])/tau)
    covariance=sigma**2*np.array([[1.,.25,0.],[.25,1.4,0.],[0.,0.,.8]])
    return dict(sigma=sigma,rho=rho,index=(.01,.05,.2).index(sigma)*3+(0.,.8,.98).index(rho),times=t,
        time_constant_s=tau,time_root=np.linalg.cholesky(corr),axis_root=np.linalg.cholesky(covariance[:2,:2]),
        covariance=np.tile(covariance,(len(t),1,1)))


def generated(case,replicate):
    import numpy as np
    rate=(0.,.06,0.,-.06)[replicate%4];heading=(replicate%3)*120.
    t,truth,up=analytic_path(heading,rate)
    rng=np.random.default_rng(np.random.SeedSequence([SEED,case['index'],replicate]))
    noise=case['time_root']@rng.normal(size=(len(t),2))@case['axis_root'].T
    observed=np.round(truth+noise,3);reference=reference_coefficients(t,truth)
    origin,change=reference
    target=math.degrees((origin[0]*change[1]-origin[1]*change[0])/float(origin@origin))
    return dict(replicate=replicate,times=t,truth_velocity_ne=truth,observed_velocity_ne=observed,vertical_mps=up,
        covariance=case['covariance'],true_window_rate_deg_s=target,instantaneous_rate_deg_s=rate,
        seed=[SEED,case['index'],replicate])


def coverage_bound(total,covered):
    from scipy.stats import beta
    if not 0<=covered<=total or total<1:raise ValueError('valid coverage counts required')
    lower=float(beta.ppf(.01,covered,total-covered+1)) if covered else 0.
    return dict(covered=covered,realizations=total,exact_99pct_lower=lower,passed=lower>=.95)


def center_indices(total,maximum=2048):
    import numpy as np
    if total<1 or maximum<1:raise ValueError('positive finite sampling scope required')
    return np.unique(np.linspace(0,total-1,min(total,maximum),dtype=int)).tolist()


def window_indices(times,sequence,index):
    import numpy as np
    t=np.asarray(times,float);sequence=np.asarray(sequence);lower=t[index]-5.;upper=t[index]+5.
    if lower<t[0] or upper>t[-1]:return None
    a=int(np.searchsorted(t,lower,side='left'));b=int(np.searchsorted(t,upper,side='right'))
    first=a if t[a]==lower else a-1;last=b-1 if t[b-1]==upper else b
    if first<0 or last>=len(t) or b-a<3:return None
    if np.any(np.diff(t[first:last+1])>.75) or np.any(np.diff(sequence[first:last+1])!=1):return None
    return a,b


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import airquantumgrav_motion,evidence_groups
    from airquantumgrav_selection_worker import development_group
    files={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    files.update('analysis/tests/'+name for name in ('esa_motion_worker.py','airquantumgrav_selection_worker.py',
        'ilvis0_channel_envelope_worker.py','run_numerical.py','test_airquantumgrav_motion.py',
        'test_airquantumgrav_velocity_reader.py','test_airquantumgrav_receiver.py','test_esa_motion_worker.py'))
    files.add('docs/esa-motion-diagnostic/PLAN.md')
    sources={name:sha(ROOT/name) for name in sorted(files)};inputs={name:sha(ROOT/name) for name in INPUTS}
    group=development_group(load(ROOT/INPUTS[3]),'187_rqh01.txt')
    policy=load(ROOT/INPUTS[4])
    if '187_rqh01.txt' not in policy['development_files'] or '187_rqh01.txt' in policy['confirmation_files']:
        raise ValueError('recording 187 must remain development-only')
    parent=load(PARENT/'manifest.json');receipt=load(PARENT/'evidence-receipt.json')
    if sha(PARENT/'inventory/selection.json.gz')!=receipt['artifacts']['inventory/selection.json.gz']:
        raise ValueError('parent selection evidence changed')
    if inputs[str(SOURCE.relative_to(ROOT))]!=parent['inputs'][str(SOURCE.relative_to(ROOT))]:raise ValueError('receiver source changed')
    for name in sources:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    for name in INPUTS[:-1]:
        target=DATA/'input-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version='esa-receiver-motion-diagnostic-v1',sources=sources,inputs=inputs,
        environment=environment(),limits=LIMITS,plan=dict(tasks=TASKS,numerical_threads=4),seed=SEED,
        group_id=group,imu_support_s=parent['imu_support_s'],scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['plan']['tasks']!=TASKS:
        raise ValueError('frozen environment or finite scope changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('frozen source changed: '+name)
    for name,digest in manifest['inputs'].items():
        if sha(ROOT/name)!=digest:raise ValueError('frozen input changed: '+name)
    return manifest


def coverage_control(task,deadline):
    from lll.airquantumgrav_motion import assess
    case=coverage_fixture(task['sigma'],task['rho']);records=[]
    counts={key:0 for key in ('independent','arbitrary_correlation','supplied_correlation')}
    unsupported=dict(counts);false_flags={'adjacent':0,'trend':0};missed=dict(false_flags);quiet=0;turns=0
    try:
        for i in range(task['realizations']):
            check_time(deadline);write(DATA/'realization-charges'/task['identity']/f'{i:04d}.json',dict(replicate=i,seed=SEED))
            sample=generated(case,i);record=dict(sample=sample);records.append(record)
            result=assess(sample['times'],sample['observed_velocity_ne'],sample['vertical_mps'],sample['covariance'],
                center_s=0.,time_constant_s=case['time_constant_s'])
            record['result']=result
            for name in counts:
                actual='independent' if name=='supplied_correlation' and case['rho']==0. else name
                interval=result['intervals'][actual];unsupported[name]+=int(not interval['supported'])
                counts[name]+=int(interval['supported'] and interval['lower_deg_s']<=sample['true_window_rate_deg_s']<=interval['upper_deg_s'])
            turning=abs(sample['true_window_rate_deg_s'])>.02;turns+=int(turning);quiet+=int(not turning)
            for name,key in (('adjacent','adjacent_median_abs_course_rate_deg_s'),('trend','course_rate_deg_s')):
                flag=result[key] is None or abs(result[key])>.02
                false_flags[name]+=int(not turning and flag);missed[name]+=int(turning and not flag)
    finally:write(DATA/'generated'/(task['identity']+'.json.gz'),dict(sigma=case['sigma'],rho=case['rho'],records=records))
    bounds={name:dict(coverage_bound(task['realizations'],value),unsupported=unsupported[name]) for name,value in counts.items()}
    return dict(passed=all(bounds[name]['passed'] and unsupported[name]==0 for name in ('supplied_correlation','arbitrary_correlation')),
        coverage=bounds,quiet_cases=quiet,turn_cases=turns,false_exclusions=false_flags,missed_turns=missed,
        independence_assumption_valid=case['rho']==0.,scientific_decision='abstain')


def observed_control(manifest,deadline):
    import numpy as np
    from lll.airquantumgrav_motion import assess,velocity_records
    rows=[]
    with SOURCE.open('rb') as stream:
        for row in velocity_records(stream):
            check_time(deadline)
            if len(rows)>=LIMITS['maximum_receiver_epochs']:raise ValueError('receiver epoch allowance exhausted')
            rows.append(row)
    times=np.array([r['time_s'] for r in rows]);sequence=np.array([r['sequence'] for r in rows])
    saved=load(PARENT/'inventory/selection.json.gz')
    if saved['total_receiver_epochs']!=len(rows):raise ValueError('receiver selection alignment changed')
    records=[];flat=[]
    for index in center_indices(len(rows),LIMITS['maximum_observed_windows']):
        check_time(deadline);row=rows[index];window=window_indices(times,sequence,index)
        base=dict(index=index,time_s=row['time_s'],gps_week=row['gps_week'],utc_date=row['utc_date'],utc_time=row['utc_time'],
            version1_reasons=saved['epoch_reasons'][index])
        if window is None:
            records.append(dict(base,supported=False,reason='unsupported_receiver_window'));flat.append(dict(index=index,supported=False));continue
        a,b=window;selected=rows[a:b];v=np.array([[r['north_mps'],r['east_mps']] for r in selected])
        covariance=np.array([r['velocity_covariance_m2_s2'] for r in selected]);up=np.array([r['up_mps'] for r in selected])
        result=assess(times[a:b],v,up,covariance,center_s=row['time_s'])
        imu_support=manifest['imu_support_s'][0]<=row['time_s']-5. and row['time_s']+5.<=manifest['imu_support_s'][1]
        airborne=bool(np.min(np.hypot(v[:,0],v[:,1]))>=50.) and imu_support
        record=dict(base,supported=True,first_index=a,last_index=b-1,airborne_supported=airborne,
            input_velocity_ne=v,reported_covariance=covariance,input_up_mps=up,result=result);records.append(record)
        line=dict(index=index,time_s=row['time_s'],supported=True,airborne_supported=airborne,
            version1_motion_failed='motion_window' in base['version1_reasons'],mean_speed_kmh=result['mean_speed_mps']*3.6,
            vertical_median_mps=result['median_abs_vertical_speed_mps'],adjacent_abs_rate_deg_s=result['adjacent_median_abs_course_rate_deg_s'],
            trend_rate_deg_s=result['course_rate_deg_s'],
            median_reported_north_sd_mps=float(np.median(np.sqrt(covariance[:,0,0]))) if np.all(covariance[:,0,0]>0.) else None,
            median_reported_east_sd_mps=float(np.median(np.sqrt(covariance[:,1,1]))) if np.all(covariance[:,1,1]>0.) else None,
            residual_north_rms_mps=result['residual_rms_ne_mps'][0],residual_east_rms_mps=result['residual_rms_ne_mps'][1],
            residual_north_lag1=result['residual_lag1_ne'][0],residual_east_lag1=result['residual_lag1_ne'][1])
        for name,interval in result['intervals'].items():
            line[name+'_supported']=interval['supported']
            line[name+'_lower_deg_s']=interval.get('lower_deg_s');line[name+'_upper_deg_s']=interval.get('upper_deg_s')
        flat.append(line)
    write(DATA/'generated/receiver-windows-187.json.gz',dict(receiver_epochs=len(rows),records=records))
    fields=list(dict.fromkeys(k for row in flat for k in row));out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=fields)
    writer.writeheader();writer.writerows(flat);durable_write(DATA/'observed-windows.csv',out.getvalue().encode())
    supported=[r for r in flat if r.get('supported')];airborne=[r for r in supported if r['airborne_supported']]
    def summary(subset):
        counts=dict(windows=len(subset),adjacent_turn_flags=0,trend_turn_flags=0,climb_flags=0,independent_quiet=0,
            arbitrary_quiet=0,independent_ambiguous=0,arbitrary_ambiguous=0)
        for row in subset:
            counts['adjacent_turn_flags']+=int(row['adjacent_abs_rate_deg_s'] is None or row['adjacent_abs_rate_deg_s']>.02)
            counts['trend_turn_flags']+=int(row['trend_rate_deg_s'] is None or abs(row['trend_rate_deg_s'])>.02)
            counts['climb_flags']+=int(row['vertical_median_mps']>1.)
            for name,label in (('independent','independent'),('arbitrary_correlation','arbitrary')):
                okay=row[name+'_supported'];low=row[name+'_lower_deg_s'];high=row[name+'_upper_deg_s']
                quiet=okay and low>=-.02 and high<=.02
                turn=okay and (low>.02 or high<-.02)
                counts[label+'_quiet']+=int(quiet);counts[label+'_ambiguous']+=int(not quiet and not turn)
        return counts
    return dict(passed=True,receiver_epochs=len(rows),selected_centers=len(records),unsupported_centers=len(records)-len(supported),
        all_windows=summary(supported),airborne_windows=summary(airborne),selection_changed=False,
        scientific_decision='abstain',reported_covariance_verified=False)


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged receiver diagnostic cannot restart')
        manifest=verify();started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s']
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')));rows=[];terminal=None
        try:
            for task in TASKS:
                check_time(deadline)
                if task['kind']=='observed' and (len(rows)!=10 or not all(r['passed'] for r in rows)):break
                identity=task['identity'];write(DATA/'charges'/(identity+'.json'),dict(task,manifest_sha256=sha(DATA/'manifest.json')))
                write(DATA/'status.json',dict(state='running',identity=identity,total=11,numerical_threads=4,pid=os.getpid()),replace=True)
                try:
                    if task['kind']=='exact':result=exact_controls()
                    elif task['kind']=='coverage':result=coverage_control(task,deadline)
                    else:result=observed_control(manifest,deadline)
                    check_time(deadline)
                except AllowanceExhausted as error:result=dict(passed=False,error=str(error));terminal=str(error)
                except Exception as error:result=dict(passed=False,error=type(error).__name__+': '+str(error))
                artifacts=[]
                for name in ('generated/'+identity+'.json.gz','observed-windows.csv' if task['kind']=='observed' else ''):
                    if name and (DATA/name).exists():artifacts.append(dict(artifact=name,sha256=sha(DATA/name)))
                result['artifacts']=artifacts;artifact='results/'+identity+'.json';write(DATA/artifact,dict(task,**result))
                rows.append(dict(task,passed=result['passed'],artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)),replace=True)
                if terminal:break
        except AllowanceExhausted as error:terminal=str(error)
        state='terminal' if terminal else 'complete';elapsed=time.time()-started
        write(DATA/'summary.json',dict(state=state,passed=len(rows)==11 and all(r['passed'] for r in rows) and not terminal,
            results=rows,elapsed_s=elapsed,wall_overrun_s=max(0.,elapsed-LIMITS['maximum_wall_s']),terminal_reason=terminal,
            optimizer_starts=0,native_evaluations=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=11,numerical_threads=0),replace=True)
    publish()


def publish():
    completion=load(DATA/'completion.json');summary=load(DATA/'summary.json');manifest=load(DATA/'manifest.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):
        raise ValueError('completed diagnostic changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('diagnostic result changed')
        names.extend([row['artifact'],'charges/'+row['identity']+'.json']);result=load(DATA/row['artifact']);results.append(result)
        for item in result['artifacts']:
            if sha(DATA/item['artifact'])!=item['sha256']:raise ValueError('diagnostic artifact changed')
            names.append(item['artifact'])
    names+=sorted(str(path.relative_to(DATA)) for path in (DATA/'realization-charges').glob('*/*.json'))
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    shutil.copytree(DATA/'input-freeze',PUBLIC/'input-freeze',dirs_exist_ok=True)
    lines=['# Receiver-motion diagnostic','',
        f"**{sum(r['passed'] for r in results)}/{len(TASKS)} identities passed** in {summary['elapsed_s']:.2f} seconds. "
        'No raw inertial reads, Earth-model fits or native integrations. Version-1 eligibility is unchanged.','',
        '| Velocity SD | Half-second correlation | Supplied-family coverage | Arbitrary-correlation coverage | False turn flags, adjacent / trend | Missed turns, adjacent / trend |',
        '|---:|---:|---:|---:|---:|---:|']
    for result in results:
        if 'coverage' in result:
            a=result['coverage']['supplied_correlation'];b=result['coverage']['arbitrary_correlation']
            f=result['false_exclusions'];m=result['missed_turns']
            lines.append(f"| {result['sigma']} m/s | {result['rho']} | {a['covered']}/{a['realizations']} | {b['covered']}/{b['realizations']} | "
                f"{f['adjacent']}/{f['trend']} of {result['quiet_cases']} | {m['adjacent']}/{m['trend']} of {result['turn_cases']} |")
        if result['kind']=='observed' and result['passed']:
            a=result['airborne_windows']
            lines+=['',f"Receiver diagnostic: {result['selected_centers']} fixed centers, {result['unsupported_centers']} unsupported; "
                f"{a['windows']} complete windows meet airborne speed and IMU-time support.",'',
                f"Among those windows, adjacent differences flag {a['adjacent_turn_flags']} for turning; the trend point estimate flags {a['trend_turn_flags']}. "
                f"Median vertical speed exceeds 1 m/s in {a['climb_flags']} windows.",'',
                f"Under reported marginal covariance and Gaussian errors, {a['independent_quiet']} trend intervals lie wholly within ±0.02°/s "
                f"assuming temporal independence, versus {a['arbitrary_quiet']} allowing arbitrary temporal correlation. "
                f"Ambiguous intervals: {a['independent_ambiguous']} and {a['arbitrary_ambiguous']}, respectively.",'',
                '[Every sampled window](observed-windows.csv).']
    lines+=['','Generated controls test the noise-free window trend, not arbitrary instantaneous motion. '
        'Receiver covariance and temporal assumptions are not observationally calibrated. A smoother point estimate '
        'does not establish steady flight or create eligible intervals.','',
        '[Frozen question and limits](PLAN.md) · [Original selection](../esa-development-selection/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names+=['PLAN.md','README.md']
    names+=['source-freeze/'+name for name in manifest['sources']]+['input-freeze/'+name for name in INPUTS[:-1]]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen eleven bounded diagnostic identities; no execution.')
    elif args.run:run();print('Finite receiver-motion diagnostic finished; inspect saved gates.')
    else:publish();print('Published saved diagnostic; no calculations.')


if __name__=='__main__':main()
