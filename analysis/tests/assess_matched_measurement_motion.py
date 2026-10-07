# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independently check saved bandwidth arrays, hashes and covariance diagnostics."""
import argparse
import json
from pathlib import Path

import numpy as np
from lll.calib import RAD2DPH
from lll.runtime import numerical_environment_hash
import refit_joint_acceleration_motion as refitter


def assess(directory):
    path=directory/'review.json';report=json.loads(path.read_text())
    if not report['complete'] or len(report['cases'])!=6:raise ValueError('six complete checks required')
    if numerical_environment_hash()!=report['numerical_environment_hash']:raise ValueError('environment differs')
    for key,value in {**report['input_sha256'],**report['helper_sha256']}.items():
        if refitter.sha(refitter.ROOT/key)!=value:raise ValueError('source/input hash differs: '+key)
    cases=[]
    for case in report['cases']:
        archive=directory/(case['task_id']+'.npz')
        if refitter.sha(archive)!=case['archive_sha256']:raise ValueError('archive hash differs')
        arrays=dict(np.load(archive,allow_pickle=False));n=len(arrays['t'])
        if n!=case['common_minutes'] or arrays['bin_mask'].sum()!=n:raise ValueError('support differs')
        for key,metric in [('legacy_residual','legacy_residual_dph'),('regridded_residual','regridded_residual_dph'),('matched_residual','matched_residual_dph')]:
            if not np.isfinite(arrays[key]).all():raise ValueError('nonfinite residual')
            actual=float(np.sqrt(np.mean(arrays[key]**2))*RAD2DPH)
            if not np.isclose(actual,case[metric],rtol=1e-12,atol=1e-12):raise ValueError('residual summary differs')
        if not np.allclose(arrays['matched_gyro']-arrays['matched_prediction'],arrays['matched_residual'],rtol=0.,atol=1e-15):raise ValueError('paired prediction closure differs')
        cov=arrays['covariance_dph2']
        if cov.shape!=(3*n,3*n) or not np.isfinite(cov).all() or not np.allclose(cov,cov.T,rtol=0.,atol=1e-10):raise ValueError('invalid covariance')
        eig=float(np.linalg.eigvalsh(cov).min())
        if eig < -1e-10:raise ValueError('covariance not positive semidefinite')
        scale=np.sqrt(np.diag(cov));correlation=cov/scale[:,None]/scale[None,:]
        indices=np.flatnonzero(abs(np.diff(arrays['t'])-60)<1e-5)
        pairs=np.array([correlation[3*i+a,3*(i+1)+a] for i in indices for a in range(3)])
        cases.append(dict(task_id=case['task_id'],minimum_eigenvalue=eig,adjacent_minute_pairs=len(indices),
            induced_adjacent_minute_axis_correlation_range=[float(pairs.min()),float(pairs.max())],
            residual_to_independent_gyro_scale_ratio=case['matched_residual_dph']/case['induced_covariance']['rms_marginal_sigma']))
    result=dict(complete=True,cases=cases,review_sha256=refitter.sha(path),helper_sha256=refitter.sha(Path(__file__)),
        optimizer_calls=0,additional_flight_attempts=0,production_enabled=False,decisions_enabled=False)
    with (directory/'verification.json').open('x') as out:out.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    assess(parser.parse_args().directory.resolve())
