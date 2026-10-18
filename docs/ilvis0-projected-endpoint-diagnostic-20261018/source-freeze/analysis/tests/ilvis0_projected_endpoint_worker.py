# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded generated-motion endpoint diagnosis; no optimizer starts or originals."""
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

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment as compute_environment
from lll.ilvis0_receipt_journal import durable_write,encoded
from ilvis0_projected_controls_worker import environment,sha,load,write

OUTPUT=ROOT/'data/ilvis0-projected-endpoint-diagnostic-20261018'
GUIDE=ROOT/'docs'/OUTPUT.name
PARENT=ROOT/'docs/ilvis0-projected-fitting-controls-20261018'
LIMITS=dict(maximum_native_sweeps=33,maximum_optimizer_starts=0,numerical_threads=4,
    maximum_wall_s=120,original_recording_reads=0,retries=0)


def prepare():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    parent=load(PARENT/'manifest.json');done=load(PARENT/'completion.json');summary=load(PARENT/'summary.json')
    if done['manifest_sha256']!=sha(PARENT/'manifest.json') or done['summary_sha256']!=sha(PARENT/'summary.json'):
        raise ValueError('verified parent completion required')
    failed=[r for r in summary['controls'] if not r['test_passed']]
    if summary['passed'] or len(failed)!=1:raise ValueError('exact single failed parent control required')
    endpoint=failed[0]
    if (endpoint['model'],endpoint['clock'],endpoint['axes'],endpoint['start'])!=('sphere_rotating','nominal',['height'],'zero'):
        raise ValueError('frozen failed endpoint required')
    values=dict(parent['sources'])
    for name in ('analysis/lll/ilvis0_projected_endpoint.py','analysis/tests/test_ilvis0_projected_endpoint.py',
                 'analysis/tests/ilvis0_projected_endpoint_worker.py'):
        values[name]=sha(ROOT/name)
    for name,digest in values.items():
        if sha(ROOT/name)!=digest:raise ValueError('parent source changed: '+name)
        target=OUTPUT/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    inputs={str((PARENT/name).relative_to(ROOT)):sha(PARENT/name) for name in ('manifest.json','summary.json','completion.json')}
    inputs[str((GUIDE/'PLAN.md').relative_to(ROOT))]=sha(GUIDE/'PLAN.md')
    manifest=dict(version='ilvis0-generated-projected-endpoint-v1',environment=environment(),limits=LIMITS,
        sources=values,inputs=inputs,endpoint=endpoint,plan=dict(numerical_threads=4,maximum_native_evaluations=33,
        tasks=[dict(identity='failed-height-endpoint')]))
    write(OUTPUT/'manifest.json',manifest)
    write(OUTPUT/'authorization.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json'),**LIMITS))
    return verify()


def verify():
    manifest=load(OUTPUT/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS:
        raise ValueError('frozen numerical environment or allowance changed')
    if load(OUTPUT/'authorization.json')!=dict(manifest_sha256=sha(OUTPUT/'manifest.json'),**LIMITS):
        raise ValueError('frozen diagnostic authorization changed')
    for name,digest in {**manifest['sources'],**manifest['inputs']}.items():
        if sha(ROOT/name)!=digest:raise ValueError('frozen dependency changed: '+name)
    for name,digest in manifest['sources'].items():
        if sha(OUTPUT/'source-freeze'/name)!=digest:raise ValueError('source snapshot changed')
    return manifest


def run():
    prepare()
    with (OUTPUT/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists() or (OUTPUT/'completion.json').exists():raise ValueError('charged diagnostic cannot restart')
        manifest=verify();write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
        write(OUTPUT/'status.json',dict(state='running',pid=os.getpid(),allocated_numerical_threads=4,total=1))
        import numpy as np
        from lll import ilvis0_geographic_controls as geographic,ilvis0_exploratory as explore
        from lll import ilvis0_precision as precision,ilvis0_projected_fitting as projected
        from lll import ilvis0_projected_endpoint as diagnostic
        from lll.ilvis0_solver_refinement import projected_stationarity
        f=geographic.fixture('sphere_rotating','nominal')
        kernel,kmeta=explore.load_kernel(OUTPUT/'kernel');tangent,tmeta=precision.load_tangent(OUTPUT/'kernel')
        base=geographic.problem(f,kernel,tangent);p=projected.ProjectedProblem(base,('height',))
        point=np.array(manifest['endpoint']['fit']['normalized_parameters']);names=list(base.bounds.active)
        if names!=manifest['endpoint']['fit']['active_parameters']:raise ValueError('original parameter ordering required')
        records=[];started=time.monotonic()
        def alarm(signum,frame):raise TimeoutError('fixed-endpoint diagnostic wall allowance exhausted')
        previous=signal.signal(signal.SIGALRM,alarm);signal.alarm(120)
        def evaluate(identity,u):
            base.bounds.decode(u)
            if len(records)>=33 or identity in {r['identity'] for r in records}:raise ValueError('native allowance or identity exhausted')
            charge=dict(identity=identity,number=len(records)+1,point=np.asarray(u).tolist(),manifest_sha256=sha(OUTPUT/'manifest.json'))
            with (OUTPUT/'calls.jsonl').open('a') as stream:
                stream.write(json.dumps(charge,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
            records.append(charge)
            full_r,full_j,boundaries=base.residual_tangent(u,'sphere_rotating')
            r,j=p.projection.apply(full_r,full_j)
            physical=(base.cholesky@full_r).reshape(-1,3)*f['metric']
            stationarity,gradient,projected_gradient,scaled=projected_stationarity(u,r,j)
            value=dict(identity=identity,point=np.asarray(u).tolist(),full_residual=full_r.tolist(),full_jacobian=full_j.tolist(),
                residual=r.tolist(),jacobian=j.tolist(),cost=float(r@r),boundaries=boundaries,
                stationarity=float(stationarity),scaled_projected_gradient=scaled.tolist(),
                maximum_retained_error_m=float(np.max(abs(physical[:,2]))),maximum_all_axis_error_m=float(np.max(abs(physical))))
            target=OUTPUT/(identity+'.json.gz');durable_write(target,gzip.compress(encoded(value),mtime=0),replace=False)
            charge.update(artifact=target.name,sha256=sha(target))
            return r,j,value
        try:
            r,j,center=evaluate('center',point)
            if not np.isclose(center['cost'],manifest['endpoint']['fit']['residual_sum_squares'],rtol=1e-8,atol=1e-16):
                raise ValueError('failed endpoint objective did not reproduce')
            rr,jj,repeat=evaluate('center-repeat',point)
            if not np.array_equal(r,rr) or not np.array_equal(j,jj):raise ValueError('repeated endpoint not deterministic')
            truth=geographic.truth_point(f,base);_,_,known=evaluate('generating-parameters',truth)
            fd={}
            for step in (.001,.0001):
                columns=[]
                for i,name in enumerate(names):
                    delta=np.eye(len(point))[i]*step
                    plus=evaluate(f'fd-{name}-{step}-plus',point+delta)[0]
                    minus=evaluate(f'fd-{name}-{step}-minus',point-delta)[0]
                    columns.append((plus-minus)/(2*step))
                fd[str(step)]=diagnostic.derivative_errors(j,np.column_stack(columns),names)
            proposals=diagnostic.linear_steps(point,r,j);probes=[]
            for method,row in proposals.items():
                delta=np.array(row['correction'])
                for fraction in (1.,.25,.0625):
                    u=np.clip(point+fraction*delta,-1.,1.)
                    fresh,fresh_j,value=evaluate(f'probe-{method}-{fraction}',u)
                    predicted=r+j@(u-point)
                    physical=p.physical_step(fresh-r)
                    probes.append(dict(method=method,fraction=fraction,cost=value['cost'],stationarity=value['stationarity'],
                        linear_cost=float(predicted@predicted),normalized_parameter_step=float(np.linalg.norm(u-point)),
                        maximum_retained_prediction_change_m=float(np.max(abs(physical))),
                        nonlinear_linear_residual_disagreement=float(np.linalg.norm(fresh-predicted)),
                        passes_stationarity=value['stationarity']<=manifest['endpoint']['fit']['stationarity_tolerance']))
            if len(records)!=33:raise ValueError('exact 33-call scope required')
            verify();summary=dict(state='complete',results=[dict(identity='failed-height-endpoint',passed=True)],
                native_evaluations=len(records),optimizer_starts=0,original_recording_reads=0,elapsed_s=time.monotonic()-started,
                columns=names,center=center,generating_parameters=known,deterministic=True,directions=diagnostic.directions(j,names),
                derivative_errors=fd,linear_proposals=proposals,probes=probes,artifacts=records,
                kernel_metadata=dict(value=kmeta,tangent=tmeta),scientific_decision='abstain',fit_labels_changed=False)
            write(OUTPUT/'summary.json',summary)
            write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
            write(OUTPUT/'status.json',dict(state='complete',allocated_numerical_threads=0,total=1,completed=1))
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=type(error).__name__+': '+str(error),charged_native_calls=len(records)))
            write(OUTPUT/'status.json',dict(state='stopped',allocated_numerical_threads=0))
            raise
        finally:
            signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish()
    print(json.dumps(dict(state='complete',native_evaluations=len(records),optimizer_starts=0)))


def publish():
    complete=load(OUTPUT/'completion.json');s=load(OUTPUT/'summary.json')
    if complete['manifest_sha256']!=sha(OUTPUT/'manifest.json') or complete['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completion hash mismatch')
    GUIDE.mkdir(exist_ok=True)
    files=['manifest.json','authorization.json','summary.json','completion.json','start.json','calls.jsonl']
    for record in s['artifacts']:
        if sha(OUTPUT/record['artifact'])!=record['sha256']:raise ValueError('native artifact changed')
        files.append(record['artifact'])
    for name in files:shutil.copy2(OUTPUT/name,GUIDE/name)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    text='# Diagnosis of the generated height-only endpoint\n\n'
    text+='Completed **33 fixed-point evaluations**, zero optimizer starts and zero original-recording reads. The saved failure reproduced deterministically; its label is unchanged.\n\n'
    text+='| Proposed correction | Fraction | Linear cost | Actual cost | Fresh stationarity | Largest retained prediction change (m) |\n|---|---:|---:|---:|---:|---:|\n'
    for row in s['probes']:
        text+=f"| {row['method']} | {row['fraction']} | {row['linear_cost']:.6g} | {row['cost']:.6g} | {row['stationarity']:.6g} | {row['maximum_retained_prediction_change_m']:.6g} |\n"
    text+='\nThese are proposals from the same saved point, not optimization trajectories or new converged fits. No archive result or qualification gate changed.\n\n'
    text+='[Fixed scope](PLAN.md) · [Prior qualification](../ilvis0-projected-fitting-controls-20261018/README.md).\n'
    (GUIDE/'README.md').write_text(text)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={name:sha(GUIDE/name) for name in [*files,'README.md','PLAN.md']}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true')
    args=parser.parse_args()
    if args.prepare_only and args.package_only:raise ValueError('one mode required')
    if args.package_only:publish();return
    os.environ.update(compute_environment(workers=1,threads=4,reserved=0))
    if args.prepare_only:prepare()
    else:run()


if __name__=='__main__':main()
