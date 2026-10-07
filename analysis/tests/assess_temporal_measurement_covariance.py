# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify all frozen temporal scenarios, covariance PSD and response arithmetic."""
import argparse
import json
from pathlib import Path

import numpy as np
import refit_joint_acceleration_motion as refitter
from lll.calib import RAD2DPH
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def assess(directory):
    plan=json.loads((directory/'plan.json').read_text());review=json.loads((directory/'review.json').read_text())
    if not review['complete'] or len(review['cases'])!=6:raise ValueError('six complete cases required')
    if refitter.sha(directory/'plan.json')!=review['plan_sha256']:raise ValueError('plan differs')
    if implementation_hash()!=plan['scientific_implementation_hash'] or numerical_environment_hash()!=plan['numerical_environment_hash']:raise ValueError('source/environment differs')
    if any(refitter.sha(refitter.ROOT/k)!=v for k,v in plan['source_sha256'].items()):raise ValueError('dependency differs')
    gps_times=plan['policy']['gps_correlation_seconds'];imu_times=plan['policy']['imu_correlation_seconds']
    expected={(g,i) for g in gps_times for i in imu_times};cases=[]
    for case in review['cases']:
        path=directory/(case['task_id']+'.npz')
        if refitter.sha(path)!=case['archive_sha256']:raise ValueError('archive differs')
        data=dict(np.load(path,allow_pickle=False));n=len(data['residual'])
        if data['bin_mask'].sum()!=case['common_minutes'] or n!=3*case['common_minutes']:raise ValueError('support differs')
        keys=[(s['gps_correlation_seconds'],s['imu_correlation_seconds']) for s in case['scenarios']]
        if len(keys)!=36 or set(keys)!=expected:raise ValueError('incomplete/duplicate scenario grid')
        minimum=1.
        for covariance in [*data['gps_covariances'],*data['imu_covariances']]:
            if not np.isfinite(covariance).all() or not np.allclose(covariance,covariance.T,atol=1e-13,rtol=1e-10):raise ValueError('invalid covariance')
            sigma=np.sqrt(np.maximum(np.diag(covariance),1e-300));correlation=covariance/sigma[:,None]/sigma[None,:]
            eigenvalue=float(np.linalg.eigvalsh((correlation+correlation.T)/2).min())
            if eigenvalue < -1e-8:raise ValueError('non-PSD component')
            minimum=min(minimum,eigenvalue)
        for scenario in case['scenarios']:
            i=gps_times.index(scenario['gps_correlation_seconds']);j=imu_times.index(scenario['imu_correlation_seconds'])
            covariance=data['gps_covariances'][i]+data['imu_covariances'][j]
            after=data['residual_response']@covariance@data['residual_response'].T
            parameters=data['parameter_response']@covariance@data['parameter_response'].T
            actual=[np.sqrt(np.mean(np.maximum(np.diag(covariance)[:n],0.)))*RAD2DPH,
                np.sqrt(np.mean(np.maximum(np.diag(after),0.)))*RAD2DPH,*np.sqrt(np.maximum(np.diag(parameters)[:3],0.))]
            expected_metrics=[scenario['fixed_parameter_sigma_dph'],scenario['local_fit_residual_sigma_dph'],*scenario['local_k_sampling_sd']]
            if not np.allclose(actual,expected_metrics,rtol=1e-11,atol=1e-11):raise ValueError('response summary differs')
        cases.append(dict(task_id=case['task_id'],scenarios_verified=36,minimum_normalized_component_eigenvalue=minimum))
    result=dict(complete=True,cases=cases,scenarios_verified=216,review_sha256=refitter.sha(directory/'review.json'),
        helper_sha256=refitter.sha(Path(__file__)),optimizer_calls=0,additional_flight_attempts=0,production_enabled=False,decisions_enabled=False)
    with (directory/'verification.json').open('x') as out:out.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(complete=True,cases=6,scenarios_verified=216)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    assess(parser.parse_args().directory.resolve())
