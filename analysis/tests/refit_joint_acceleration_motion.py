# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resume bounded diagnostic refits of six existing recordings; never synthesize flights."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
import joint_acceleration_motion as joint
import review_acceleration_motion as observed
from lll import models
from lll.calib import RAD2DPH
from lll.inference_policy import INFERENCE_POLICY
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment, numerical_environment_hash
from lll.wind_tas import WIND_TAS_POLICY

ROOT=Path(__file__).resolve().parents[2]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as out:
        out.write(json.dumps(value,indent=2,allow_nan=False)+'\n');out.flush();os.fsync(out.fileno())
    temporary.replace(path)


def build(directory,row):
    folder=directory/'diagnostics'/row['task_id']
    inputs=observed.observed_inputs(folder)
    context=joint.MotionContext(inputs)
    analysis=json.loads((folder/'analysis.json').read_text())
    saved=dict(np.load(folder/'fit-rows.npz',allow_pickle=False))
    cal=analysis['calibration'];b0,b1=(np.asarray(cal[k]['bias_dph'])/RAD2DPH for k in ('pre','post'))
    t0,t1=(cal[k]['t_mid_s'] for k in ('pre','post'))
    def bias(t): return b0+np.clip((np.asarray(t)-t0)/(t1-t0),0,1)[...,None]*(b1-b0)
    settings=dict(row['fit_options'])
    settings['max_nfev']=200
    for key in ('bias_knot_seconds','bias_rw_sigma_dph_sqrth','crab_rate_sigma_dph'):
        if settings.get(key) is None:settings[key]=INFERENCE_POLICY[key]
    if settings.get('crab_knot_seconds') is None:settings['crab_knot_seconds']=INFERENCE_POLICY['wind_knot_seconds']
    if settings['crab_model']=='wind_tas':settings['wind_tas_policy']=dict(WIND_TAS_POLICY)
    problem=joint.JointAccelerationProblem(context,bias,np.asarray(analysis['bias_model']['prior_sigma_dph'])/RAD2DPH,settings)
    sigma=np.asarray(analysis['fit']['noise']['sigma_by_bin_axis_dph'])[context.bin_mask]
    problem.w=(RAD2DPH/sigma.ravel())**2
    return problem,problem.expand_saved(saved['parameters'])


def run(directory,output):
    if any(os.environ.get(key)!='1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')):
        raise ValueError('refits require one numerical thread')
    campaign_path=directory/'campaign.json';campaign=json.loads(campaign_path.read_text())
    if len(campaign['records'])!=6 or not campaign['execution']['complete']:
        raise ValueError('exactly the six completed saved cases required')
    if implementation_hash()!=campaign['implementation_hash']:raise ValueError('scientific implementation differs')
    source_paths=[Path(__file__),Path(joint.__file__),Path(observed.__file__),ROOT/'analysis/tests/acceleration_motion.py',campaign_path]
    for row in campaign['records']:
        folder=directory/'diagnostics'/row['task_id']
        source_paths += [folder/name for name in ('session.zip','analysis.json','fit-input.npz','fit-rows.npz')]
    frozen={str(p.relative_to(ROOT)):sha(p) for p in source_paths}
    plan=dict(version='saved-joint-motion-refits-1',cases=[r['task_id'] for r in campaign['records']],
        fits_per_case=['free',*models.EXPECTED_K],nesting_repair='One predefined free restart at the best fixed-model fit if nesting fails',
        maximum_optimizer_calls=30,max_nfev_per_fit=200,additional_flight_attempts=0,bootstrap=0,
        numerical_threads=1,source_sha256=frozen,numerical_environment_hash=numerical_environment_hash(),
        numerical_environment=numerical_environment(),
        scientific_implementation_hash=campaign['implementation_hash'],policy=joint.JOINT_POLICY,
        production_enabled=False,decisions_enabled=False)
    output.mkdir(exist_ok=True)
    plan_path=output/'plan.json'
    if plan_path.exists():
        if json.loads(plan_path.read_text())!=plan:raise ValueError('refit plan/source/environment mismatch')
    else:atomic(plan_path,plan)
    import fcntl
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        journal=output/'attempts.jsonl'
        history=[json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
        started=sum(r['event']=='started' for r in history)
        def append(value):
            with journal.open('a') as out:
                out.write(json.dumps(value,allow_nan=False)+'\n');out.flush();os.fsync(out.fileno())
        records=[]
        for row in campaign['records']:
            case_dir=output/row['task_id'];case_dir.mkdir(exist_ok=True)
            final=case_dir/'result.json'
            if final.exists():records.append(json.loads(final.read_text()));continue
            if any(sha(ROOT/k)!=v for k,v in frozen.items()):raise ValueError('frozen refit sources changed')
            problem,start=build(directory,row)
            fits={};began=time.monotonic()
            for name in plan['fits_per_case']+['nesting-repair']:
                if name=='nesting-repair':
                    best=min((fits[k] for k in models.EXPECTED_K),key=lambda v:v['objective'])
                    if fits['free']['objective']<=best['objective']+1e-6:break
                    reference=best['z'];fixed=None
                else:
                    fixed=None if name=='free' else models.EXPECTED_K[name]
                    reference=start if name=='free' else fits['free']['z']
                saved=case_dir/(name+'.npz');meta=case_dir/(name+'.json')
                if saved.exists() and meta.exists():
                    metadata=json.loads(meta.read_text())
                    if sha(saved)!=metadata['archive_sha256']:raise ValueError('saved refit archive hash mismatch')
                    fit=dict(np.load(saved,allow_pickle=False));fit.update(metadata)
                else:
                    if any(sha(ROOT/k)!=v for k,v in frozen.items()):raise ValueError('frozen refit sources changed')
                    atomic(output/'status.json',dict(state='running',task_id=row['task_id'],fit=name,completed_cases=len(records),pid=os.getpid()))
                    if started>=plan['maximum_optimizer_calls']:raise ValueError('bounded optimizer-call scope exhausted')
                    started+=1
                    append(dict(event='started',task_id=row['task_id'],fit=name,attempt=started,started_utc=time.time()))
                    tick=time.monotonic();fit=problem.solve(start=reference,fixed=fixed)
                    elapsed=time.monotonic()-tick
                    temporary=saved.with_suffix('.tmp.npz')
                    np.savez_compressed(temporary,z=fit['z'],pred=fit['pred'],J=fit['J'],cov=fit['cov'])
                    temporary.replace(saved)
                    metadata=dict(objective=fit['objective'],success=fit['success'],elapsed_s=elapsed,
                                  convergence=problem.convergence[-1],archive_sha256=sha(saved))
                    atomic(meta,metadata);fit.update(metadata)
                    append(dict(event='complete',task_id=row['task_id'],fit=name,attempt=started,elapsed_s=elapsed,success=fit['success']))
                fits[name]=fit
                print(json.dumps(dict(task=row['task_id'],fit=name,success=bool(fit['success']),objective=float(fit['objective']))),flush=True)
            free=fits.get('nesting-repair',fits['free'])
            nesting=all(free['objective']<=fits[k]['objective']+1e-6 for k in models.EXPECTED_K)
            residual=(problem.y-free['pred']).reshape(-1,3)
            result=dict(task_id=row['task_id'],truth=row['truth'],crab_model=row['fit_options']['crab_model'],
                fixed_supported_minutes=len(problem.bins['t']),converged=all(bool(f['success']) for f in fits.values()),
                nested=nesting,k=free['z'][:3].tolist(),local_k_sd=np.sqrt(np.maximum(np.diag(free['cov'])[:3],0)).tolist(),
                residual_rms_dph=float(np.sqrt(np.mean(residual**2))*RAD2DPH),free_objective=float(free['objective']),
                fixed_objectives={k:float(fits[k]['objective']) for k in models.EXPECTED_K},
                diagnostic_delta_objectives={k:float(fits[k]['objective']-free['objective']) for k in models.EXPECTED_K},
                fits={k:{key:f[key] for key in ('objective','success','elapsed_s','convergence')} for k,f in fits.items()},
                elapsed_this_resume_s=time.monotonic()-began,provenance=problem.provenance(),decisions='disabled',bootstrap=0)
            atomic(final,result);records.append(result)
        atomic(output/'review.json',dict(plan_sha256=sha(plan_path),cases=records,complete=len(records)==6,
            additional_flight_attempts=0,optimizer_calls=started,completed_fits=sum(len(r['fits']) for r in records),
            interpretation='Diagnostic saved-data refits with frozen old weights, six coherent error modes and no empirical decisions'))
        atomic(output/'status.json',dict(state='complete',completed_cases=len(records),pid=os.getpid(),additional_flight_attempts=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:run(args.directory.resolve(),args.output.resolve())
    except Exception as error:
        if args.output.exists():atomic(args.output/'status.json',dict(state='stopped',error=str(error),pid=os.getpid()))
        raise
