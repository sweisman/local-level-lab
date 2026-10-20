# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite software equivalence and long-record scaling; no observed data."""
import argparse
import fcntl
import os
from pathlib import Path
import resource
import shutil
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_channel_envelope_worker import sha,load,write,environment

NAME='ilvis0-structured-error-controls-20261019'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-structured-error-controls'
TASKS=[dict(identity='dense-equivalence',epochs=16,columns=27),
    dict(identity='scale-4000',epochs=4000,columns=1),dict(identity='scale-64080',epochs=64080,columns=27)]
LIMITS=dict(maximum_identities=3,maximum_epochs=64080,maximum_columns=27,numerical_threads=4,
    maximum_wall_s=300,original_reads=0,optimizer_starts=0,native_evaluations=0,retries=0)


class Deadline(BaseException): pass


def prepare():
    if (DATA/'manifest.json').exists(): return verify()
    from lll import ilvis0_structured_covariance
    files={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    files.update(['analysis/tests/ilvis0_structured_error_worker.py','analysis/tests/ilvis0_channel_envelope_worker.py',
        'analysis/tests/run_numerical.py','analysis/tests/test_ilvis0_structured_covariance.py',
        'analysis/tests/test_ilvis0_structured_error_worker.py','docs/ilvis0-structured-error-controls/PLAN.md',
        'docs/ilvis0-structured-error-controls/BENCHMARK_PLAN.md'])
    sources={name:sha(ROOT/name) for name in sorted(files)}
    for name in sources:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version='structured-error-software-v1',sources=sources,environment=environment(),
        limits=LIMITS,plan=dict(tasks=TASKS,numerical_threads=4),scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['plan']['tasks']!=TASKS:
        raise ValueError('frozen environment or finite scope changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('frozen source changed')
    return manifest


def fixture(n):
    import numpy as np
    from lll.ilvis0_error_model import Spec
    times=np.cumsum(1.+.1*np.sin(np.arange(n)*.11))
    a=np.array([[1.,.2,-.1],[.2,1.5,.3],[-.1,.3,2.]])
    b=np.array([[.8,-.1,.1],[-.1,.7,.15],[.1,.15,1.1]])
    spec=Spec(white=.1*a,components=((10.,a),(300.,b)),offset=.3*b,drift=.2*a,
        drift_origin_s=0.,drift_span_s=float(times[-1]+1.))
    return times,spec


def values(first,last,columns):
    import numpy as np
    return np.sin(np.arange(3*first,3*last)[:,None]*.013+np.arange(columns)[None,:]*.17)


def evaluate(task):
    import hashlib
    import numpy as np
    from scipy.linalg import solve_triangular
    from lll.ilvis0_error_model import covariance,factor
    from lll.ilvis0_structured_covariance import Innovations
    n=task['epochs'];columns=task['columns'];times,spec=fixture(n)
    begin=time.monotonic();operator=Innovations(times,spec);setup=time.monotonic()-begin
    raw=values(0,n,columns);begin=time.monotonic();white=operator.whiten(raw);whole=time.monotonic()-begin
    if task['identity']=='dense-equivalence':
        dense=covariance(times,spec);expected=solve_triangular(factor(dense),raw,lower=True)
        error=float(np.max(abs(white-expected)));inverse=float(np.max(abs(operator.unwhiten(white)-raw)))
        target=Innovations(times,spec,axes=(0,1));selected=raw.reshape(n,3,columns)[:,:2].reshape(2*n,columns)
        indices=np.array([3*i+j for i in range(n) for j in (0,1)])
        projected=target.whiten(selected);projection=float(np.max(abs(operator.project_to(white,target)-projected)))
        marginal=float(np.max(abs(projected-solve_triangular(factor(dense[np.ix_(indices,indices)]),selected,lower=True))))
        determinant=abs(operator.log_determinant-float(np.linalg.slogdet(dense)[1]))
        return dict(passed=max(error,inverse,projection,marginal,determinant)<1e-10,
            dense_max_error=error,inverse_max_error=inverse,projection_max_error=projection,
            marginal_max_error=marginal,logdet_error=determinant,setup_s=setup,whole_whiten_s=whole)
    begin=time.monotonic();forward=None;backward=None;block_error=0.;inverse_error=0.
    for first in range(0,n,1024):
        last=min(n,first+1024);piece=values(first,last,columns)
        transformed,forward=operator.apply_block(piece,first_epoch=first,state=forward)
        restored,backward=operator.apply_block(white[3*first:3*last],first_epoch=first,state=backward,inverse=True)
        block_error=max(block_error,float(np.max(abs(transformed-white[3*first:3*last]))))
        inverse_error=max(inverse_error,float(np.max(abs(restored-piece))))
    block_time=time.monotonic()-begin
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    return dict(passed=block_error<1e-11 and inverse_error<1e-10,epochs=n,columns=columns,
        setup_s=setup,whole_whiten_s=whole,block_forward_inverse_s=block_time,
        block_max_error=block_error,inverse_max_error=inverse_error,cache_bytes=operator.storage_bytes,
        cache_bytes_per_epoch=operator.storage_bytes/n,process_peak_rss_bytes=rss,
        raw_and_whitened_matrix_bytes=raw.nbytes+white.nbytes,
        whitened_sha256=hashlib.sha256(white.tobytes()).hexdigest(),log_determinant=operator.log_determinant)


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged software benchmark cannot restart')
        manifest=verify();started=time.time();write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        def timeout(*_):raise Deadline('software benchmark wall allowance exhausted')
        signal.signal(signal.SIGALRM,timeout);signal.alarm(LIMITS['maximum_wall_s']);rows=[]
        try:
            for task in TASKS:
                if rows and not rows[0]['passed']:break
                write(DATA/'charges'/(task['identity']+'.json'),dict(identity=task['identity'],manifest_sha256=sha(DATA/'manifest.json')))
                try: result=evaluate(task)
                except Exception as error:result=dict(passed=False,error=type(error).__name__+': '+str(error))
                artifact='results/'+task['identity']+'.json';write(DATA/artifact,dict(task,**result))
                rows.append(dict(task,passed=result['passed'],artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                write(DATA/'status.json',dict(state='running',identity=task['identity'],total=3,numerical_threads=4,pid=os.getpid()),replace=True)
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)),replace=True)
            scaling=None
            if len(rows)==3 and all(r['passed'] for r in rows):
                small=load(DATA/rows[1]['artifact']);large=load(DATA/rows[2]['artifact'])
                scaling=small['cache_bytes_per_epoch']==large['cache_bytes_per_epoch']
            summary=dict(state='complete',results=rows,passed=len(rows)==3 and all(r['passed'] for r in rows) and scaling is True,
                cache_linear_scaling=scaling,elapsed_s=time.time()-started,native_evaluations=0,optimizer_starts=0,
                scientific_decision='abstain')
            write(DATA/'summary.json',summary)
            write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',total=3,numerical_threads=0),replace=True)
        except Deadline as error:
            write(DATA/'terminal.json',dict(state='deadline',error=str(error)));raise
        finally:signal.alarm(0)
    publish()


def publish():
    completion=load(DATA/'completion.json');summary=load(DATA/'summary.json');manifest=load(DATA/'manifest.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):
        raise ValueError('completed benchmark changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('sealed benchmark result changed')
        names.extend([row['artifact'],'charges/'+row['identity']+'.json']);results.append(load(DATA/row['artifact']))
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Structured covariance software controls','',
        f"Qualification **{'passed' if summary['passed'] else 'failed'}**: {sum(r['passed'] for r in results)}/{len(results)} identities in {summary['elapsed_s']:.2f} seconds. No original reads, model fits or native integrations.",'',
        '| Epochs | Columns | Setup | Whole whitening | Block forward + inverse | Cached storage | Process peak RSS |',
        '|---:|---:|---:|---:|---:|---:|---:|']
    for result in results:
        if 'cache_bytes' in result:
            lines.append(f"| {result['epochs']:,} | {result['columns']} | {result['setup_s']:.2f} s | {result['whole_whiten_s']:.2f} s | {result['block_forward_inverse_s']:.2f} s | {result['cache_bytes']/2**20:.2f} MiB | {result['process_peak_rss_bytes']/2**20:.2f} MiB |")
    lines+=['','Cache storage scales linearly with epochs. Process peak includes Python, imported libraries and generated input/output matrices; '
        'it is not the cache size. Structured paths construct no whole-record covariance, factor or projection matrix.','',
        'These are supplied-covariance software checks. Covariance estimation, bounded parameter uncertainty, predictive adequacy and native streaming integration remain separate.', '',
        '[Method](PLAN.md) · [Frozen benchmark limits](BENCHMARK_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    names+=['PLAN.md','BENCHMARK_PLAN.md','README.md']+['source-freeze/'+name for name in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen three software identities; no benchmark execution.')
    elif args.run:run();print('Completed bounded structured-covariance benchmark.')
    else:publish();print('Published saved software evidence.')


if __name__=='__main__':main()
