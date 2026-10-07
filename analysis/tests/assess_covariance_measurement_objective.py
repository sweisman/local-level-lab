# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independently verify all frozen GLS objectives and local sampling responses."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular
import refit_joint_acceleration_motion as refitter
from lll.calib import RAD2DPH
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def assess(directory,temporal):
    plan=json.loads((directory/'plan.json').read_text());review=json.loads((directory/'review.json').read_text())
    if not review['complete'] or len(review['cases'])!=6:raise ValueError('six completed checks required')
    if refitter.sha(directory/'plan.json')!=review['plan_sha256']:raise ValueError('plan differs')
    if implementation_hash()!=plan['scientific_implementation_hash'] or numerical_environment_hash()!=plan['numerical_environment_hash']:raise ValueError('source/environment differs')
    if any(refitter.sha(refitter.ROOT/k)!=v for k,v in plan['source_sha256'].items()):raise ValueError('dependency differs')
    gps=plan['temporal_policy']['gps_correlation_seconds'];imu=plan['temporal_policy']['imu_correlation_seconds']
    records=[]
    for case in review['cases']:
        path=directory/(case['task_id']+'.npz')
        if refitter.sha(path)!=case['archive_sha256']:raise ValueError('archive differs')
        data=dict(np.load(path,allow_pickle=False));parent=dict(np.load(temporal/(case['task_id']+'.npz'),allow_pickle=False))
        if not np.array_equal(data['t'],parent['t']) or not np.array_equal(data['bin_mask'],parent['bin_mask']):raise ValueError('support differs')
        keys=[(s['gps_correlation_seconds'],s['imu_correlation_seconds']) for s in case['scenarios']]
        if len(keys)!=36 or set(keys)!={(g,i) for g in gps for i in imu}:raise ValueError('incomplete/duplicate grid')
        max_response=0.;r=data['raw_residual'];G=data['raw_jacobian'];P=data['penalty'];z=data['parameters'];n=len(parent['residual'])
        for k,scenario in enumerate(case['scenarios']):
            i=gps.index(scenario['gps_correlation_seconds']);j=imu.index(scenario['imu_correlation_seconds'])
            C=parent['gps_covariances'][i]+parent['imu_covariances'][j];scale=np.sqrt(np.diag(C));correlation=C/scale[:,None]/scale[None,:]
            quadratic=float((r/scale)@np.linalg.solve(correlation,r/scale));sign,logdet=np.linalg.slogdet(correlation)
            if sign!=1:raise ValueError('nonpositive covariance determinant')
            logdet=float(logdet+2*np.log(scale).sum());penalty=float(np.sum((P@z)**2))
            expected=[quadratic,penalty,quadratic+penalty,logdet,quadratic+logdet,.5*(quadratic+logdet+len(r)*np.log(2*np.pi)),quadratic+logdet+penalty]
            names=['data_quadratic','penalty_quadratic','penalized_least_squares','covariance_logdet','gaussian_deviance','gaussian_nll','penalized_gaussian_deviance']
            if not np.allclose([scenario[x] for x in names],expected,rtol=1e-10,atol=1e-8):raise ValueError('objective arithmetic differs')
            # Direct least-squares estimator response, distinct from pinv-based producer.
            W=solve_triangular(np.linalg.cholesky(correlation),np.diag(1/scale),lower=True)
            A=np.vstack([W@G,P]);columns=np.maximum(np.linalg.norm(A,axis=0),1e-30)
            driver=np.vstack([-W,np.zeros((len(P),len(r)))])
            response=np.linalg.lstsq(A/columns,driver,rcond=1e-10)[0]/columns[:,None]
            sampling=response@C@response.T;remaining=np.eye(len(r))+G@response
            residual_cov=remaining@C@remaining.T
            discrepancy=float(np.linalg.norm(sampling[:3,:3]-data['sampling_k_covariances'][k])/max(np.linalg.norm(sampling[:3,:3]),1e-30))
            max_response=max(max_response,discrepancy)
            if discrepancy>1e-7:raise ValueError('local sampling response differs')
            if not np.allclose(np.sqrt(np.maximum(np.diag(sampling)[:3],0.)),scenario['local_gls_sampling_k_sd'],rtol=1e-7,atol=1e-10):raise ValueError('sampling summary differs')
            sigma=float(np.sqrt(np.maximum(np.diag(residual_cov)[:n],0.).mean())*RAD2DPH)
            if not np.isclose(sigma,scenario['local_gls_residual_sigma_dph'],rtol=1e-7):raise ValueError('residual response differs')
            for cov in (data['sampling_k_covariances'][k],data['curvature_k_covariances'][k]):
                if not np.isfinite(cov).all() or np.linalg.eigvalsh((cov+cov.T)/2).min() < -1e-10:raise ValueError('invalid science covariance')
        records.append(dict(task_id=case['task_id'],scenarios_verified=36,maximum_independent_sampling_response_relative_error=max_response))
    result=dict(complete=True,cases=records,scenarios_verified=216,review_sha256=refitter.sha(directory/'review.json'),
        helper_sha256=refitter.sha(Path(__file__)),optimizer_calls=0,additional_flight_attempts=0,production_enabled=False,decisions_enabled=False)
    with (directory/'verification.json').open('x') as out:out.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(complete=True,scenarios_verified=216,maximum_sampling_response_check=max(x['maximum_independent_sampling_response_relative_error'] for x in records))))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path);parser.add_argument('temporal',type=Path)
    a=parser.parse_args();assess(a.directory.resolve(),a.temporal.resolve())
