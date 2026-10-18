# SPDX-License-Identifier: AGPL-3.0-or-later
"""Persistent complete projected trust qualification, generated motion only."""
import argparse
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
from lll.compute_budget import environment as compute_environment
from lll import ilvis0_projected_trust_qualification as q
from lll.ilvis0_receipt_journal import durable_write,encoded
from ilvis0_projected_controls_worker import environment,sha,load,write

OUTPUT=ROOT/'data/ilvis0-projected-trust-qualification-20261018'
GUIDE=ROOT/'docs'/OUTPUT.name
PARENT=ROOT/'docs/ilvis0-projected-fitting-controls-20261018'
LIMITS=dict(maximum_starts=24,maximum_native_evaluations=3888,maximum_tangents_per_start=160,
    maximum_diagnostic_calls_per_start=2,numerical_threads=4,maximum_wall_s=1800,
    original_recording_reads=0,observed_starts=0,retries=0)


def prepare():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    parent=load(PARENT/'manifest.json');done=load(PARENT/'completion.json')
    if done['manifest_sha256']!=sha(PARENT/'manifest.json') or done['summary_sha256']!=sha(PARENT/'summary.json'):
        raise ValueError('verified preceding qualification required')
    values=dict(parent['sources'])
    for name in ('analysis/lll/ilvis0_solver_trust_v2.py','analysis/lll/ilvis0_projected_trust.py',
        'analysis/lll/ilvis0_projected_trust_qualification.py','analysis/tests/ilvis0_projected_trust_worker.py',
        'analysis/tests/test_ilvis0_projected_trust.py','analysis/tests/test_ilvis0_projected_trust_qualification.py'):
        values[name]=sha(ROOT/name)
    for name,digest in values.items():
        if sha(ROOT/name)!=digest:raise ValueError('preserved source changed: '+name)
    command=[sys.executable,'-m','pytest','-q','--tb=short','analysis/tests/test_ilvis0_projected_trust.py',
        'analysis/tests/test_ilvis0_projected_trust_qualification.py','--junitxml='+str(OUTPUT/'software-tests.xml')]
    with (OUTPUT/'software-tests.log').open('w') as stream:
        result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=30)
    checks=list(ET.parse(OUTPUT/'software-tests.xml').iter('testcase'))
    if result.returncode or len(checks)!=11 or any(c.find(t) is not None for c in checks for t in ('failure','error','skipped')):
        raise ValueError('all eleven constructed software checks required')
    inputs={str((PARENT/name).relative_to(ROOT)):sha(PARENT/name) for name in ('manifest.json','summary.json','completion.json')}
    diagnostic=ROOT/'docs/ilvis0-projected-endpoint-diagnostic-20261018'
    for name in ('manifest.json','summary.json','completion.json'):
        inputs[str((diagnostic/name).relative_to(ROOT))]=sha(diagnostic/name)
    inputs[str((GUIDE/'PLAN.md').relative_to(ROOT))]=sha(GUIDE/'PLAN.md')
    inputs[str((OUTPUT/'software-tests.xml').relative_to(ROOT))]=sha(OUTPUT/'software-tests.xml')
    for name in values:
        target=OUTPUT/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    write(OUTPUT/'manifest.json',dict(version='ilvis0-projected-trust-qualification-v1',environment=environment(),
        limits=LIMITS,plan=dict(LIMITS,tasks=q.tasks()),sources=values,inputs=inputs))
    write(OUTPUT/'authorization.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json'),**LIMITS))
    return verify()


def verify():
    m=load(OUTPUT/'manifest.json')
    if m['environment']!=environment() or m['limits']!=LIMITS or m['plan']!=dict(LIMITS,tasks=q.tasks()):
        raise ValueError('frozen environment or scope changed')
    if load(OUTPUT/'authorization.json')!=dict(manifest_sha256=sha(OUTPUT/'manifest.json'),**LIMITS):raise ValueError('allowance mismatch')
    for name,digest in {**m['sources'],**m['inputs']}.items():
        if sha(ROOT/name)!=digest:raise ValueError('frozen dependency changed: '+name)
    for name,digest in m['sources'].items():
        if sha(OUTPUT/'source-freeze'/name)!=digest:raise ValueError('snapshot changed')
    return m


def run():
    prepare()
    with (OUTPUT/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists() or (OUTPUT/'completion.json').exists():raise ValueError('charged batch cannot restart')
        m=verify();write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
        start=time.monotonic();rows=[];calls=[]
        def alarm(signum,frame):raise TimeoutError('fixed qualification wall allowance exhausted')
        previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(1800)
        try:
            import numpy as np
            from lll import ilvis0_geographic_controls as geographic,ilvis0_exploratory as explore
            from lll import ilvis0_precision as precision,ilvis0_projected_trust as candidate
            kernel,kmeta=explore.load_kernel(OUTPUT/'kernel');tangent,tmeta=precision.load_tangent(OUTPUT/'kernel')
            class Counted:
                def __init__(self,base,identity):
                    self.base=base;self.identity=identity;self.bounds=base.bounds;self.gps=base.gps;self.cholesky=base.cholesky
                    self.fit_calls=0;self.diagnostic_calls=0
                def charge(self,phase,point):
                    count=self.fit_calls if phase=='fit' else self.diagnostic_calls
                    maximum=160 if phase=='fit' else 2
                    if len(calls)>=3888 or count>=maximum:raise ValueError('generated native allowance exhausted')
                    row=dict(number=len(calls)+1,identity=self.identity,phase=phase,point=np.asarray(point).tolist())
                    with (OUTPUT/'calls.jsonl').open('a') as stream:
                        stream.write(json.dumps(row,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
                    calls.append(row)
                    if phase=='fit':self.fit_calls+=1
                    else:self.diagnostic_calls+=1
                def residual_tangent(self,u,model):
                    self.charge('fit',u);return self.base.residual_tangent(u,model)
                def predict(self,u,model):
                    self.charge('diagnostic',u);return self.base.prediction_tangent(u,model)[0]
            for index,task in enumerate(m['plan']['tasks']):
                identity=task['identity']
                write(OUTPUT/'status.json',dict(state='working',pid=os.getpid(),allocated_numerical_threads=4,
                    identity=identity,total=24,completed=len(rows),native_evaluations=len(calls)))
                with (OUTPUT/'starts.jsonl').open('a') as stream:
                    stream.write(json.dumps(dict(identity=identity,maximum_evaluations=160,number=index+1))+'\n');stream.flush();os.fsync(stream.fileno())
                row=dict(task);counted=None
                try:
                    f=geographic.fixture(task['model'],task['clock']);base=geographic.problem(f,kernel,tangent)
                    counted=Counted(base,identity);p=candidate.ProjectedProblem(counted,tuple(task['axes']))
                    truth=geographic.truth_point(f,base)
                    initial=np.zeros(len(truth)) if task['start']=='zero' else -.8*np.sign(truth)
                    fit=candidate.fit_control(p,task['model'],start=initial,maximum_evaluations=160)
                    point=np.array(fit['normalized_parameters'])
                    prediction=counted.predict(point,task['model']);reference=counted.predict(truth,task['model'])
                    truth_r=base.whiten(reference-base.gps)
                    truth_r,_=p.projection.apply(truth_r,np.zeros((len(truth_r),len(truth))))
                    error=(prediction-base.gps)*f['metric'];columns=[('latitude','longitude','height').index(a) for a in task['axes']]
                    row.update(fit=fit,prediction_error_m=error.tolist(),truth_cost=float(truth_r@truth_r),
                        maximum_retained_error_m=float(np.max(abs(error[:,columns]))),maximum_all_axis_error_m=float(np.max(abs(error))),
                        start_point=initial.tolist(),status='complete')
                    row['passed']=q.assess_fit(row)
                except TimeoutError:raise
                except Exception as error:row.update(status='error',passed=False,error=type(error).__name__+': '+str(error))
                row.update(native_fit_calls=counted.fit_calls if counted else 0,native_diagnostic_calls=counted.diagnostic_calls if counted else 0)
                target=OUTPUT/(identity+'.json.gz');durable_write(target,gzip.compress(encoded(row),mtime=0),replace=False)
                rows.append(row)
                write(OUTPUT/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows),native_evaluations=len(calls)))
            pairs=[]
            for a in rows[::2]:
                b=next(r for r in rows if r['model']==a['model'] and r['clock']==a['clock'] and r['axes']==a['axes'] and r['start']=='opposed')
                pairs.append(dict(model=a['model'],clock=a['clock'],axes=a['axes'],**q.compare_pair(a,b)))
            verify();passed=len(rows)==24 and all(r['passed'] for r in rows) and all(p['passed'] for p in pairs)
            summary=dict(state='complete',results=rows,pairs=pairs,passed=passed,native_evaluations=len(calls),
                generated_starts=24,observed_starts=0,original_recording_reads=0,elapsed_s=time.monotonic()-start,
                kernel_metadata=dict(value=kmeta,tangent=tmeta),scientific_decision='abstain',archival_fits_qualified=False)
            write(OUTPUT/'summary.json',summary)
            write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
            write(OUTPUT/'status.json',dict(state='complete',allocated_numerical_threads=0,completed=24,total=24,passed=passed))
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=type(error).__name__+': '+str(error),native_evaluations=len(calls),completed=len(rows)))
            write(OUTPUT/'status.json',dict(state='stopped',allocated_numerical_threads=0));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print(json.dumps(dict(passed=passed,fits=sum(r['passed'] for r in rows),pairs=sum(p['passed'] for p in pairs),native_calls=len(calls))))


def publish():
    c=load(OUTPUT/'completion.json');s=load(OUTPUT/'summary.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):raise ValueError('completion mismatch')
    names=['manifest.json','authorization.json','summary.json','completion.json','start.json','starts.jsonl','calls.jsonl','software-tests.xml','software-tests.log']
    names.extend(r['identity']+'.json.gz' for r in s['results'])
    for name in names:shutil.copy2(OUTPUT/name,GUIDE/name)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    text='# Projected trust-region qualification\n\n'
    text+=f"**{'Passed' if s['passed'] else 'Not qualified'}:** {sum(r['passed'] for r in s['results'])}/24 generated fits and {sum(p['passed'] for p in s['pairs'])}/12 paired-start comparisons passed. "
    text+=f"Used {s['native_evaluations']} of 3,888 allowed native calls, with no original-recording reads or observed fits.\n\n"
    text+='| Model | Clock | Coordinates scored | Start | Pass | Cost | Largest scored error (mm) |\n|---|---|---|---|---|---:|---:|\n'
    for r in s['results']:
        cost=r.get('fit',{}).get('residual_sum_squares');error=r.get('maximum_retained_error_m')
        text+=f"| {r['model']} | {r['clock']} | {'/'.join(r['axes'])} | {r['start']} | {r['passed']} | {cost if cost is not None else 'error'} | {1000*error if error is not None else 'error'} |\n"
    text+='\nAll parameter columns and the original physical limits are retained. Omitted axes are not constrained by the projected objective. Passing these short generated controls does not qualify full-calibration archive refits, empirical uncertainty or scientific significance.\n\n'
    text+='[Scope and gates](PLAN.md) · [Measurement-contribution work](../ilvis0-measurement-contribution/README.md).\n'
    (GUIDE/'README.md').write_text(text)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={name:sha(GUIDE/name) for name in [*names,'README.md','PLAN.md']}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true');parser.add_argument('--detach',action='store_true')
    args=parser.parse_args()
    if sum((args.prepare_only,args.package_only,args.detach))>1:raise ValueError('one mode required')
    if args.package_only:publish();return
    os.environ.update(compute_environment(workers=1,threads=4,reserved=0));os.environ['PYTHONPATH']=str(ROOT/'analysis')
    if args.prepare_only:prepare();return
    if args.detach:
        prepare()
        with (OUTPUT/'launch.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (OUTPUT/'launch.json').exists() or (OUTPUT/'start.json').exists():raise ValueError('launch already charged')
            with (OUTPUT/'worker.log').open('ab') as log:
                child=subprocess.Popen([sys.executable,__file__],cwd=ROOT,env=os.environ.copy(),stdin=subprocess.DEVNULL,
                    stdout=log,stderr=log,start_new_session=True)
            write(OUTPUT/'launch.json',dict(pid=child.pid));print(json.dumps(dict(state='launched',pid=child.pid,numerical_threads=4)))
    else:run()


if __name__=='__main__':main()
