# SPDX-License-Identifier: AGPL-3.0-or-later
"""One finite continuation of the exact remaining generated-data pair."""
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
from ilvis0_projected_controls_worker import environment,load,sha,write
from lll.ilvis0_receipt_journal import durable_write,encoded
NAME='ilvis0-horizontal-pair-continuation-20261018'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
PARENT=ROOT/'docs/ilvis0-horizontal-ridge-qualification-20261018'
LIMITS=dict(maximum_native_evaluations=1204,maximum_starts=2,maximum_tangents_per_start=600,
            maximum_diagnostics_per_start=2,maximum_wall_s=900,numerical_threads=4,retries=0,
            original_recording_reads=0,observed_starts=0)


def select(parent):
    failures=[p for p in parent['pairs'] if not p['passed']]
    if (len(parent['results'])!=8 or not all(r['passed'] for r in parent['results'])
            or len(parent['pairs'])!=6 or len(failures)!=1
            or (failures[0]['model'],failures[0]['case_id'])!=('sphere_still','bias1_unsubtracted')):
        raise ValueError('exact single remaining paired-cost failure required')
    primaries=parent['primaries']
    expected={(m,c,s) for m in ('sphere_rotating','sphere_still','flat_still')
              for c in ('bias1_unsubtracted','bias1_profiled_removal') for s in ('zero','opposed')}
    if (len(primaries)!=12 or {(r['model'],r['case_id'],r['start']) for r in primaries}!=expected
            or not all(r['passed'] for r in primaries)):
        raise ValueError('complete twelve passing parent primaries required')
    return [copy.deepcopy(r) for r in primaries if r['model']=='sphere_still' and r['case_id']=='bias1_unsubtracted']


def verify():
    m=load(DATA/'manifest.json')
    if m['environment']!=environment() or m['limits']!=LIMITS:raise ValueError('environment or allowance changed')
    for p,d in {**m['sources'],**m['inputs']}.items():
        if sha(ROOT/p)!=d:raise ValueError('frozen dependency changed: '+p)
    for p,d in m['sources'].items():
        if sha(DATA/'source-freeze'/p)!=d:raise ValueError('source snapshot changed')
    return m


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    done=load(PARENT/'completion.json')
    if done['manifest_sha256']!=sha(PARENT/'manifest.json') or done['summary_sha256']!=sha(PARENT/'summary.json'):raise ValueError('parent completion mismatch')
    for p,d in load(PARENT/'evidence-receipt.json')['artifacts'].items():
        if sha(PARENT/p)!=d:raise ValueError('parent publication changed')
    parent=load(PARENT/'summary.json');endpoints=select(parent)
    tests=subprocess.run([sys.executable,'-m','pytest','analysis/tests/test_ilvis0_horizontal_pair_worker.py','-q'],cwd=ROOT,capture_output=True,text=True,timeout=30)
    (DATA/'software-tests.log').write_text(tests.stdout+tests.stderr)
    if tests.returncode:raise ValueError('pair-selection software tests failed')
    sources=dict(load(PARENT/'manifest.json')['sources'])
    for p in ('analysis/tests/ilvis0_horizontal_pair_worker.py','analysis/tests/test_ilvis0_horizontal_pair_worker.py',str((PUBLIC/'PLAN.md').relative_to(ROOT))):sources[p]=sha(ROOT/p)
    for p,d in sources.items():
        if sha(ROOT/p)!=d:raise ValueError('preserved source changed')
        target=DATA/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
    tasks=[dict(identity=r['identity']+'--pair600',model=r['model'],case_id=r['case_id'],start=r['start'],
                clock=r['clock'],profile=r['profile'],axes=r['axes'],point=r['fit']['normalized_parameters']) for r in endpoints]
    m=dict(version='horizontal-pair-continuation-v1',sources=sources,environment=environment(),limits=LIMITS,
        inputs={str((PARENT/p).relative_to(ROOT)):sha(PARENT/p) for p in ('manifest.json','summary.json','completion.json','evidence-receipt.json')},
        plan=dict(tasks=tasks,**LIMITS))
    write(DATA/'manifest.json',m);write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def publish():
    d=load(DATA/'completion.json');s=load(DATA/'summary.json')
    if d['manifest_sha256']!=sha(DATA/'manifest.json') or d['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('completion mismatch')
    names=['manifest.json','authorization.json','summary.json','completion.json','start.json','starts.jsonl','calls.jsonl','software-tests.log']
    for r in s['results']:
        n=r['identity']+'.json.gz'
        if sha(DATA/n)!=r['artifact_sha256']:raise ValueError('result artifact changed')
        names.append(n)
    for n in names:shutil.copy2(DATA/n,PUBLIC/n)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    (PUBLIC/'README.md').write_text('# Remaining horizontal paired-cost continuation\n\n'
        +f"**{'Passed' if s['passed'] else 'Not qualified'}:** {sum(r['passed'] for r in s['results'])}/2 individual continuations and {sum(p['passed'] for p in s['pairs'])}/6 combined paired comparisons. Used {s['native_evaluations']} of 1,204 allowed native calls.\n\n"
        +'Ten passing primary companions and both preceding fresh controls are preserved by exact identity. Earlier failed qualifications remain failed. These are generated-motion software controls, with no original-recording reads, observed fits or scientific label changes.\n\n'
        +'[Frozen scope](PLAN.md) · [Next analyses](../NEXT_STEPS.md).\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in [*names,'README.md','PLAN.md']}))


def run():
    m=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists() or (DATA/'completion.json').exists():raise ValueError('charged pair study cannot restart')
        verify();write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        write(DATA/'status.json',dict(state='running',pid=os.getpid(),allocated_numerical_threads=4,total=2,completed=0))
        import numpy as np
        from lll import ilvis0_geographic_controls as geographic,ilvis0_exploratory as explore,ilvis0_precision as precision
        from lll import ilvis0_projected_fullcal as fullcal,ilvis0_projected_ridge as candidate
        from lll.ilvis0_projected_fitting import ProjectedProblem
        kernel,kmeta=explore.load_kernel(DATA/'kernel');tangent,tmeta=precision.load_tangent(DATA/'kernel')
        results=[];calls=[];started=time.monotonic()
        def alarm(*args):raise TimeoutError('finite pair-continuation wall ceiling exceeded')
        previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(900)
        class Counted:
            def __init__(self,base,identity):
                self.base=base;self.identity=identity;self.bounds=base.bounds;self.gps=base.gps;self.cholesky=base.cholesky
                self.fit_calls=0;self.diagnostic_calls=0
            def charge(self,phase,u):
                if len(calls)>=1204 or (self.fit_calls>=600 if phase=='fit' else self.diagnostic_calls>=2):raise ValueError('finite native allowance exhausted')
                value=dict(identity=self.identity,phase=phase,point=np.asarray(u).tolist(),number=len(calls)+1)
                with (DATA/'calls.jsonl').open('ab') as stream:stream.write(encoded(value));stream.flush();os.fsync(stream.fileno())
                calls.append(value)
                if phase=='fit':self.fit_calls+=1
                else:self.diagnostic_calls+=1
            def residual_tangent(self,u,model):self.charge('fit',u);return self.base.residual_tangent(u,model)
            def predict(self,u,model):self.charge('diagnostic',u);return self.base.prediction_tangent(u,model)[0]
        try:
            for task in m['plan']['tasks']:
                write(DATA/'status.json',dict(state='working',pid=os.getpid(),allocated_numerical_threads=4,total=2,completed=len(results),identity=task['identity'],native_evaluations=len(calls)))
                with (DATA/'starts.jsonl').open('ab') as stream:stream.write(encoded(dict(identity=task['identity'],maximum_evaluations=600)));stream.flush();os.fsync(stream.fileno())
                f=geographic.fixture(task['model'],task['clock']);base=fullcal.problem(task,f,kernel,tangent);c=Counted(base,task['identity'])
                p=ProjectedProblem(c,('latitude','longitude'));point=np.array(task['point'])
                fit=candidate.fit_control(p,task['model'],start=point,maximum_evaluations=600)
                prediction=c.predict(np.array(fit['normalized_parameters']),task['model']);reference=c.predict(fullcal.truth_point(task,f,base),task['model'])
                truth=base.whiten(reference-base.gps);truth,_=p.projection.apply(truth,np.zeros((len(truth),len(point))))
                error=(prediction-base.gps)*f['metric']
                row=dict(task,fit=fit,prediction_error_m=error.tolist(),truth_cost=float(truth@truth),status='complete',
                    native_fit_calls=c.fit_calls,native_diagnostic_calls=c.diagnostic_calls,
                    maximum_retained_error_m=float(np.max(abs(error[:,:2]))),maximum_all_axis_error_m=float(np.max(abs(error))))
                row['passed']=fullcal.assess_fit(row)
                target=DATA/(row['identity']+'.json.gz');durable_write(target,gzip.compress(encoded(row),mtime=0),replace=False)
                row['artifact_sha256']=sha(target);results.append(row)
                write(DATA/'progress.json',dict(completed=len(results),passed=sum(r['passed'] for r in results)))
            parent=load(PARENT/'summary.json');select(parent)
            replacements={r['start']:r for r in results}
            primaries=[replacements[r['start']] if r['model']=='sphere_still' and r['case_id']=='bias1_unsubtracted' else r for r in parent['primaries']]
            pairs=[]
            for a in primaries:
                if a['start']!='zero':continue
                b=next(r for r in primaries if r['model']==a['model'] and r['case_id']==a['case_id'] and r['start']=='opposed')
                pairs.append(dict(model=a['model'],case_id=a['case_id'],**fullcal.compare_pair(a,b)))
            verify();s=dict(state='complete',results=results,primaries=primaries,pairs=pairs,
                passed=bool(all(r['passed'] for r in results) and all(p['passed'] for p in pairs)),
                native_evaluations=len(calls),elapsed_s=time.monotonic()-started,observed_starts=0,generated_starts=2,
                original_recording_reads=0,scientific_decision='abstain',kernel_metadata=dict(value=kmeta,tangent=tmeta))
            write(DATA/'summary.json',s);write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',allocated_numerical_threads=0,total=2,completed=2))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=str(error),charged_native_calls=len(calls),completed=len(results)))
            write(DATA/'status.json',dict(state='stopped',allocated_numerical_threads=0));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print('Pair continuation complete; passed='+str(s['passed']))


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
            write(DATA/'launch.json',dict(pid=child.pid));print('Launched pair continuation PID '+str(child.pid))
    else:run()
