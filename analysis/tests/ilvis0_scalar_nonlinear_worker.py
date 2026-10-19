# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite qualification followed by matched constructed-history calibration."""
import argparse
import csv
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from lll.ilvis0_receipt_journal import durable_write,encoded

NAME='ilvis0-scalar-nonlinear-controls-20261019'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
PREVIOUS=ROOT/'docs/ilvis0-scalar-calibration-controls-20261019'
MODELS=('sphere_rotating','sphere_still','flat_still')
PROFILES=('stationary','eastbound','changing_direction','climbing')
FIXTURES=('interior','near_boundary','exact_boundary','constant_degenerate')
LIMITS=dict(maximum_starts=228,qualification_starts=12,matrix_starts=216,
    maximum_calls=91656,calls_per_start=402,observed_starts=0,native_evaluations=0,
    original_reads=0,numerical_threads=4,maximum_wall_s=300,retries=0)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_bytes())
def write(path,value):durable_write(path,encoded(value),replace=True)


def environment():
    return dict(python=sys.version,executable=sys.executable,platform=platform.platform(),
        packages={name:importlib.metadata.version(name) for name in ('numpy','scipy','pytest')})


def tasks():
    result=[dict(identity='qualification--'+name+'--s'+str(start),kind='qualification',
        base_identity=name,start=start) for name in FIXTURES for start in range(3)]
    for profile in PROFILES:
        for truth in MODELS:
            for candidate in MODELS:
                for attitude in (0,1):
                    base='--'.join((profile,truth,candidate,str(attitude)))
                    result.extend(dict(identity='matrix--'+base+'--s'+str(start),kind='matrix',
                        base_identity=base,start=start) for start in range(3))
    return result


def require_unstarted():
    if (DATA/'start.json').exists() or (DATA/'completion.json').exists():
        raise ValueError('charged or completed nonlinear controls cannot restart')


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    previous=load(PREVIOUS/'evidence-receipt.json')
    names=['analysis/lll/ilvis0_scalar_nonlinear.py','analysis/lll/compute_budget.py',
        'analysis/lll/ilvis0_receipt_journal.py','analysis/tests/run_numerical.py',
        'analysis/tests/ilvis0_scalar_nonlinear_controls.py',
        'analysis/tests/ilvis0_scalar_nonlinear_worker.py',
        'analysis/tests/test_ilvis0_scalar_nonlinear.py',
        'analysis/tests/test_ilvis0_scalar_nonlinear_worker.py','docs/'+NAME+'/PLAN.md']
    sources={name:sha(ROOT/name) for name in names}
    for name in names:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,target)
    inputs={}
    for task in tasks():
        if task['kind']!='matrix':continue
        name=task['base_identity']+'.json'
        if name in inputs:continue
        if sha(PREVIOUS/name)!=previous['artifacts'][name]:raise ValueError('changed constructed history: '+name)
        inputs[name]=sha(PREVIOUS/name);target=DATA/'input-freeze'/name
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PREVIOUS/name,target)
    write(DATA/'manifest.json',dict(version='bounded-scalar-nonlinear-v1',sources=sources,
        inputs=inputs,previous_receipt_sha256=sha(PREVIOUS/'evidence-receipt.json'),
        environment=environment(),tasks=tasks(),limits=LIMITS,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['tasks']!=tasks() or manifest['limits']!=LIMITS:
        raise ValueError('frozen environment, task identities or allowance changed')
    if load(DATA/'authorization.json')['manifest_sha256']!=sha(DATA/'manifest.json'):
        raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:
            raise ValueError('frozen source changed: '+name)
    if manifest['previous_receipt_sha256']!=sha(PREVIOUS/'evidence-receipt.json'):
        raise ValueError('prior evidence receipt changed')
    for name,digest in manifest['inputs'].items():
        if sha(DATA/'input-freeze'/name)!=digest or sha(PREVIOUS/name)!=digest:
            raise ValueError('constructed input changed: '+name)
    return manifest


def agreement(results,score_tolerance):
    import numpy as np
    if len(results)!=3 or not all(r.get('passed',False) for r in results):
        return dict(passed=False,reason='three passing endpoints required')
    score=max(r['rms_mps2'] for r in results)-min(r['rms_mps2'] for r in results)
    spread=max(float(np.linalg.norm(np.array(a['residual_mps2'])-b['residual_mps2'])/
        np.sqrt(len(a['residual_mps2']))) for i,a in enumerate(results) for b in results[i+1:])
    return dict(passed=bool(score<=score_tolerance and spread<=1e-7),
        score_spread_mps2=score,residual_spread_rms_mps2=spread)


def qualification(results):
    report={}
    for name in FIXTURES:
        group=[r for r in results if r['kind']=='qualification' and r['base_identity']==name]
        check=agreement(group,1e-7)
        check['passed']=bool(check['passed'] and max((r.get('rms_mps2',float('inf')) for r in group),default=float('inf'))<=1e-7)
        report[name]=check
    return report


def evaluate(task):
    from ilvis0_scalar_nonlinear_controls import fixture,LIMITS as bounds,STARTS
    from lll.ilvis0_scalar_nonlinear import Problem,fit
    if task['kind']=='qualification':body,force,_=fixture(task['base_identity'])
    else:
        old=load(DATA/'input-freeze'/(task['base_identity']+'.json'))
        body,force=old['body_force_mps2'],old['required_force_ned_mps2']
    return dict(task,**fit(Problem(body,force,bounds),STARTS[task['start']]))


def publish():
    summary=load(DATA/'summary.json');complete=load(DATA/'completion.json')
    if (complete['manifest_sha256']!=sha(DATA/'manifest.json')
            or complete['summary_sha256']!=sha(DATA/'summary.json')):
        raise ValueError('completed evidence changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('sealed start changed')
        names.extend((row['artifact'],row['charge']));results.append(load(DATA/row['artifact']))
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    for directory in ('source-freeze','input-freeze'):
        shutil.copytree(DATA/directory,PUBLIC/directory,dirs_exist_ok=True)
    fields=['identity','kind','base_identity','start','passed','rms_mps2','stationarity',
        'solver_status','calls','residual_calls','jacobian_calls','error']
    with (PUBLIC/'starts.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for row in results:writer.writerow({key:row.get(key,'') for key in fields})
    lines=['# Bounded nonlinear scalar calibration controls','',
        f"Completed **{len(results)} mathematical starts** in {summary['elapsed_s']:.2f} seconds, using {summary['known_calls']} counted residual/Jacobian calls. No observed fits, original-file reads or native integrations.",'',
        f"Known-answer qualification: **{'passed' if summary['qualification_passed'] else 'failed'}**. The matched matrix is **{'blocked' if summary['matrix_blocked'] else 'complete'}**.",'',
        f"Passing endpoints: **{sum(r['passed'] for r in results)}/{len(results)}**. Passing three-start matrix comparisons: **{sum(r['passed'] for r in summary['matrix_agreement'].values())}/72**. A passing endpoint alone does not satisfy a repeat comparison.",'',
        '[Every start](starts.csv) and the hashed artifacts preserve failures, parameter points, residual histories, costs, stationarity and numerical calls. Three starts do not certify a global optimum.','',
        'The same bounds apply to every candidate. There is no required wrong-model separation; an uninformative scalar diagnostic is a valid outcome. Passing these software checks does not qualify observational uncertainty.','',
        'The main result remains 53 globe preferences, zero flat preferences and zero unresolved. The separate IMU21 horizontal-only sensitivity result remains unresolved.','',
        '[Frozen plan and limits](PLAN.md) · [Local calibration controls](../ilvis0-scalar-calibration-controls-20261019/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    manifest=load(DATA/'manifest.json')
    names+=['README.md','PLAN.md','starts.csv']
    names+=['input-freeze/'+name for name in manifest['inputs']]
    names+=['source-freeze/'+name for name in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}))


def run():
    manifest=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);require_unstarted()
        write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        started=time.monotonic();rows=[];full=[];gate=False
        def timeout(*_):raise TimeoutError('finite five-minute software allowance exhausted')
        previous=signal.signal(signal.SIGALRM,timeout);signal.alarm(300)
        try:
            for i,task in enumerate(manifest['tasks'],1):
                if task['kind']=='matrix' and not gate:break
                verify();charge=f'charges/{i:03d}.json';(DATA/'charges').mkdir(exist_ok=True)
                durable_write(DATA/charge,encoded(dict(task,manifest_sha256=sha(DATA/'manifest.json'),
                    mathematical_start_allowance=1,residual_jacobian_call_allowance=402)))
                write(DATA/'status.json',dict(state='software_controls',pid=os.getpid(),
                    allocated_numerical_threads=4,total=228,completed=len(rows),identity=task['identity']))
                try:result=evaluate(task)
                except Exception as error:
                    result=dict(task,passed=False,error=type(error).__name__+': '+str(error),
                        actual_call_count_unknown=True,maximum_reserved_calls=402,scientific_decision='abstain')
                name=task['identity']+'.json';durable_write(DATA/name,encoded(result));full.append(result)
                rows.append(dict(task,passed=result['passed'],artifact=name,artifact_sha256=sha(DATA/name),charge=charge))
                if i==12:gate=all(r['passed'] for r in qualification(full).values())
            verify();matrix={}
            for identity in sorted({t['base_identity'] for t in manifest['tasks'] if t['kind']=='matrix'}):
                matrix[identity]=agreement([r for r in full if r['kind']=='matrix' and r['base_identity']==identity],1e-8)
            summary=dict(state='complete',results=rows,elapsed_s=time.monotonic()-started,
                qualification=qualification(full),qualification_passed=gate,matrix_blocked=not gate,
                matrix_agreement=matrix,matrix_qualified=bool(gate and all(r['passed'] for r in matrix.values())),
                known_calls=sum(r.get('calls',0) for r in full),
                starts_with_unknown_call_count=sum(r.get('actual_call_count_unknown',False) for r in full),
                mathematical_starts=len(rows),observed_starts=0,native_evaluations=0,original_reads=0,
                scientific_decision='abstain',main_findings_changed=False)
            write(DATA/'summary.json',summary)
            write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),
                summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',total=len(rows),completed=len(rows),allocated_numerical_threads=0))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=type(error).__name__+': '+str(error),completed=len(rows)))
            raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print(f"Completed {len(rows)} mathematical starts; qualification={gate}; matrix qualified={summary['matrix_qualified']}.")


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true')
    args=parser.parse_args()
    if args.package_only:publish()
    elif args.prepare_only:prepare()
    else:
        from lll.compute_budget import environment as budget_environment
        os.environ.update(budget_environment(workers=1,threads=4,reserved=0));run()
