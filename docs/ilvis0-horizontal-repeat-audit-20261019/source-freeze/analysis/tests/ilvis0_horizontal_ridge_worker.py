# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite staged software qualification; never fits recorded measurements."""
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
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_projected_controls_worker import environment,load,sha,write
from lll.ilvis0_receipt_journal import durable_write,encoded

NAME='ilvis0-horizontal-ridge-qualification-20261018'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
PARENT=ROOT/'docs/ilvis0-projected-horizontal-fullcal-20261018'
PROBE=ROOT/'docs/ilvis0-horizontal-probe-20261018'
LIMITS=dict(maximum_native_evaluations=1616,maximum_starts=8,maximum_tangents_per_start=200,
            maximum_diagnostics_per_start=2,maximum_wall_s=1800,numerical_threads=4,retries=0,
            observed_starts=0,original_recording_reads=0)


def tasks(parent):
    expected={f'{m}-{c}-horizontal-{s}' for m in ('sphere_rotating','sphere_still','flat_still')
              for c in ('bias1_unsubtracted','bias1_profiled_removal') for s in ('zero','opposed')}
    if len(parent)!=12 or {r['identity'] for r in parent}!=expected:raise ValueError('exact parent matrix required')
    rows=[]
    for r in parent:
        if r['model']=='flat_still' or (r['model']=='sphere_still' and r['case_id']=='bias1_unsubtracted'):
            rows.append(dict(identity=r['identity']+'--ridge-continuation',parent_identity=r['identity'],
                model=r['model'],case_id=r['case_id'],profile=r['profile'],clock=r['clock'],axes=r['axes'],
                start=r['start'],point=r['fit']['normalized_parameters'],phase='continuation'))
    for model in ('sphere_rotating','flat_still'):
        rows.append(dict(identity=model+'--fresh-opposed',model=model,case_id='bias1_unsubtracted',profile=False,
            clock='nominal',axes=['latitude','longitude'],start='opposed',phase='fresh'))
    return rows


def review(parent,rows,compare):
    expected=tasks(parent)
    if len(rows)!=8 or {r['identity'] for r in rows}!={r['identity'] for r in expected}:
        raise ValueError('all eight charged identities required')
    replacements={r['parent_identity']:r for r in rows if r['phase']=='continuation'}
    primaries=[replacements.get(r['identity'],r) for r in parent]
    companions=[r for r in parent if r['identity'] not in replacements]
    if len(companions)!=6 or not all(r['passed'] for r in companions):raise ValueError('six exact passing companions required')
    pairs=[]
    for a in primaries:
        if a['start']!='zero':continue
        b=next(r for r in primaries if r['model']==a['model'] and r['case_id']==a['case_id'] and r['start']=='opposed')
        pairs.append(dict(model=a['model'],case_id=a['case_id'],**compare(a,b)))
    return dict(primaries=primaries,pairs=pairs,
        passed=bool(all(r['passed'] for r in rows) and all(r['passed'] for r in primaries) and all(p['passed'] for p in pairs)),
        reused_parent_identities=[r['identity'] for r in companions])


def verify():
    m=load(DATA/'manifest.json')
    if m['environment']!=environment() or m['limits']!=LIMITS:raise ValueError('environment or allowance changed')
    for p,digest in {**m['sources'],**m['inputs']}.items():
        if sha(ROOT/p)!=digest:raise ValueError('frozen dependency changed: '+p)
    for p,digest in m['sources'].items():
        if sha(DATA/'source-freeze'/p)!=digest:raise ValueError('source snapshot changed')
    return m


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    inputs={}
    for p in (PARENT,PROBE):
        done=load(p/'completion.json')
        if done['manifest_sha256']!=sha(p/'manifest.json') or done['summary_sha256']!=sha(p/'summary.json'):
            raise ValueError('parent completion mismatch')
        for n,digest in load(p/'evidence-receipt.json')['artifacts'].items():
            if sha(p/n)!=digest:raise ValueError('parent receipt mismatch')
        for n in ('manifest.json','summary.json','completion.json','evidence-receipt.json'):
            inputs[str((p/n).relative_to(ROOT))]=sha(p/n)
    probes=load(PROBE/'summary.json')['results']
    if len(probes)!=12 or not all(next(v for v in r['probes'] if v['method']=='scaled_ridge')['passes_local_limits'] for r in probes):
        raise ValueError('all twelve fixed-point ridge probes required')
    tests=['analysis/tests/test_ilvis0_projected_ridge.py','analysis/tests/test_ilvis0_horizontal_ridge_worker.py']
    result=subprocess.run([sys.executable,'-m','pytest',*tests,'-q','--junitxml='+str(DATA/'software-tests.xml')],cwd=ROOT,capture_output=True,text=True,timeout=60)
    (DATA/'software-tests.log').write_text(result.stdout+result.stderr)
    checks=list(ET.parse(DATA/'software-tests.xml').iter('testcase'))
    if result.returncode or len(checks)!=10 or any(list(c) for c in checks):raise ValueError('ten constructed checks must pass')
    sources=dict(load(PARENT/'manifest.json')['sources'])
    for p in ['analysis/lll/ilvis0_projected_ridge.py',*tests,'analysis/tests/ilvis0_horizontal_ridge_worker.py',str((PUBLIC/'PLAN.md').relative_to(ROOT))]:sources[p]=sha(ROOT/p)
    for p,digest in sources.items():
        if sha(ROOT/p)!=digest:raise ValueError('original source mismatch')
        target=DATA/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
    m=dict(version='horizontal-ridge-continuation-qualification-v1',environment=environment(),sources=sources,
           inputs=inputs,limits=LIMITS,plan=dict(tasks=tasks(load(PARENT/'summary.json')['results']),**LIMITS))
    write(DATA/'manifest.json',m);write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def publish():
    done=load(DATA/'completion.json');s=load(DATA/'summary.json')
    if done['summary_sha256']!=sha(DATA/'summary.json') or done['manifest_sha256']!=sha(DATA/'manifest.json'):raise ValueError('completion mismatch')
    names=['manifest.json','authorization.json','summary.json','completion.json','start.json','calls.jsonl','starts.jsonl','software-tests.xml','software-tests.log']
    for r in s['results']:
        name=r['identity']+'.json.gz'
        if sha(DATA/name)!=r['artifact_sha256']:raise ValueError('result artifact changed')
        names.append(name)
    for n in names:shutil.copy2(DATA/n,PUBLIC/n)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Horizontal ridge-probe qualification','',
        f"**{'Passed' if s['passed'] else 'Not qualified'}:** {sum(r['passed'] for r in s['results'])}/8 staged fits; {sum(p['passed'] for p in s['pairs'])}/6 combined paired comparisons. Used {s['native_evaluations']} of 1,616 permitted native calls, with no original-recording reads or observed fits.",
        '', '| Identity | Individual check | Final cost | Native fit calls |', '|---|---|---:|---:|']
    for r in s['results']:lines.append(f"| {r['identity']} | {r['passed']} | {r.get('fit',{}).get('residual_sum_squares')} | {r['native_fit_calls']} |")
    lines+=['','Six passing parent companions are reused by exact identity; every affected pair and both fresh controls must pass. This staged software method does not relabel the failed one-stage study or calibrate scientific uncertainty.',
            '', '[Frozen scope](PLAN.md) · [Next analyses](../NEXT_STEPS.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in [*names,'README.md','PLAN.md']}))


def run():
    m=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists() or (DATA/'completion.json').exists():raise ValueError('charged batch cannot restart')
        verify();write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        write(DATA/'status.json',dict(state='running',pid=os.getpid(),allocated_numerical_threads=4,total=8,completed=0))
        import numpy as np
        from lll import ilvis0_geographic_controls as geographic,ilvis0_exploratory as explore,ilvis0_precision as precision
        from lll import ilvis0_projected_fullcal as fullcal,ilvis0_projected_ridge as candidate
        from lll.ilvis0_projected_fitting import ProjectedProblem
        kernel,kmeta=explore.load_kernel(DATA/'kernel');tangent,tmeta=precision.load_tangent(DATA/'kernel')
        rows=[];calls=[];started=time.monotonic()
        def alarm(*args):raise TimeoutError('finite qualification wall ceiling exceeded')
        previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(1800)
        class Counted:
            def __init__(self,base,identity):
                self.base=base;self.identity=identity;self.bounds=base.bounds;self.gps=base.gps;self.cholesky=base.cholesky
                self.fit_calls=0;self.diagnostic_calls=0
            def charge(self,phase,u):
                count=self.fit_calls if phase=='fit' else self.diagnostic_calls;limit=200 if phase=='fit' else 2
                if count>=limit or len(calls)>=1616:raise ValueError('finite native allowance exhausted')
                value=dict(identity=self.identity,phase=phase,number=len(calls)+1,point=np.asarray(u).tolist())
                with (DATA/'calls.jsonl').open('ab') as stream:stream.write(encoded(value));stream.flush();os.fsync(stream.fileno())
                calls.append(value)
                if phase=='fit':self.fit_calls+=1
                else:self.diagnostic_calls+=1
            def residual_tangent(self,u,model):self.charge('fit',u);return self.base.residual_tangent(u,model)
            def predict(self,u,model):self.charge('diagnostic',u);return self.base.prediction_tangent(u,model)[0]
        try:
            for task in m['plan']['tasks']:
                write(DATA/'status.json',dict(state='working',pid=os.getpid(),allocated_numerical_threads=4,total=8,
                    completed=len(rows),identity=task['identity'],native_evaluations=len(calls)))
                with (DATA/'starts.jsonl').open('ab') as stream:
                    stream.write(encoded(dict(identity=task['identity'],maximum_evaluations=200)));stream.flush();os.fsync(stream.fileno())
                row=copy.deepcopy(task);counted=None
                try:
                    f=geographic.fixture(task['model'],task['clock']);base=fullcal.problem(task,f,kernel,tangent)
                    counted=Counted(base,task['identity']);p=ProjectedProblem(counted,('latitude','longitude'))
                    initial=np.array(task['point']) if task['phase']=='continuation' else fullcal.start(task,base)
                    fit=candidate.fit_control(p,task['model'],start=initial,maximum_evaluations=200)
                    point=np.array(fit['normalized_parameters']);prediction=counted.predict(point,task['model'])
                    reference=counted.predict(fullcal.truth_point(task,f,base),task['model'])
                    truth=base.whiten(reference-base.gps);truth,_=p.projection.apply(truth,np.zeros((len(truth),len(point))))
                    error=(prediction-base.gps)*f['metric']
                    row.update(fit=fit,prediction_error_m=error.tolist(),truth_cost=float(truth@truth),
                        maximum_retained_error_m=float(np.max(abs(error[:,:2]))),maximum_all_axis_error_m=float(np.max(abs(error))),
                        status='complete',start_point=initial.tolist())
                    row['passed']=fullcal.assess_fit(row)
                except TimeoutError:raise
                except Exception as error:row.update(status='error',passed=False,error=type(error).__name__+': '+str(error))
                row.update(native_fit_calls=counted.fit_calls if counted else 0,native_diagnostic_calls=counted.diagnostic_calls if counted else 0)
                path=DATA/(row['identity']+'.json.gz');durable_write(path,gzip.compress(encoded(row),mtime=0),replace=False)
                row['artifact_sha256']=sha(path);rows.append(row)
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)))
            combined=review(load(PARENT/'summary.json')['results'],rows,fullcal.compare_pair)
            verify();s=dict(state='complete',results=rows,**combined,native_evaluations=len(calls),generated_starts=8,
                observed_starts=0,original_recording_reads=0,elapsed_s=time.monotonic()-started,
                scientific_decision='abstain',archival_fits_qualified=False,kernel_metadata=dict(value=kmeta,tangent=tmeta))
            write(DATA/'summary.json',s);write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',allocated_numerical_threads=0,completed=8,total=8))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=str(error),charged_native_calls=len(calls),completed=len(rows)))
            write(DATA/'status.json',dict(state='stopped',allocated_numerical_threads=0));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print('Qualification complete; passed='+str(s['passed']))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--detach',action='store_true');parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
    if args.detach and args.package_only:raise ValueError('one mode required')
    if args.package_only:publish()
    elif args.detach:
        prepare()
        with (DATA/'launch.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (DATA/'launch.json').exists() or (DATA/'start.json').exists():raise ValueError('launch already charged')
            with (DATA/'worker.log').open('ab') as log:
                child=subprocess.Popen([sys.executable,__file__],cwd=ROOT,env=os.environ.copy(),stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
            write(DATA/'launch.json',dict(pid=child.pid));print('Launched qualification PID '+str(child.pid))
    else:run()
