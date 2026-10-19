# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen fixed-point correction probes on generated motion only."""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_projected_controls_worker import environment

NAME='ilvis0-horizontal-probe-20261018'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
PARENT=ROOT/'docs/ilvis0-projected-horizontal-fullcal-20261018'
AUDIT=ROOT/'docs/ilvis0-horizontal-correction-audit-20261018'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def write(path,value):
    tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(value,sort_keys=True,allow_nan=False)+'\n');tmp.replace(path)


def verify():
    m=load(DATA/'manifest.json')
    if m['environment']!=environment():raise ValueError('numerical environment mismatch')
    for filename,digest in {**m['sources'],**m['inputs']}.items():
        if sha(ROOT/filename)!=digest:raise ValueError('frozen dependency changed: '+filename)
    return m


def publish():
    done=load(DATA/'completion.json');summary=load(DATA/'summary.json')
    if done['manifest_sha256']!=sha(DATA/'manifest.json') or done['summary_sha256']!=sha(DATA/'summary.json'):
        raise ValueError('completion hashes disagree')
    names=['manifest.json','completion.json','summary.json','calls.jsonl','start.json']
    for record in summary['artifacts']:
        if sha(DATA/record['artifact'])!=record['sha256']:raise ValueError('saved point changed')
        names.append(record['artifact'])
    for filename in names:shutil.copy2(DATA/filename,PUBLIC/filename)
    text=['# Fixed-point horizontal correction checks','',
        'Completed **36 generated-motion tangent evaluations**, zero optimizer starts and zero original-recording reads. Original fit labels and paired-start failures remain unchanged.','',
        '| Endpoint | Original probe passes | Ridge probe passes | Original actual cost | Ridge actual cost |',
        '|---|---|---|---:|---:|']
    for r in summary['results']:
        a,b=r['probes']
        text.append(f"| {r['identity']} | {a['passes_local_limits']} | {b['passes_local_limits']} | {a['cost']:.6g} | {b['cost']:.6g} |")
    text+=['','Passing an endpoint probe does not qualify a fitting algorithm or demonstrate paired-start repeatability. No observed-data refit follows automatically.',
           '', '[Frozen scope](PLAN.md) · [Saved-array diagnosis](../ilvis0-horizontal-correction-audit-20261018/INTERPRETATION.md).']
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in [*names,'README.md','PLAN.md']}))


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'manifest.json').exists():raise ValueError('charged probe study cannot restart')
        if any(os.environ.get(n)!='4' for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')):
            raise ValueError('run through run_numerical.py --threads 4')
        inputs={}
        for path in (PARENT,AUDIT):
            done=load(path/'completion.json')
            if done['manifest_sha256']!=sha(path/'manifest.json') or done['summary_sha256']!=sha(path/'summary.json'):
                raise ValueError('input completion hash mismatch')
            for filename,digest in load(path/'evidence-receipt.json')['artifacts'].items():
                if sha(path/filename)!=digest:raise ValueError('input publication changed')
            for n in ('manifest.json','summary.json','completion.json','evidence-receipt.json'):
                inputs[str((path/n).relative_to(ROOT))]=sha(path/n)
        source=load(PARENT/'manifest.json')['sources']
        for p in ('analysis/tests/ilvis0_horizontal_probe_worker.py',str((PUBLIC/'PLAN.md').relative_to(ROOT))):source[p]=sha(ROOT/p)
        for p,digest in source.items():
            if sha(ROOT/p)!=digest:raise ValueError('parent source changed')
        m=dict(version='horizontal-fixed-probe-v1',sources=source,inputs=inputs,environment=environment(),
            limits=dict(maximum_native_evaluations=36,maximum_optimizer_starts=0,maximum_wall_s=120,numerical_threads=4,retries=0))
        write(DATA/'manifest.json',m)
        for p in source:
            target=PUBLIC/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
        write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        import numpy as np
        from lll import ilvis0_geographic_controls as geographic,ilvis0_exploratory as explore,ilvis0_precision as precision
        from lll import ilvis0_projected_fullcal as fullcal
        from lll.ilvis0_projected_fitting import ProjectedProblem
        from lll.ilvis0_solver_refinement import projected_stationarity
        kernel,kmeta=explore.load_kernel(DATA/'kernel');tangent,tmeta=precision.load_tangent(DATA/'kernel')
        parent=load(PARENT/'summary.json')['results'];saved=load(AUDIT/'summary.json')['results']
        if len(parent)!=12 or {r['identity'] for r in saved}!={r['identity'] for r in parent}:raise ValueError('exact matched twelve endpoints required')
        records=[];results=[];started=time.monotonic()
        def alarm(*args):raise TimeoutError('finite native probe ceiling exceeded')
        previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(120)
        try:
            for row in parent:
                fixture=geographic.fixture(row['model'],row['clock']);base=fullcal.problem(row,fixture,kernel,tangent)
                p=ProjectedProblem(base,('latitude','longitude'))
                point=np.array(row['fit']['normalized_parameters']);linear=next(r for r in saved if r['identity']==row['identity'])
                proposals={r['method']:np.array(r['step']) for r in linear['corrections']}
                def evaluate(method,u):
                    if len(records)>=36:raise ValueError('native allowance exhausted')
                    base.bounds.decode(u)
                    identity=row['identity']+'--'+method
                    if identity in {r['identity'] for r in records}:raise ValueError('duplicate charged identity')
                    with (DATA/'calls.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(identity=identity,point=u.tolist(),number=len(records)+1))+'\n');stream.flush();os.fsync(stream.fileno())
                    records.append(dict(identity=identity))
                    r,j,edges=p.residual_tangent(u,row['model'])
                    stationarity=projected_stationarity(u,r,j)[0]
                    value=dict(identity=identity,point=u.tolist(),residual=r.tolist(),jacobian=j.tolist(),cost=float(r@r),stationarity=stationarity,boundaries=edges)
                    target=DATA/(identity+'.json.gz')
                    target.write_bytes(gzip.compress(json.dumps(value,sort_keys=True,allow_nan=False).encode(),mtime=0))
                    records[-1].update(artifact=target.name,sha256=sha(target))
                    return r,j,value
                center_r,center_j,center=evaluate('center',point)
                if not np.array_equal(center_r,row['fit']['local_linearization']['residual']) or not np.array_equal(center_j,row['fit']['local_linearization']['jacobian']):
                    raise ValueError('saved center did not reproduce bit-for-bit')
                probes=[]
                for method in ('original','scaled_ridge'):
                    step=proposals[method];u=np.clip(point+step,-1,1)
                    r,j,value=evaluate(method,u)
                    movement=p.physical_step(r-center_r);rms=np.sqrt(np.mean(movement**2,axis=0));maximum=np.max(abs(movement),axis=0)
                    change=abs(value['cost']-center['cost'])/max(value['cost'],center['cost'],1.)
                    passed=bool(center['stationarity']<=1e-4 and value['stationarity']<=1e-4 and change<=1e-8 and np.all(rms<=.001) and np.all(maximum<=.01))
                    predicted=center_r+center_j@(u-point)
                    probes.append(dict(method=method,passes_local_limits=passed,cost=value['cost'],stationarity=value['stationarity'],actual_cost_change=change,
                        predicted_cost=float(predicted@predicted),retained_movement_rms_m=rms.tolist(),retained_movement_maximum_m=maximum.tolist()))
                results.append(dict(identity=row['identity'],center_cost=center['cost'],original_fit_passed=row['passed'],probes=probes))
            if len(records)!=36:raise ValueError('exact fixed scope incomplete')
            verify();summary=dict(state='complete',results=results,artifacts=records,native_evaluations=36,optimizer_starts=0,
                elapsed_s=time.monotonic()-started,scientific_decision='abstain',fit_labels_changed=False,kernel_metadata=dict(value=kmeta,tangent=tmeta))
            write(DATA/'summary.json',summary);write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=str(error),charged_native_calls=len(records)));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print('Completed 36 fixed-point native calls; zero optimizer starts or original reads.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
    publish() if args.package_only else run()
