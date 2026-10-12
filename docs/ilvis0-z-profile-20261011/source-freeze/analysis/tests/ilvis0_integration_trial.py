# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded matched integration comparison; preparing or packaging never starts fits."""
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
from lll import ilvis0_compensation as candidate

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'ilvis0-matched-integration-trial-v1'
OUTPUT = Path('data/ilvis0-integration-trial-20261011')
GUIDE = Path('docs/ilvis0-integration-trial-20261011')
REFERENCE = clock.GUIDE
QUALIFICATION = Path('docs/ilvis0-latitude-controls-20261011')
TARGET = clock.TARGET


def identities():
    return [TARGET+'::'+c['case_id']+'::'+m
            for c in clock.base.primary_cases() for m in clock.base.explore.MODELS]


def scope():
    return dict(version=VERSION, identities=identities(), cases=clock.base.primary_cases(),
        maximum_starts=6, maximum_per_identity=1, maximum_evaluations_per_start=200,
        retry_reserve=0, clock='header_elapsed', mode='combined',
        increment_convention='ordinary_rate_integrals',
        optimizer='frozen_original_fit_shape_candidate', original_initialization_reused=True)


def check_scope(manifest):
    if any(manifest.get(k)!=v for k,v in scope().items()):
        raise ValueError('integration comparison scope changed')


def journal(path, digest):
    rows=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if (len(rows)>6 or len({r['identity'] for r in rows})!=len(rows) or
        any(r['number']!=i+1 or r['identity'] not in identities() or
            r['manifest_sha256']!=digest or r['maximum_evaluations']!=200
            for i,r in enumerate(rows))):
        raise ValueError('invalid integration start journal')
    return rows


def charge(path, identity, digest):
    with path.open('a+') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        rows=journal(path,digest)
        if identity not in identities() or len(rows)>=6:
            raise ValueError('outside six-start scope')
        if any(r['identity']==identity for r in rows):
            raise ValueError('identity already charged; no retry')
        row=dict(number=len(rows)+1,identity=identity,manifest_sha256=digest,maximum_evaluations=200)
        stream.write(json.dumps(row,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return row


class NativeBudget:
    """Count every attempted native pass, including failures and saved diagnostics."""
    def __init__(self,problem,maximum=200):
        if type(maximum) is not int or not 1<=maximum<=200:
            raise ValueError('native allowance must be between 1 and 200')
        self.problem=problem;self.bounds=problem.bounds;self.maximum=maximum
        self.used=0;self.tangents=0;self.values=0

    def take(self,kind):
        if self.used>=self.maximum:
            raise clock.base.estimator.EvaluationLimit('native sweep allowance exhausted')
        self.used+=1
        if kind=='tangent':self.tangents+=1
        else:self.values+=1

    def residual_tangent(self,*args):
        self.take('tangent')
        return self.problem.residual_tangent(*args)

    def predict(self,problem,*args):
        self.take('value')
        return problem.predict(*args)


def snapshot_path(output,name):
    return output/'source-freeze'/Path(name).resolve().relative_to(ROOT)


def check_qualification_environment(environment):
    # The control report labels the same numerical thread settings as "threads".
    normalized={name:environment[name] for name in ('python','numpy','scipy')}
    normalized['thread_settings']=environment['threads']
    clock.base.runtime.check_environment(normalized)


def receipt_hashes(receipt,field,directory):
    root=ROOT if field=='sources' else directory.resolve()
    result={}
    for name,digest in receipt[field].items():
        path=Path(name)
        if not path.is_absolute():
            path=(root/path).resolve()
            if not path.is_relative_to(root):raise ValueError('receipt relative path escapes its root')
        result[str(path)]=digest
    return result


def verify(output):
    base=clock.base;manifest=base.load(output/'manifest.json');check_scope(manifest)
    clock.residuals.check_hashes(manifest['sources']);clock.residuals.check_hashes(manifest['inputs'])
    base.runtime.check_environment(manifest['environment'])
    for name,digest in manifest['sources'].items():
        if base.il.sha256(snapshot_path(output,name))!=digest:
            raise ValueError('integration source snapshot changed')
    if base.il.sha256(output/'selection.json.gz')!=manifest['selection_sha256']:
        raise ValueError('selected interval changed')
    return manifest


def prepare(output):
    base=clock.base;output.mkdir(parents=True,exist_ok=True)
    if (output/'manifest.json').exists():return verify(output)
    old=clock.verify(clock.OUTPUT)
    clock.audit.verify_artifacts(REFERENCE,base.load(REFERENCE/'evidence-receipt.json'))
    completion=base.load(REFERENCE/'completion.json')
    if (completion['state']!='complete' or completion['starts']!=6 or
        completion['manifest_sha256']!=base.il.sha256(REFERENCE/'manifest.json') or
        completion['summary_sha256']!=base.il.sha256(REFERENCE/'summary.json')):
        raise ValueError('invalid completed reference')
    reference=base.load(REFERENCE/'summary.json')
    expected={(c['case_id'],m) for c in base.primary_cases() for m in base.explore.MODELS}
    keys=[(c['case_id'],f['model']) for c in reference['cases'] for f in c['fits']]
    if (len(keys)!=6 or set(keys)!=expected or any(clock.audit.fit_status(f)!='converged'
        for c in reference['cases'] for f in c['fits'])):
        raise ValueError('reference requires six converged fits')
    sources=dict(old['sources']);inputs=dict(old['inputs'])
    for name in ('report-receipt.json','findings-receipt.json'):
        receipt=base.load(QUALIFICATION/name)
        clock.audit.verify_artifacts(QUALIFICATION,receipt)
        for field,target in (('sources',sources),('inputs',inputs)):
            hashes=receipt_hashes(receipt,field,QUALIFICATION)
            clock.residuals.check_hashes(hashes)
            for path,digest in hashes.items():
                if path in target and target[path]!=digest:raise ValueError('qualification hash conflict')
                target[path]=digest
        if 'environment' in receipt:check_qualification_environment(receipt['environment'])
    qualified=base.load(QUALIFICATION/'completion.json')
    if (qualified['charged_starts']!=24 or qualified['charged_predictions']!=36 or
        qualified['passed']!=24 or
        qualified['manifest_sha256']!=base.il.sha256(QUALIFICATION/'manifest.json') or
        qualified['summary_sha256']!=base.il.sha256(QUALIFICATION/'summary.json')):
        raise ValueError('qualification completion mismatch')
    for path in (Path(__file__),Path('analysis/tests/test_ilvis0_integration_trial.py')):
        sources[str(path.resolve())]=base.il.sha256(path)
    for path in (REFERENCE/'manifest.json',REFERENCE/'summary.json',REFERENCE/'completion.json',
                 REFERENCE/'evidence-receipt.json',REFERENCE/'selection.json.gz',GUIDE/'PLAN.md',
                 QUALIFICATION/'report-receipt.json',QUALIFICATION/'findings-receipt.json',
                 QUALIFICATION/'manifest.json',QUALIFICATION/'summary.json',QUALIFICATION/'completion.json'):
        inputs[str(path.resolve())]=base.il.sha256(path)
    shutil.copyfile(REFERENCE/'selection.json.gz',output/'selection.json.gz')
    for name in sources:
        snapshot=snapshot_path(output,name);snapshot.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(name,snapshot)
    _,build=candidate.load_kernel(output/'kernel')
    manifest=dict(**scope(),environment=old['environment'],sources=sources,inputs=inputs,
        selection_sha256=base.il.sha256(output/'selection.json.gz'),candidate_kernel=build,
        reference_sha256=base.il.sha256(REFERENCE/'summary.json'),scientific_decision='abstain')
    base.follow.atomic_json(output/'manifest.json',manifest)
    return verify(output)


def fit_one(output,identity,case,model,values,times,gps,provenance,covs,metric,kernel):
    base=clock.base;fit={};budget=None
    try:
        seed,force=base.corpus.initialize(times,gps,values,model)
        kwargs=dict(fit_earth_removal=case['profile'],kernel=None,tangent_kernel=kernel,
            clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
            maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.,
            convention='ordinary_rate_integrals')
        args=(values[:,9:12],values[:,12:15],values[:,2],times,gps)
        bounds=base.estimator.Bounds(case['limits'])
        problem=candidate.CompensatedProblem(*args,covs['h1_v3_tau60'],seed,bounds,mode='combined',**kwargs)
        original=candidate.CompensatedProblem(*args,covs['h1_v3_tau60'],seed,bounds,mode='baseline',**kwargs)
        generous=candidate.CompensatedProblem(*args,covs['h10_v30_tau300'],seed,bounds,mode='combined',**kwargs)
        budget=NativeBudget(problem)
        fit=base.shape.fit_shape_candidate(budget,model,
            start=clock.initial_point(problem,force,case['limits']),maximum_evaluations=200)
        point=np.array(fit['normalized_parameters'])
        prediction=budget.predict(problem,point,model)
        old_prediction=budget.predict(original,point,model)
        delta=prediction-gps;delta[:,1]=(delta[:,1]+math.pi)%(2*math.pi)-math.pi
        old_delta=old_prediction-gps;old_delta[:,1]=(old_delta[:,1]+math.pi)%(2*math.pi)-math.pi
        physical=delta/metric;primary=problem.whiten(delta).reshape(-1,3)
        conservative=generous.whiten(delta).reshape(-1,3)
        if not math.isclose(float(np.sum(primary**2)),fit['residual_sum_squares'],rel_tol=1e-6,abs_tol=1e-9):
            raise ValueError('saved prediction/tangent objective disagreement')
        epochs=[]
        for i in range(len(times)):
            epoch=dict(epoch=i,time_utc_week_s=float(times[i]+provenance['first_interval_start_utc_s']))
            for j,axis in enumerate(('north','east','up')):
                for label,array in (('residual_m',physical),('coordinate_residual',delta),
                                     ('primary_innovation',primary),('conservative_innovation',conservative)):
                    epoch[axis+'_'+label]=float(array[i,j])
            epochs.append(epoch)
        name=identity.replace('::','-')+'.csv.gz'
        clock.residuals.atomic_bytes(output/name,
            clock.residuals.gzip.compress(clock.residuals.csv_bytes(epochs),mtime=0))
        fit.update(residual_file=name,residual_sha256=base.il.sha256(output/name),
            residual_rms_neu_m=np.sqrt(np.mean(physical**2,axis=0)).tolist(),
            original_integration_fixed_parameter_rms_neu_m=np.sqrt(np.mean((old_delta/metric)**2,axis=0)).tolist(),
            conservative_fixed_parameter_cost=float(np.sum(conservative**2)),
            epoch_diagnostics=clock.stats.summarize(times,physical,primary,conservative,
                clock.residuals.covariates(times,gps)))
    except Exception as error:
        fit.update(converged=False,error=type(error).__name__+': '+str(error))
    fit.update(model=model,case_id=case['case_id'],evaluations=budget.used if budget else 0,
        actual_tangent_sweeps=budget.tangents if budget else 0,diagnostic_predictions=budget.values if budget else 0,
        maximum_evaluations=200,clock_hypothesis='header_elapsed',integration_mode='combined',
        increment_convention='ordinary_rate_integrals',scientific_decision='abstain')
    return fit


def checked_cache(output,identity,digest):
    base=clock.base;target=output/(identity.replace('::','-')+'.json')
    charged=any(r['identity']==identity for r in journal(output/'starts.jsonl',digest))
    fit=base.cached(target,digest)
    if fit is not None:
        if not charged:raise ValueError('uncharged saved fit')
        if fit.get('residual_file'):
            path=output/fit['residual_file']
            if path.resolve().parent!=output.resolve():raise ValueError('residual outside trial')
            clock.residuals.check_hashes({str(path):fit['residual_sha256']})
        return fit
    if charged:
        fit=dict(model=identity.split('::')[-1],case_id=identity.split('::')[-2],converged=False,
            error='interrupted charged start; no retry',evaluations=None,
            charged_native_sweep_allowance=200,scientific_decision='abstain')
        base.save(target,fit,digest)
        return fit
    return None


def run(output,lock_fd=None):
    base=clock.base;output.mkdir(parents=True,exist_ok=True)
    lock=os.fdopen(lock_fd,'a') if lock_fd is not None else (output/'worker.lock').open('a')
    with lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'completion.json').exists():raise ValueError('completed trial is frozen; package only')
        manifest=prepare(output);digest=base.il.sha256(output/'manifest.json')
        base.follow.atomic_json(output/'status.json',dict(state='preparing',pid=os.getpid(),
            charged_starts=len(journal(output/'starts.jsonl',digest)),maximum_starts=6))
        kernel,build=candidate.load_kernel(output/'kernel')
        if build!=manifest['candidate_kernel']:raise ValueError('native build differs from freeze')
        chosen=base.load(output/'selection.json.gz')['selected'][0]
        contexts={r['task_id']:r for r in base.load('data/ilvis0-followup-20261007/summary.json')['results']}
        values,times,gps,provenance=base.segments.extract_segment(
            Path(chosen['source_path']),contexts[chosen['task']],chosen['segment'])
        reference=base.load(REFERENCE/'summary.json')
        if provenance!=reference['provenance']:raise ValueError('extraction provenance changed')
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
                verify(output);identity=TARGET+'::'+case['case_id']+'::'+model
                fit=checked_cache(output,identity,digest)
                if fit is None:
                    charged=charge(output/'starts.jsonl',identity,digest);begin=time.monotonic()
                    base.follow.atomic_json(output/'status.json',dict(state='fitting',identity=identity,
                        pid=os.getpid(),charged_starts=charged['number'],maximum_starts=6))
                    fit=fit_one(output,identity,case,model,values,times,gps,provenance,covs,metric,kernel)
                    fit.update(start_charge=charged,elapsed_s=time.monotonic()-begin)
                    verify(output);base.save(output/(identity.replace('::','-')+'.json'),fit,digest)
                    print(json.dumps(dict(identity=identity,converged=fit['converged'],error=fit.get('error'))),flush=True)
                fits.append(fit)
            rows.append(dict(case_id=case['case_id'],fits=fits))
        count=len(journal(output/'starts.jsonl',digest))
        if count!=6:raise ValueError('incomplete start ledger')
        both=[dict(r,case_id=treatment+'__'+r['case_id'])
              for treatment,cases in (('original',reference['cases']),('combined',rows)) for r in cases]
        summary=dict(version=VERSION,state='complete',starts=count,cases=rows,
            profile=base.shape.hierarchical_profile(rows),
            integration_robustness_profile=base.shape.hierarchical_profile(both),
            header_reference=reference,provenance=provenance,scientific_decision='abstain')
        base.follow.atomic_json(output/'summary.json',summary)
        base.follow.atomic_json(output/'completion.json',dict(state='complete',manifest_sha256=digest,
            summary_sha256=base.il.sha256(output/'summary.json'),starts=count,scientific_decision='abstain'))
        base.follow.atomic_json(output/'status.json',dict(state='complete',pid=os.getpid(),
            charged_starts=count,maximum_starts=6,converged=sum(f['converged'] for r in rows for f in r['fits'])))


def publish(output):
    base=clock.base;verify(output);complete=base.load(output/'completion.json')
    digest=base.il.sha256(output/'manifest.json')
    if (complete['state']!='complete' or complete['starts']!=6 or len(journal(output/'starts.jsonl',digest))!=6 or
        complete['manifest_sha256']!=digest or complete['summary_sha256']!=base.il.sha256(output/'summary.json')):
        raise ValueError('integration completion mismatch')
    summary=base.load(output/'summary.json')
    expected={(c['case_id'],m) for c in base.primary_cases() for m in base.explore.MODELS}
    keys=[(c['case_id'],f['model']) for c in summary['cases'] for f in c['fits']]
    if len(keys)!=6 or set(keys)!=expected:raise ValueError('incomplete comparison')
    names=['manifest.json','selection.json.gz','summary.json','completion.json','starts.jsonl']
    table=[]
    old={(c['case_id'],f['model']):f for c in summary['header_reference']['cases'] for f in c['fits']}
    for case in summary['cases']:
        for saved in case['fits']:
            identity=TARGET+'::'+case['case_id']+'::'+saved['model']
            fit=checked_cache(output,identity,digest)
            if fit!=saved:raise ValueError('summary and saved fit differ')
            if fit.get('residual_file'):names.append(fit['residual_file'])
            ref=old[(case['case_id'],fit['model'])];params=fit.get('parameters',{})
            rms=fit.get('residual_rms_neu_m')
            table.append(dict(case_id=case['case_id'],model=fit['model'],status=clock.audit.fit_status(fit),
                original_cost=ref['residual_sum_squares'],combined_cost=fit.get('residual_sum_squares'),
                original_horizontal_rms_m=math.hypot(*ref['residual_rms_neu_m'][:2]),
                combined_horizontal_rms_m=math.hypot(*rms[:2]) if rms else None,
                original_vertical_rms_m=ref['residual_rms_neu_m'][2],combined_vertical_rms_m=rms[2] if rms else None,
                original_z_gain=ref['parameters']['gyro_gain_z'],combined_z_gain=params.get('gyro_gain_z'),
                original_z_bias_dph=ref['parameters']['gyro_bias_z']*648000/math.pi,
                combined_z_bias_dph=params['gyro_bias_z']*648000/math.pi if 'gyro_bias_z' in params else None,
                original_active_bounds=len(ref['active_bounds']),combined_active_bounds=len(fit.get('active_bounds',[])),
                native_sweeps=fit.get('evaluations'),error=fit.get('error')))
    GUIDE.mkdir(parents=True,exist_ok=True)
    for name in names:shutil.copyfile(output/name,GUIDE/name)
    shutil.copytree(output/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    base.write_csv(GUIDE/'comparison.csv',table,list(table[0]));names.append('comparison.csv')
    lines=['# Matched NASA integration comparison','',
        'Completed six-start development comparison. The original results remain unchanged.',
        'This tests an integration alternative on the same 438-second IMU type 21 recording,',
        'at median ground speed 878.06 km/h. Both paths use packet-header intervals and identical calibration bounds.','',
        'IMU means inertial measurement unit. The alternative assumes its angle and velocity increments',
        'are ordinary rate integrals and applies within-interval coning and rotating-force corrections.',
        'Improved fit alone does not establish the recorder’s proprietary processing convention.','',
        '| Processing case | Model | Completion | Original cost | Alternative cost |',
        '|---|---|---|---:|---:|']
    for row in table:
        cost=row['combined_cost'];value=f'{cost:.6g}' if cost is not None else 'unavailable'
        lines.append(f"| {row['case_id']} | {row['model']} | {row['status']} | {row['original_cost']:.6g} | {value} |")
    lines+=['',f"Shape-first comparison across both integration treatments: **{summary['integration_robustness_profile']['conditional_shape_preference']}**.",
        '', 'See [comparison table](comparison.csv) for axis errors, Z calibration and boundary counts;',
        'saved fits retain gradients, singular values and residual diagnostics. Failures remain recorded.',
        'These are exploratory fit comparisons. Residual adequacy and statistical calibration are separate checks.',
        'Neither this comparison nor its six fits constitutes independent replication.',
        '', '[Frozen plan](PLAN.md). Publication reads saved results and performs no fits.']
    rotation=summary['integration_robustness_profile']['rotation_diagnostics']
    if rotation is not None:
        contrasts=[r['conditional_still_minus_rotating_cost'] for r in rotation]
        preference=('rotating globe' if all(v>0 for v in contrasts) else
                    'still globe' if all(v<0 for v in contrasts) else 'mixed or tied')
        lines+=['',f'After the resolved globe comparison, the rotation preference is **{preference}**.']
    (GUIDE/'README.md').write_text('\n'.join(lines)+'\n');names.append('README.md')
    artifacts={name:base.il.sha256(GUIDE/name) for name in names}
    for name in base.load(output/'manifest.json')['sources']:
        snapshot=snapshot_path(GUIDE,name);artifacts[str(snapshot.relative_to(GUIDE))]=base.il.sha256(snapshot)
    base.follow.atomic_json(GUIDE/'evidence-receipt.json',dict(version=VERSION,
        scientific_decision='abstain',artifacts=artifacts))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    actions=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare-only','package-only','detach','run'):actions.add_argument('--'+name,action='store_true')
    parser.add_argument('--lock-fd',type=int);args=parser.parse_args()
    if args.lock_fd is not None and not args.run:parser.error('--lock-fd requires --run')
    if args.prepare_only:
        OUTPUT.mkdir(parents=True,exist_ok=True)
        with (OUTPUT/'worker.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            prepare(OUTPUT)
        print('Prepared six-start integration freeze; no fits started.');return
    if args.package_only:publish(OUTPUT);return
    if args.detach:
        OUTPUT.mkdir(parents=True,exist_ok=True)
        lock=(OUTPUT/'worker.lock').open('a')
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (OUTPUT/'completion.json').exists():raise ValueError('completed integration trial is frozen')
            prepare(OUTPUT)
            with (OUTPUT/'worker.log').open('ab') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--run','--lock-fd',str(lock.fileno())],
                    cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                    pass_fds=(lock.fileno(),),start_new_session=True)
            clock.base.follow.atomic_json(OUTPUT/'worker.json',dict(pid=child.pid,
                manifest_sha256=clock.base.il.sha256(OUTPUT/'manifest.json'),maximum_starts=6))
        finally:lock.close()
        print('Integration worker launched with inherited exclusive lock.');return
    run(OUTPUT,args.lock_fd);publish(OUTPUT)


if __name__=='__main__':main()
