# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify every explicit wind-discrepancy objective without modifying parent artifacts."""
import argparse
import json
from pathlib import Path

import numpy as np
import refit_joint_acceleration_motion as refitter
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def assess(directory,parent,temporal):
    plan=json.loads((directory/'plan.json').read_text());review=json.loads((directory/'review.json').read_text())
    original={c['task_id']:c for c in json.loads((parent/'review.json').read_text())['cases']}
    if not review['complete'] or len(review['cases'])!=6:raise ValueError('six completed cases required')
    if refitter.sha(directory/'plan.json')!=review['plan_sha256']:raise ValueError('plan differs')
    if implementation_hash()!=plan['scientific_implementation_hash'] or numerical_environment_hash()!=plan['numerical_environment_hash']:raise ValueError('source/environment differs')
    if any(refitter.sha(refitter.ROOT/k)!=v for k,v in plan['source_sha256'].items()):raise ValueError('dependency differs')
    gps=plan['temporal_policy']['gps_correlation_seconds'];imu=plan['temporal_policy']['imu_correlation_seconds'];records=[]
    for case in review['cases']:
        path=directory/(case['task_id']+'.npz')
        if refitter.sha(path)!=case['archive_sha256']:raise ValueError('archive differs')
        data=dict(np.load(path,allow_pickle=False));source=dict(np.load(parent/(case['task_id']+'.npz'),allow_pickle=False))
        matrices=dict(np.load(temporal/(case['task_id']+'.npz'),allow_pickle=False));n=len(matrices['residual']);r=source['raw_residual']
        model=np.zeros((len(r),len(r)));model[n:,n:]=np.eye(len(r)-n)
        if not np.array_equal(data['model_discrepancy_covariance'],model):raise ValueError('model discrepancy differs')
        if not np.array_equal(data['t'],source['t']) or not np.array_equal(data['bin_mask'],source['bin_mask']):raise ValueError('support differs')
        keys=[(s['gps_correlation_seconds'],s['imu_correlation_seconds']) for s in case['scenarios']]
        if len(keys)!=36 or set(keys)!={(g,i) for g in gps for i in imu}:raise ValueError('incomplete/duplicate grid')
        penalty=float(np.sum((source['penalty']@source['parameters'])**2))
        for k,scenario in enumerate(case['scenarios']):
            i=gps.index(scenario['gps_correlation_seconds']);j=imu.index(scenario['imu_correlation_seconds'])
            measured=matrices['gps_covariances'][i]+matrices['imu_covariances'][j];C=measured+model
            sigma=np.sqrt(np.diag(C));correlation=C/sigma[:,None]/sigma[None,:]
            quadratic=float((r/sigma)@np.linalg.solve(correlation,r/sigma));sign,logdet=np.linalg.slogdet(correlation)
            if sign!=1:raise ValueError('nonpositive covariance determinant')
            logdet=float(logdet+2*np.log(sigma).sum())
            expected=[quadratic,penalty,quadratic+penalty,logdet,quadratic+logdet,.5*(quadratic+logdet+len(r)*np.log(2*np.pi)),quadratic+logdet+penalty]
            fields=['data_quadratic','penalty_quadratic','penalized_least_squares','covariance_logdet','gaussian_deviance','gaussian_nll','penalized_gaussian_deviance']
            if not np.allclose([scenario[f] for f in fields],expected,rtol=1e-10,atol=1e-8):raise ValueError('objective arithmetic differs')
            if case['crab_model']=='wind' and not np.allclose([scenario[f] for f in fields],[original[case['task_id']]['scenarios'][k][f] for f in fields],rtol=1e-12):raise ValueError('broad wind objective changed')
            for key,field in [('sampling_k_covariances','local_gls_sampling_k_sd'),('curvature_k_covariances','local_penalized_curvature_k_sd')]:
                covariance=data[key][k]
                if not np.isfinite(covariance).all() or np.linalg.eigvalsh((covariance+covariance.T)/2).min() < -1e-10:raise ValueError('invalid science covariance')
                if not np.allclose(np.sqrt(np.maximum(np.diag(covariance),0.)),scenario[field],rtol=1e-12,atol=1e-12):raise ValueError('science covariance summary differs')
        if case['maximum_independent_response_relative_error']>1e-7:raise ValueError('producer direct least-squares check failed')
        records.append(dict(task_id=case['task_id'],scenarios_verified=36,shared_covariance_and_model_discrepancy_verified=True))
    result=dict(complete=True,cases=records,scenarios_verified=216,review_sha256=refitter.sha(directory/'review.json'),helper_sha256=refitter.sha(Path(__file__)),
        optimizer_calls=0,additional_flight_attempts=0,production_enabled=False,decisions_enabled=False)
    with (directory/'verification.json').open('x') as out:out.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(complete=True,scenarios_verified=216)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('directory','parent','temporal'):parser.add_argument(name,type=Path)
    a=parser.parse_args();assess(a.directory.resolve(),a.parent.resolve(),a.temporal.resolve())
