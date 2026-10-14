# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded covariance/prediction worker. Preparation never integrates archive data."""
import argparse
from contextlib import contextmanager
import fcntl
import gzip
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np

import ilvis0_clock_trial as clock
from lll import ilvis0_prediction as prediction, ilvis0_uncertainty_adapter as adapter
from lll import ilvis0_sweep_journal as journal

base=clock.base
VERSION='ilvis0-prediction-covariance-worker-v1'
OUTPUT=Path('data/ilvis0-prediction-covariance-20261012')
GUIDE=Path('docs/ilvis0-prediction-covariance-20261012')
PREPARATION=Path('docs/ilvis0-prediction-covariance-preparation-20261012')
REFERENCE=Path('docs/ilvis0-prediction-trial-20261011')


def axis_probes(point,step):
    p=np.asarray(point,dtype=float)
    if p.ndim!=1 or not len(p) or not np.all(np.isfinite(p)) or np.any(abs(p)>1) or not 0<step<1:
        raise ValueError('finite feasible center and small positive step required')
    rows=[p.copy()];omitted=[]
    for k in range(len(p)):
        for sign in (-1,1):
            row=p.copy();row[k]+=sign*step
            if abs(row[k])>1:omitted.append(dict(parameter=k,direction=sign))
            else:rows.append(row)
    return np.array(rows),omitted


@contextmanager
def worker_lock(output,inherited_fd=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    stream=os.fdopen(inherited_fd,'a') if inherited_fd is not None else (output/'worker.lock').open('a')
    with stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield stream


class ChargedProblem(base.shape.TangentProblem):
    def __init__(self,*args,ledger,identity,phase='fit',**kwargs):
        super().__init__(*args,**kwargs);self.ledger=ledger;self.identity=identity;self.phase=phase

    def predict(self,point,model):
        return self.ledger.call(self.identity,self.phase,'value',super().predict,point,model)

    def prediction_tangent(self,point,model):
        return self.ledger.call(self.identity,self.phase,'tangent',super().prediction_tangent,point,model)


def physical_metric(gps):
    phi=gps[:,0];height=gps[:,2];d=1-6.6943799901413165e-3*np.sin(phi)**2
    return np.column_stack((6378137.*(1-6.6943799901413165e-3)/d**1.5+height,
        (6378137./np.sqrt(d)+height)*np.cos(phi),np.ones(len(gps))))


def prediction_report(times,gps,coordinates,covariance,metric,cut):
    delta=coordinates-gps;delta[:,1]=(delta[:,1]+np.pi)%(2*np.pi)-np.pi
    raw=delta*metric
    conditioned=prediction.conditional_errors(covariance,delta.ravel(),3*cut)
    innovations=np.concatenate((conditioned['training_innovations'],conditioned['innovations'])).reshape(-1,3)
    report=dict(parameter_uncertainty_included=False,confidence_calibrated=False,scientific_decision='abstain')
    rows=[]
    for name,section in [('training',slice(0,cut)),('prediction',slice(cut,None))]:
        physical=raw[section];white=innovations[section]
        rms=np.sqrt(np.mean(physical**2,axis=0))
        correlations=[]
        for axis in range(3):
            x=white[:,axis]
            correlations.append(float(np.corrcoef(x[:-1],x[1:])[0,1]) if len(x)>2 and np.std(x[:-1])>0 and np.std(x[1:])>0 else None)
        report[name]=dict(epochs=len(physical),rms_neu_m=rms.tolist(),
            horizontal_rms_m=float(math.hypot(*rms[:2])),vertical_rms_m=float(rms[2]),
            conditional_cost=float(np.sum(white**2)),whitened_rms=float(np.sqrt(np.mean(white**2))),
            innovation_lag1_neu=correlations)
    for i,t in enumerate(times):
        row=dict(epoch=i,time_s=float(t),role='training' if i<cut else 'prediction')
        for k,axis in enumerate(('north','east','up')):
            row[axis+'_direct_error_m']=float(raw[i,k]);row[axis+'_innovation']=float(innovations[i,k])
        rows.append(row)
    return report,rows


def save_epochs(output,name,rows):
    path=output/name
    clock.residuals.atomic_bytes(path,gzip.compress(clock.residuals.csv_bytes(rows),mtime=0))
    return name,base.il.sha256(path)


def prepare(output):
    with worker_lock(output):
        if (output/'manifest.json').exists():return verify(output)
        control=base.load(GUIDE/'control-receipt.json')
        clock.audit.verify_artifacts(GUIDE,control);clock.residuals.check_hashes(control['sources'])
        base.runtime.check_environment(control['numerical_environment'])
        clock.audit.verify_artifacts(PREPARATION,base.load(PREPARATION/'preparation-receipt.json'))
        proposal=base.load(PREPARATION/'proposal.json')
        clock.residuals.check_hashes(proposal['references']);clock.residuals.check_hashes(proposal['preparation_sources'])
        prior=base.load(REFERENCE/'manifest.json')
        clock.audit.verify_artifacts(REFERENCE,base.load(REFERENCE/'evidence-receipt.json'))
        sources=dict(prior['sources'])
        paths=[Path(__file__),Path(journal.__file__),Path(adapter.__file__),
            Path('analysis/lll/ilvis0_uncertainty_geometry.py'),Path('analysis/lll/ilvis0_error_model.py'),
            Path('analysis/lll/ilvis0_prediction_comparison_plan.py'),
            Path('analysis/tests/test_ilvis0_prediction_covariance_worker.py')]
        for path in paths:sources[str(path.resolve())]=base.il.sha256(path)
        clock.residuals.check_hashes(sources)
        if len({Path(p).name for p in sources})!=len(sources):raise ValueError('snapshot filename collision')
        inputs=dict(prior['inputs'])
        for path in [PREPARATION/'proposal.json',PREPARATION/'preparation-receipt.json',GUIDE/'PLAN.md',
                GUIDE/'control-receipt.json',REFERENCE/'summary.json',REFERENCE/'selection.json.gz',
                REFERENCE/'manifest.json',REFERENCE/'evidence-receipt.json']:
            inputs[str(path.resolve())]=base.il.sha256(path)
        originals=[str(Path(base.load(REFERENCE/'selection.json.gz')['selected'][0]['source_path']).resolve())]
        shutil.copyfile(REFERENCE/'selection.json.gz',output/'selection.json.gz')
        base.follow.atomic_json(output/'split.json',proposal['split'])
        (output/'source-freeze').mkdir(exist_ok=True)
        for path in sources:shutil.copyfile(path,output/'source-freeze'/Path(path).name)
        manifest=dict(version=VERSION,proposal=proposal,sources=sources,inputs=inputs,
            originals_pending_launch_verification=originals,environment=base.runtime.numerical_environment(),
            value_kernel=prior['value_kernel'],tangent_kernel=prior['tangent_kernel'],
            artifacts={n:base.il.sha256(output/n) for n in ('selection.json.gz','split.json')},
            scientific_decision='abstain')
        base.follow.atomic_json(output/'manifest.json',manifest)
        return verify(output)


def verify(output,originals=False):
    manifest=base.load(output/'manifest.json');p=manifest['proposal']
    if manifest['version']!=VERSION or p!=base.load(PREPARATION/'proposal.json'):
        raise ValueError('worker scope differs from prepared proposal')
    clock.residuals.check_hashes(manifest['sources'])
    pending=set(manifest['originals_pending_launch_verification'])
    clock.residuals.check_hashes({k:v for k,v in manifest['inputs'].items() if originals or k not in pending})
    base.runtime.check_environment(manifest['environment'])
    if any(v!='2' for v in manifest['environment']['thread_settings'].values()):
        raise ValueError('exactly two numerical threads required')
    for path,digest in manifest['sources'].items():
        if base.il.sha256(output/'source-freeze'/Path(path).name)!=digest:raise ValueError('source snapshot mismatch')
    for name,digest in manifest['artifacts'].items():
        if base.il.sha256(output/name)!=digest:raise ValueError('selected interval or split changed')
    if base.load(output/'split.json')!=p['split']:raise ValueError('split differs from proposal')
    return manifest


def authorization(output):
    path=output/'authorization.json'
    if not path.exists():raise ValueError('explicit finite compute authorization required')
    value=base.load(path)
    expected=dict(manifest_sha256=base.il.sha256(output/'manifest.json'),maximum_starts=12,
        maximum_native_sweeps=3060,retries=0,approval='explicit_user_approval')
    if value!=expected:raise ValueError('authorization does not match finite freeze')
    return value


def authorize(output):
    with worker_lock(output):
        if (output/'completion.json').exists():raise ValueError('completed study is frozen')
        verify(output)
        base.follow.atomic_json(output/'authorization.json',dict(
            manifest_sha256=base.il.sha256(output/'manifest.json'),maximum_starts=12,
            maximum_native_sweeps=3060,retries=0,approval='explicit_user_approval'))


def profiles(tasks,fits,role):
    rows=[]
    for cov in ('h1_v3_tau10','h1_v3_tau300'):
        for case in ('bias1_unsubtracted','bias1_profiled_removal'):
            current=[]
            for task in tasks:
                if task['covariance']==cov and task['processing_case']==case:
                    fit=dict(fits[task['identity']])
                    if role=='prediction':
                        fit['converged']=fit.get('converged',False) and 'prediction_diagnostics' in fit
                        fit['residual_sum_squares']=fit.get('prediction_diagnostics',{}).get('prediction',{}).get('conditional_cost',0.)
                    current.append(fit)
            rows.append(dict(case_id=cov+'::'+case,fits=current))
    return base.shape.hierarchical_profile(rows)


def fit_task(output,task,case,values,times,gps,covariance,kernels,book,cut,provenance):
    identity=task['identity'];charged=book.start(identity);begin=time.monotonic();fit={}
    try:
        tt,tg,tv=prediction.training_inputs(times,gps,values,case['limits']['time_offset'])
        seed,force=base.corpus.initialize(tt,tg,tv,task['model'])
        kwargs=dict(fit_earth_removal=case['profile'],kernel=kernels[0],tangent_kernel=kernels[1],
            clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
            maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.,ledger=book,identity=identity)
        bounds=base.estimator.Bounds(case['limits'])
        training=ChargedProblem(tv[:,9:12],tv[:,12:15],tv[:,2],tt,tg,covariance[:3*cut,:3*cut],seed,bounds,**kwargs)
        whole=ChargedProblem(values[:,9:12],values[:,12:15],values[:,2],times,gps,covariance,seed,bounds,**kwargs)
        fit=base.shape.fit_shape_candidate(training,task['model'],
            start=clock.initial_point(training,force,case['limits']),maximum_evaluations=200)
        fit['training_optimizer_converged']=fit['converged']
        point=np.array(fit['normalized_parameters'])
        first=training.predict(point,task['model']);full=whole.predict(point,task['model'])
        if not np.allclose(first,full[:cut],rtol=1e-10,atol=1e-7):raise ValueError('training prefix disagreement')
        metric=physical_metric(gps)
        diagnostics,epochs=prediction_report(times,gps,full,covariance,metric,cut)
        if not math.isclose(diagnostics['training']['conditional_cost'],fit['residual_sum_squares'],rel_tol=1e-6,abs_tol=1e-9):
            raise ValueError('native value/tangent objective disagreement')
        for row in epochs:row['time_utc_week_s']=row['time_s']+provenance['first_interval_start_utc_s']
        stem=identity.replace('::','-')
        name,digest=save_epochs(output,stem+'.csv.gz',epochs)
        fit.update(prediction_diagnostics=diagnostics,residual_file=name,residual_sha256=digest,
            continuous_propagation_without_gps_reset=True,prediction_receiver_positions_used_in_training=False,
            initialization_gps_epochs=len(tt),training_native_packets=len(tv))
        whole.phase='diagnostic';probes,omitted=axis_probes(point,.01)
        physical_cov=covariance*metric.ravel()[:,None]*metric.ravel()[None,:]
        detail=adapter.evaluate(whole,task['model'],point,probes,metric,physical_cov,cut,adapter.SweepBudget(1,54))
        if not np.allclose(detail['center_coordinates'],full,rtol=1e-10,atol=1e-7):raise ValueError('diagnostic tangent center disagreement')
        detail.update(probe_parameters=probes,omitted_directions=omitted)
        payload={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in detail.items()}
        name=stem+'-geometry.json.gz'
        clock.residuals.atomic_bytes(output/name,gzip.compress(json.dumps(payload,sort_keys=True,allow_nan=False).encode(),mtime=0))
        fit.update(uncertainty_geometry=detail['geometry'],geometry_file=name,
            geometry_sha256=base.il.sha256(output/name),omitted_probe_directions=omitted)
    except Exception as error:
        fit.update(model=task['model'],converged=False,error=type(error).__name__+': '+str(error))
    fit.update(case_id=task['processing_case'],covariance=task['covariance'],start_charge=charged,
        fit_native_sweeps=book.count(identity,'fit'),diagnostic_native_sweeps=book.count(identity,'diagnostic'),
        elapsed_s=time.monotonic()-begin,scientific_decision='abstain',scientific_eligible=False,
        confidence_calibrated=False,prospective_validation=False)
    fit['evaluations']=fit['fit_native_sweeps']
    return fit


def run(output,lock_fd=None):
    if (output/'completion.json').exists():raise ValueError('completed study is frozen; package only')
    authorization(output)
    with worker_lock(output,lock_fd):
        if (output/'completion.json').exists():raise ValueError('completed study is frozen; package only')
        manifest=verify(output,originals=True);authorization(output)
        digest=base.il.sha256(output/'manifest.json');p=manifest['proposal']
        book=journal.Ledger(output,digest,p['identities'])
        book.read('starts');book.read('sweeps')
        kernel,build=base.explore.load_kernel(output/'kernel');tangent,tbuild=base.shape.load_tangent(output/'kernel')
        if build!=manifest['value_kernel'] or tbuild!=manifest['tangent_kernel']:raise ValueError('native build mismatch')
        selected=base.load(output/'selection.json.gz')['selected'][0]
        context={r['task_id']:r for r in base.load('data/ilvis0-followup-20261007/summary.json')['results']}
        values,times,gps,provenance=base.segments.extract_segment(Path(selected['source_path']),context[selected['task']],selected['segment'])
        if provenance!=base.load(REFERENCE/'summary.json')['provenance']:raise ValueError('extraction provenance changed')
        layout=base.load(output/'split.json');cut=layout['training_epochs']
        if prediction.split(times)!={k:layout[k] for k in prediction.split(times)}:raise ValueError('actual split changed')
        blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
        grid={a.name:a for a in base.sensitivity.assumptions()}
        covs={c['name']:base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,grid[c['name']]) for c in p['covariances']}
        cases={c['case_id']:c for c in p['cases']};fits={}
        for task in p['tasks']:
            verify(output);identity=task['identity'];target=output/(identity.replace('::','-')+'.json')
            fit=base.cached(target,digest)
            if fit is not None and identity not in {r['identity'] for r in book.read('starts')}:
                raise ValueError('cached result has no charged start')
            if fit is None:
                if identity in {r['identity'] for r in book.read('starts')}:
                    fit=dict(model=task['model'],converged=False,error='interrupted charged start; no retry',
                        scientific_decision='abstain',fit_native_sweeps=book.count(identity,'fit'),
                        diagnostic_native_sweeps=book.count(identity,'diagnostic'))
                else:
                    base.follow.atomic_json(output/'status.json',dict(state='fitting',identity=identity,pid=os.getpid()))
                    fit=fit_task(output,task,cases[task['processing_case']],values,times,gps,covs[task['covariance']],
                        (kernel,tangent),book,cut,provenance)
                verify(output);base.save(target,fit,digest)
            for file_key,hash_key in (('residual_file','residual_sha256'),('geometry_file','geometry_sha256')):
                if file_key in fit:clock.residuals.check_hashes({str(output/fit[file_key]):fit[hash_key]})
            fits[identity]=fit
        summary=dict(version=VERSION,state='complete',results=fits,provenance=provenance,split=layout,
            starts=len(book.read('starts')),native_sweeps=len(book.read('sweeps')),
            training_profile=profiles(p['tasks'],fits,'training'),prediction_profile=profiles(p['tasks'],fits,'prediction'),
            scientific_decision='abstain',confidence_calibrated=False,prospective_validation=False)
        base.follow.atomic_json(output/'summary.json',summary)
        base.follow.atomic_json(output/'completion.json',dict(state='complete',manifest_sha256=digest,
            summary_sha256=base.il.sha256(output/'summary.json'),starts=summary['starts'],native_sweeps=summary['native_sweeps'],
            journal_hashes={name:base.il.sha256(output/name) for name in ('starts.jsonl','sweeps.jsonl')}))
        base.follow.atomic_json(output/'status.json',dict(state='complete',starts=summary['starts'],native_sweeps=summary['native_sweeps']))


def publish(output):
    manifest=verify(output);complete=base.load(output/'completion.json')
    if (complete['state']!='complete' or complete['manifest_sha256']!=base.il.sha256(output/'manifest.json')
            or complete['summary_sha256']!=base.il.sha256(output/'summary.json')):raise ValueError('invalid completion')
    summary=base.load(output/'summary.json');check_accounting(output,manifest,summary,complete)
    names=['manifest.json','selection.json.gz','split.json',
        'summary.json','completion.json','starts.jsonl','sweeps.jsonl','authorization.json']
    for fit in summary['results'].values():
        for key,hash_key in (('residual_file','residual_sha256'),('geometry_file','geometry_sha256')):
            if key in fit:
                name=fit[key];clock.residuals.check_hashes({str(output/name):fit[hash_key]});names.append(name)
    for name in names:shutil.copyfile(output/name,GUIDE/name)
    shutil.copytree(output/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    table=[]
    for task in manifest['proposal']['tasks']:
        fit=summary['results'][task['identity']];d=fit.get('prediction_diagnostics',{})
        table.append(dict(identity=task['identity'],covariance=task['covariance'],
            processing=task['processing_case'],model=task['model'],
            status='converged' if fit['converged'] else 'unresolved',
            fit_sweeps=fit['fit_native_sweeps'],diagnostic_sweeps=fit['diagnostic_native_sweeps'],
            training_horizontal_rms_m=d.get('training',{}).get('horizontal_rms_m'),
            prediction_horizontal_rms_m=d.get('prediction',{}).get('horizontal_rms_m'),
            prediction_vertical_rms_m=d.get('prediction',{}).get('vertical_rms_m'),
            rank=fit.get('uncertainty_geometry',{}).get('rank')))
    clock.residuals.atomic_bytes(GUIDE/'fits.csv',clock.residuals.csv_bytes(table));names.append('fits.csv')
    text=f"# Completed matched prediction comparison\n\n{sum(r['status']=='converged' for r in table)}/12 fits converged. "
    text+=f"Charged starts: {summary['starts']}; native sweeps: {summary['native_sweeps']}.\n\n"
    text+=f"Training shape preference: **{summary['training_profile']['conditional_shape_preference']}**. "
    text+=f"Prediction-cost shape preference: **{summary['prediction_profile']['conditional_shape_preference']}**.\n\n"
    text+='These are retrospective numerical preferences under two shared receiver-error assumptions. '
    text+='Unfinished fits remain unresolved. Prediction innovations condition receiver error on training residuals; '
    text+='their covariance excludes bounded calibration uncertainty. Axis probes and local rank are diagnostics, '
    text+='not calibrated intervals. This comparison establishes neither statistical significance nor the cause '
    text+='of a background rotation field. See [fit details](fits.csv) and [frozen method](PLAN.md).\n'
    (GUIDE/'RESULTS.md').write_text(text);names.append('RESULTS.md')
    base.follow.atomic_json(GUIDE/'evidence-receipt.json',dict(version=VERSION,
        artifacts={n:base.il.sha256(GUIDE/n) for n in names},scientific_decision='abstain'))


def check_accounting(output,manifest,summary,complete):
    p=manifest['proposal'];book=journal.Ledger(output,base.il.sha256(output/'manifest.json'),p['identities'])
    starts=book.read('starts');sweeps=book.read('sweeps')
    if (len(starts)!=12 or summary['starts']!=len(starts) or complete['starts']!=len(starts)
            or summary['native_sweeps']!=len(sweeps) or complete['native_sweeps']!=len(sweeps)
            or set(summary['results'])!=set(p['identities'])):raise ValueError('completion accounting mismatch')
    clock.residuals.check_hashes({str(output/name):digest for name,digest in complete['journal_hashes'].items()})
    if set(complete['journal_hashes'])!={'starts.jsonl','sweeps.jsonl'}:raise ValueError('missing journal hashes')
    for identity,fit in summary['results'].items():
        if (fit['fit_native_sweeps']!=book.count(identity,'fit')
                or fit['diagnostic_native_sweeps']!=book.count(identity,'diagnostic')):
            raise ValueError('saved fit accounting mismatch')


def software_control(output):
    from lll import ilvis0_geographic_controls as geographic
    f=geographic.fixture('sphere_rotating','nominal')
    kernel=base.explore.load_kernel(output/'kernel')[0];tangent=base.shape.load_tangent(output/'kernel')[0]
    p=geographic.problem(f,kernel,tangent)
    covariance=p.cholesky@p.cholesky.T
    book=journal.Ledger(output,'software-only',['control']);book.start('control')
    training=ChargedProblem(f['theta'],f['dv'],f['dt'],f['gps_times'][:16],f['gps'][:16],
        covariance[:48,:48],f['initial'],p.bounds.base,fit_earth_removal=False,kernel=kernel,tangent_kernel=tangent,
        clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.,ledger=book,identity='control')
    whole=ChargedProblem(f['theta'],f['dv'],f['dt'],f['gps_times'],f['gps'],covariance,
        f['initial'],p.bounds.base,fit_earth_removal=False,kernel=kernel,tangent_kernel=tangent,
        clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.,ledger=book,identity='control')
    truth=geographic.truth_point(f,p)
    fit=base.shape.fit_shape_candidate(training,f['model'],start=truth,maximum_evaluations=8)
    point=np.array(fit['normalized_parameters']);first=training.predict(point,f['model']);full=whole.predict(point,f['model'])
    probes,_=axis_probes(point,.01);whole.phase='diagnostic'
    metric=np.tile(f['metric'],(24,1));physical=covariance*metric.ravel()[:,None]*metric.ravel()[None,:]
    detail=adapter.evaluate(whole,f['model'],point,probes,metric,physical,16,adapter.SweepBudget(1,12))
    report,epochs=prediction_report(f['gps_times'],f['gps'],full,covariance,metric,16)
    name,_=save_epochs(output,'software-epochs.csv.gz',epochs)
    return dict(maximum_truth_error_m=geographic.position_error(f,full),
        fit_native_sweeps=book.count('control','fit'),diagnostic_native_sweeps=book.count('control','diagnostic'),
        training_epochs=16,prediction_epochs=8,prefix_agreement=bool(np.allclose(first,full[:16],atol=1e-7,rtol=1e-10)),
        epochs_written=len(epochs),residual_path=str(output/name),observed_fit_starts=0,archive_records_loaded=0,
        geometry=detail['geometry'],prediction_report=report,training_optimizer_converged=fit['converged'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    for flag in ('prepare-only','package-only','detach','record-authorization','software-control'):
        group.add_argument('--'+flag,action='store_true')
    parser.add_argument('--lock-fd',type=int)
    args=parser.parse_args()
    if args.package_only:publish(OUTPUT);return
    if args.software_control:
        from tempfile import TemporaryDirectory
        with TemporaryDirectory(prefix='ilvis0-worker-control-') as directory:
            print(json.dumps(software_control(Path(directory)),sort_keys=True))
        return
    if args.prepare_only:prepare(OUTPUT);print('Freeze prepared; no archive extraction or numerical starts.');return
    if args.record_authorization:authorize(OUTPUT);print('Explicit finite allowance recorded.');return
    if args.detach:
        authorization(OUTPUT);verify(OUTPUT)
        if (OUTPUT/'completion.json').exists():raise ValueError('completed study is frozen')
        with worker_lock(OUTPUT) as lock:
            with (OUTPUT/'worker.log').open('ab') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--lock-fd',str(lock.fileno())],
                    cwd=Path.cwd(),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                    pass_fds=(lock.fileno(),),start_new_session=True)
            base.follow.atomic_json(OUTPUT/'worker.json',dict(pid=child.pid,manifest_sha256=base.il.sha256(OUTPUT/'manifest.json')))
        print('Worker launched with inherited exclusive lock.');return
    run(OUTPUT,args.lock_fd);publish(OUTPUT)


if __name__=='__main__':main()
