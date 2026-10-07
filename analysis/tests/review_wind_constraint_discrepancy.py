# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare explicit registered wind discrepancy across saved frozen GLS scenarios."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import time

import numpy as np
import refit_joint_acceleration_motion as refitter
import covariance_measurement_objective as objective
import wind_constraint_discrepancy as discrepancy
from lll.calib import RAD2DPH
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def run(parent,temporal,output):
    if any(os.environ.get(k)!='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')):raise ValueError('one numerical thread required')
    original=json.loads((parent/'plan.json').read_text());review=json.loads((parent/'review.json').read_text())
    if not review['complete'] or len(review['cases'])!=6:raise ValueError('six completed objective checks required')
    files=dict(original['source_sha256'])
    for path in [Path(__file__),Path(discrepancy.__file__),parent/'plan.json',parent/'review.json',parent/'verification.json']:
        files[str(path.relative_to(refitter.ROOT))]=refitter.sha(path)
    for c in review['cases']:
        path=parent/(c['task_id']+'.npz')
        if refitter.sha(path)!=c['archive_sha256']:raise ValueError('parent archive differs')
        files[str(path.relative_to(refitter.ROOT))]=refitter.sha(path)
    def verify():
        if implementation_hash()!=original['scientific_implementation_hash'] or numerical_environment_hash()!=original['numerical_environment_hash']:raise ValueError('source/environment differs')
        if any(refitter.sha(refitter.ROOT/k)!=v for k,v in files.items()):raise ValueError('frozen dependency differs')
    verify();output.mkdir(exist_ok=True)
    plan=dict(version='registered-wind-discrepancy-objective-checks-1',policy=discrepancy.POLICY,
        objective_policy=original['policy'],temporal_policy=original['temporal_policy'],source_sha256=files,
        scientific_implementation_hash=implementation_hash(),numerical_environment_hash=numerical_environment_hash(),
        task_ids=original['task_ids'],scenarios_per_case=36,optimizer_calls=0,additional_flight_attempts=0,bootstrap=0)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);plan_path=output/'plan.json'
        if plan_path.exists():
            if json.loads(plan_path.read_text())!=plan:raise ValueError('resume identity differs')
        else:refitter.atomic(plan_path,plan)
        cases=[]
        for case in review['cases']:
            verify();checkpoint=output/(case['task_id']+'.json')
            if checkpoint.exists():
                result=json.loads(checkpoint.read_text())
                if refitter.sha(output/(case['task_id']+'.npz'))!=result['archive_sha256']:raise ValueError('archive differs')
            else:
                refitter.atomic(output/'status.json',dict(state='running',completed_cases=len(cases),task_id=case['task_id'],pid=os.getpid()))
                start=time.monotonic();data=dict(np.load(parent/(case['task_id']+'.npz'),allow_pickle=False));matrices=dict(np.load(temporal/(case['task_id']+'.npz'),allow_pickle=False))
                G,P,z,r=(data[k] for k in ('raw_jacobian','penalty','parameters','raw_residual'));n=len(matrices['residual'])
                model=discrepancy.discrepancy_covariance(len(r),n,case['crab_model']);scenarios=[];covariances=[];curvatures=[];error=0.
                gps=original['temporal_policy']['gps_correlation_seconds'];imu=original['temporal_policy']['imu_correlation_seconds']
                for i,gt in enumerate(gps):
                    for j,it in enumerate(imu):
                        measured=matrices['gps_covariances'][i]+matrices['imu_covariances'][j];C=measured+model;W=objective.FrozenWhitening(C)
                        scores=W.scores(r,P@z);response,residual,curve=objective.local_response(G,P,W)
                        sampling=response@C@response.T;remaining=residual@C@residual.T
                        # Independent direct least-squares response with the same explicit covariance.
                        white=W.apply(np.eye(len(r)));A=np.vstack([white@G,P]);columns=np.maximum(np.linalg.norm(A,axis=0),1e-30)
                        driver=np.vstack([-white,np.zeros((len(P),len(r)))])
                        direct=np.linalg.lstsq(A/columns,driver,rcond=1e-10)[0]/columns[:,None]
                        check=float(np.linalg.norm(direct-response)/max(np.linalg.norm(direct),1e-30));error=max(error,check)
                        normalized=C/W.sigma[:,None]/W.sigma[None,:];scaled=r/W.sigma
                        quadratic=float(scaled@np.linalg.solve(normalized,scaled))
                        if check>1e-7 or not np.isclose(quadratic,scores['data_quadratic'],rtol=1e-10):raise ValueError('independent objective/response differs')
                        if not np.array_equal(C[:n,n:],measured[:n,n:]):raise ValueError('shared GPS covariance was altered')
                        covariances.append(sampling[:3,:3]);curvatures.append(curve[:3,:3])
                        scenarios.append(dict(gps_correlation_seconds=gt,imu_correlation_seconds=it,**scores,
                            local_gls_sampling_k_sd=np.sqrt(np.maximum(np.diag(sampling)[:3],0.)).tolist(),
                            local_penalized_curvature_k_sd=np.sqrt(np.maximum(np.diag(curve)[:3],0.)).tolist(),
                            local_gls_residual_sigma_dph=float(np.sqrt(np.maximum(np.diag(remaining)[:n],0.).mean())*RAD2DPH)))
                path=output/(case['task_id']+'.npz');temporary=path.with_suffix('.tmp.npz')
                np.savez_compressed(temporary,t=data['t'],bin_mask=data['bin_mask'],model_discrepancy_covariance=model,
                    sampling_k_covariances=np.array(covariances),curvature_k_covariances=np.array(curvatures))
                temporary.replace(path)
                result=dict(task_id=case['task_id'],truth=case['truth'],crab_model=case['crab_model'],common_minutes=case['common_minutes'],
                    scenarios=scenarios,maximum_independent_response_relative_error=error,archive_sha256=refitter.sha(path),elapsed_s=time.monotonic()-start)
                refitter.atomic(checkpoint,result)
            cases.append(result);values=[s['data_quadratic'] for s in result['scenarios']]
            print(json.dumps(dict(crab=result['crab_model'],truth=result['truth'],quadratic_range=[min(values),max(values)])),flush=True)
        verify();result=dict(complete=True,cases=cases,plan_sha256=refitter.sha(plan_path),optimizer_calls=0,additional_flight_attempts=0,bootstrap=0,
            production_enabled=False,decisions_enabled=False)
        report=output/'review.json'
        if report.exists():
            if json.loads(report.read_text())!=result:raise ValueError('completed review differs')
        else:refitter.atomic(report,result)
        refitter.atomic(output/'status.json',dict(state='complete',completed_cases=6,active_workers=0,pid=os.getpid()))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','temporal'):parser.add_argument(name,type=Path)
    parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    run(a.parent.resolve(),a.temporal.resolve(),a.output.resolve())
