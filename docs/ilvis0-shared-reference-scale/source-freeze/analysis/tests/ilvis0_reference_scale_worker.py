# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated qualification of a shared fixed-reference scale bound."""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_channel_envelope_worker import sha,load,write,environment

NAME='ilvis0-shared-reference-scale-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-shared-reference-scale'
SEED=2026101926
FAMILIES=('central','reference_mean','small_noncentral','large_mean','zero_rank','dependent_columns','correlated','smooth_mean')
TASKS=[dict(identity=family,family=family,realizations=1024,maximum_assessments=1024) for family in FAMILIES]
LIMITS=dict(maximum_identities=8,maximum_assessments=8192,maximum_wall_s=120,numerical_threads=4,
    original_reads=0,native_evaluations=0,optimizer_starts=0,retries=0,deadline_policy='cooperative-no-signals')


class AllowanceExhausted(BaseException):pass


def check_time(deadline):
    if time.monotonic()>=deadline:raise AllowanceExhausted('cooperative scale-study wall allowance exhausted')


def generate(task):
    import numpy as np
    from scipy.linalg import cholesky,solve_triangular
    n=96;t=np.linspace(-1.,1.,n);x=np.zeros((n,27));x[:,:4]=np.column_stack((t**0,t,t*t,t**3))
    mean=np.zeros(n);family=task['family'];identity=FAMILIES.index(family)
    if family=='reference_mean':mean=x[:,:4]@np.array([100.,-200.,300.,-100.])
    elif family=='small_noncentral':
        mean=np.cos(4.*np.pi*t);mean*=2./np.linalg.norm(mean)
    elif family=='large_mean':mean=1000.*np.cos(7.*np.pi*t)
    elif family=='zero_rank':x[:]=0.
    elif family=='dependent_columns':x[:,4:8]=x[:,:4];x[:,10]=1e-14*t
    elif family=='smooth_mean':mean=20.*np.sin(2.*t)
    rng=np.random.default_rng(np.random.SeedSequence([SEED,identity]))
    values=mean[:,None]+rng.normal(size=(n,task['realizations']))
    result=dict(whitened_values=values,reference=x,true_scale=1.,shape_source='supplied_identity',deterministic_mean=mean)
    if family=='correlated':
        covariance=.8**np.abs(np.arange(n)[:,None]-np.arange(n)[None,:]);factor=cholesky(covariance,lower=True)
        physical=factor@values;whitened=solve_triangular(factor,physical,lower=True)
        result.update(whitened_values=whitened,reference=solve_triangular(factor,x,lower=True),cholesky=factor,
            physical_values=physical,shape_source='supplied_ar1_0.8')
    return result


def evaluate(task,output=None,deadline=None):
    import numpy as np
    from scipy.stats import beta
    from lll.ilvis0_reference_scale import fixed_reference_scale
    if type(task['realizations']) is not int or not 0<task['realizations']<=task['maximum_assessments']:
        raise ValueError('finite scale-assessment allowance required')
    data=generate(task);rows=[];calls=0;unsupported=0;covered=0;context=dict(task=task,generated=data,results=rows)
    try:
        for i in range(task['realizations']):
            if deadline is not None:check_time(deadline)
            if calls>=task['maximum_assessments']:raise ValueError('scale identity allowance exhausted')
            calls+=1
            assessment=fixed_reference_scale(data['whitened_values'][:,i],data['reference'],alpha=.01,
                source_id='fixed-training-reference-'+task['identity'],covariance_id=data['shape_source'],design_is_fixed=True,
                error_distribution='gaussian',residual_numerical_allowance=1e-9)
            row=assessment.report();good=assessment.scale.upper is not None
            unsupported+=not good;covered+=good and assessment.scale.upper>=data['true_scale'];rows.append(row)
        lower=float(beta.ppf(.01,covered,len(rows)-covered+1)) if covered else 0.
        widths=[row['scale_upper']/data['true_scale'] for row in rows if row['scale_upper'] is not None]
        return dict(passed=unsupported==0 and lower>=.97,assessments=calls,covered=int(covered),unsupported=int(unsupported),
            realizations=len(rows),coverage=float(covered/len(rows)),coverage_lower_99=lower,parameter_count=data['reference'].shape[1],
            reference_rank=rows[0]['reference_rank'],true_scale=data['true_scale'],median_scale_upper_ratio=float(np.median(widths)) if widths else None,
            nominal_model_coverage=.99,finite_software_qualification_lower_target=.97,observational_coverage_qualified=False,
            scientific_decision='abstain')
    finally:
        context['assessments']=calls
        if output is not None:write(output,context)


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import ilvis0_reference_scale
    sources={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    sources.update('analysis/tests/'+n for n in ('ilvis0_reference_scale_worker.py','test_ilvis0_reference_scale_worker.py',
        'test_ilvis0_reference_scale.py','ilvis0_channel_envelope_worker.py','run_numerical.py'))
    sources.update('docs/ilvis0-shared-reference-scale/'+n for n in ('PLAN.md','MATHEMATICS.md'))
    hashes={name:sha(ROOT/name) for name in sorted(sources)}
    for name in hashes:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version='fixed-reference-shared-scale-v1',sources=hashes,environment=environment(),limits=LIMITS,
        tasks=TASKS,seed=SEED,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS));return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['tasks']!=TASKS:raise ValueError('shared-scale scope/environment changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('shared-scale authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('shared-scale frozen source changed: '+name)
    return manifest


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged shared-scale study cannot restart')
        verify();started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s'];rows=[];charged=0;terminal=None
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        try:
            for task in TASKS:
                check_time(deadline);identity=task['identity']
                if charged+task['maximum_assessments']>LIMITS['maximum_assessments']:raise ValueError('shared-scale total allowance exhausted')
                write(DATA/'charges'/(identity+'.json'),dict(task,manifest_sha256=sha(DATA/'manifest.json')));charged+=task['maximum_assessments']
                write(DATA/'status.json',dict(state='running',identity=identity,total=8,numerical_threads=4,pid=os.getpid()),replace=True)
                generated='generated/'+identity+'.json.gz'
                try:result=evaluate(task,DATA/generated,deadline)
                except AllowanceExhausted as error:result=dict(passed=False,error=str(error));terminal=str(error)
                except Exception as error:result=dict(passed=False,error=type(error).__name__+': '+str(error))
                if not (DATA/generated).exists():write(DATA/generated,dict(task=task,error=result.get('error','missing evidence')))
                artifact='results/'+identity+'.json';write(DATA/artifact,dict(task,**result,generated_artifact=generated,generated_sha256=sha(DATA/generated)))
                rows.append(dict(task,passed=result['passed'],artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)),replace=True)
                if terminal:break
        except AllowanceExhausted as error:terminal=str(error)
        state='terminal' if terminal else 'complete'
        write(DATA/'summary.json',dict(state=state,passed=len(rows)==8 and all(r['passed'] for r in rows) and not terminal,results=rows,
            elapsed_s=time.time()-started,terminal_reason=terminal,charged_assessments=charged,native_evaluations=0,
            optimizer_starts=0,original_reads=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=8,numerical_threads=0),replace=True)
    publish()


def publish():
    manifest=load(DATA/'manifest.json');summary=load(DATA/'summary.json');completion=load(DATA/'completion.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('scale completion changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('scale result changed')
        result=load(DATA/row['artifact']);results.append(result)
        if sha(DATA/result['generated_artifact'])!=result['generated_sha256']:raise ValueError('scale generated evidence changed')
        names.extend([row['artifact'],result['generated_artifact'],'charges/'+row['identity']+'.json'])
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Shared fixed-reference error-scale controls','',f"**{sum(r['passed'] for r in results)}/8 generated identities passed** in {summary['elapsed_s']:.2f} seconds. "
        'No archive reads, model fits or withheld observations.','',
        '| Family | Covered / realizations | 99% coverage lower limit | Median upper scale / true scale |',
        '|---|---:|---:|---:|']
    for row in results:
        lines.append(f"| {row['family']} | {row.get('covered',0)}/{row.get('realizations',0)} | "
            f"{row.get('coverage_lower_99',0.):.5f} | {row.get('median_scale_upper_ratio','unavailable')} |")
    lines+=['','The finite software gate is a 99% lower coverage limit of at least 0.97 for every family, around nominal 0.99 model coverage. '
        'The fixed reference can be wrong without making the scale upper bound anti-conservative under the stated Gaussian law. '
        'A wrong mean can instead make it very wide. Covariance shape, selection effects and airborne coverage remain unqualified.',
        '', '[Mathematics](MATHEMATICS.md) · [Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names+=['README.md','PLAN.md','MATHEMATICS.md']+['source-freeze/'+n for n in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen eight shared-scale identities; no execution.')
    elif args.run:run();print('Finite shared-scale qualification finished; inspect saved results.')
    else:publish();print('Published saved scale controls; no assessments.')


if __name__=='__main__':main()
