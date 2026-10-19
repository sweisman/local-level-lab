# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite known-answer multi-start controls; no archive input or native kernel."""
import argparse
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
from lll.ilvis0_receipt_journal import durable_write,encoded
NAME='ilvis0-multistart-controls-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
LIMITS=dict(maximum_starts=24,maximum_evaluations_per_start=200,maximum_function_evaluations=4800,
    numerical_threads=4,maximum_wall_s=120,retries=0)
CONFIGS=[dict(name='left_well',a=-.45,b=.55),dict(name='right_well',a=.45,b=-.55),
    dict(name='near_bound',a=.98,b=-.5),dict(name='boundary',a=1.2,b=1.7)]


def load(p):
    import json
    return json.loads(Path(p).read_bytes())


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    parent=load(ROOT/'data/ilvis0-horizontal-timing-path-20261019/manifest.json')
    sources=dict(parent['sources'])
    for name in ('analysis/tests/ilvis0_multistart_controls.py','analysis/lll/ilvis0_multistart.py',
                 'analysis/tests/test_ilvis0_multistart.py',str((PUBLIC/'PLAN.md').relative_to(ROOT))):sources[name]=sha(ROOT/name)
    for p,h in sources.items():
        if sha(ROOT/p)!=h:raise ValueError('preserved qualified dependency changed')
        target=DATA/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
    tasks=[dict(identity=f"{c['name']}::{seed}::{grid}",config=c,seed=seed,grid=grid)
           for c in CONFIGS for seed in ('negative','positive') for grid in range(3)]
    write(DATA/'manifest.json',dict(version='known-answer-multistart-v1',environment=environment(),sources=sources,
        limits=LIMITS,plan=dict(tasks=tasks,**LIMITS),timing_grid=[-.8,0.,.8],scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def verify():
    m=load(DATA/'manifest.json')
    if m['environment']!=environment() or m['limits']!=LIMITS:raise ValueError('environment/allowance changed')
    for p,h in m['sources'].items():
        if sha(ROOT/p)!=h or sha(DATA/'source-freeze'/p)!=h:raise ValueError('frozen source changed')
    return m


def expected(config):
    a,b=config['a'],config['b'];epsilon=.08
    # dJ/dt = 2(t-a)[(t-b)(2t-a-b)+epsilon²].
    candidates=[-1.,1.]
    if -1<=a<=1:candidates.append(a)
    disc=(a+3*b)**2-8*(b*(a+b)+epsilon**2)
    if disc>=0:
        candidates.extend(t for t in ((a+3*b-math.sqrt(disc))/4,(a+3*b+math.sqrt(disc))/4) if -1<=t<=1)
    def residual(t):return [(t-a)*(t-b),epsilon*(t-a),0.,-.2]
    t=min(candidates,key=lambda t:sum(v*v for v in residual(t)))
    return dict(time=t,residual=residual(t),cost=sum(v*v for v in residual(t)))


def publish():
    c=load(DATA/'completion.json');s=load(DATA/'summary.json')
    if c['manifest_sha256']!=sha(DATA/'manifest.json') or c['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('completion mismatch')
    names=['manifest.json','authorization.json','summary.json','completion.json','start.json']
    for r in s['results']:
        if sha(DATA/r['artifact'])!=r['artifact_sha256']:raise ValueError('result changed')
        names.append(r['artifact'])
    for n in names:shutil.copy2(DATA/n,PUBLIC/n)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Known-answer multi-start qualification','',
        f"Completed 24 constructed starts /{s['function_evaluations']} function calls. Qualification **{'passed' if s['passed'] else 'failed'}**. No archive files, native kernels or observed optimizer starts were used.",'',
        '| Control | Algebraic best cost | Negative-seed best | Positive-seed best | Selected/repeat checks |',
        '|---|---:|---:|---:|---|']
    for r in s['controls']:
        lines.append(f"| {r['name']} | {r['expected']['cost']:.10g} | {r['selections'][0]['selected_cost']:.10g} | {r['selections'][1]['selected_cost']:.10g} | {'pass' if r['passed'] else 'fail'} |")
    lines+=['','All attempts remain saved, including local optima and failed stops. Choosing the best checked start is not a global-optimum certificate for observed data. Physical scores and numerical gates are unchanged.','',
        '[Frozen scope and limits](PLAN.md) · [Timing-path evidence](../ilvis0-horizontal-timing-path-20261019/DIAGNOSIS.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in [*names,'README.md','PLAN.md']}))


def run():
    m=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged/completed controls cannot restart')
        write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        import numpy as np
        from lll import ilvis0_multistart as policy,ilvis0_projected_ridge as candidate
        from lll.ilvis0_receipt_journal import Ledger
        from lll.ilvis0_estimator import EvaluationLimit
        book=Ledger(DATA,sha(DATA/'manifest.json'),[t['identity'] for t in m['plan']['tasks']],fit_limit=200,diagnostic_limit=0)
        class Bounds:
            active=['time_offset','calibration','invisible','at_bound']
            def decode(self,u):
                if len(u)!=4 or not np.all(np.isfinite(u)) or np.any(abs(u)>1):raise ValueError('finite box point required')
                return dict(zip(self.active,u))
        class Problem:
            bounds=Bounds()
            projection=type('Projection',(),dict(axes=('latitude','longitude')))()
            def __init__(self,config,identity):self.config=config;self.identity=identity
            def raw(self,u):
                t,c,n,q=u;a,b=self.config['a'],self.config['b']
                r=np.array([(t-a)*(t-b),.08*(t-a),10*(c-.6*np.sin(4*t)),q-1.2])
                j=np.array([[2*t-a-b,0,0,0],[.08,0,0,0],[-24*np.cos(4*t),10,0,0],[0,0,0,1.]])
                return r,j,0
            def residual_tangent(self,u,model):return book.call(self.identity,'fit','constructed_tangent',self.raw,u)
            def physical_step(self,d):return np.column_stack((np.array(d).reshape(-1,2),np.zeros(2)))
        rows=[];controls=[];started=time.monotonic()
        def alarm(*args):raise TimeoutError('120-second software allowance exhausted')
        previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(120)
        try:
            for task in m['plan']['tasks']:
                identity=task['identity'];book.start(identity)
                write(DATA/'status.json',dict(state='software_controls',pid=os.getpid(),allocated_numerical_threads=4,total=24,completed=len(rows),identity=identity))
                seed=[0.,-.6,-.7,-.4] if task['seed']=='negative' else [0.,.6,.7,.4]
                start=policy.starts(seed,Bounds.active,m['timing_grid'])[task['grid']]
                problem=Problem(task['config'],identity)
                fit=candidate.fit_control(problem,'flat_still',start=start,maximum_evaluations=200)
                if fit['evaluations']!=book.count(identity,'fit'):raise ValueError('software call accounting mismatch')
                residual=fit['local_linearization']['residual']
                row=dict(task,fit=fit,start_point=start,predicted_residual=residual,passed=fit['converged'])
                name=identity.replace('::','-')+'.json.gz';durable_write(DATA/name,gzip.compress(encoded(row),mtime=0),replace=False)
                rows.append(dict(row,artifact=name,artifact_sha256=sha(DATA/name)))
            for config in CONFIGS:
                exp=expected(config);selections=[];selected=[]
                for seed in ('negative','positive'):
                    group=[r for r in rows if r['config']['name']==config['name'] and r['seed']==seed]
                    selection=policy.select(group,expected_ids=[r['identity'] for r in group]);selections.append(selection)
                    selected.append(next(r for r in group if r['identity']==selection['selected_identity']))
                differences=np.array(selected[0]['predicted_residual'])-selected[1]['predicted_residual']
                expected_errors=[float(np.max(abs(np.array(r['predicted_residual'])-exp['residual']))) for r in selected]
                physical=differences.reshape(-1,2);rms=np.sqrt(np.mean(physical**2,axis=0));maximum=np.max(abs(physical),axis=0)
                passed=all(s['passed'] and abs(s['selected_cost']-exp['cost'])<=1e-8*max(exp['cost'],1.) for s in selections)
                passed=bool(passed and max(expected_errors)<=1e-5 and np.all(rms<=.001) and np.all(maximum<=.01))
                controls.append(dict(name=config['name'],expected=exp,selections=selections,passed=passed,
                    expected_residual_max_errors=expected_errors,repeat_rms_m=rms.tolist(),repeat_max_m=maximum.tolist()))
            verify();book.export()
            s=dict(state='complete',results=rows,controls=controls,passed=all(c['passed'] for c in controls),
                function_evaluations=len(book.read('sweeps')),native_evaluations=0,observed_starts=0,
                software_starts=24,elapsed_s=time.monotonic()-started,scientific_decision='abstain')
            write(DATA/'summary.json',s);write(DATA/'completion.json',dict(manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',allocated_numerical_threads=0,total=24,completed=24))
        except BaseException as e:
            write(DATA/'failure.json',dict(error=str(e),completed=len(rows)));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print('Multi-start software qualification '+('passed' if s['passed'] else 'failed')+'.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepare-only',action='store_true');p.add_argument('--package-only',action='store_true');a=p.parse_args()
    if a.package_only:publish()
    elif a.prepare_only:prepare()
    else:
        from lll.compute_budget import environment as budget_environment
        os.environ.update(budget_environment(workers=1,threads=4,reserved=0));run()
