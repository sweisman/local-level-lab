# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read completed joint refits, verify checkpoints and report boundary diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import refit_joint_acceleration_motion as refitter
from lll import models


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def assess(directory,refits,output):
    plan_path=refits/'plan.json';plan=json.loads(plan_path.read_text())
    review_path=refits/'review.json';review=json.loads(review_path.read_text())
    if not review['complete']:raise ValueError('refits not complete')
    if any(sha(refitter.ROOT/k)!=v for k,v in plan['source_sha256'].items()):raise ValueError('frozen refit source/input mismatch')
    rows={r['task_id']:r for r in json.loads((directory/'campaign.json').read_text())['records']}
    history=[json.loads(line) for line in (refits/'attempts.jsonl').read_text().splitlines()]
    starts=[r for r in history if r['event']=='started'];completed=[r for r in history if r['event']=='complete']
    if len(starts)>30 or len(starts)!=review['optimizer_calls']:raise ValueError('optimizer scope/count differs')
    files={str(plan_path.relative_to(refitter.ROOT)):sha(plan_path),str(review_path.relative_to(refitter.ROOT)):sha(review_path)}
    cases=[]
    for result in review['cases']:
        problem,_=refitter.build(directory,rows[result['task_id']])
        lo,hi=problem.bounds();boundaries={}
        for name in result['fits']:
            folder=refits/result['task_id'];archive=folder/(name+'.npz');meta_path=folder/(name+'.json')
            meta=json.loads(meta_path.read_text())
            if sha(archive)!=meta['archive_sha256']:raise ValueError('checkpoint hash mismatch')
            files[str(archive.relative_to(refitter.ROOT))]=sha(archive)
            files[str(meta_path.relative_to(refitter.ROOT))]=sha(meta_path)
            saved=dict(np.load(archive,allow_pickle=False));z=saved['z']
            if not np.isfinite(z).all() or np.any(z<lo-1e-8) or np.any(z>hi+1e-8):raise ValueError('invalid fitted parameters')
            limited=np.isfinite(lo)&np.isfinite(hi)
            margin=float(np.min(np.minimum(z[limited]-lo[limited],hi[limited]-z[limited])/(hi[limited]-lo[limited])))
            boundary=dict(minimum_relative_margin=margin,near_boundary=margin<=.01,
                forward_sigma_offset=float(z[-1]/problem.forward_sigma),coherent_error_sigmas=z[problem.error_slice].tolist())
            if problem.wind_tas is not None:boundary['physical_wind_tas']=problem.wind_tas.boundary(z[problem.p:problem.p+problem.nc])
            boundaries[name]=boundary
        cases.append({**result,'boundaries':boundaries,'any_fit_near_boundary':any(v['near_boundary'] for v in boundaries.values())})
    report=dict(complete=True,cases=cases,all_converged=all(c['converged'] for c in cases),all_nested=all(c['nested'] for c in cases),
        any_fit_near_boundary=any(c['any_fit_near_boundary'] for c in cases),optimizer_starts=len(starts),completed_optimizer_calls=len(completed),
        summed_completed_optimizer_seconds=sum(c['elapsed_s'] for c in completed),additional_flight_attempts=0,bootstrap=0,
        checkpoints_sha256=files,helper_sha256=sha(Path(__file__)),production_enabled=False,decisions_enabled=False,
        limitations=['Uncalibrated diagnostic objectives; no model rejection or winner.',
            'Frozen old gyro weights and six coherent error modes remain provisional.',
            'Convergence and nesting do not establish coverage, an unconditional design gate or power.'])
    with output.open('x') as out:out.write(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('cases','checkpoints_sha256','limitations')}))
    print(json.dumps([dict(truth=c['truth'],crab=c['crab_model'],residual_dph=c['residual_rms_dph'],converged=c['converged'],
        nested=c['nested'],near_boundary=c['any_fit_near_boundary'],delta_objectives=c['diagnostic_delta_objectives']) for c in cases]))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('refits',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assess(args.directory.resolve(),args.refits.resolve(),args.output.resolve())
