# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen 28-point diagnosis; no nonlinear optimization or finding promotion."""
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
NAME='ilvis0-horizontal-repeat-probes-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
PARENT=ROOT/'docs/ilvis0-horizontal-observed-20261018';AUDIT=ROOT/'docs/ilvis0-horizontal-repeat-audit-20261019'
LIMITS=dict(maximum_native_evaluations=28,maximum_optimizer_starts=0,maximum_diagnostic_identities=8,
    numerical_threads=4,maximum_wall_s=900,retries=0)


def tasks(rows,pairs,endpoints,selected):
    target=next(r['segment']['segment_id'] for r in selected if r['segment']['imu_type']==21)
    control=next(r['segment']['segment_id'] for r in selected if r['segment']['imu_type']==8)
    failed=[p for p in pairs if not p['passed']]
    expected={('bias1_unsubtracted','sphere_still'),('bias1_profiled_removal','sphere_still'),('bias1_unsubtracted','flat_still')}
    if len(failed)!=3 or {(p['case_id'],p['model']) for p in failed}!=expected or any(p['segment_id']!=target for p in failed):
        raise ValueError('exact three failed target pairs required')
    result=[]
    for r in rows:
        is_target=r['segment_id']==target and (r['case_id'],r['model']) in expected
        is_control=r['segment_id']==control and (r['case_id'],r['model'])==('bias1_unsubtracted','sphere_rotating')
        if not (is_target or is_control):continue
        u=r['fit']['normalized_parameters'];names=r['fit']['active_parameters']
        correction=next(c for c in next(e for e in endpoints if e['identity']==r['identity'])['corrections'] if c['method']=='range_scaled')
        if not correction['feasible']:raise ValueError('saved feasible correction required')
        shifted=[a+b for a,b in zip(u,correction['step'])]
        if len(shifted)!=len(u) or any(not math.isfinite(x) or abs(x)>1+1e-14 for x in shifted):raise ValueError('full feasible proposed point required')
        points=[dict(method='center',point=list(u))]
        coordinate=None
        if is_target:
            other=next(x for x in rows if (x['segment_id'],x['case_id'],x['model'])==(r['segment_id'],r['case_id'],r['model']) and x['role']!=r['role'])
            v=other['fit']['normalized_parameters']
            if names!=other['fit']['active_parameters']:raise ValueError('matched parameter order required')
            i=max(range(len(u)),key=lambda k:abs(v[k]-u[k]));coordinate=names[i]
            swapped=list(u);swapped[i]=v[i]
            points.extend([dict(method='coordinate_swap',point=swapped),dict(method='full_midpoint',point=[(a+b)/2 for a,b in zip(u,v)])])
        points.append(dict(method='affine',point=[max(-1.,min(1.,x)) for x in shifted]))
        result.append(dict(identity=r['identity'],segment_id=r['segment_id'],case_id=r['case_id'],model=r['model'],role=r['role'],
            is_control=is_control,swapped_coordinate=coordinate,points=points,linearization_file=r.get('linearization_file')))
    if len(result)!=8 or sum(len(r['points']) for r in result)!=28:raise ValueError('exact eight identities /28 points required')
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
    for p in (PARENT,AUDIT):
        checked_publication(p)
        for n in ('manifest.json','summary.json','completion.json','evidence-receipt.json'):
            inputs[str((p/n).relative_to(ROOT))]=sha(p/n)
    parent=load(PARENT/'summary.json');audit=load(AUDIT/'summary.json');old=load(PARENT/'manifest.json')
    if len(parent['results'])!=24 or not all(r['passed'] for r in parent['results']):raise ValueError('complete parent fits required')
    plan=tasks(parent['results'],audit['pairs'],audit['endpoints'],old['selected'])
    test='analysis/tests/test_ilvis0_horizontal_repeat_probes.py'
    run=subprocess.run([sys.executable,'-m','pytest',test,'-q'],cwd=ROOT,capture_output=True,text=True,timeout=30)
    (DATA/'software-tests.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('probe scope controls failed')
    sources=dict(old['sources'])
    for p in ('analysis/tests/ilvis0_horizontal_repeat_probes.py',test,str((PUBLIC/'PLAN.md').relative_to(ROOT))):sources[p]=sha(ROOT/p)
    for p,d in sources.items():
        if sha(ROOT/p)!=d:raise ValueError('preserved source changed')
        target=DATA/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
    for task in plan:
        p=PARENT/task['linearization_file'];inputs[str(p.relative_to(ROOT))]=sha(p)
    for p,d in old['inputs'].items():inputs[p]=d
    write(DATA/'manifest.json',dict(version='horizontal-fixed-repeat-probes-v1',sources=sources,inputs=inputs,
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
    lines=['# Fixed-point diagnosis of horizontal repeat failures','',
        'Completed **28 native tangent evaluations**, with zero optimizer starts. All eight saved centers reproduced before their diagnostic points were evaluated. No fit or repeat labels changed.',
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
        write(DATA/'status.json',dict(state='extracting',pid=os.getpid(),allocated_numerical_threads=4,total=8,completed=0))
        import numpy as np
        from scipy.linalg import solve_triangular
        from lll import ilvis0_exploratory as explore,ilvis0_precision as precision,ilvis0_segments as segments,ilvis0_gps_sensitivity as sensitivity
        from lll.ilvis0_projected_fitting import ProjectedProblem
        from lll.ilvis0_solver_refinement import projected_stationarity
        from lll.ilvis0_solver_position import physical_metric
        from lll.ilvis0_receipt_journal import Ledger
        started=time.monotonic();rows=[];artifacts=[]
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
            book=Ledger(DATA,sha(DATA/'manifest.json'),[t['identity'] for t in m['plan']['tasks']],fit_limit=1,diagnostic_limit=4)
            for task in m['plan']['tasks']:
                write(DATA/'status.json',dict(state='probing',pid=os.getpid(),allocated_numerical_threads=4,total=8,completed=len(rows),identity=task['identity'],native_evaluations=len(artifacts)))
                task=dict(task,profile=task['case_id']=='bias1_profiled_removal')
                full,_=make_problem(old,task,arrays[task['segment_id']],kernel,tangent);projected=ProjectedProblem(full,('latitude','longitude'))
                saved=load(PARENT/task['linearization_file']);gps=arrays[task['segment_id']][2]
                book.start(task['identity']);center_r=None;center_prediction=None;probes=[]
                for point in task['points']:
                    u=np.array(point['point']);prediction,jac,edges=book.call(task['identity'],'diagnostic','tangent',full.prediction_tangent,u,task['model'])
                    full_r=full.whiten(prediction-gps);full_j=solve_triangular(full.cholesky,jac,lower=True)
                    r,j=projected.projection.apply(full_r,full_j)
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
                write(DATA/'progress.json',dict(completed=len(rows),passed=len(rows)))
            if len(artifacts)!=28 or len(book.read('sweeps'))!=28:raise ValueError('exact 28-call scope required')
            verify();s=dict(state='complete',results=rows,artifacts=artifacts,native_evaluations=28,observed_starts=0,
                optimizer_starts=0,fit_labels_changed=False,elapsed_s=time.monotonic()-started,scientific_decision='abstain')
            write(DATA/'summary.json',s);write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',allocated_numerical_threads=0,total=8,completed=8))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=str(error),charged_completed_artifacts=len(artifacts),completed=len(rows)))
            write(DATA/'status.json',dict(state='stopped',allocated_numerical_threads=0));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print('Completed 28 fixed-point calls; no optimizer starts or label changes.')


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
