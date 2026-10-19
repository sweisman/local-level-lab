# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen timing path and finite-difference diagnosis; no nonlinear optimization or finding promotion."""
import argparse
import copy
import fcntl
import gzip
import math
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
from lll.ilvis0_receipt_journal import durable_write,encoded
NAME='ilvis0-horizontal-timing-path-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
PARENT=ROOT/'docs/ilvis0-horizontal-observed-20261018';AUDIT=ROOT/'docs/ilvis0-horizontal-repeat-audit-20261019'
LIMITS=dict(maximum_native_evaluations=29,maximum_optimizer_starts=0,maximum_diagnostic_identities=3,
    numerical_threads=4,maximum_wall_s=900,retries=0)


TIME_STEP_NORMALIZED=1e-6/.15  # one microsecond, within the existing clock model


def derivative_check(center,minus,plus,*,index,step):
    if not math.isfinite(step) or step<=0:raise ValueError('positive finite difference step required')
    r=center['residual'];a=[row[index] for row in center['jacobian']]
    if not(len(r)==len(a)==len(minus['residual'])==len(plus['residual'])):raise ValueError('matched residual rows required')
    fd=[(p-m)/(2*step) for p,m in zip(plus['residual'],minus['residual'])]
    if not all(math.isfinite(v) for v in [*r,*a,*fd]):raise ValueError('finite residual derivatives required')
    an=math.hypot(*a);fn=math.hypot(*fd);err=math.hypot(*(p-q for p,q in zip(a,fd)))
    return dict(relative_residual_derivative_error=err/max(an,fn,1e-30),absolute_residual_derivative_error=err,
        analytic_derivative_norm=an,finite_difference_derivative_norm=fn,
        analytic_cost_derivative=2*math.fsum(v*w for v,w in zip(r,a)),
        finite_difference_cost_derivative=(math.fsum(v*v for v in plus['residual'])-math.fsum(v*v for v in minus['residual']))/(2*step))


def tasks(rows,pairs,endpoints,selected):
    target=next(r['segment']['segment_id'] for r in selected if r['segment']['imu_type']==21)
    control=next(r['segment']['segment_id'] for r in selected if r['segment']['imu_type']==8)
    expected={('bias1_unsubtracted','sphere_still'),('bias1_profiled_removal','sphere_still'),('bias1_unsubtracted','flat_still')}
    failed=[p for p in pairs if not p['passed']]
    if len(failed)!=3 or {(p['case_id'],p['model']) for p in failed}!=expected or any(p['segment_id']!=target for p in failed):
        raise ValueError('exact parent failed population required')
    result=[]
    for sid,case,model in ((target,'bias1_unsubtracted','sphere_still'),(target,'bias1_profiled_removal','sphere_still'),(control,'bias1_unsubtracted','sphere_rotating')):
        r=next(r for r in rows if (r['segment_id'],r['case_id'],r['model'],r['role'])==(sid,case,model,'primary'))
        u=r['fit']['normalized_parameters'];names=r['fit']['active_parameters'];i=names.index('time_offset')
        points=[dict(method='center',point=list(u))]
        def symmetric(v,label):
            for sign,suffix in ((-1,'minus'),(1,'plus')):
                p=list(v);p[i]+=sign*TIME_STEP_NORMALIZED
                if any(abs(x)>1 for x in p):raise ValueError('symmetric timing points must be interior')
                points.append(dict(method='time_'+label+'_'+suffix,point=p))
        symmetric(u,'primary');repeat_file=None
        if sid==target:
            repeat=next(r for r in rows if (r['segment_id'],r['case_id'],r['model'],r['role'])==(sid,case,model,'repeat'))
            if repeat['fit']['active_parameters']!=names:raise ValueError('matched columns required')
            v=repeat['fit']['normalized_parameters'];repeat_file=repeat.get('linearization_file')
            points.append(dict(method='repeat_center',point=list(v)));symmetric(v,'repeat')
            points.extend(dict(method='path_'+str(k),point=[a+(b-a)*k/8 for a,b in zip(u,v)]) for k in range(1,8))
        result.append(dict(identity=r['identity'],segment_id=sid,case_id=case,model=model,role='primary',is_control=sid==control,
            swapped_coordinate='time_offset',points=points,linearization_file=r.get('linearization_file'),repeat_linearization_file=repeat_file,
            time_index=i,time_step_normalized=TIME_STEP_NORMALIZED))
    if len(result)!=3 or sum(len(t['points']) for t in result)!=29:raise ValueError('exact three identities /29 points required')
    return result


def verify():
    m=load(DATA/'manifest.json')
    if m['environment']!=environment() or m['limits']!=LIMITS:raise ValueError('environment or finite allowance changed')
    for p,d in {**m['sources'],**m['inputs']}.items():
        if sha(ROOT/p)!=d:raise ValueError('frozen dependency changed: '+p)
    for p,d in m['sources'].items():
        if sha(DATA/'source-freeze'/p)!=d:raise ValueError('source snapshot changed')
    return m


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    inputs={}
    for p in (PARENT,AUDIT,ROOT/'docs/ilvis0-horizontal-repeat-probes-20261019'):
        checked_publication(p)
        for n in ('manifest.json','summary.json','completion.json','evidence-receipt.json'):
            inputs[str((p/n).relative_to(ROOT))]=sha(p/n)
    parent=load(PARENT/'summary.json');audit=load(AUDIT/'summary.json');old=load(PARENT/'manifest.json')
    if len(parent['results'])!=24 or not all(r['passed'] for r in parent['results']):raise ValueError('complete parent fits required')
    plan=tasks(parent['results'],audit['pairs'],audit['endpoints'],old['selected'])
    test='analysis/tests/test_ilvis0_horizontal_timing_path.py'
    run=subprocess.run([sys.executable,'-m','pytest',test,'-q'],cwd=ROOT,capture_output=True,text=True,timeout=30)
    (DATA/'software-tests.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('probe scope controls failed')
    sources=dict(old['sources'])
    for p in ('analysis/tests/ilvis0_horizontal_timing_path.py',test,'analysis/tests/test_ilvis0_horizontal_repeat_probes.py',str((PUBLIC/'PLAN.md').relative_to(ROOT))):sources[p]=sha(ROOT/p)
    for p,d in sources.items():
        if sha(ROOT/p)!=d:raise ValueError('preserved source changed')
        target=DATA/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
    for task in plan:
        for name in (task['linearization_file'],task['repeat_linearization_file']):
            if name:
                p=PARENT/name;inputs[str(p.relative_to(ROOT))]=sha(p)
    for p,d in old['inputs'].items():inputs[p]=d
    write(DATA/'manifest.json',dict(version='horizontal-timing-path-v1',sources=sources,inputs=inputs,
        originals=old['originals'],environment=environment(),limits=LIMITS,plan=dict(tasks=plan,**LIMITS)))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def publish():
    c=load(DATA/'completion.json');s=load(DATA/'summary.json')
    if c['manifest_sha256']!=sha(DATA/'manifest.json') or c['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('completion mismatch')
    names=['manifest.json','authorization.json','summary.json','completion.json','start.json','software-tests.log']
    for r in s['artifacts']:
        if sha(DATA/r['filename'])!=r['sha256']:raise ValueError('point artifact changed')
        names.append(r['filename'])
    for n in names:shutil.copy2(DATA/n,PUBLIC/n)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    ledger=DATA/'charges';chain=[load(p) for p in sorted(ledger.glob('[0-9]*.json'))]
    durable_write(PUBLIC/'charges.json.gz',gzip.compress(encoded(dict(events=chain,head=load(ledger/'HEAD.json'))),mtime=0),replace=True)
    names.append('charges.json.gz')
    lines=['# Timing path and derivative checks','',
        'Completed **29 native tangent evaluations**, with zero optimizer starts. The primary and repeat centers reproduced exactly. The study samples the full parameter path and symmetric one-microsecond timing changes. No fit or repeat labels changed.',
        '', '| Endpoint | Point | Scored cost | Fresh stationarity | Horizontal change RMS (m) | Height change RMS (m) |',
        '|---|---|---:|---:|---:|---:|']
    for r in s['results']:
        for p in r['probes']:lines.append(f"| {r['identity']} | {p['method']} | {p['cost']:.8g} | {p['stationarity']:.6g} | {p['horizontal_change_rms_m']:.6g} | {p['change_rms_neu_m'][2]:.6g} |")
    lines+=['','The probes test competing timing/calibration directions at fixed points. An improved score is not a converged fit or a passed repeat; the two-recording sensitivity study and original 53-stretch findings retain their published labels.',
        '', '[Frozen scope](PLAN.md) · [Saved-fit diagnosis](../ilvis0-horizontal-repeat-audit-20261019/README.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in [*names,'README.md','PLAN.md']}))


def run():
    m=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists() or (DATA/'completion.json').exists():raise ValueError('charged/completed probe batch cannot restart')
        verify()
        for p,d in m['originals'].items():
            if sha(Path(p))!=d:raise ValueError('retained original container changed')
        write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        write(DATA/'status.json',dict(state='extracting',pid=os.getpid(),allocated_numerical_threads=4,total=3,completed=0))
        import numpy as np
        from scipy.linalg import solve_triangular
        from lll import ilvis0_exploratory as explore,ilvis0_precision as precision,ilvis0_segments as segments,ilvis0_gps_sensitivity as sensitivity
        from lll.ilvis0_projected_fitting import ProjectedProblem
        from lll.ilvis0_solver_refinement import projected_stationarity
        from lll.ilvis0_solver_position import physical_metric
        from lll.ilvis0_receipt_journal import Ledger
        started=time.monotonic();rows=[];artifacts=[];timing_checks=[]
        def alarm(*args):raise TimeoutError('finite 15-minute diagnostic allowance exceeded')
        previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(900)
        try:
            old=load(PARENT/'manifest.json');arrays={}
            assumption=next(a for a in sensitivity.assumptions() if a.name=='h1_v3_tau60')
            kernel,kmeta=explore.load_kernel(DATA/'kernel');tangent,tmeta=precision.load_tangent(DATA/'kernel')
            expected=load(PARENT/'kernel.json')
            if kmeta!=expected['value'] or tmeta!=expected['tangent']:raise ValueError('parent native build mismatch')
            for chosen in old['selected']:
                sid=chosen['segment']['segment_id'];values,times,gps,provenance=segments.extract_segment(Path(chosen['source_path']),old['contexts'][chosen['task']],chosen['segment'])
                if provenance!=old['provenance'][sid]:raise ValueError('saved extraction did not reproduce')
                cov=sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1)),assumption)
                arrays[sid]=(values,times,gps,cov)
            book=Ledger(DATA,sha(DATA/'manifest.json'),[t['identity'] for t in m['plan']['tasks']],fit_limit=1,diagnostic_limit=13)
            for task in m['plan']['tasks']:
                write(DATA/'status.json',dict(state='probing',pid=os.getpid(),allocated_numerical_threads=4,total=3,completed=len(rows),identity=task['identity'],native_evaluations=len(artifacts)))
                task=dict(task,profile=task['case_id']=='bias1_profiled_removal')
                full,_=make_problem(old,task,arrays[task['segment_id']],kernel,tangent);projected=ProjectedProblem(full,('latitude','longitude'))
                saved=load(PARENT/task['linearization_file']);gps=arrays[task['segment_id']][2]
                book.start(task['identity']);center_r=None;center_prediction=None;probes=[]
                for point in task['points']:
                    u=np.array(point['point']);prediction,jac,edges=book.call(task['identity'],'diagnostic','tangent',full.prediction_tangent,u,task['model'])
                    full_r=full.whiten(prediction-gps);full_j=solve_triangular(full.cholesky,jac,lower=True)
                    r,j=projected.projection.apply(full_r,full_j)
                    if point['method']=='repeat_center':
                        repeat_saved=load(PARENT/task['repeat_linearization_file'])
                        if not np.array_equal(r,repeat_saved['residual']) or not np.array_equal(j,repeat_saved['jacobian']):raise ValueError('saved repeat center did not reproduce exactly')
                    if point['method']=='center':
                        if not np.array_equal(r,saved['residual']) or not np.array_equal(j,saved['jacobian']):raise ValueError('saved center did not reproduce exactly')
                        center_r=r;center_prediction=prediction
                    error=prediction-gps;error[:,1]=(error[:,1]+np.pi)%(2*np.pi)-np.pi;error*=physical_metric(gps)
                    change=prediction-center_prediction;change[:,1]=(change[:,1]+np.pi)%(2*np.pi)-np.pi;change*=physical_metric(gps)
                    rms=np.sqrt(np.mean(change**2,axis=0));value=dict(identity=task['identity'],method=point['method'],point=u.tolist(),
                        prediction_gps=prediction.tolist(),full_residual=full_r.tolist(),full_jacobian=full_j.tolist(),
                        residual=r.tolist(),jacobian=j.tolist(),cost=float(r@r),stationarity=projected_stationarity(u,r,j)[0],
                        absolute_rms_neu_m=np.sqrt(np.mean(error**2,axis=0)).tolist(),change_rms_neu_m=rms.tolist(),
                        horizontal_change_rms_m=float(np.linalg.norm(rms[:2])),boundaries=edges)
                    name=task['identity'].replace('::','-')+'--'+point['method']+'.json.gz'
                    durable_write(DATA/name,gzip.compress(encoded(value),mtime=0),replace=False)
                    artifacts.append(dict(filename=name,sha256=sha(DATA/name)))
                    probes.append({k:v for k,v in value.items() if k not in ('prediction_gps','full_residual','full_jacobian','residual','jacobian')})
                rows.append(dict(identity=task['identity'],passed=True,is_control=task['is_control'],swapped_coordinate=task['swapped_coordinate'],probes=probes))
                for label,method in (('primary','center'),('repeat','repeat_center')):
                    if task['is_control'] and label=='repeat':continue
                    def saved_point(method):
                        return load(DATA/(task['identity'].replace('::','-')+'--'+method+'.json.gz'))
                    center=saved_point(method);p=full.bounds.decode(np.array(center['point']))
                    phase=np.mod(full.gps_times+p['time_offset'],.005)
                    nearest=float(np.min(np.minimum(phase,.005-phase)))
                    check=derivative_check(center,saved_point('time_'+label+'_minus'),saved_point('time_'+label+'_plus'),
                        index=task['time_index'],step=task['time_step_normalized'])
                    timing_checks.append(dict(identity=task['identity'],endpoint=label,step_s=1e-6,
                        nearest_nominal_clock_boundary_s=nearest,crosses_nominal_boundary=nearest<=1e-6,**check))
                write(DATA/'progress.json',dict(completed=len(rows),passed=len(rows)))
            if len(artifacts)!=29 or len(book.read('sweeps'))!=29:raise ValueError('exact 29-call scope required')
            verify();s=dict(state='complete',results=rows,artifacts=artifacts,native_evaluations=29,observed_starts=0,
                optimizer_starts=0,fit_labels_changed=False,timing_derivative_checks=timing_checks,
                elapsed_s=time.monotonic()-started,scientific_decision='abstain')
            write(DATA/'summary.json',s);write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',allocated_numerical_threads=0,total=3,completed=3))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=str(error),charged_completed_artifacts=len(artifacts),completed=len(rows)))
            write(DATA/'status.json',dict(state='stopped',allocated_numerical_threads=0));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print('Completed 29 fixed-point calls; no optimizer starts or label changes.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--detach',action='store_true');parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
    if args.detach and args.package_only:raise ValueError('one mode required')
    if args.package_only:publish()
    else:
        from lll.compute_budget import environment as compute_environment
        os.environ.update(compute_environment(workers=1,threads=4,reserved=0));os.environ['PYTHONPATH']=str(ROOT/'analysis')
        if args.detach:
            prepare()
            with (DATA/'launch.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                if (DATA/'launch.json').exists() or (DATA/'start.json').exists():raise ValueError('launch already charged')
                with (DATA/'worker.log').open('ab') as log:
                    child=subprocess.Popen([sys.executable,__file__],cwd=ROOT,env=os.environ.copy(),stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
                write(DATA/'launch.json',dict(pid=child.pid));print('Launched fixed-point probes PID '+str(child.pid))
        else:run()
