# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated-data prediction coverage and structured scaling controls."""
import argparse
import fcntl
import os
from pathlib import Path
import resource
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_channel_envelope_worker import sha,load,write,environment
from ilvis0_prediction_controls import CASES,SEED

NAME='ilvis0-bounded-prediction-controls-20261019'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-bounded-prediction-controls'
TASKS=[dict(identity='dense-forecast',kind='dense')]+[
    dict(identity=name,kind='coverage',realizations=512) for name in CASES]+[
    dict(identity='long-forecast',kind='long',training_epochs=42720,future_epochs=21360,columns=27)]
LIMITS=dict(maximum_identities=8,maximum_realizations=3072,maximum_covariance_alternatives=2,
    maximum_dense_epochs=40,maximum_epochs=64080,maximum_columns=27,maximum_wall_s=300,
    numerical_threads=4,original_reads=0,optimizer_starts=0,native_evaluations=0,retries=0,
    deadline_policy='cooperative-no-signals')


class AllowanceExhausted(BaseException):pass


def check_time(deadline):
    if time.monotonic()>=deadline:raise AllowanceExhausted('cooperative wall allowance exhausted')


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import ilvis0_structured_prediction,ilvis0_bounded_prediction
    files={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    files.update(['analysis/tests/'+name for name in (
        'ilvis0_bounded_prediction_worker.py','ilvis0_prediction_controls.py','ilvis0_channel_envelope_worker.py',
        'run_numerical.py','test_ilvis0_structured_prediction.py','test_ilvis0_bounded_prediction.py',
        'test_ilvis0_prediction_controls.py','test_ilvis0_bounded_prediction_worker.py')])
    files.update('docs/ilvis0-bounded-prediction-controls/'+name for name in ('PLAN.md','MATHEMATICS.md','CONTROL_PLAN.md'))
    sources={name:sha(ROOT/name) for name in sorted(files)}
    for name in sources:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version='bounded-prediction-software-v1',sources=sources,environment=environment(),
        limits=LIMITS,plan=dict(tasks=TASKS,numerical_threads=4),seed=SEED,
        coverage_gate=dict(lower_confidence=.99,minimum_lower_bound=.95,unsupported_counts_as_miss=True),
        scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['plan']['tasks']!=TASKS:
        raise ValueError('frozen environment or finite scope changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('frozen source changed: '+name)
    return manifest


def coverage_summary(total,covered,unsupported):
    from scipy.stats import beta
    if not 0<=covered<=total or not 0<=unsupported<=total-covered or total<=0:raise ValueError('invalid coverage counts')
    lower=float(beta.ppf(.01,covered,total-covered+1)) if covered else 0.
    return dict(realizations=total,simultaneous_covered=covered,unsupported=unsupported,
        exact_99pct_lower=lower,passed=lower>=.95 and unsupported==0)


def dense_gate():
    import numpy as np
    from scipy.linalg import solve_triangular
    from lll.ilvis0_error_model import covariance
    from ilvis0_prediction_controls import fixture
    control=fixture('fixed_linear');member=control['family']['common']
    op=member['operator'];forecast=member['forecast'];cut=3*control['nt']
    times=np.concatenate((op.times,forecast.times));dense=covariance(times,op.spec)
    gain=np.linalg.solve(dense[:cut,:cut],dense[:cut,cut:]).T
    variance=np.diag(dense[cut:,cut:]-gain@dense[:cut,cut:])
    x=control['training_design'];expected=gain@x
    response=np.linalg.norm(solve_triangular(np.linalg.cholesky(dense[:cut,:cut]),dense[:cut,cut:],lower=True).T,axis=1)
    errors=dict(mean_max_error=float(np.max(abs(forecast.mean(x)-expected))),
        variance_max_error=float(np.max(abs(forecast.variance-variance))),
        response_norm_max_error=float(np.max(abs(forecast.training_response_norm-response))))
    return dict(passed=max(errors.values())<1e-10,epochs=len(times),columns=x.shape[1],**errors)


def long_gate(training_epochs=42720,future_epochs=21360,columns=27,deadline=None):
    import hashlib
    import numpy as np
    from lll.ilvis0_structured_covariance import Innovations
    from lll.ilvis0_structured_prediction import Forecast
    from ilvis0_prediction_controls import specification
    n=training_epochs+future_epochs;times=np.arange(n,dtype=float)+.07*np.sin(np.arange(n))
    spec=specification(times);begin=time.monotonic();operator=Innovations(times[:training_epochs],spec)
    if deadline is not None:check_time(deadline)
    forecast=Forecast(operator,times[training_epochs:]);setup=time.monotonic()-begin
    if deadline is not None:check_time(deadline)
    values=np.sin(np.arange(3*training_epochs)[:,None]*.013+np.arange(columns)[None,:]*.17)
    begin=time.monotonic();predicted=forecast.mean(values);predict_s=time.monotonic()-begin
    u=(times[training_epochs:]-spec.drift_origin_s)/spec.drift_span_s
    base=spec.white+spec.offset+sum((value for _,value in spec.components),np.zeros((3,3)))
    unconditional=np.diag(base)[None,:]+u[:,None]**2*np.diag(spec.drift)[None,:]
    error=float(np.max(abs(forecast.variance+forecast.training_response_norm**2-unconditional.ravel())))
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    return dict(passed=error<1e-10 and predicted.shape==(3*future_epochs,columns) and np.all(np.isfinite(predicted)),
        training_epochs=training_epochs,future_epochs=future_epochs,total_epochs=n,predicted_columns=columns,
        setup_s=setup,prediction_s=predict_s,variance_identity_max_error=error,
        cache_bytes=operator.storage_bytes+forecast.storage_bytes,process_peak_rss_bytes=rss,
        predicted_sha256=hashlib.sha256(predicted.tobytes()).hexdigest(),dense_long_matrix_constructed=False)


def coverage_gate(task,deadline):
    import numpy as np
    from ilvis0_prediction_controls import fixture,realization,envelope
    control=fixture(task['identity']);records=[];covered=0;unsupported=0
    # Save only generator inputs, not cached filter objects. The frozen factory
    # reproduces the supplied covariance, design and independent error streams.
    inputs={k:v for k,v in control.items() if k!='family'}
    artifact='generated/'+task['identity']+'.json.gz'
    try:
        for i in range(task['realizations']):
            check_time(deadline)
            write(DATA/'realization-charges'/task['identity']/f'{i:04d}.json',dict(replicate=i,seed=SEED))
            sample=realization(control,i);record=dict(sample=sample);records.append(record)
            arguments={k:sample[k] for k in ('calibration','training','training_design')}
            # Future values are deliberately not arguments to envelope().
            prediction=envelope(control,**arguments)
            success=prediction['supported'] and bool(np.all(sample['future']>=prediction['lower'])
                and np.all(sample['future']<=prediction['upper']))
            covered+=int(success);unsupported+=int(not prediction['supported'])
            record.update(prediction=prediction,simultaneous_covered=success)
    finally:write(DATA/artifact,dict(inputs=inputs,records=records))
    return dict(coverage_summary(task['realizations'],covered,unsupported),
        generated_artifact=artifact,generated_sha256=sha(DATA/artifact),
        original_parameter_count=control['parameters'],covariance_alternatives=len(control['family']))


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged software qualification cannot restart')
        verify();started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s']
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        rows=[];terminal=None
        try:
            for task in TASKS:
                check_time(deadline)
                if rows and not rows[0]['passed']:break
                identity=task['identity'];write(DATA/'charges'/(identity+'.json'),dict(task,manifest_sha256=sha(DATA/'manifest.json')))
                write(DATA/'status.json',dict(state='running',identity=identity,total=8,numerical_threads=4,pid=os.getpid()),replace=True)
                try:
                    if task['kind']=='dense':result=dense_gate()
                    elif task['kind']=='coverage':result=coverage_gate(task,deadline)
                    else:result=long_gate(task['training_epochs'],task['future_epochs'],task['columns'],deadline)
                    check_time(deadline)
                except AllowanceExhausted as error:
                    result=dict(passed=False,error=str(error));terminal=str(error)
                except Exception as error:result=dict(passed=False,error=type(error).__name__+': '+str(error))
                generated='generated/'+identity+'.json.gz'
                if (DATA/generated).exists():
                    result.update(generated_artifact=generated,generated_sha256=sha(DATA/generated))
                artifact='results/'+identity+'.json';write(DATA/artifact,dict(task,**result))
                rows.append(dict(task,passed=bool(result['passed']),artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)),replace=True)
                if terminal:break
        except AllowanceExhausted as error:terminal=str(error)
        elapsed=time.time()-started;state='terminal' if terminal else 'complete'
        summary=dict(state=state,results=rows,passed=terminal is None and len(rows)==8 and all(r['passed'] for r in rows),
            elapsed_s=elapsed,wall_overrun_s=max(0.,elapsed-LIMITS['maximum_wall_s']),terminal_reason=terminal,
            native_evaluations=0,optimizer_starts=0,scientific_decision='abstain')
        write(DATA/'summary.json',summary)
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=8,numerical_threads=0),replace=True)
    publish()


def publish():
    completion=load(DATA/'completion.json');summary=load(DATA/'summary.json');manifest=load(DATA/'manifest.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):
        raise ValueError('completed qualification changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('sealed result changed')
        names.extend([row['artifact'],'charges/'+row['identity']+'.json']);result=load(DATA/row['artifact']);results.append(result)
        if 'generated_artifact' in result:
            if sha(DATA/result['generated_artifact'])!=result['generated_sha256']:raise ValueError('generated control evidence changed')
            names.append(result['generated_artifact'])
    for directory in (DATA/'realization-charges').glob('*'):
        names.extend(str(path.relative_to(DATA)) for path in sorted(directory.glob('*.json')))
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Bounded prediction software qualification','',
        f"Qualification **{'passed' if summary['passed'] else 'failed'}**: {sum(r['passed'] for r in results)}/8 identities, {summary['elapsed_s']:.2f} seconds. No archive reads, model fits or native integrations.",'',
        '| Generated control | Simultaneous coverage | Unsupported | Exact 99% lower bound |','|---|---:|---:|---:|']
    for result in results:
        if 'realizations' in result and 'simultaneous_covered' in result:
            lines.append(f"| {result['identity'].replace('_',' ')} | {result['simultaneous_covered']}/{result['realizations']} | {result['unsupported']} | {result['exact_99pct_lower']:.4f} |")
        if 'variance_identity_max_error' in result:
            lines+=['',f"Long-record forecast: {result['total_epochs']:,} epochs, {result['predicted_columns']} columns; "
                f"{result['cache_bytes']/2**20:.2f} MiB cached, {result['process_peak_rss_bytes']/2**20:.2f} MiB process peak. "
                f"Marginal-variance identity maximum error {result['variance_identity_max_error']:.3g}."]
    lines+=['','These tests assess a declared Gaussian error family and independently bounded mean errors. '
        'They do not calibrate archive uncertainty, verify a global nonlinear remainder for the aircraft integrator, '
        'or establish withheld physical adequacy. Unsupported cases count as misses. No future observations enter envelope construction.',
        '', '[Mathematics](MATHEMATICS.md) · [Frozen limits](CONTROL_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    names+=['README.md','PLAN.md','MATHEMATICS.md','CONTROL_PLAN.md']+['source-freeze/'+name for name in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen eight software identities; no execution.')
    elif args.run:run();print('Finite prediction qualification finished; see saved summary.')
    else:publish();print('Published saved qualification without calculations.')


if __name__=='__main__':main()
