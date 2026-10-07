# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate frozen-covariance research objectives at six saved states; never refit."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import time

import numpy as np
import refit_joint_acceleration_motion as refitter
import review_temporal_measurement_covariance as saved
import covariance_measurement_objective as objective
from lll.calib import RAD2DPH
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def evaluate(directory,refits,baseline,temporal,row,output,policy):
    eq,_,_,z=saved.prepare(directory,refits,row)
    prior=dict(np.load(baseline/(row['task_id']+'.npz'),allow_pickle=False))
    matrices=dict(np.load(temporal/(row['task_id']+'.npz'),allow_pickle=False))
    if not np.array_equal(eq.bins['t'],prior['t']) or not np.array_equal(eq.keep,matrices['bin_mask']):raise ValueError('fixed support differs')
    raw=np.r_[eq.residual(z),eq.auxiliary(z)]
    if not np.allclose(raw[:len(prior['residual'])],prior['residual'],atol=1e-15,rtol=1e-12):raise ValueError('saved equation differs')
    G=np.vstack([-prior['parameter_jacobian'],prior['auxiliary_jacobian']]);P=prior['penalty']
    direction=np.zeros_like(z);direction[:3]=[.003,-.005,.004]
    direction[3:eq.problem.p]=1e-7*np.sin(np.arange(eq.problem.p-3))
    q=direction[eq.problem.p:eq.problem.p+eq.problem.nc]
    if eq.problem.wind_tas is None:q[:]=2e-5*np.sin(np.arange(len(q)))
    else:q.reshape(-1,3)[:]=np.array([.01,-.01,.0001])
    direction[eq.problem.error_slice]=.001*np.sin(np.arange(6));direction[-1]=2e-5
    step=.1
    def residual(state):return np.r_[eq.residual(state),eq.auxiliary(state)]
    direct=(residual(z+step*direction)-residual(z-step*direction))/(2*step)
    scenarios=[];sampling=[];curvature=[];max_gradient_error=0.;max_quadratic_error=0.;n=len(prior['residual'])
    for i,gps in enumerate(policy['gps_correlation_seconds']):
        for j,imu in enumerate(policy['imu_correlation_seconds']):
            C=matrices['gps_covariances'][i]+matrices['imu_covariances'][j]
            working=objective.FrozenCovarianceObjective(eq,C,penalty=P);W=working.whitening
            scores=working.scores(z)
            # Independent normalized full-matrix solve retains all cross blocks.
            scaled=C/W.sigma[:,None]/W.sigma[None,:];r=raw/W.sigma
            reference=float(r@np.linalg.solve(scaled,r))
            error=abs(reference-scores['data_quadratic'])/max(1.,abs(reference));max_quadratic_error=max(max_quadratic_error,error)
            derivative_error=np.linalg.norm(W.apply(direct-G@direction))/max(np.linalg.norm(W.apply(direct)),1e-30)
            max_gradient_error=max(max_gradient_error,float(derivative_error))
            if error>1e-9 or derivative_error>2e-3:raise ValueError('full-covariance objective/derivative check failed')
            response,residual_response,curve=objective.local_response(G,P,W)
            cov=response@C@response.T;after=residual_response@C@residual_response.T
            sampling.append(cov[:3,:3]);curvature.append(curve[:3,:3])
            scenarios.append(dict(gps_correlation_seconds=gps,imu_correlation_seconds=imu,**scores,
                relative_correlation_eigenvalue_margin=W.relative_eigenvalue_margin,
                local_gls_sampling_k_sd=np.sqrt(np.maximum(np.diag(cov)[:3],0.)).tolist(),
                local_penalized_curvature_k_sd=np.sqrt(np.maximum(np.diag(curve)[:3],0.)).tolist(),
                local_gls_residual_sigma_dph=float(np.sqrt(np.maximum(np.diag(after)[:n],0.).mean())*RAD2DPH)))
    path=output/(row['task_id']+'.npz');temporary=path.with_suffix('.tmp.npz')
    np.savez_compressed(temporary,t=prior['t'],bin_mask=eq.keep,parameters=z,raw_residual=raw,raw_jacobian=G,penalty=P,
        sampling_k_covariances=np.array(sampling),curvature_k_covariances=np.array(curvature))
    temporary.replace(path)
    return dict(task_id=row['task_id'],truth=row['truth'],crab_model=row['fit_options']['crab_model'],common_minutes=len(prior['t']),
        scenarios=scenarios,maximum_full_solve_quadratic_relative_error=max_quadratic_error,
        maximum_whitened_direction_relative_error=max_gradient_error,archive_sha256=refitter.sha(path))


def run(directory,refits,baseline,temporal,output):
    if any(os.environ.get(k)!='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')):raise ValueError('one numerical thread required')
    parent=json.loads((temporal/'plan.json').read_text());review=json.loads((temporal/'review.json').read_text())
    if not review['complete'] or len(review['cases'])!=6:raise ValueError('six completed parent cases required')
    files=dict(parent['source_sha256'])
    for p in [Path(__file__),Path(objective.__file__),temporal/'plan.json',temporal/'review.json',temporal/'verification.json']:
        files[str(p.relative_to(refitter.ROOT))]=refitter.sha(p)
    for c in review['cases']:
        p=temporal/(c['task_id']+'.npz')
        if refitter.sha(p)!=c['archive_sha256']:raise ValueError('parent archive differs')
        files[str(p.relative_to(refitter.ROOT))]=refitter.sha(p)
    def verify():
        if implementation_hash()!=parent['scientific_implementation_hash'] or numerical_environment_hash()!=parent['numerical_environment_hash']:raise ValueError('source/environment differs')
        if any(refitter.sha(refitter.ROOT/k)!=v for k,v in files.items()):raise ValueError('frozen dependency differs')
    verify();rows=json.loads((directory/'campaign.json').read_text())['records'];output.mkdir(exist_ok=True)
    plan=dict(version='six-saved-frozen-covariance-objective-1',policy=objective.POLICY,temporal_policy=parent['policy'],
        source_sha256=files,task_ids=[r['task_id'] for r in rows],scenarios_per_case=36,
        scientific_implementation_hash=implementation_hash(),numerical_environment_hash=numerical_environment_hash(),
        optimizer_calls=0,additional_flight_attempts=0,bootstrap=0)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);path=output/'plan.json'
        if path.exists():
            if json.loads(path.read_text())!=plan:raise ValueError('resume identity differs')
        else:refitter.atomic(path,plan)
        cases=[]
        for row in rows:
            verify();checkpoint=output/(row['task_id']+'.json')
            if checkpoint.exists():
                case=json.loads(checkpoint.read_text())
                if refitter.sha(output/(row['task_id']+'.npz'))!=case['archive_sha256']:raise ValueError('checkpoint differs')
            else:
                refitter.atomic(output/'status.json',dict(state='running',completed_cases=len(cases),task_id=row['task_id'],pid=os.getpid()))
                start=time.monotonic();case=evaluate(directory,refits,baseline,temporal,row,output,parent['policy']);case['elapsed_s']=time.monotonic()-start
                refitter.atomic(checkpoint,case)
            cases.append(case)
            print(json.dumps(dict(truth=case['truth'],crab=case['crab_model'],scenarios=len(case['scenarios']),
                quadratic_check=case['maximum_full_solve_quadratic_relative_error'],direction_check=case['maximum_whitened_direction_relative_error'])),flush=True)
        verify();result=dict(complete=True,cases=cases,plan_sha256=refitter.sha(path),optimizer_calls=0,additional_flight_attempts=0,bootstrap=0,
            production_enabled=False,decisions_enabled=False)
        report=output/'review.json'
        if report.exists():
            if json.loads(report.read_text())!=result:raise ValueError('completed review differs')
        else:refitter.atomic(report,result)
        refitter.atomic(output/'status.json',dict(state='complete',completed_cases=6,active_workers=0,pid=os.getpid()))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('directory','refits','baseline','temporal'):parser.add_argument(name,type=Path)
    parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    run(a.directory.resolve(),a.refits.resolve(),a.baseline.resolve(),a.temporal.resolve(),a.output.resolve())
