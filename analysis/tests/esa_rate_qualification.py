# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite engineering-rate quadrature/body controls, with no archive reads."""
import argparse
import fcntl
import math
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment as guarded_environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in guarded_environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with four threads')
from ilvis0_channel_envelope_worker import sha,load,write,environment
from lll import airquantumgrav_increments as increments,airquantumgrav_body_bounds as body

NAME='esa-rate-qualification-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/esa-rate-qualification'
TASKS=[dict(kind='quadrature',method=method,family=family,profile=profile)
    for method in increments.METHODS for family in ('constant','linear','sinusoidal') for profile in range(4)]
TASKS += [dict(kind='body',period=h,variant=v) for h in (1/300.,.0049,.1) for v in range(4)]
TASKS=[dict(t,identity=f"{t['kind']}-{i:02d}") for i,t in enumerate(TASKS)]
LIMITS=dict(maximum_identities=48,maximum_component_intervals=1152,maximum_ode_solves=24,
    maximum_ode_rhs=24000,maximum_wall_s=60,numerical_threads=4,native_evaluations=0,
    optimizer_starts=0,original_reads=0,retries=0,deadline_policy='cooperative-no-signals')
SOURCES=['analysis/lll/'+n for n in ('airquantumgrav_increments.py','airquantumgrav_body_bounds.py',
    'compute_budget.py','ilvis0_receipt_journal.py')]
SOURCES += ['analysis/tests/'+n for n in ('esa_rate_qualification.py','test_esa_rate_qualification.py',
    'test_airquantumgrav_increments.py','test_airquantumgrav_body_bounds.py','ilvis0_channel_envelope_worker.py')]
SOURCES += ['docs/esa-rate-adapter/PLAN.md','docs/esa-rate-adapter/BODY_BOUNDS.md']


def quadrature(task):
    profile=task['profile'];times=[100.]
    for i in range(16):times.append(times[-1]+(.003+profile*.0002+(.0002 if i%2 else -.0002)))
    offsets=[.001,-.002,.003,.02,-.01,-9.81]
    slopes=[.1*(i+1) if task['family']=='linear' else 0. for i in range(6)]
    amplitudes=[.002*(i+1) if task['family']=='sinusoidal' else 0. for i in range(6)]
    w=3.+profile*5.;phases=[.2*i for i in range(6)]
    def values(t):return [a+b*(t-100.)+c*math.sin(w*(t-100.)+p) for a,b,c,p in zip(offsets,slopes,amplitudes,phases)]
    rows=[]
    for i,t in enumerate(times):
        v=values(t);rows.append(dict(gps_time_s=t,angular_rate_rads=v[:3],acceleration_mps2=v[3:],line_number=i+1))
    actual=list(increments.intervals(rows,method=task['method']))
    stream=increments.IntervalStream(method=task['method']);chunked=list(stream.push(rows[:7]))+list(stream.push(rows[7:]))
    error=0.;excess=0.
    for interval in actual:
        a=interval['raw_left']['gps_time_s']-100.;b=interval['raw_right']['gps_time_s']-100.;h=interval['dt_s']
        for j,value in enumerate(interval['dtheta_rad']+interval['dv_mps']):
            exact=offsets[j]*h+slopes[j]*h*(a+b)/2+amplitudes[j]*(math.cos(w*a+phases[j])-math.cos(w*b+phases[j]))/w
            allowance=increments.integral_error_bound(h,method=task['method'],
                first_derivative_bound=abs(slopes[j])+abs(amplitudes[j]*w),second_derivative_bound=abs(amplitudes[j]*w*w))
            discrepancy=abs(value-exact);error=max(error,discrepancy);excess=max(excess,discrepancy-allowance)
    preserved=all(r['raw_left']==rows[i] and r['raw_right']==rows[i+1] for i,r in enumerate(actual))
    return dict(passed=actual==chunked and excess<=1e-11 and preserved,maximum_component_error=error,
        maximum_excess_over_mathematical_bound=excess,component_intervals=32,ode_solves=0,ode_rhs=0,
        raw_preserved=preserved)


def body_control(task,deadline):
    import numpy as np
    from scipy.integrate import solve_ivp
    from scipy.spatial.transform import Rotation
    h=task['period'];variant=task['variant'];count=0
    a=np.array([.12,-.03,.02]);b=np.array([-.02,.11,.04]) if variant&1 else a.copy()
    f=np.array([.1,-.2,-9.81]);g=np.array([-.2,.4,-9.7]) if variant&2 else f.copy()
    def rhs(t,y):
        nonlocal count
        if count>=2000 or time.time()>=deadline:raise ValueError('finite RHS/wall allowance exhausted')
        count+=1;r=y[:9].reshape(3,3);x,z,q=a+(b-a)*t/h
        skew=np.array([[0.,-q,z],[q,0.,-x],[-z,x,0.]])
        return np.r_[(r@skew).ravel(),r@(f+(g-f)*t/h)]
    initial=np.r_[np.eye(3).ravel(),np.zeros(3)];solutions=[]
    for steps in (16,32):
        sol=solve_ivp(rhs,[0.,h],initial,rtol=1e-12,atol=1e-14,max_step=h/steps)
        if not sol.success:raise ValueError('independent ODE did not finish')
        solutions.append(sol.y[:,-1])
    reference=solutions[-1];middle=(a+b)/2
    rotation=Rotation.from_rotvec(middle*h).as_matrix();force=Rotation.from_rotvec(middle*h/2).apply((f+g)*h/2)
    error_r=float(np.linalg.norm(reference[:9].reshape(3,3)-rotation,ord=2));error_f=float(np.linalg.norm(reference[9:]-force))
    allowance=body.local_bounds(a,b,f,g,h);agreement=float(np.max(abs(solutions[0]-solutions[1])))
    return dict(passed=error_r<=allowance['rotation_operator_error']+1e-11 and error_f<=allowance['force_integral_error_mps']+1e-11 and agreement<=1e-11,
        actual_rotation_operator_error=error_r,actual_force_integral_error_mps=error_f,
        mathematical_bounds=allowance,reference_resolution_difference=agreement,
        component_intervals=0,ode_solves=2,ode_rhs=count)


def prepare():
    if DATA.exists():raise ValueError('freeze exists; never overwrite')
    manifest=dict(version=NAME,tasks=TASKS,limits=LIMITS,environment=environment(),
        numerical_environment=guarded_environment(threads=4),sources={n:sha(ROOT/n) for n in SOURCES})
    write(DATA/'manifest.json',manifest)
    for name in SOURCES:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(DATA/'authorization.json',dict(scope='standing E01 generated-only software roadmap',manifest_sha256=sha(DATA/'manifest.json'),limits=LIMITS))


def verify(current=False):
    manifest=load(DATA/'manifest.json')
    if load(DATA/'authorization.json')['manifest_sha256']!=sha(DATA/'manifest.json'):raise ValueError('authorization hash mismatch')
    for name,digest in manifest['sources'].items():
        if sha(DATA/'source-freeze'/name)!=digest or (current and sha(ROOT/name)!=digest):raise ValueError('source freeze changed')
    if current and manifest['environment']!=environment():raise ValueError('environment changed')
    if (DATA/'completion.json').exists():
        seal=load(DATA/'completion.json')
        if seal['manifest_sha256']!=sha(DATA/'manifest.json') or seal['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('completion changed')
        for row in load(DATA/'summary.json')['results']:
            if row['artifact_sha256']!=sha(DATA/row['artifact']):raise ValueError('result changed')
    return manifest


def run():
    manifest=verify(True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('already started; no restart/retry')
        started=time.time();deadline=started+LIMITS['maximum_wall_s'];write(DATA/'start.json',dict(started_unix=started,pid=os.getpid()))
        write(DATA/'status.json',dict(state='running',numerical_threads=4,total=len(manifest['tasks'])),replace=True)
        rows=[];terminal=None;charged=dict(component_intervals=0,ode_solves=0,ode_rhs=0)
        for task in manifest['tasks']:
            if time.time()>=deadline:terminal='cooperative wall allowance exhausted';break
            reserve=dict(component_intervals=32 if task['kind']=='quadrature' else 0,
                ode_solves=2 if task['kind']=='body' else 0,ode_rhs=2000 if task['kind']=='body' else 0)
            for key,value in reserve.items():
                if charged[key]+value>manifest['limits']['maximum_'+key]:raise ValueError('finite reservation overflow')
                charged[key]+=value
            write(DATA/'charges'/(task['identity']+'.json'),dict(task=task,reservation=reserve,cumulative=charged))
            try:result=quadrature(task) if task['kind']=='quadrature' else body_control(task,deadline)
            except Exception as error:result=dict(passed=False,error_type=type(error).__name__,error=str(error))
            result=dict(result,identity=task['identity'],task=task,scientific_decision='abstain',original_reads=0,optimizer_starts=0)
            artifact='results/'+task['identity']+'.json';write(DATA/artifact,result)
            rows.append(dict(identity=task['identity'],passed=result['passed'],artifact=artifact,artifact_sha256=sha(DATA/artifact)))
            write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)),replace=True)
            if not result['passed']:terminal='qualification failed; remaining tasks not run';break
        state='terminal' if terminal else 'complete'
        write(DATA/'summary.json',dict(state=state,passed=not terminal and len(rows)==len(manifest['tasks']),results=rows,
            charged=charged,terminal_reason=terminal,elapsed_s=time.time()-started,native_evaluations=0,optimizer_starts=0,original_reads=0))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,numerical_threads=0,total=len(manifest['tasks'])),replace=True)
    publish()


def publish():
    manifest=verify();summary=load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['charges/'+r['identity']+'.json' for r in summary['results']]
    names += ['source-freeze/'+n for n in manifest['sources']]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    rows=[load(DATA/r['artifact']) for r in summary['results']]
    lines=['# ESA engineering-rate qualification','',f"{sum(r['passed'] for r in rows)}/{len(manifest['tasks'])} generated controls pass; state: {summary['state']}.",'',
        'Analytic component integrals are checked under left-hold, right-hold and linear-point hypotheses. '
        'Independent rotation/force ODE solutions check the local body approximation bounds. '
        'No actual sampling phase, coning compensation or instrument processing is inferred.','',
        '| Family | Completed | Passed |','|---|---:|---:|']
    for kind in ('quadrature','body'):
        selected=[r for r in rows if r['task']['kind']==kind];lines.append(f"| {kind} | {len(selected)} | {sum(r['passed'] for r in selected)} |")
    lines+=['','Reported rates remain original observations; constructed increments remain labeled calculations. '
        'The body bounds assume linear point samples and exclude geographic transport, gravity, antenna motion and cross-interval accumulation. '
        'No source recording was reread, no selection changed, and no model fit or protected confirmation evaluation ran.','',
        f"Reserved {summary['charged']['component_intervals']} component intervals, {summary['charged']['ode_solves']} ODE solves and "
        f"{summary['charged']['ode_rhs']} RHS evaluations; elapsed {summary['elapsed_s']:.2f} seconds.",'',
        '[Adapter and source distinctions](../esa-rate-adapter/README.md) · [Frozen plan](source-freeze/docs/esa-rate-adapter/PLAN.md) · '
        '[Body-bound derivation](source-freeze/docs/esa-rate-adapter/BODY_BOUNDS.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names+['README.md']}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 generated rate/body controls.')
    elif args.run:run();print('Finite rate/body qualification finished.')
    elif args.package_only:publish();print('Published saved results only.')
    else:verify();print('Verified rate/body freeze and saved artifacts.')


if __name__=='__main__':main()
