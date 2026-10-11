# SPDX-License-Identifier: AGPL-3.0-or-later
"""Approved twelve-start Z calibration ablation; completed studies remain frozen."""
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

VERSION = 'ilvis0-z-calibration-ablation-v1'
OUTPUT = Path('data/ilvis0-calibration-trial-20261011')
GUIDE = Path('docs/ilvis0-calibration-trial-20261011')
REFERENCE = clock.GUIDE
TARGET = clock.TARGET
ALTERNATIVES = ('gain_zero', 'offset_zero')


def cases():
    result = []
    for alternative in ALTERNATIVES:
        fixed = 'gyro_gain_z' if alternative=='gain_zero' else 'gyro_bias_z'
        for prior in clock.base.primary_cases():
            limits = dict(prior['limits']); limits[fixed]=0.
            result.append(dict(case_id=alternative+'__'+prior['case_id'],
                reference_case_id=prior['case_id'], alternative=alternative,
                fixed_parameter=fixed, profile=prior['profile'], limits=limits))
    return result


def identities():
    return [TARGET+'::'+c['case_id']+'::'+model
            for c in cases() for model in clock.base.explore.MODELS]


def scope():
    return dict(version=VERSION, identities=identities(), cases=cases(),
        maximum_starts=12, maximum_per_identity=1, maximum_evaluations_per_start=200,
        retry_reserve=0, clock='header_elapsed',
        optimizer='frozen_original_fit_shape_candidate', original_initialization_reused=True)


def check_scope(manifest):
    if any(manifest.get(k)!=v for k,v in scope().items()):
        raise ValueError('calibration trial freeze scope changed')


def journal(path, digest):
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if (len(rows)>12 or len({r['identity'] for r in rows})!=len(rows) or
        any(r['number']!=i+1 or r['identity'] not in identities() or
            r['manifest_sha256']!=digest or r['maximum_evaluations']!=200
            for i,r in enumerate(rows))):
        raise ValueError('invalid calibration start journal')
    return rows


def charge(path, identity, digest):
    with path.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        rows=journal(path, digest)
        if identity not in identities() or len(rows)>=12:
            raise ValueError('outside approved twelve-start scope')
        if any(r['identity']==identity for r in rows):
            raise ValueError('calibration identity already charged; no retry')
        row=dict(number=len(rows)+1, identity=identity,
                 manifest_sha256=digest, maximum_evaluations=200)
        stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
    fd=os.open(path.parent, os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
    return row


def verify(output):
    base=clock.base; manifest=base.load(output/'manifest.json'); check_scope(manifest)
    clock.residuals.check_hashes(manifest['sources'])
    clock.residuals.check_hashes(manifest['inputs'])
    base.runtime.check_environment(manifest['environment'])
    for name,digest in manifest['sources'].items():
        if base.il.sha256(output/'source-freeze'/Path(name).name)!=digest:
            raise ValueError('calibration source snapshot changed')
    if base.il.sha256(output/'selection.json.gz')!=manifest['selection_sha256']:
        raise ValueError('calibration selected interval changed')
    return manifest


def prepare(output):
    base=clock.base; output.mkdir(parents=True, exist_ok=True)
    if (output/'manifest.json').exists(): return verify(output)
    old=clock.verify(clock.OUTPUT)
    clock.audit.verify_artifacts(REFERENCE, base.load(REFERENCE/'evidence-receipt.json'))
    completion=base.load(REFERENCE/'completion.json')
    if (completion['state']!='complete' or completion['starts']!=6 or
        completion['manifest_sha256']!=base.il.sha256(REFERENCE/'manifest.json') or
        completion['summary_sha256']!=base.il.sha256(REFERENCE/'summary.json')):
        raise ValueError('invalid completed clock reference')
    reference=base.load(REFERENCE/'summary.json')
    expected={(c['case_id'],m) for c in base.primary_cases() for m in base.explore.MODELS}
    keys=[(c['case_id'],f['model']) for c in reference['cases'] for f in c['fits']]
    if (len(keys)!=6 or set(keys)!=expected or any(clock.audit.fit_status(f)!='converged'
            for c in reference['cases'] for f in c['fits'])):
        raise ValueError('reference does not contain six completed fits')
    sources=dict(old['sources'])
    for path in (Path(__file__), Path('analysis/tests/test_ilvis0_calibration_trial.py')):
        sources[str(path.resolve())]=base.il.sha256(path)
    if len({Path(p).name for p in sources})!=len(sources):
        raise ValueError('source snapshot filename collision')
    inputs=dict(old['inputs'])
    for path in (REFERENCE/'manifest.json', REFERENCE/'summary.json',
                 REFERENCE/'completion.json', REFERENCE/'evidence-receipt.json', GUIDE/'PLAN.md'):
        inputs[str(path.resolve())]=base.il.sha256(path)
    shutil.copyfile(REFERENCE/'selection.json.gz', output/'selection.json.gz')
    (output/'source-freeze').mkdir(exist_ok=True)
    for name in sources: shutil.copyfile(name, output/'source-freeze'/Path(name).name)
    manifest=dict(**scope(), environment=old['environment'], sources=sources, inputs=inputs,
        selection_sha256=base.il.sha256(output/'selection.json.gz'),
        value_kernel=old['value_kernel'], tangent_kernel=old['tangent_kernel'],
        reference_sha256=base.il.sha256(REFERENCE/'summary.json'), scientific_decision='abstain')
    base.follow.atomic_json(output/'manifest.json', manifest)
    return verify(output)


def profiles(rows, profile=None):
    profile=profile or clock.base.shape.hierarchical_profile
    return {a:profile([dict(r, case_id=r['reference_case_id'])
                      for r in rows if r['alternative']==a]) for a in ALTERNATIVES}


def run(output, lock_fd=None):
    base=clock.base; output.mkdir(parents=True, exist_ok=True)
    lock=os.fdopen(lock_fd, 'a') if lock_fd is not None else (output/'worker.lock').open('a')
    with lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'completion.json').exists():
            raise ValueError('completed calibration trial is frozen; package only')
        manifest=prepare(output); digest=base.il.sha256(output/'manifest.json')
        base.follow.atomic_json(output/'status.json', dict(state='preparing', pid=os.getpid(),
            charged_starts=len(journal(output/'starts.jsonl',digest)), maximum_starts=12))
        kernel,build=base.explore.load_kernel(output/'kernel')
        tangent,tangent_build=base.shape.load_tangent(output/'kernel')
        if build!=manifest['value_kernel'] or tangent_build!=manifest['tangent_kernel']:
            raise ValueError('native build differs from reference')
        chosen=base.load(output/'selection.json.gz')['selected'][0]
        contexts={r['task_id']:r for r in base.load('data/ilvis0-followup-20261007/summary.json')['results']}
        values,times,gps,provenance=base.segments.extract_segment(
            Path(chosen['source_path']), contexts[chosen['task']], chosen['segment'])
        reference=base.load(REFERENCE/'summary.json')
        if provenance!=reference['provenance']: raise ValueError('extraction provenance changed')
        blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
        grid={a.name:a for a in base.sensitivity.assumptions()}
        covs={n:base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,grid[n])
              for n in ('h1_v3_tau60','h10_v30_tau300')}
        metric=np.column_stack((1/(6378137.+gps[:,2]),
                    1/((6378137.+gps[:,2])*np.cos(gps[:,0])),np.ones(len(gps))))
        rows=[]
        for case in manifest['cases']:
            fits=[]
            for model in base.explore.MODELS:
                verify(output); identity=TARGET+'::'+case['case_id']+'::'+model
                target=output/(identity.replace('::','-')+'.json')
                fit=base.cached(target,digest)
                if fit is not None:
                    if fit.get('residual_file'):
                        clock.residuals.check_hashes({str(output/fit['residual_file']):fit['residual_sha256']})
                    fits.append(fit); continue
                if any(r['identity']==identity for r in journal(output/'starts.jsonl',digest)):
                    fit=dict(model=model,case_id=case['case_id'],converged=False,
                        error='interrupted charged start; no retry',scientific_decision='abstain')
                    base.save(target,fit,digest); fits.append(fit); continue
                seed,force=base.corpus.initialize(times,gps,values,model)
                kwargs=dict(fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=tangent,
                    clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
                    maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
                args=(values[:,9:12],values[:,12:15],values[:,2],times,gps)
                bounds=base.estimator.Bounds(case['limits'])
                problem=base.shape.TangentProblem(*args,covs['h1_v3_tau60'],seed,bounds,**kwargs)
                generous=base.shape.TangentProblem(*args,covs['h10_v30_tau300'],seed,bounds,**kwargs)
                charged=charge(output/'starts.jsonl',identity,digest); begin=time.monotonic()
                base.follow.atomic_json(output/'status.json',dict(state='fitting',identity=identity,
                    pid=os.getpid(),charged_starts=charged['number'],maximum_starts=12))
                fit={}
                try:
                    fit=base.shape.fit_shape_candidate(problem,model,
                        start=clock.initial_point(problem,force,case['limits']),maximum_evaluations=200)
                    point=np.array(fit['normalized_parameters']); prediction=problem.predict(point,model)
                    fit['evaluations']+=1
                    if fit['evaluations']>200: raise ValueError('calibration fit exceeded allowance')
                    if fit['parameters'][case['fixed_parameter']]!=0.:
                        raise ValueError('ablated calibration parameter is not zero')
                    delta=prediction-gps; delta[:,1]=(delta[:,1]+math.pi)%(2*math.pi)-math.pi
                    physical=delta/metric; primary=problem.whiten(delta).reshape(-1,3)
                    conservative=generous.whiten(delta).reshape(-1,3)
                    if not math.isclose(float(np.sum(primary**2)),fit['residual_sum_squares'],
                                        rel_tol=1e-6,abs_tol=1e-9):
                        raise ValueError('value/tangent objective disagreement')
                    epochs=[]
                    for i in range(len(times)):
                        epoch=dict(epoch=i,time_utc_week_s=float(times[i]+provenance['first_interval_start_utc_s']))
                        for j,axis in enumerate(('north','east','up')):
                            for label,array in [('residual_m',physical),('coordinate_residual',delta),
                                                ('primary_innovation',primary),('conservative_innovation',conservative)]:
                                epoch[axis+'_'+label]=float(array[i,j])
                        epochs.append(epoch)
                    name=identity.replace('::','-')+'.csv.gz'
                    clock.residuals.atomic_bytes(output/name,
                        clock.residuals.gzip.compress(clock.residuals.csv_bytes(epochs),mtime=0))
                    fit.update(residual_file=name,residual_sha256=base.il.sha256(output/name),
                        residual_rms_neu_m=np.sqrt(np.mean(physical**2,axis=0)).tolist(),
                        conservative_fixed_parameter_cost=float(np.sum(conservative**2)),
                        epoch_diagnostics=clock.stats.summarize(times,physical,primary,conservative,
                            clock.residuals.covariates(times,gps)),diagnostic_predictions=1,
                        clock_hypothesis='header_elapsed',fixed_parameter=case['fixed_parameter'])
                except Exception as error:
                    fit.update(model=model,converged=False,scientific_decision='abstain',
                               error=type(error).__name__+': '+str(error))
                fit.update(case_id=case['case_id'],alternative=case['alternative'],
                    reference_case_id=case['reference_case_id'],start_charge=charged,
                    elapsed_s=time.monotonic()-begin)
                verify(output); base.save(target,fit,digest); fits.append(fit)
                print(json.dumps(dict(identity=identity,converged=fit['converged'],error=fit.get('error'))),flush=True)
            rows.append(dict(case_id=case['case_id'],alternative=case['alternative'],
                reference_case_id=case['reference_case_id'],fits=fits))
        count=len(journal(output/'starts.jsonl',digest))
        summary=dict(version=VERSION,state='complete',starts=count,cases=rows,
            profiles=profiles(rows),header_reference=reference,provenance=provenance,scientific_decision='abstain')
        base.follow.atomic_json(output/'summary.json',summary)
        base.follow.atomic_json(output/'completion.json',dict(state='complete',manifest_sha256=digest,
            summary_sha256=base.il.sha256(output/'summary.json'),starts=count,scientific_decision='abstain'))
        base.follow.atomic_json(output/'status.json',dict(state='complete',pid=os.getpid(),
            charged_starts=count,maximum_starts=12,converged=sum(f['converged'] for r in rows for f in r['fits'])))


def publish(output):
    base=clock.base; verify(output); complete=base.load(output/'completion.json')
    if (complete['state']!='complete' or complete['manifest_sha256']!=base.il.sha256(output/'manifest.json') or
        complete['summary_sha256']!=base.il.sha256(output/'summary.json')):
        raise ValueError('calibration completion mismatch')
    summary=base.load(output/'summary.json')
    names=['manifest.json','selection.json.gz','summary.json','completion.json','starts.jsonl']
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
        prepare(OUTPUT); print('Prepared twelve-start calibration freeze; no fits started.'); return
    if args.package_only: publish(OUTPUT); return
    if args.detach:
        prepare(OUTPUT)
        if (OUTPUT/'completion.json').exists(): raise ValueError('completed calibration trial is frozen')
        lock=(OUTPUT/'worker.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with (OUTPUT/'worker.log').open('ab') as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--lock-fd',str(lock.fileno())],
                cwd=Path.cwd(),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                pass_fds=(lock.fileno(),),start_new_session=True)
        lock.close()
        clock.base.follow.atomic_json(OUTPUT/'worker.json',dict(pid=child.pid,
            manifest_sha256=clock.base.il.sha256(OUTPUT/'manifest.json'),maximum_starts=12))
        print('Calibration worker launched with inherited exclusive lock.'); return
    run(OUTPUT,args.lock_fd); publish(OUTPUT)


if __name__=='__main__': main()
