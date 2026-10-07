# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check frozen continuous-equation covariance and local least-squares response."""
import argparse
import json
from pathlib import Path

import numpy as np
import refit_joint_acceleration_motion as refitter
from lll.calib import RAD2DPH
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def assess(directory):
    plan_path=directory/'plan.json';plan=json.loads(plan_path.read_text())
    review=json.loads((directory/'review.json').read_text())
    if not review['complete'] or len(review['cases'])!=6:raise ValueError('six complete cases required')
    if refitter.sha(plan_path)!=review['plan_sha256']:raise ValueError('plan differs')
    if numerical_environment_hash()!=plan['numerical_environment_hash'] or implementation_hash()!=plan['scientific_implementation_hash']:raise ValueError('environment/source differs')
    if any(refitter.sha(refitter.ROOT/k)!=v for k,v in plan['source_sha256'].items()):raise ValueError('frozen dependency differs')
    records=[]
    for case in review['cases']:
        archive=directory/(case['task_id']+'.npz')
        if refitter.sha(archive)!=case['archive_sha256']:raise ValueError('array archive differs')
        data=dict(np.load(archive,allow_pickle=False));n=3*len(data['t'])
        if len(data['t'])!=case['common_minutes'] or data['bin_mask'].sum()*3!=n:raise ValueError('support differs')
        rms=float(np.sqrt(np.mean(data['residual']**2))*RAD2DPH)
        if not np.isclose(rms,case['residual_rms_dph'],rtol=1e-12):raise ValueError('RMS differs')
        augmented=data['covariance_augmented'];components=sum(data[k] for k in ('gps_covariance','force_covariance','gyro_covariance','force_gyro_cross_covariance'))
        if not np.allclose(components,augmented,atol=1e-15,rtol=1e-11):raise ValueError('shared covariance components do not close')
        minima={}
        for key in ('covariance_augmented','covariance_after_fit','parameter_covariance','gps_covariance','force_covariance','gyro_covariance'):
            covariance=data[key]
            if not np.isfinite(covariance).all() or not np.allclose(covariance,covariance.T,atol=1e-12,rtol=1e-10):raise ValueError('invalid covariance '+key)
            scale=np.sqrt(np.maximum(np.diag(covariance),1e-300))
            normalized=covariance/scale[:,None]/scale[None,:]
            minimum=float(np.linalg.eigvalsh((normalized+normalized.T)/2).min())
            if minimum < -1e-8:raise ValueError('non-PSD normalized covariance '+key)
            minima[key]=minimum
        for key,response in [('covariance_after_fit',data['residual_response']),('parameter_covariance',data['parameter_response'])]:
            if not np.allclose(data[key],response@augmented@response.T,atol=1e-13,rtol=1e-9):raise ValueError('propagation differs '+key)
        # Independent direct least-squares response, including the shared GPS auxiliary.
        J,w,P,aux=(data[k] for k in ('parameter_jacobian','weights','penalty','auxiliary_jacobian'))
        A=np.vstack([J*np.sqrt(w)[:,None],aux,P]);scales=np.maximum(np.linalg.norm(A,axis=0),1e-30)
        driver=np.zeros((len(A),n+len(aux)));driver[:n,:n]=np.diag(np.sqrt(w))
        driver[n:n+len(aux),n:]=-np.eye(len(aux))
        independent=np.linalg.lstsq(A/scales,driver,rcond=1e-10)[0]/scales[:,None]
        discrepancy=float(np.linalg.norm(independent-data['parameter_response'])/max(np.linalg.norm(independent),1e-30))
        if discrepancy>1e-6:raise ValueError('least-squares response differs')
        records.append(dict(task_id=case['task_id'],normalized_covariance_minimum_eigenvalues=minima,
            independent_least_squares_response_relative_error=discrepancy))
    result=dict(complete=True,cases=records,review_sha256=refitter.sha(directory/'review.json'),
        helper_sha256=refitter.sha(Path(__file__)),optimizer_calls=0,additional_flight_attempts=0,
        production_enabled=False,decisions_enabled=False)
    with (directory/'verification.json').open('x') as out:out.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(complete=True,cases=6,maximum_response_check_error=max(r['independent_least_squares_response_relative_error'] for r in records))))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    assess(parser.parse_args().directory.resolve())
