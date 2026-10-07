# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded, resumable research GLS refits of six saved recordings; no decisions."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from scipy.optimize import least_squares

import continuous_measurement_motion as continuous
import covariance_measurement_objective as objective
import refit_joint_acceleration_motion as saved
import review_temporal_measurement_covariance as preparation
import temporal_measurement_covariance as temporal
import wind_constraint_discrepancy as discrepancy
from lll import models
from lll.calib import RAD2DPH
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash

ROOT=saved.ROOT
OUTPUT=ROOT/'docs/covariance-refits-20261007'
ORIGINAL=ROOT/'docs/observed-pair-replay-20261007/run'
JOINT=ROOT/'docs/joint-acceleration-motion-20261007/refits'
TEMPORAL=ROOT/'docs/temporal-measurement-covariance-20261007'
PARENT=ROOT/'docs/covariance-measurement-objective-20261007/wind-discrepancy'
POLICY=dict(version='saved-full-covariance-refits-1',correlation_pairs_seconds=[[0,0],[15,15],[300,300],[15,300]],
    primary_fits_per_case=['free',*models.EXPECTED_K],primary_fits=96,maximum_optimizer_starts=120,
    max_nfev=200,ftol=1e-10,xtol=1e-10,gtol=1e-8,x_scale='jac',numerical_threads=1,
    nesting_tolerance=1e-6,nesting_repair='At most one free restart per case, from the lowest fixed penalized objective; interrupted repair is not repeated',
    initialization='Saved joint free parameters; fixed fits start from the new free fit when available, otherwise the saved state',
    covariance='Frozen saved-state linearization, same full covariance for all four fits; registered independent 2 m/s auxiliary discrepancy retained',
    interrupted_starts='Count toward 120-start ceiling; never repeat a completed failure or nonconverged fit',
    additional_flight_attempts=0,bootstrap=0,production_enabled=False,decisions_enabled=False)


class FastObjective(objective.FrozenCovarianceObjective):
    """Same equation; exact linear columns avoid repeated finite differences."""
    def __init__(self,eq,C):
        super().__init__(eq,C)
        p=eq.problem;zero=np.zeros(p.npar);base=eq.residual(zero)
        self.bias_jacobian=np.zeros((len(base),p.p-3))
        for j in range(3,p.p):
            z=zero.copy();z[j]=1.
            self.bias_jacobian[:,j-3]=eq.residual(z)-base

    def raw_jacobian(self,z):
        eq=self.equation;p=eq.problem;local=eq.local_inputs(eq.x)
        C,_=eq.local_prediction(local,z)
        terms=np.stack(models.terms(local[:,3],local[:,2],local[:,0],local[:,1],local[:,4]),axis=-1)
        J=np.zeros((3*len(eq.bins['t']),len(z)))
        for j in range(3):J[:,j]=-eq.output(np.einsum('nij,nj->ni',C,terms[:,:,j]))
        J[:,3:p.p]=self.bias_jacobian
        lo,hi=p.bounds()
        for j in range(p.p,p.npar):
            if p.wind_tas is not None and j<p.p+p.nc and (j-p.p)%3==2:continue
            step=2e-3 if p.error_slice.start<=j<p.error_slice.stop or p.wind_tas is not None and j<p.p+p.nc else 2e-6
            a,b=z.copy(),z.copy();a[j]=min(z[j]+step,hi[j]);b[j]=max(z[j]-step,lo[j])
            J[:,j]=(eq.residual(a)-eq.residual(b))/(a[j]-b[j])
        _,aux=eq.auxiliary(z,jac=True)
        return np.vstack([J,aux])


def solve(working,start,fixed=None):
    p=working.equation.problem;lo,hi=p.bounds();z=np.clip(np.asarray(start,float).copy(),lo,hi)
    keep=np.arange(p.npar)
    if fixed is not None:z[:3]=fixed;keep=keep[3:]
    def unpack(x):
        value=z.copy();value[keep]=x;return value
    result=least_squares(lambda x:working.residual(unpack(x)),z[keep],
        jac=lambda x:working.jacobian(unpack(x))[:,keep],bounds=(lo[keep],hi[keep]),
        max_nfev=POLICY['max_nfev'],ftol=POLICY['ftol'],xtol=POLICY['xtol'],gtol=POLICY['gtol'],x_scale=POLICY['x_scale'])
    state=unpack(result.x);raw=working.raw_residual(state);J=working.raw_jacobian(state)
    response,_,curvature=objective.local_response(J[:,keep],working.penalty[:,keep],working.whitening)
    # Unit-normalized covariance reconstructed from the frozen whitening factor.
    L=working.whitening.sigma[:,None]*working.whitening.cholesky;C=L@L.T
    sampling=np.zeros((p.npar,p.npar));curv=sampling.copy()
    sampling[np.ix_(keep,keep)]=response@C@response.T;curv[np.ix_(keep,keep)]=curvature
    finite=np.isfinite(lo)&np.isfinite(hi);relative=np.full(p.npar,np.inf)
    relative[finite]=np.minimum(state[finite]-lo[finite],hi[finite]-state[finite])/(hi[finite]-lo[finite])
    meta=dict(success=bool(result.success),status=int(result.status),message=str(result.message),nfev=int(result.nfev),
        njev=int(result.njev or 0),optimality=float(result.optimality),scores=working.scores(state),
        boundary_parameter_indices=np.flatnonzero(relative<=1e-5).tolist(),minimum_relative_bound_margin=float(np.min(relative[finite])) if finite.any() else None,
        residual_rms_dph=float(np.sqrt(np.mean(raw[:3*len(working.equation.bins['t'])]**2))*RAD2DPH))
    return dict(z=state,raw_residual=raw,raw_jacobian=J,sampling_covariance=sampling,curvature_covariance=curv),meta


def append(path,value):
    with path.open('a') as out:
        out.write(json.dumps(value,allow_nan=False)+'\n');out.flush();os.fsync(out.fileno())


def archive(path,**arrays):
    temporary=path.with_suffix('.tmp.npz')
    with temporary.open('wb') as out:
        np.savez_compressed(out,**arrays);out.flush();os.fsync(out.fileno())
    temporary.replace(path)


def history(path):
    if not path.exists():return []
    data=path.read_bytes()
    if data and not data.endswith(b'\n'):
        end=data.rfind(b'\n')+1
        append(path.with_name('recovery.jsonl'),dict(truncated_hex=data[end:].hex(),utc=time.time()))
        with path.open('r+b') as out:out.truncate(end);out.flush();os.fsync(out.fileno())
        data=data[:end]
    records=[json.loads(line) for line in data.splitlines()]
    starts=[r['attempt'] for r in records if r['event']=='started']
    if starts!=list(range(1,len(starts)+1)):raise ValueError('optimizer journal start sequence differs')
    return records


def identity(row,pair):
    return hashlib.sha256(json.dumps([POLICY['version'],row['task_id'],pair],separators=(',',':')).encode()).hexdigest()


def load_fit(folder,name):
    meta=folder/(name+'.json')
    if not meta.exists():return None
    value=json.loads(meta.read_text())
    if value.get('archive'):
        archive=folder/value['archive']
        if saved.sha(archive)!=value['archive_sha256']:raise ValueError('fit checkpoint hash differs')
        value['arrays']=dict(np.load(archive,allow_pickle=False))
    return value


def freeze(output):
    parent=json.loads((PARENT/'plan.json').read_text());files=dict(parent['source_sha256'])
    for name in ('plan.json','review.json','verification.json'):
        p=PARENT/name;files[str(p.relative_to(ROOT))]=saved.sha(p)
    for p in [Path(__file__),ROOT/'analysis/tests/test_refit_covariance_measurement.py']:
        files[str(p.relative_to(ROOT))]=saved.sha(p)
    def verify():
        if implementation_hash()!=parent['scientific_implementation_hash'] or numerical_environment_hash()!=parent['numerical_environment_hash']:raise ValueError('frozen source/environment differs')
        if any(saved.sha(ROOT/k)!=v for k,v in files.items()):raise ValueError('frozen dependency changed')
    verify();rows=json.loads((ORIGINAL/'campaign.json').read_text())['records']
    if len(rows)!=6:raise ValueError('exactly six saved cases required')
    tasks=[dict(case_id=identity(row,pair),task_id=row['task_id'],correlation_seconds=pair) for row in rows for pair in POLICY['correlation_pairs_seconds']]
    plan=dict(policy=POLICY,source_sha256=files,tasks=tasks,
        scientific_implementation_hash=parent['scientific_implementation_hash'],numerical_environment_hash=parent['numerical_environment_hash'])
    path=output/'plan.json'
    if path.exists():
        if json.loads(path.read_text())!=plan:raise ValueError('resume plan differs')
    else:saved.atomic(path,plan)
    return plan,rows,verify


def run(output):
    if any(os.environ.get(k)!='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')):raise ValueError('one numerical thread required')
    output.mkdir(exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            plan,rows,verify=freeze(output);journal=output/'attempts.jsonl';events=history(journal)
            started=sum(e['event']=='started' for e in events);records=[]
            for row in rows:
                eq=None
                for pair in POLICY['correlation_pairs_seconds']:
                    verify();case_id=identity(row,pair);folder=output/case_id;folder.mkdir(exist_ok=True)
                    final=folder/'result.json'
                    if final.exists():
                        result=json.loads(final.read_text())
                        for name in result['fits']:load_fit(folder,name)
                        records.append(result);continue
                    if eq is None:
                        eq,_,_,start=preparation.prepare(ORIGINAL,JOINT,row)
                        prior=dict(np.load(TEMPORAL/(row['task_id']+'.npz'),allow_pickle=False))
                        if not np.array_equal(eq.keep,prior['bin_mask']) or not np.array_equal(eq.bins['t'],prior['t']):raise ValueError('support differs')
                    gi=temporal.POLICY['gps_correlation_seconds'].index(pair[0]);ii=temporal.POLICY['imu_correlation_seconds'].index(pair[1])
                    C=discrepancy.add_discrepancy(prior['gps_covariances'][gi]+prior['imu_covariances'][ii],3*len(eq.bins['t']),row['fit_options']['crab_model'])
                    working=FastObjective(eq,C);fits={}
                    covariance_path=folder/'covariance.npz'
                    if covariance_path.exists():
                        stored=np.load(covariance_path,allow_pickle=False)
                        if not np.array_equal(stored['covariance'],C):raise ValueError('frozen working covariance differs')
                    else:
                        archive(covariance_path,covariance=C,bin_mask=eq.keep,t=eq.bins['t'])
                    for name in POLICY['primary_fits_per_case']+['nesting-repair']:
                        if name=='nesting-repair':
                            if not all('arrays' in f for f in fits.values()):break
                            best=min((fits[k] for k in models.EXPECTED_K),key=lambda f:f['scores']['penalized_least_squares'])
                            if fits['free']['scores']['penalized_least_squares']<=best['scores']['penalized_least_squares']+POLICY['nesting_tolerance']:break
                            reference=best['arrays']['z'];fixed=None
                        else:
                            fixed=None if name=='free' else models.EXPECTED_K[name]
                            reference=start if name=='free' or 'arrays' not in fits['free'] else fits['free']['arrays']['z']
                        fit=load_fit(folder,name)
                        if fit is None:
                            if name=='nesting-repair' and any(e['event']=='started' and e['case_id']==case_id and e['fit']==name for e in events):
                                fit=dict(success=False,error='Interrupted single repair; no second repair authorized')
                                saved.atomic(folder/(name+'.json'),fit);fits[name]=fit;break
                            if started>=POLICY['maximum_optimizer_starts']:raise ValueError('120-start budget exhausted')
                            verify();started+=1;event=dict(event='started',attempt=started,case_id=case_id,fit=name,utc=time.time());append(journal,event);events.append(event)
                            saved.atomic(output/'status.json',dict(state='running',pid=os.getpid(),completed_cases=len(records),optimizer_starts=started,case_id=case_id,fit=name))
                            tick=time.monotonic()
                            try:
                                arrays,fit=solve(working,reference,fixed)
                                path=folder/(name+'-'+str(started)+'.npz');archive(path,**arrays)
                                fit.update(archive=path.name,archive_sha256=saved.sha(path))
                            except Exception as error:fit=dict(success=False,error=repr(error))
                            fit.update(elapsed_s=time.monotonic()-tick,attempt=started)
                            saved.atomic(folder/(name+'.json'),fit)
                            append(journal,dict(event='complete',attempt=started,case_id=case_id,fit=name,success=fit['success'],elapsed_s=fit['elapsed_s']))
                            fit=load_fit(folder,name)
                            print(json.dumps(dict(case=case_id[:12],fit=name,success=fit['success'],elapsed_s=fit['elapsed_s'])),flush=True)
                        fits[name]=fit
                    candidates=[k for k in ('free','nesting-repair') if k in fits and 'arrays' in fits[k]]
                    free=min(candidates,key=lambda k:fits[k]['scores']['penalized_least_squares']) if candidates else None
                    q=lambda name:fits[name]['scores']['penalized_least_squares']
                    valid=free is not None and all('arrays' in fits[k] for k in models.EXPECTED_K)
                    result=dict(case_id=case_id,task_id=row['task_id'],truth=row['truth'],crab_model=row['fit_options']['crab_model'],correlation_seconds=pair,
                        common_minutes=len(eq.bins['t']),covariance_sha256=saved.sha(covariance_path),selected_free_fit=free,
                        all_primary_converged=all(fits[k]['success'] for k in POLICY['primary_fits_per_case']),
                        selected_comparison_converged=bool(valid and fits[free]['success'] and all(fits[k]['success'] for k in models.EXPECTED_K)),
                        nested=bool(valid and all(q(free)<=q(k)+POLICY['nesting_tolerance'] for k in models.EXPECTED_K)),
                        diagnostic_delta_objectives={k:q(k)-q(free) for k in models.EXPECTED_K} if valid else None,
                        fits={k:{key:value for key,value in f.items() if key!='arrays'} for k,f in fits.items()},decisions_enabled=False)
                    saved.atomic(final,result);records.append(result)
                    saved.atomic(output/'status.json',dict(state='running',pid=os.getpid(),completed_cases=len(records),optimizer_starts=started))
            verify();report=dict(complete=len(records)==24,cases=records,plan_sha256=saved.sha(output/'plan.json'),optimizer_starts=started,
                additional_flight_attempts=0,bootstrap=0,decisions_enabled=False,production_enabled=False)
            path=output/'review.json'
            if path.exists():
                if json.loads(path.read_text())!=report:raise ValueError('completed review differs')
            else:saved.atomic(path,report)
            saved.atomic(output/'status.json',dict(state='complete',pid=os.getpid(),completed_cases=len(records),optimizer_starts=started,active_workers=0))
        except BaseException as error:
            saved.atomic(output/'status.json',dict(state='stopped',pid=os.getpid(),error=repr(error)));raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUTPUT);parser.add_argument('--detach',action='store_true')
    args=parser.parse_args();output=args.output.resolve()
    if args.detach:
        output.mkdir(exist_ok=True)
        with (output/'launch.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            # A running worker owns the separate scientific execution lock.
            with (output/'run.lock').open('a') as active:
                fcntl.flock(active,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with (output/'worker.log').open('a') as log:
                command=[sys.executable,str(Path(__file__).resolve()),'--output',str(output)]
                child=subprocess.Popen(command,stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True)
                saved.atomic(output/'launch.json',dict(pid=child.pid,command=command,utc=time.time()))
            print(json.dumps(dict(pid=child.pid,output=str(output))))
    else:run(output)


if __name__=='__main__':main()
