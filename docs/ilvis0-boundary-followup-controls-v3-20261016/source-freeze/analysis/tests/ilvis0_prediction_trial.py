# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six-start retrospective prediction trial with training-only initialization."""
import argparse
import fcntl
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
from lll import ilvis0_prediction as prediction

VERSION='ilvis0-training-prediction-trial-v1'
OUTPUT=Path('data/ilvis0-prediction-trial-20261011')
GUIDE=Path('docs/ilvis0-prediction-trial-20261011')
REFERENCE=clock.GUIDE
identities=clock.identities
journal=clock.journal
charge=clock.charge


def scope():
    return dict(version=VERSION,identities=identities(),cases=clock.base.primary_cases(),
        maximum_starts=6,maximum_per_identity=1,maximum_evaluations_per_start=200,retry_reserve=0,
        clock='header_elapsed',optimizer='frozen_original_fit_shape_candidate',
        initialization='training_receiver_and_training_imu_only',
        split_policy='first floor(2*N/3) receiver epochs train; remainder predict',
        covariance_policy='full-window declared covariance; training marginal block',
        prospective_validation=False,parameter_uncertainty_included=False)


def expected_split(selection,reference):
    chosen=selection['selected'][0]; origin=reference['provenance']['first_interval_start_utc_s']
    times=np.array([r['time_s']-origin for r in chosen['segment']['receiver_fixes']])
    return dict(**prediction.split(times),segment_id=clock.TARGET,
        first_interval_start_utc_week_s=origin,
        last_training_utc_week_s=float(times[2*len(times)//3-1]+origin),
        first_prediction_utc_week_s=float(times[2*len(times)//3]+origin))


def verify(output):
    base=clock.base; manifest=base.load(output/'manifest.json')
    if any(manifest.get(k)!=v for k,v in scope().items()):
        raise ValueError('prediction trial freeze scope changed')
    clock.residuals.check_hashes(manifest['sources']); clock.residuals.check_hashes(manifest['inputs'])
    base.runtime.check_environment(manifest['environment'])
    for name,digest in manifest['sources'].items():
        if base.il.sha256(output/'source-freeze'/Path(name).name)!=digest:
            raise ValueError('prediction source snapshot changed')
    for name in ('selection.json.gz','split.json'):
        if base.il.sha256(output/name)!=manifest['artifacts'][name]:
            raise ValueError('prediction interval/split changed')
    reference=base.load(REFERENCE/'summary.json')
    if base.load(output/'split.json')!=expected_split(base.load(output/'selection.json.gz'),reference):
        raise ValueError('prediction split differs from frozen receiver geometry')
    return manifest


def prepare(output):
    base=clock.base; output.mkdir(parents=True,exist_ok=True)
    if (output/'manifest.json').exists(): return verify(output)
    old=clock.verify(clock.OUTPUT)
    clock.audit.verify_artifacts(REFERENCE,base.load(REFERENCE/'evidence-receipt.json'))
    complete=base.load(REFERENCE/'completion.json')
    if (complete['state']!='complete' or complete['starts']!=6 or
        complete['summary_sha256']!=base.il.sha256(REFERENCE/'summary.json') or
        complete['manifest_sha256']!=base.il.sha256(REFERENCE/'manifest.json')):
        raise ValueError('invalid completed reference')
    reference=base.load(REFERENCE/'summary.json')
    shutil.copyfile(REFERENCE/'selection.json.gz',output/'selection.json.gz')
    layout=expected_split(base.load(output/'selection.json.gz'),reference)
    base.follow.atomic_json(output/'split.json',layout)
    sources=dict(old['sources'])
    for path in (Path(__file__),Path(prediction.__file__),Path('analysis/tests/test_ilvis0_prediction.py'),
                 Path('analysis/tests/test_ilvis0_prediction_trial.py')):
        sources[str(path.resolve())]=base.il.sha256(path)
    if len({Path(p).name for p in sources})!=len(sources):
        raise ValueError('source snapshot filename collision')
    inputs=dict(old['inputs'])
    for path in (REFERENCE/'manifest.json',REFERENCE/'summary.json',REFERENCE/'completion.json',
                 REFERENCE/'evidence-receipt.json',GUIDE/'PLAN.md'):
        inputs[str(path.resolve())]=base.il.sha256(path)
    (output/'source-freeze').mkdir(exist_ok=True)
    for name in sources: shutil.copyfile(name,output/'source-freeze'/Path(name).name)
    manifest=dict(**scope(),environment=old['environment'],sources=sources,inputs=inputs,
        artifacts={n:base.il.sha256(output/n) for n in ('selection.json.gz','split.json')},
        value_kernel=old['value_kernel'],tangent_kernel=old['tangent_kernel'],scientific_decision='abstain')
    base.follow.atomic_json(output/'manifest.json',manifest)
    return verify(output)


def prediction_profile(rows,profile=None):
    profile=profile or clock.base.shape.hierarchical_profile
    projected=[]
    for row in rows:
        fits=[]
        for fit in row['fits']:
            current=dict(fit)
            if fit.get('prediction_diagnostics'):
                current['residual_sum_squares']=fit['prediction_diagnostics']['prediction']['primary_conditional_cost']
            else:
                current['converged']=False
            fits.append(current)
        projected.append(dict(case_id=row['case_id'],fits=fits))
    return profile(projected)


def run(output,lock_fd=None):
    base=clock.base; output.mkdir(parents=True,exist_ok=True)
    lock=os.fdopen(lock_fd,'a') if lock_fd is not None else (output/'worker.lock').open('a')
    with lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'completion.json').exists(): raise ValueError('completed prediction trial is frozen')
        manifest=prepare(output); digest=base.il.sha256(output/'manifest.json')
        base.follow.atomic_json(output/'status.json',dict(state='preparing',pid=os.getpid(),
            charged_starts=len(journal(output/'starts.jsonl',digest)),maximum_starts=6))
        kernel,build=base.explore.load_kernel(output/'kernel')
        tangent,tangent_build=base.shape.load_tangent(output/'kernel')
        if build!=manifest['value_kernel'] or tangent_build!=manifest['tangent_kernel']:
            raise ValueError('native build differs from reference')
        chosen=base.load(output/'selection.json.gz')['selected'][0]
        context={r['task_id']:r for r in base.load('data/ilvis0-followup-20261007/summary.json')['results']}
        values,times,gps,provenance=base.segments.extract_segment(
            Path(chosen['source_path']),context[chosen['task']],chosen['segment'])
        reference=base.load(REFERENCE/'summary.json')
        if provenance!=reference['provenance']: raise ValueError('extraction provenance changed')
        layout=base.load(output/'split.json'); cut=layout['training_epochs']
        if prediction.split(times)!={k:layout[k] for k in prediction.split(times)}:
            raise ValueError('extracted receiver times differ from frozen split')
        blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
        grid={a.name:a for a in base.sensitivity.assumptions()}
        covs={n:base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,grid[n])
              for n in ('h1_v3_tau60','h10_v30_tau300')}
        rows=[]
        for case in manifest['cases']:
            fits=[]
            training_times,training_gps,training_values=prediction.training_inputs(
                times,gps,values,case['limits']['time_offset'])
            for model in base.explore.MODELS:
                verify(output); identity=clock.TARGET+'::'+case['case_id']+'::'+model
                target=output/(identity.replace('::','-')+'.json'); fit=base.cached(target,digest)
                if fit is not None:
                    if fit.get('residual_file'):
                        clock.residuals.check_hashes({str(output/fit['residual_file']):fit['residual_sha256']})
                    fits.append(fit); continue
                if any(r['identity']==identity for r in journal(output/'starts.jsonl',digest)):
                    fit=dict(model=model,case_id=case['case_id'],converged=False,
                        error='interrupted charged start; no retry',scientific_decision='abstain')
                    base.save(target,fit,digest); fits.append(fit); continue
                seed,force=base.corpus.initialize(training_times,training_gps,training_values,model)
                kwargs=dict(fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=tangent,
                    clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
                    maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
                bounds=base.estimator.Bounds(case['limits'])
                training=base.shape.TangentProblem(training_values[:,9:12],training_values[:,12:15],
                    training_values[:,2],training_times,training_gps,covs['h1_v3_tau60'][:3*cut,:3*cut],seed,bounds,**kwargs)
                whole=base.shape.TangentProblem(values[:,9:12],values[:,12:15],values[:,2],
                    times,gps,covs['h1_v3_tau60'],seed,bounds,**kwargs)
                charged=charge(output/'starts.jsonl',identity,digest); begin=time.monotonic()
                base.follow.atomic_json(output/'status.json',dict(state='fitting',identity=identity,
                    pid=os.getpid(),charged_starts=charged['number'],maximum_starts=6))
                fit={}
                try:
                    fit=base.shape.fit_shape_candidate(training,model,
                        start=clock.initial_point(training,force,case['limits']),maximum_evaluations=200)
                    fit['training_optimizer_converged']=fit['converged']
                    point=np.array(fit['normalized_parameters'])
                    first=training.predict(point,model); fit['evaluations']+=1
                    full=whole.predict(point,model); fit['evaluations']+=1
                    if fit['evaluations']>200: raise ValueError('prediction fit exceeded allowance')
                    if not np.allclose(first,full[:cut],rtol=1e-10,atol=1e-7):
                        raise ValueError('continuous prediction disagrees on training prefix')
                    error=full-gps; error[:,1]=(error[:,1]+math.pi)%(2*math.pi)-math.pi
                    diag=prediction.diagnostics(times,gps,error,covs['h1_v3_tau60'],covs['h10_v30_tau300'])
                    if not math.isclose(diag['training']['primary_conditional_cost'],
                            fit['residual_sum_squares'],rel_tol=1e-6,abs_tol=1e-9):
                        raise ValueError('value/tangent training objective disagreement')
                    epochs=diag.pop('epoch_rows')
                    for epoch in epochs:
                        epoch['time_utc_week_s']=epoch['time_s']+provenance['first_interval_start_utc_s']
                    name=identity.replace('::','-')+'.csv.gz'
                    clock.residuals.atomic_bytes(output/name,
                        clock.residuals.gzip.compress(clock.residuals.csv_bytes(epochs),mtime=0))
                    fit.update(prediction_diagnostics=diag,residual_file=name,
                        residual_sha256=base.il.sha256(output/name),diagnostic_predictions=2,
                        training_native_packets=len(training_values),
                        training_last_native_time_s=float(np.sum(training_values[:,2])),
                        initialization_gps_epochs=len(training_times),
                        prediction_receiver_positions_used_in_training=False,
                        continuous_propagation_without_gps_reset=True,
                        clock_hypothesis='header_elapsed',prospective_validation=False)
                except Exception as error:
                    fit.update(model=model,converged=False,scientific_decision='abstain',
                               error=type(error).__name__+': '+str(error))
                fit.update(case_id=case['case_id'],start_charge=charged,elapsed_s=time.monotonic()-begin)
                verify(output); base.save(target,fit,digest); fits.append(fit)
                print(json.dumps(dict(identity=identity,converged=fit['converged'],error=fit.get('error'))),flush=True)
            rows.append(dict(case_id=case['case_id'],fits=fits))
        count=len(journal(output/'starts.jsonl',digest))
        summary=dict(version=VERSION,state='complete',starts=count,cases=rows,split=layout,
            training_profile=base.shape.hierarchical_profile(rows),prediction_profile=prediction_profile(rows),
            provenance=provenance,header_reference=reference,prospective_validation=False,scientific_decision='abstain')
        base.follow.atomic_json(output/'summary.json',summary)
        base.follow.atomic_json(output/'completion.json',dict(state='complete',manifest_sha256=digest,
            summary_sha256=base.il.sha256(output/'summary.json'),starts=count,scientific_decision='abstain'))
        base.follow.atomic_json(output/'status.json',dict(state='complete',pid=os.getpid(),charged_starts=count,
            maximum_starts=6,converged=sum(f['converged'] for r in rows for f in r['fits'])))


def publish(output):
    base=clock.base; verify(output); complete=base.load(output/'completion.json')
    if (complete['state']!='complete' or complete['manifest_sha256']!=base.il.sha256(output/'manifest.json') or
        complete['summary_sha256']!=base.il.sha256(output/'summary.json')):
        raise ValueError('prediction completion mismatch')
    summary=base.load(output/'summary.json')
    names=['manifest.json','selection.json.gz','split.json','summary.json','completion.json','starts.jsonl']
    names += [f['residual_file'] for c in summary['cases'] for f in c['fits'] if f.get('residual_file')]
    for name in names: shutil.copyfile(output/name,GUIDE/name)
    shutil.copytree(output/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    base.follow.atomic_json(GUIDE/'evidence-receipt.json',dict(version=VERSION,scientific_decision='abstain',
        artifacts={name:base.il.sha256(GUIDE/name) for name in names}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true'); parser.add_argument('--package-only',action='store_true')
    parser.add_argument('--detach',action='store_true'); parser.add_argument('--lock-fd',type=int)
    args=parser.parse_args()
    if sum((args.prepare_only,args.package_only,args.detach))>1: parser.error('choose one action')
    if args.prepare_only:
        prepare(OUTPUT); print('Prediction freeze prepared/verified; this command starts no fits.'); return
    if args.package_only: publish(OUTPUT); return
    if args.detach:
        prepare(OUTPUT)
        if (OUTPUT/'completion.json').exists(): raise ValueError('completed prediction trial is frozen')
        lock=(OUTPUT/'worker.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with (OUTPUT/'worker.log').open('ab') as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--lock-fd',str(lock.fileno())],
                cwd=Path.cwd(),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                pass_fds=(lock.fileno(),),start_new_session=True)
        lock.close()
        clock.base.follow.atomic_json(OUTPUT/'worker.json',dict(pid=child.pid,
            manifest_sha256=clock.base.il.sha256(OUTPUT/'manifest.json'),maximum_starts=6))
        print('Prediction worker launched with inherited exclusive lock.'); return
    run(OUTPUT,args.lock_fd); publish(OUTPUT)


if __name__=='__main__': main()
