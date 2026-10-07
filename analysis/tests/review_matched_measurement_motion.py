# SPDX-License-Identifier: AGPL-3.0-or-later
"""Readonly bandwidth and induced-covariance check of six completed saved fits."""
import argparse
import json
from pathlib import Path

import numpy as np
import matched_measurement_motion as matched
import refit_joint_acceleration_motion as refitter
from lll.attitude import epoch_of
from lll.calib import RAD2DPH
from lll.format import read_session
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def review(directory,refits,output):
    plan=json.loads((refits/'plan.json').read_text())
    if implementation_hash()!=plan['scientific_implementation_hash']:raise ValueError('scientific source changed')
    if numerical_environment_hash()!=plan['numerical_environment_hash']:raise ValueError('numerical environment differs')
    if any(refitter.sha(refitter.ROOT/k)!=v for k,v in plan['source_sha256'].items()):raise ValueError('frozen sources/inputs differ')
    frozen=json.loads((refits/'review.json').read_text())
    if not frozen['complete']:raise ValueError('completed fits required')
    rows={r['task_id']:r for r in json.loads((directory/'campaign.json').read_text())['records']}
    output.mkdir(exist_ok=True)
    if (output/'review.json').exists(): raise ValueError('completed diagnostic is immutable')
    sources={str((refits/'plan.json').relative_to(refitter.ROOT)):refitter.sha(refits/'plan.json')}
    cases=[]
    for saved in frozen['cases']:
        task=saved['task_id'];folder=directory/'diagnostics'/task
        archive=refits/task/'free.npz';meta=refits/task/'free.json'
        if refitter.sha(archive)!=json.loads(meta.read_text())['archive_sha256']:raise ValueError('fit checkpoint changed')
        for path in (archive,meta,folder/'session.zip',folder/'analysis.json',folder/'fit-input.npz'):
            sources[str(path.relative_to(refitter.ROOT))]=refitter.sha(path)
        problem,_=refitter.build(directory,rows[task]);context=problem.context
        z=np.load(archive,allow_pickle=False)['z']
        session=read_session(folder/'session.zip');flight=session.phase('flight')
        stream=session.slice(session.gyro_stream(),flight['start_ns'],flight['end_ns'])
        st=stream['t_ns']/1e9
        analysis=json.loads((folder/'analysis.json').read_text())
        epochs=[dict(t0_s=-np.inf if e['t0_s'] is None else e['t0_s'],t1_s=np.inf if e['t1_s'] is None else e['t1_s']) for e in analysis['mount_epochs']]
        gyro,cov,valid=matched.gyro_seconds(context.t,st,np.column_stack([stream[k] for k in ('x','y','z')]),
            epoch_of(st,epochs),context.bins['mount_matrices'],problem.bias_fn)
        prediction,support,closure=matched.high_prediction(problem,z)
        result=matched.paired_bandwidth(context.t,gyro,prediction,valid & support,context.bins,context.matrices)
        keep=result['keep'];old_prediction=problem.prediction(z).reshape(-1,3)[keep]
        old_y=problem.y.reshape(-1,3)[keep]
        raw_residual=result['unfiltered_gyro']-result['unfiltered_prediction']
        filtered_residual=result['matched_gyro']-result['matched_prediction']
        covariance=matched.rotate_covariance(result['operator'],cov,result['matrices'])*RAD2DPH**2
        rms=lambda x:float(np.sqrt(np.mean(x*x))*RAD2DPH)
        case=dict(task_id=task,truth=saved['truth'],crab_model=saved['crab_model'],
            original_joint_minutes=len(keep),common_minutes=int(keep.sum()),
            legacy_residual_dph=rms(old_y-old_prediction),regridded_residual_dph=rms(raw_residual),
            matched_residual_dph=rms(filtered_residual),slow_prediction_lift_change_dph=rms(result['unfiltered_prediction']-old_prediction),
            gyro_regridding_change_dph=rms(result['unfiltered_gyro']-old_y),motion_reconstruction_max_error_dph=closure*RAD2DPH,
            induced_covariance=matched.covariance_summary(covariance),
            residual_correlation=matched.residual_correlation(filtered_residual,context.bins['t'][keep],result['matrices']))
        path=output/(task+'.npz')
        with path.open('xb') as out:
            np.savez_compressed(out,t=context.bins['t'][keep],bin_mask=keep,legacy_residual=old_y-old_prediction,
                regridded_residual=raw_residual,matched_residual=filtered_residual,
                covariance_dph2=covariance,matched_gyro=result['matched_gyro'],matched_prediction=result['matched_prediction'])
        case['archive_sha256']=refitter.sha(path);cases.append(case)
        print(json.dumps(case),flush=True)
    helpers=[Path(__file__),Path(matched.__file__)]
    report=dict(complete=True,cases=cases,policy=matched.POLICY,input_sha256=sources,
        helper_sha256={str(p.relative_to(refitter.ROOT)):refitter.sha(p) for p in helpers},
        numerical_environment_hash=plan['numerical_environment_hash'],scientific_implementation_hash=implementation_hash(),
        optimizer_calls=0,additional_flight_attempts=0,bootstrap=0,production_enabled=False,decisions_enabled=False,
        limitations=['Additional output filtering is applied to both sides; smoothing gyro alone against an unchanged prediction would be inconsistent.',
            'Slow science/bias terms are interpolated within epochs; this is not a refit-ready continuous observation equation.',
            'Within-second gyro variation includes motion. Propagated covariance assumes independent seconds and omits GPS/force/mount/calibration error and shared-error correlations.',
            'Residual correlations are descriptive and conditional on saved fitted parameters; no calibrated significance or power claim.'])
    with (output/'review.json').open('x') as f:f.write(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('refits',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();review(args.directory.resolve(),args.refits.resolve(),args.output.resolve())
