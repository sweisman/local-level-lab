# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite matched horizontal-only archival refits; never changes production findings."""
import argparse
import csv
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_projected_controls_worker import environment,sha,write
from lll.ilvis0_receipt_journal import durable_write,encoded
from lll import ilvis0_horizontal_observed as policy

NAME='ilvis0-horizontal-observed-20261018'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
QUALIFIED=ROOT/'docs/ilvis0-horizontal-pair-continuation-20261018'
INVENTORY=ROOT/'docs/ilvis0-contribution-inventory-20261018'
BASELINE=ROOT/'docs/ilvis0-highspeed-segments-20261008'
CONTEXT=ROOT/'data/ilvis0-followup-20261007/summary.json'


def load(path):
    raw=Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def require_sources(sources):
    for p,digest in sources.items():
        if sha(ROOT/p)!=digest:raise ValueError('qualified source changed: '+p)


def require_qualification(summary):
    expected={(m,c,s) for m in policy.MODELS for c in policy.CASES for s in ('zero','opposed')}
    primaries=summary.get('primaries',[]);pairs=summary.get('pairs',[])
    if (summary.get('passed') is not True or len(summary.get('results',[]))!=2
            or not all(r['passed'] for r in summary['results']) or len(primaries)!=12
            or {(r['model'],r['case_id'],r['start']) for r in primaries}!=expected
            or not all(r['passed'] for r in primaries) or len(pairs)!=6
            or {(r['model'],r['case_id']) for r in pairs}!={(m,c) for m in policy.MODELS for c in policy.CASES}
            or not all(r['passed'] for r in pairs)):
        raise ValueError('complete passed horizontal software qualification required')


def require_preflight(expected,rows):
    if (len(rows)!=len(expected) or {r['identity'] for r in rows}!=set(expected)
            or not all(r['passed'] for r in rows)):
        raise ValueError('every exact baseline system must reproduce before fitting')


def checked_publication(path):
    done=load(path/'completion.json')
    if done['manifest_sha256']!=sha(path/'manifest.json') or done['summary_sha256']!=sha(path/'summary.json'):
        raise ValueError('parent completion hash mismatch: '+str(path))
    for filename,digest in load(path/'evidence-receipt.json')['artifacts'].items():
        if sha(path/filename)!=digest:raise ValueError('parent publication hash mismatch')


def project_source(name):
    path=Path(name)
    if path.is_absolute():
        if path.is_relative_to(ROOT):path=path.relative_to(ROOT)
        elif 'analysis' in path.parts:path=Path(*path.parts[path.parts.index('analysis'):])
        else:raise ValueError('unsupported historical source prefix')
    if '..' in path.parts or not (ROOT/path).is_file():raise ValueError('missing declared project source')
    return str(path)


def verify(*,originals=False):
    m=load(DATA/'manifest.json')
    if m['environment']!=environment():raise ValueError('frozen numerical environment changed')
    if m['plan']!=policy.plan(m['selected']):raise ValueError('finite plan changed')
    for p,digest in {**m['sources'],**m['inputs']}.items():
        if sha(ROOT/p)!=digest:raise ValueError('frozen source/input changed: '+p)
    for p,digest in m['sources'].items():
        if sha(DATA/'source-freeze'/p)!=digest:raise ValueError('source snapshot changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**m['plan']):raise ValueError('allowance changed')
    if originals:
        for p,digest in m['originals'].items():
            if sha(Path(p))!=digest:raise ValueError('original container changed')
    return m


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    checked_publication(QUALIFIED);checked_publication(INVENTORY)
    require_qualification(load(QUALIFIED/'summary.json'))
    require_sources(load(QUALIFIED/'manifest.json')['sources'])
    with (INVENTORY/'inventory.csv').open() as stream:inventory=list(csv.DictReader(stream))
    selection=load(BASELINE/'selection.json.gz');selected=policy.select(selection,inventory);plan=policy.plan(selected)
    tasks=load(INVENTORY/'manifest.json')['tasks']
    baseline={r['segment_id']:r for r in load(BASELINE/'summary.json.gz')['results']}
    contexts={r['task_id']:r for r in load(CONTEXT)['results']}
    references={};provenance={};context={};originals={};inputs={}
    def remember(path):inputs[str(path.relative_to(ROOT))]=sha(path)
    for directory in (QUALIFIED,INVENTORY):
        for n in ('manifest.json','summary.json','completion.json','evidence-receipt.json'):remember(directory/n)
    for p in (INVENTORY/'inventory.csv',BASELINE/'selection.json.gz',BASELINE/'summary.json.gz',CONTEXT):remember(p)
    for chosen in selected:
        sid=chosen['segment']['segment_id'];original=Path(chosen['source_path'])
        if not original.is_relative_to(ROOT/'data/ilvis0-ready'):raise ValueError('documented retained source required')
        originals[str(original)]=sha(original)
        provenance[sid]=baseline[sid]['provenance']
        source=contexts[chosen['task']]
        context[chosen['task']]=dict(timing=source['timing'],inspection=dict(source_sha256=source['inspection']['source_sha256']))
        for case in policy.CASES:
            for model in policy.MODELS:
                task=next(t for t in tasks if (t['segment_id'],t['case_id'],t['model'])==(sid,case,model))
                row=next(r for r in inventory if (r['segment_id'],r['case_id'],r['model'])==(sid,case,model))
                fit=task['fit'];saved=load(ROOT/row['linearization_file'])
                if (fit.get('converged') is not True or saved['active_parameters']!=fit['active_parameters']
                        or saved['normalized_parameters']!=fit['normalized_parameters']):raise ValueError('exact passing reference required')
                for prefix in ('linearization','epoch'):
                    if row.get(prefix+'_file'):
                        p=ROOT/row[prefix+'_file']
                        if sha(p)!=row[prefix+'_sha256']:raise ValueError('declared saved artifact changed')
                        remember(p)
                references['::'.join((sid,case,model))]=dict(active_parameters=fit['active_parameters'],
                    normalized_parameters=fit['normalized_parameters'],residual_sum_squares=fit['residual_sum_squares'],
                    linearization_file=row['linearization_file'],origin=task['origin'])
    tests=['analysis/tests/test_ilvis0_horizontal_observed.py','analysis/tests/test_ilvis0_horizontal_observed_worker.py']
    result=subprocess.run([sys.executable,'-m','pytest',*tests,'-q','--junitxml='+str(DATA/'software-tests.xml')],cwd=ROOT,capture_output=True,text=True,timeout=60)
    (DATA/'software-tests.log').write_text(result.stdout+result.stderr)
    checks=list(ET.parse(DATA/'software-tests.xml').iter('testcase'))
    if result.returncode or len(checks)!=11 or any(list(c) for c in checks):raise ValueError('all eleven preparation controls required')
    sources=dict(load(QUALIFIED/'manifest.json')['sources'])
    for p in load(BASELINE/'manifest.json')['sources']:sources[project_source(p)]=sha(ROOT/project_source(p))
    for p in ['analysis/lll/ilvis0_horizontal_observed.py',*tests,'analysis/tests/ilvis0_horizontal_observed_worker.py',
              'analysis/lll/ilvis0_receipt_journal.py',str((PUBLIC/'PLAN.md').relative_to(ROOT))]:sources[p]=sha(ROOT/p)
    # Include parser/context dependencies explicitly; historical source lists
    # also preserve their original scientific implementation snapshots.
    for name in ('applanix','ilvis0','ilvis0_followup','ilvis0_installation','ilvis0_motion_diagnosis',
                 'ilvis0_segments','ilvis0_corpus_modeling','ilvis0_gps_sensitivity','ilvis0_gnss','gnss_position','ilvis0_forward'):
        p='analysis/lll/'+name+'.py';sources[p]=sha(ROOT/p)
    for p,digest in sources.items():
        if sha(ROOT/p)!=digest:raise ValueError('qualified dependency changed')
        target=DATA/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
    manifest=dict(version=policy.VERSION,environment=environment(),sources=sources,inputs=inputs,originals=originals,
        selected=selected,plan=plan,references=references,contexts=context,provenance=provenance,
        qualified_kernel_metadata=load(QUALIFIED/'summary.json')['kernel_metadata'],scientific_decision='abstain')
    write(DATA/'manifest.json',manifest);write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**plan))
    write(PUBLIC/'SELECTION.json',dict(selected=selected,selection_rule='shortest complete-six-artifact stretch per IMU8/IMU21; no model scores'))
    (PUBLIC/'README.md').write_text('# Horizontal-only recorded-flight development study\n\n'
        +'Prepared two independently selected stretches, one IMU8 and one IMU21. Twelve reconstruction checks must pass before any of the 24 planned optimizer starts. The finite ceiling is 4,860 native calls on four threads; the earlier 53-stretch findings remain unchanged.\n\n'
        +'[Frozen method and limits](PLAN.md) · [What each measurement contributes](../ilvis0-measurement-contribution/README.md).\n')
    return verify()


def make_problem(m,task,arrays,kernel,tangent):
    import numpy as np
    from lll import ilvis0_shape as shape,ilvis0_estimator as estimator,ilvis0_corpus_modeling as corpus
    values,times,gps,covariance=arrays
    seed,force=corpus.initialize(times,gps,values,task['model']);limits=shape.instrument_limits(1.)
    problem=shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,covariance,
        seed,estimator.Bounds(limits),fit_earth_removal=task['profile'],kernel=kernel,tangent_kernel=tangent,
        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
    return problem,force


def package():
    c=load(DATA/'completion.json');s=load(DATA/'summary.json')
    if c['manifest_sha256']!=sha(DATA/'manifest.json') or c['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('completion mismatch')
    names=['manifest.json','authorization.json','summary.json','completion.json','start.json','preflight.json','kernel.json','software-tests.xml','software-tests.log']
    for r in s['results']:
        name=r['identity'].replace('::','-')+'.json.gz'
        if sha(DATA/name)!=r['artifact_sha256']:raise ValueError('fit result hash mismatch')
        names.append(name)
        for prefix in ('linearization','epoch'):
            if prefix+'_file' in r:
                n=r[prefix+'_file']
                if sha(DATA/n)!=r[prefix+'_sha256']:raise ValueError('saved fit array changed')
                names.append(n)
    for n in names:shutil.copy2(DATA/n,PUBLIC/n)
    for label,directory in (('fit',DATA),('preflight',DATA/'preflight')):
        events=directory/'charges'
        chain=[load(p) for p in sorted(events.glob('[0-9]*.json'))]
        payload=dict(events=chain,head=load(events/'HEAD.json'))
        durable_write(PUBLIC/(label+'-charges.json.gz'),gzip.compress(encoded(payload),mtime=0),replace=True)
        names.append(label+'-charges.json.gz')
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Horizontal-only recorded-flight refits','',
        f"Completed {len(s['results'])}/24 fits, with {sum(r['passed'] for r in s['results'])} passing the numerical fit gate. Used {s['native_evaluations']} of 4,860 permitted native calls, including twelve reconstruction checks. The original **53 globe / zero flat / zero unresolved** findings are preserved.",
        '', '| Stretch | IMU configuration | Duration (min) | Horizontal-only matched result | Passed repeat pairs |', '|---|---:|---:|---|---:|']
    for r in s['comparisons']:
        profile=r['profile'];label=profile.get('shape_preference',profile.get('conditional_shape_preference','see detailed comparison'))
        lines.append(f"| {r['segment_id']} | {r['imu_type']} | {r['duration_s']/60:.2f} | {label} | {sum(p['passed'] for p in r['pairs'])}/6 |")
    lines+=['','These are development refits under assumed covariance and calibration limits. Horizontal-only scoring retains heights in initialization, covariance and propagation, as well as both IMU channels. An unresolved fit or repeat withholds the matched comparison; it is not equal model support.',
        '', '[Frozen selection, method and allowance](PLAN.md) · [Measurement-contribution study](../ilvis0-measurement-contribution/README.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names+=['README.md','PLAN.md','SELECTION.json']
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names}))


def run():
    m=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists() or (DATA/'completion.json').exists():raise ValueError('charged or completed observed batch cannot restart')
        verify(originals=True);write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        write(DATA/'status.json',dict(state='extracting',pid=os.getpid(),allocated_numerical_threads=4,total=24,completed=0))
        import numpy as np
        from lll import ilvis0_exploratory as explore,ilvis0_precision as precision,ilvis0_segments as segments
        from lll import ilvis0_gps_sensitivity as sensitivity,ilvis0_projected_ridge as candidate,ilvis0_shape as shape
        from lll.ilvis0_projected_fitting import ProjectedProblem
        from lll.ilvis0_solver_position import physical_metric
        from lll.ilvis0_receipt_journal import Ledger
        started=time.monotonic();rows=[];preflight=[];book=None;pre=None
        def alarm(*args):raise TimeoutError('eight-hour study allowance exceeded')
        previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(28800)
        try:
            kernel,kmeta=explore.load_kernel(DATA/'kernel');tangent,tmeta=precision.load_tangent(DATA/'kernel')
            expected=m['qualified_kernel_metadata']
            for label,current in (('value',kmeta),('tangent',tmeta)):
                for key in ('source_sha256','compiler','flags','internal_mantissa_bits'):
                    if key in expected[label] and current.get(key)!=expected[label][key]:raise ValueError('qualified kernel configuration changed')
            write(DATA/'kernel.json',dict(value=kmeta,tangent=tmeta))
            arrays={};problems={};force={};assumption=next(a for a in sensitivity.assumptions() if a.name=='h1_v3_tau60')
            for chosen in m['selected']:
                sid=chosen['segment']['segment_id']
                values,times,gps,provenance=segments.extract_segment(Path(chosen['source_path']),m['contexts'][chosen['task']],chosen['segment'])
                if provenance!=m['provenance'][sid]:raise ValueError('saved extraction provenance did not reproduce')
                covariance=sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1)),assumption)
                arrays[sid]=(values,times,gps,covariance)
            diagnostic_ids=list(m['references']);digest=sha(DATA/'manifest.json')
            pre=Ledger(DATA/'preflight',digest,diagnostic_ids,fit_limit=1,diagnostic_limit=1)
            for key,reference in m['references'].items():
                sid,case,model=key.split('::');task=dict(segment_id=sid,case_id=case,model=model,profile=case=='bias1_profiled_removal')
                full,f=make_problem(m,task,arrays[sid],kernel,tangent);point=np.array(reference['normalized_parameters'])
                if list(full.bounds.active)!=reference['active_parameters']:raise ValueError('reference parameter order changed')
                pre.start(key);r,j,_=pre.call(key,'diagnostic','tangent',full.residual_tangent,point,model)
                saved=load(ROOT/reference['linearization_file']);check=policy.reproduction(r,j,saved)
                projected=ProjectedProblem(full,('latitude','longitude'));pr,_=projected.projection.apply(r,j)
                check.update(identity=key,projected_reference_cost=float(pr@pr));preflight.append(check)
                write(DATA/'preflight.json',preflight)
                problems[key]=full;force[key]=f
            require_preflight(diagnostic_ids,preflight);pre.export()
            book=Ledger(DATA,digest,[t['identity'] for t in m['plan']['tasks']],fit_limit=200,diagnostic_limit=2)
            class Counted:
                def __init__(self,base,identity):
                    self.base=base;self.identity=identity;self.bounds=base.bounds;self.gps=base.gps;self.cholesky=base.cholesky
                    self.fit_calls=0;self.diagnostic_calls=0
                def residual_tangent(self,u,model):
                    self.fit_calls+=1
                    return book.call(self.identity,'fit','tangent',self.base.residual_tangent,u,model)
                def prediction(self,u,model):
                    self.diagnostic_calls+=1
                    return book.call(self.identity,'diagnostic','tangent',self.base.prediction_tangent,u,model)[0]
            for task in m['plan']['tasks']:
                verify();identity=task['identity'];sid=task['segment_id'];key='::'.join((sid,task['case_id'],task['model']))
                full=problems[key];reference=m['references'][key];gps=arrays[sid][2];times=arrays[sid][1]
                write(DATA/'status.json',dict(state='fitting',pid=os.getpid(),allocated_numerical_threads=4,total=24,completed=len(rows),identity=identity,
                    native_evaluations=len(book.read('sweeps'))+12))
                book.start(identity);counted=Counted(full,identity);row=dict(task);begin=time.monotonic()
                try:
                    point=np.array(reference['normalized_parameters'])
                    initial=point.copy() if task['role']=='primary' else np.zeros(len(point))
                    if task['role']=='repeat':
                        for i,name in enumerate(full.bounds.active):
                            if name.startswith('accel_gain'):initial[i]=np.clip((force[key]/9.81-1)/full.bounds.limits[name],-.9,.9)
                            if name=='earth_removal':initial[i]=-1.
                    projected=ProjectedProblem(counted,('latitude','longitude'))
                    fit=candidate.fit_control(projected,task['model'],start=initial,maximum_evaluations=200)
                    if fit['evaluations']!=counted.fit_calls:raise ValueError('fit call accounting mismatch')
                    if task['role']=='primary':
                        expected_cost=next(p['projected_reference_cost'] for p in preflight if p['identity']==key)
                        if abs(fit['initial_cost']-expected_cost)>1e-6*max(expected_cost,fit['initial_cost'],1.):raise ValueError('projected warm-start cost mismatch')
                    local=fit.pop('local_linearization')
                    local.update(times_s=times.tolist(),gps=gps.tolist())
                    stem=identity.replace('::','-')
                    name=stem+'-linearization.json.gz';durable_write(DATA/name,gzip.compress(encoded(local),mtime=0),replace=False)
                    row.update(linearization_file=name,linearization_sha256=sha(DATA/name))
                    predicted=counted.prediction(np.array(fit['normalized_parameters']),task['model']);old=counted.prediction(point,task['model'])
                    error=predicted-gps;error[:,1]=(error[:,1]+np.pi)%(2*np.pi)-np.pi;error*=physical_metric(gps)
                    delta=predicted-old;delta[:,1]=(delta[:,1]+np.pi)%(2*np.pi)-np.pi;delta*=physical_metric(gps)
                    epoch=dict(times_s=times.tolist(),gps=gps.tolist(),predicted_gps=predicted.tolist(),errors_neu_m=error.tolist(),reference_change_neu_m=delta.tolist())
                    name=stem+'-epochs.json.gz';durable_write(DATA/name,gzip.compress(encoded(epoch),mtime=0),replace=False)
                    row.update(fit=fit,start_point=initial.tolist(),epoch_file=name,epoch_sha256=sha(DATA/name),
                        prediction_error_m=error.tolist(),track_rms_neu_m=np.sqrt(np.mean(error**2,axis=0)).tolist(),
                        maximum_absolute_neu_m=np.max(abs(error),axis=0).tolist(),passed=bool(fit['converged']),status='complete')
                except TimeoutError:raise
                except Exception as error:row.update(passed=False,status='error',error=type(error).__name__+': '+str(error))
                row.update(native_fit_calls=counted.fit_calls,native_diagnostic_calls=counted.diagnostic_calls,elapsed_s=time.monotonic()-begin,scientific_decision='abstain')
                if counted.fit_calls!=book.count(identity,'fit') or counted.diagnostic_calls!=book.count(identity,'diagnostic'):raise ValueError('charged call mismatch')
                target=DATA/(identity.replace('::','-')+'.json.gz');durable_write(target,gzip.compress(encoded(row),mtime=0),replace=False)
                row['artifact_sha256']=sha(target);rows.append(row)
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)))
            comparisons=[]
            for chosen in m['selected']:
                sid=chosen['segment']['segment_id'];pairs=[];cases=[]
                for case in policy.CASES:
                    fits=[]
                    for model in policy.MODELS:
                        a=next(r for r in rows if (r['segment_id'],r['case_id'],r['model'],r['role'])==(sid,case,model,'primary'))
                        b=next(r for r in rows if (r['segment_id'],r['case_id'],r['model'],r['role'])==(sid,case,model,'repeat'))
                        check=policy.repeat_check(a,b);pairs.append(dict(case_id=case,model=model,**check))
                        fit=dict(a.get('fit',{}),model=model)
                        fit['converged']=bool(check['passed'] and a['passed'] and b['passed']);fits.append(fit)
                    cases.append(dict(case_id=case,fits=fits))
                comparisons.append(dict(segment_id=sid,imu_type=chosen['segment']['imu_type'],duration_s=chosen['segment']['duration_s'],
                    pairs=pairs,cases=cases,profile=shape.hierarchical_profile(cases)))
            verify(originals=True);book.export()
            total=len(book.read('sweeps'))+len(pre.read('sweeps'))
            if total>4860 or len(book.read('starts'))!=24:raise ValueError('finite scope accounting mismatch')
            summary=dict(state='complete',results=rows,comparisons=comparisons,native_evaluations=total,observed_starts=24,
                preflight=preflight,elapsed_s=time.monotonic()-started,scientific_decision='abstain',original_findings_changed=False)
            write(DATA/'summary.json',summary);write(DATA/'completion.json',dict(state='complete',manifest_sha256=digest,summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',allocated_numerical_threads=0,total=24,completed=24))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=type(error).__name__+': '+str(error),completed=len(rows),preflight_completed=len(preflight)))
            write(DATA/'status.json',dict(state='stopped',allocated_numerical_threads=0,completed=len(rows),total=24));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    package();print('Horizontal-only observed study complete.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true');parser.add_argument('--detach',action='store_true')
    args=parser.parse_args()
    if sum((args.prepare_only,args.package_only,args.detach))>1:raise ValueError('one mode required')
    if args.package_only:package();return
    from lll.compute_budget import environment as compute_environment
    os.environ.update(compute_environment(workers=1,threads=4,reserved=0));os.environ['PYTHONPATH']=str(ROOT/'analysis')
    if args.prepare_only:prepare();print('Prepared two stretches /24 starts /4,860 native calls.');return
    if args.detach:
        prepare()
        with (DATA/'launch.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (DATA/'launch.json').exists() or (DATA/'start.json').exists():raise ValueError('launch already charged')
            with (DATA/'worker.log').open('ab') as log:
                child=subprocess.Popen([sys.executable,__file__],cwd=ROOT,env=os.environ.copy(),stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
            write(DATA/'launch.json',dict(pid=child.pid));print('Launched observed study PID '+str(child.pid))
    else:run()


if __name__=='__main__':main()
