# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately frozen matched horizontal-only multi-start study."""
import argparse
import copy
import fcntl
import gzip
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_projected_controls_worker import environment,sha,write
from ilvis0_horizontal_observed_worker import load,make_problem,checked_publication
from lll import ilvis0_horizontal_multistart as policy,ilvis0_horizontal_observed as preceding,ilvis0_multistart as starts_policy
from lll.ilvis0_receipt_journal import durable_write,encoded,Ledger
NAME='ilvis0-horizontal-multistart-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
PARENT=ROOT/'docs/ilvis0-horizontal-observed-20261018'
QUALIFIED=ROOT/'docs/ilvis0-multistart-controls-v3-20261019'
TIMING=ROOT/'docs/ilvis0-horizontal-timing-path-20261019'


def seeds(plan,parent,rows):
    vectors={};preflight={}
    for task in plan['tasks']:
        key='::'.join((task['segment_id'],task['case_id'],task['model']))
        original=next(r for r in rows if r['identity']==key+'::'+task['role'])
        if task['control']:
            point=list(original['fit']['normalized_parameters']);ref=original
        else:
            point=list(parent['references'][key]['normalized_parameters']) if task['role']=='primary' else list(original['start_point'])
            point=starts_policy.starts(point,original['fit']['active_parameters'],[task['timing_start']])[0]
            ref=next(r for r in rows if r['identity']==key+'::primary')
        vectors[task['identity']]=point;preflight[ref['identity']]=ref
    if len(vectors)!=38 or len(preflight)!=8:raise ValueError('exact starts and preflight population required')
    return vectors,preflight


def new_ledger(path,digest,ids,*,preflight=False):
    return Ledger(path,digest,ids,fit_limit=1 if preflight else 200,diagnostic_limit=1)


def verify(*,originals=False):
    m=load(DATA/'manifest.json')
    if m['environment']!=environment() or m['plan']!=policy.plan(m['selected']):raise ValueError('environment or finite plan changed')
    for p,d in {**m['sources'],**m['inputs']}.items():
        if sha(ROOT/p)!=d:raise ValueError('frozen dependency changed: '+p)
    for p,d in m['sources'].items():
        if sha(DATA/'source-freeze'/p)!=d:raise ValueError('source snapshot changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**policy.LIMITS):raise ValueError('allowance changed')
    if originals:
        for p,d in m['originals'].items():
            if sha(Path(p))!=d:raise ValueError('retained original changed')
    return m


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    for path in (PARENT,QUALIFIED,TIMING):checked_publication(path)
    qualified=load(QUALIFIED/'summary.json')
    if qualified.get('passed') is not True or len(qualified['controls'])!=4 or qualified['software_starts']!=24:
        raise ValueError('complete known-answer multi-start qualification required')
    parent=load(PARENT/'manifest.json');old=load(PARENT/'summary.json')
    if len(old['results'])!=24 or not all(r['passed'] for r in old['results']):raise ValueError('complete exact parent required')
    plan=policy.plan(parent['selected']);vectors,preflight=seeds(plan,parent,old['results'])
    tests=['analysis/tests/test_ilvis0_multistart.py','analysis/tests/test_ilvis0_horizontal_multistart.py',
           'analysis/tests/test_ilvis0_horizontal_multistart_worker.py']
    result=subprocess.run([sys.executable,'-m','pytest',*tests,'-q'],cwd=ROOT,capture_output=True,text=True,timeout=30)
    (DATA/'software-tests.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise ValueError('preparation controls failed')
    sources=dict(parent['sources']);sources.update(load(QUALIFIED/'manifest.json')['sources'])
    for p in ['analysis/tests/ilvis0_horizontal_multistart_worker.py','analysis/lll/ilvis0_horizontal_multistart.py',
              'analysis/lll/ilvis0_multistart.py',*tests,str((PUBLIC/'PLAN.md').relative_to(ROOT))]:sources[p]=sha(ROOT/p)
    for p,d in sources.items():
        if sha(ROOT/p)!=d:raise ValueError('qualified source changed')
        target=DATA/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
    inputs=dict(parent['inputs'])
    for path in (PARENT,QUALIFIED,TIMING):
        for n in ('manifest.json','summary.json','completion.json','evidence-receipt.json'):inputs[str((path/n).relative_to(ROOT))]=sha(path/n)
    inputs[str((PARENT/'kernel.json').relative_to(ROOT))]=sha(PARENT/'kernel.json')
    for ref in preflight.values():
        p=PARENT/ref['linearization_file'];inputs[str(p.relative_to(ROOT))]=sha(p)
    manifest=dict(version=policy.VERSION,environment=environment(),sources=sources,inputs=inputs,plan=plan,
        selected=parent['selected'],originals=parent['originals'],task_vectors=vectors,preflight_references=preflight,
        parent_manifest_sha256=sha(PARENT/'manifest.json'),scientific_decision='abstain')
    write(DATA/'manifest.json',manifest);write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**policy.LIMITS))
    (PUBLIC/'README.md').write_text('# Matched horizontal-only multi-start study\n\n'
        'Prepared 36 target starts and two fresh controls, with eight exact reconstruction checks before fitting. '
        'The ceiling is 7,646 native calls /20 hours on four threads. Expected runtime is roughly six hours. '
        'Original findings and earlier sensitivity results remain intact.\n\n[Method and limits](PLAN.md).\n')
    return verify()


def publish():
    c=load(DATA/'completion.json');s=load(DATA/'summary.json')
    if c['manifest_sha256']!=sha(DATA/'manifest.json') or c['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('completion mismatch')
    names=['manifest.json','authorization.json','summary.json','completion.json','start.json','preflight.json','kernel.json','software-tests.log']
    for r in s['results']:
        for filename,digest in r['artifacts'].items():
            if sha(DATA/filename)!=digest:raise ValueError('fit artifact changed')
            names.append(filename)
    for n in names:shutil.copy2(DATA/n,PUBLIC/n)
    for label,directory in (('fit',DATA),('preflight',DATA/'preflight')):
        events=directory/'charges';chain=[load(p) for p in sorted(events.glob('[0-9]*.json'))]
        name=label+'-charges.json.gz';durable_write(PUBLIC/name,gzip.compress(encoded(dict(events=chain,head=load(events/'HEAD.json'))),mtime=0),replace=True);names.append(name)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Matched horizontal-only multi-start results','',
        f"Completed {len(s['results'])}/38 starts and eight exact reconstructions, using {s['native_evaluations']} native calls in {s['elapsed_s']/3600:.2f} hours. Fresh controls {'passed' if s['controls_passed'] else 'failed'}. No previous fit labels changed.",'',
        '| Processing case | Model | Primary selected cost | Repeat selected cost | Repeat gate |',
        '|---|---|---:|---:|---|']
    for p in s['pairs']:
        costs=p.get('selected_costs',[None,None]);fmt=lambda v:'unavailable' if v is None else f'{v:.10g}'
        lines.append(f"| {p['case_id']} | {p['model']} | {fmt(costs[0])} | {fmt(costs[1])} | {'pass' if p['passed'] else 'unresolved'} |")
    profile=s['profile'];label=profile.get('shape_preference',profile.get('conditional_shape_preference','unresolved'))
    lines+=['',f"The new IMU21 matched sensitivity disposition is **{label}**. Only complete model/case comparisons with passing fresh controls enter the shape-first interpretation.",'',
        'Every attempted start, including failed stops and local optima, is preserved. This is a finite search, not proof of a global optimum or calibrated significance. Heights remain in initialization, covariance and propagation; unscored height errors are retained. A horizontal score advantage is not a valid full-flight reconstruction or gyro-only evidence.','',
        'The original **53 globe / zero flat / zero unresolved** full-position findings and earlier one-complete/one-unresolved sensitivity study are preserved separately.','',
        '[Frozen scope](PLAN.md) · [Measurement contributions](../ilvis0-measurement-contribution/README.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in [*dict.fromkeys(names),'README.md','PLAN.md']}))


def run():
    m=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged or completed study cannot restart')
        verify(originals=True);write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        import numpy as np
        from scipy.linalg import solve_triangular
        from lll import ilvis0_exploratory as explore,ilvis0_precision as precision,ilvis0_segments as segments,ilvis0_gps_sensitivity as sensitivity
        from lll import ilvis0_projected_ridge as candidate,ilvis0_shape as shape
        from lll.ilvis0_projected_fitting import ProjectedProblem
        from lll.ilvis0_solver_position import physical_metric
        rows=[];preflight=[];started=time.monotonic();digest=sha(DATA/'manifest.json')
        def alarm(*args):raise TimeoutError('finite 20-hour study allowance exhausted')
        previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(policy.LIMITS['maximum_wall_s'])
        try:
            write(DATA/'status.json',dict(state='extracting',pid=os.getpid(),allocated_numerical_threads=4,total=38,completed=0))
            old=load(PARENT/'manifest.json');arrays={};problems={}
            kernel,kmeta=explore.load_kernel(DATA/'kernel');tangent,tmeta=precision.load_tangent(DATA/'kernel')
            if dict(value=kmeta,tangent=tmeta)!=load(PARENT/'kernel.json'):raise ValueError('parent native kernel configuration changed')
            write(DATA/'kernel.json',dict(value=kmeta,tangent=tmeta))
            assumption=next(a for a in sensitivity.assumptions() if a.name=='h1_v3_tau60')
            for chosen in old['selected']:
                sid=chosen['segment']['segment_id'];values,times,gps,provenance=segments.extract_segment(Path(chosen['source_path']),old['contexts'][chosen['task']],chosen['segment'])
                if provenance!=old['provenance'][sid]:raise ValueError('extraction provenance changed')
                covariance=sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1)),assumption)
                arrays[sid]=(values,times,gps,covariance)
            pre=new_ledger(DATA/'preflight',digest,list(m['preflight_references']),preflight=True)
            for identity,ref in m['preflight_references'].items():
                sid,case,model,role=identity.split('::');task=dict(segment_id=sid,case_id=case,model=model,profile=case=='bias1_profiled_removal')
                key='::'.join((sid,case,model));full,_=make_problem(old,task,arrays[sid],kernel,tangent);problems[key]=full
                projected=ProjectedProblem(full,('latitude','longitude'));pre.start(identity)
                r,j,_=pre.call(identity,'diagnostic','tangent',projected.residual_tangent,np.array(ref['fit']['normalized_parameters']),model)
                saved=load(PARENT/ref['linearization_file']);check=dict(identity=identity,passed=bool(np.array_equal(r,saved['residual']) and np.array_equal(j,saved['jacobian'])))
                preflight.append(check);write(DATA/'preflight.json',preflight)
            if len(preflight)!=8 or not all(r['passed'] for r in preflight):raise ValueError('all eight exact preflight checks required')
            pre.export();book=new_ledger(DATA,digest,[t['identity'] for t in m['plan']['tasks']])
            class Counted:
                def __init__(self,full,identity):self.base=full;self.identity=identity;self.bounds=full.bounds;self.gps=full.gps;self.cholesky=full.cholesky
                def residual_tangent(self,u,model):return book.call(self.identity,'fit','tangent',self.base.residual_tangent,u,model)
            for task in m['plan']['tasks']:
                identity=task['identity'];verify();book.start(identity);begin=time.monotonic();row=dict(task,artifacts={})
                write(DATA/'status.json',dict(state='fitting',pid=os.getpid(),allocated_numerical_threads=4,total=38,completed=len(rows),identity=identity))
                full=problems['::'.join((task['segment_id'],task['case_id'],task['model']))];gps=arrays[task['segment_id']][2];times=arrays[task['segment_id']][1]
                counted=Counted(full,identity);projected=ProjectedProblem(counted,('latitude','longitude'));point=np.array(m['task_vectors'][identity])
                try:
                    fit=candidate.fit_control(projected,task['model'],start=point,maximum_evaluations=200)
                    if fit['evaluations']!=book.count(identity,'fit'):raise ValueError('fit call accounting mismatch')
                    local=fit.pop('local_linearization');prediction,jac,edges=book.call(identity,'diagnostic','tangent',full.prediction_tangent,np.array(fit['normalized_parameters']),task['model'])
                    error=prediction-gps;error[:,1]=(error[:,1]+np.pi)%(2*np.pi)-np.pi;error*=physical_metric(gps)
                    epoch=dict(times_s=times.tolist(),gps=gps.tolist(),predicted_gps=prediction.tolist(),errors_neu_m=error.tolist(),
                        full_residual=full.whiten(prediction-gps).tolist(),full_jacobian=solve_triangular(full.cholesky,jac,lower=True).tolist())
                    stem=identity.replace('::','-')
                    for label,payload in (('linearization',dict(local,times_s=times.tolist(),gps=gps.tolist())),('epochs',epoch)):
                        name=stem+'-'+label+'.json.gz';durable_write(DATA/name,gzip.compress(encoded(payload),mtime=0),replace=False);row['artifacts'][name]=sha(DATA/name)
                        row[label+'_file']=name;row[label+'_sha256']=sha(DATA/name)
                    row.update(fit=fit,passed=bool(fit['converged']),start_point=point.tolist(),prediction_error_m=error.tolist(),
                        track_rms_neu_m=np.sqrt(np.mean(error**2,axis=0)).tolist(),status='complete')
                except TimeoutError:raise
                except Exception as error:row.update(passed=False,status='error',error=type(error).__name__+': '+str(error))
                row.update(native_fit_calls=book.count(identity,'fit'),native_diagnostic_calls=book.count(identity,'diagnostic'),elapsed_s=time.monotonic()-begin,scientific_decision='abstain')
                name=identity.replace('::','-')+'.json.gz';durable_write(DATA/name,gzip.compress(encoded(row),mtime=0),replace=False);row['artifacts'][name]=sha(DATA/name);rows.append(row)
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)))
            original=load(PARENT/'summary.json')['results'];controls=[r for r in rows if r['control']]
            control_checks=[]
            for r in controls:
                ref=next(x for x in original if x['identity']=='::'.join((r['segment_id'],r['case_id'],r['model'],r['role'])))
                control_checks.append(preceding.repeat_check(r,dict(ref,role='repeat' if r['role']=='primary' else 'primary')))
            controls_passed=all(c['passed'] for c in control_checks) and preceding.repeat_check(*controls)['passed']
            pairs=[];selections=[];cases=[]
            for case in preceding.CASES:
                fits=[]
                for model in preceding.MODELS:
                    selected=[];qualified=[]
                    for role in ('primary','repeat'):
                        tasks=[t for t in m['plan']['tasks'] if not t['control'] and (t['case_id'],t['model'],t['role'])==(case,model,role)]
                        group=[r for r in rows if r['identity'] in {t['identity'] for t in tasks}]
                        try:
                            selection=policy.choose(group,tasks);best=next(r for r in group if r['identity']==selection['selected_identity'])
                        except ValueError as error:selection=dict(passed=False,error=str(error));best=None
                        selections.append(dict(case_id=case,model=model,role=role,**selection));qualified.append(selection['passed']);selected.append(best)
                    check=preceding.repeat_check(*selected) if all(r is not None for r in selected) else dict(passed=False,reason='incomplete_start_group')
                    check['passed']=bool(check['passed'] and all(qualified) and controls_passed)
                    pairs.append(dict(case_id=case,model=model,selected_costs=[r['fit']['residual_sum_squares'] if r else None for r in selected],**check))
                    fits.append(dict(selected[0]['fit'] if selected[0] else {},model=model,converged=check['passed']))
                cases.append(dict(case_id=case,fits=fits))
            verify(originals=True);book.export();total=len(book.read('sweeps'))+len(pre.read('sweeps'))
            if total>7646 or len(book.read('starts'))!=38:raise ValueError('finite scope accounting mismatch')
            s=dict(state='complete',results=rows,preflight=preflight,selections=selections,pairs=pairs,cases=cases,
                controls_passed=controls_passed,control_checks=control_checks,profile=shape.hierarchical_profile(cases),
                native_evaluations=total,observed_starts=38,elapsed_s=time.monotonic()-started,original_findings_changed=False,scientific_decision='abstain')
            write(DATA/'summary.json',s);write(DATA/'completion.json',dict(manifest_sha256=digest,summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',allocated_numerical_threads=0,total=38,completed=38))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=type(error).__name__+': '+str(error),completed=len(rows),preflight_completed=len(preflight)))
            write(DATA/'status.json',dict(state='stopped',allocated_numerical_threads=0,total=38,completed=len(rows)));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print('Matched multi-start study completed and published.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true');parser.add_argument('--detach',action='store_true');args=parser.parse_args()
    if sum((args.prepare_only,args.package_only,args.detach))>1:raise ValueError('one mode required')
    if args.package_only:publish()
    else:
        from lll.compute_budget import environment as budget_environment
        os.environ.update(budget_environment(workers=1,threads=4,reserved=0));os.environ['PYTHONPATH']=str(ROOT/'analysis')
        if args.prepare_only:prepare()
        elif args.detach:
            prepare()
            with (DATA/'launch.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                if (DATA/'launch.json').exists() or (DATA/'start.json').exists():raise ValueError('launch already charged')
                with (DATA/'worker.log').open('ab') as log:
                    child=subprocess.Popen([sys.executable,__file__],cwd=ROOT,env=os.environ.copy(),stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
                write(DATA/'launch.json',dict(pid=child.pid));print('Launched matched multi-start PID '+str(child.pid))
        else:run()
