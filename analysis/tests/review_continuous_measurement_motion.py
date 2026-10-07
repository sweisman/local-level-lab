# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checkpoint six readonly continuous-equation/shared-error evaluations; no refits."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import time

import numpy as np
import refit_joint_acceleration_motion as refitter
import review_acceleration_motion as observed
import continuous_measurement_motion as continuous
import matched_measurement_motion as matched
from lll.attitude import epoch_of
from lll.calib import RAD2DPH
from lll.format import read_session
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def evaluate(directory,refits,row,output):
    folder=directory/'diagnostics'/row['task_id'];problem,_=refitter.build(directory,row)
    inputs=observed.observed_inputs(folder)
    fit_path=refits/row['task_id']/'free.npz';fit_meta=refits/row['task_id']/'free.json'
    if refitter.sha(fit_path)!=json.loads(fit_meta.read_text())['archive_sha256']:raise ValueError('checkpoint differs')
    z=np.load(fit_path,allow_pickle=False)['z'];session=read_session(folder/'session.zip');flight=session.phase('flight')
    gs=session.slice(session.gyro_stream(),flight['start_ns'],flight['end_ns'])
    acc=session.slice('accel',flight['start_ns'],flight['end_ns'])
    st=gs['t_ns']/1e9;gyro_raw=np.column_stack([gs[k] for k in ('x','y','z')]);force_raw=np.column_stack([acc[k] for k in ('x','y','z')])
    analysis=json.loads((folder/'analysis.json').read_text())
    epochs=[dict(t0_s=-np.inf if e['t0_s'] is None else e['t0_s'],t1_s=np.inf if e['t1_s'] is None else e['t1_s']) for e in analysis['mount_epochs']]
    epoch=epoch_of(st,epochs);matrices=inputs['bins']['mount_matrices']
    gyro,_,valid=matched.gyro_seconds(inputs['t'],st,gyro_raw,epoch,matrices,problem.bias_fn)
    force_t=acc['t_ns']/1e9
    imu_cov,paired=continuous.paired_imu_covariance(inputs['t'],st,force_raw,gyro_raw,epoch,matrices,problem.bias_fn,
        force_t=force_t,force_epoch=epoch_of(force_t,epochs))
    eq=continuous.ContinuousEquation(problem,inputs,gyro,valid & paired)
    S=continuous.input_covariance(inputs,imu_cov)
    B=eq.input_jacobians(z);before=continuous.propagate(B,S)
    # Independent complete-equation difference, not a second call to the chain rule.
    direction=np.sqrt(np.maximum(np.diagonal(S,axis1=1,axis2=2),0.))*.03*np.sin(np.arange(len(eq.t))[:,None]*.27+np.arange(11))
    step=.25
    actual=np.r_[(eq.residual(z,eq.x+step*direction)-eq.residual(z,eq.x-step*direction))/(2*step),
                 (eq.auxiliary(z,eq.x+step*direction)-eq.auxiliary(z,eq.x-step*direction))/(2*step)]
    calculated=sum(b@direction[:,j] for j,b in enumerate(B))
    check=float(np.linalg.norm(actual-calculated)/max(np.linalg.norm(actual),1e-30))
    if check>1e-3:raise ValueError('complete shared-input derivative check failed: '+str(check))
    J=eq.parameter_jacobian(z);_,auxJ=eq.auxiliary(z,jac=True)
    weights=problem.w.reshape(-1,3)[eq.keep].ravel();P=problem.penalty()
    parameter,response=continuous.fit_response(J,weights,P,auxJ)
    after=response@before@response.T;parameter_cov=parameter@before@parameter.T
    residual=eq.residual(z);ng=len(residual);gyro_cov=before[:ng,:ng]
    groups={}
    for name,channels in [('gps',range(5)),('force',range(5,8)),('gyro',range(8,11))]:
        subset=np.zeros_like(S)
        for a in channels:
            for b in channels:subset[:,a,b]=S[:,a,b]
        groups[name]=continuous.propagate(B,subset)
    no_cross=sum(groups.values());cross=before-no_cross
    record=dict(task_id=row['task_id'],truth=row['truth'],crab_model=row['fit_options']['crab_model'],
        common_minutes=len(eq.bins['t']),residual_rms_dph=float(np.sqrt(np.mean(residual**2))*RAD2DPH),
        propagated_fixed_parameter_sigma_dph=float(np.sqrt(np.mean(np.diag(gyro_cov)))*RAD2DPH),
        propagated_local_fit_residual_sigma_dph=float(np.sqrt(np.mean(np.maximum(np.diag(after),0.)))*RAD2DPH),
        propagated_local_k_sampling_sd=np.sqrt(np.maximum(np.diag(parameter_cov)[:3],0.)).tolist(),
        independent_input_direction_relative_error=check,
        variance_contributions_dph2={k:float(np.mean(np.diag(v)[:ng])*RAD2DPH**2) for k,v in {**groups,'force_gyro_cross':cross}.items()},
        residual_correlation=matched.residual_correlation(residual.reshape(-1,3),eq.bins['t'],eq.matrices),
        limits=['Conditional on fixed mount/forward references, old weights, and independent input seconds.',
            'GPS accuracy fields are provisional sigma scales; horizontal marginals and missing GPS channel correlations are assumed.',
            'Empirical paired IMU covariance includes motion, not just device noise.',
            'Local fit response is evaluated at saved parameters without a new fit; penalties are deterministic and prior/calibration uncertainty is omitted.',
            'Filtering nonlinear attitude can have systematic error; no coverage, model significance, power or decisions.'])
    path=output/(row['task_id']+'.npz');temporary=path.with_suffix('.tmp.npz')
    np.savez_compressed(temporary,t=eq.bins['t'],bin_mask=eq.keep,residual=residual,
        covariance_augmented=before,covariance_after_fit=after,parameter_covariance=parameter_cov,
        parameter_response=parameter,residual_response=response,parameter_jacobian=J,weights=weights,
        auxiliary_jacobian=auxJ,penalty=P,gps_covariance=groups['gps'],force_covariance=groups['force'],
        gyro_covariance=groups['gyro'],force_gyro_cross_covariance=cross)
    temporary.replace(path);record['archive_sha256']=refitter.sha(path)
    return record


def run(directory,refits,output):
    if any(os.environ.get(k)!='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')):raise ValueError('one numerical thread required')
    old_plan=json.loads((refits/'plan.json').read_text());campaign=json.loads((directory/'campaign.json').read_text())
    if not json.loads((refits/'review.json').read_text())['complete'] or len(campaign['records'])!=6:raise ValueError('six complete saved cases required')
    files=dict(old_plan['source_sha256'])
    for p in [Path(__file__),Path(continuous.__file__),Path(matched.__file__),refits/'review.json',refits/'plan.json']:
        files[str(p.relative_to(refitter.ROOT))]=refitter.sha(p)
    for row in campaign['records']:
        for name in ('free.npz','free.json'):
            p=refits/row['task_id']/name;files[str(p.relative_to(refitter.ROOT))]=refitter.sha(p)
    def verify():
        if implementation_hash()!=old_plan['scientific_implementation_hash'] or numerical_environment_hash()!=old_plan['numerical_environment_hash']:raise ValueError('source/environment changed')
        if any(refitter.sha(refitter.ROOT/k)!=v for k,v in files.items()):raise ValueError('frozen input/helper changed')
    verify();output.mkdir(exist_ok=True)
    plan=dict(version='six-saved-continuous-propagation-checks-1',policy=continuous.POLICY,
        task_ids=[r['task_id'] for r in campaign['records']],source_sha256=files,
        scientific_implementation_hash=implementation_hash(),numerical_environment_hash=numerical_environment_hash(),
        optimizer_calls=0,additional_flight_attempts=0,bootstrap=0)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        plan_path=output/'plan.json'
        if plan_path.exists():
            if json.loads(plan_path.read_text())!=plan:raise ValueError('resume identity differs')
        else:refitter.atomic(plan_path,plan)
        records=[]
        for row in campaign['records']:
            verify();result=output/(row['task_id']+'.json')
            if result.exists():
                record=json.loads(result.read_text())
                if refitter.sha(output/(row['task_id']+'.npz'))!=record['archive_sha256']:raise ValueError('completed archive differs')
            else:
                refitter.atomic(output/'status.json',dict(state='running',task_id=row['task_id'],completed_cases=len(records),pid=os.getpid()))
                started=time.monotonic();record=evaluate(directory,refits,row,output);record['elapsed_s']=time.monotonic()-started
                refitter.atomic(result,record)
            records.append(record)
            print(json.dumps({k:record[k] for k in ('truth','crab_model','common_minutes','residual_rms_dph','propagated_fixed_parameter_sigma_dph','propagated_local_fit_residual_sigma_dph','independent_input_direction_relative_error')}),flush=True)
        verify()
        review=dict(complete=True,cases=records,plan_sha256=refitter.sha(plan_path),optimizer_calls=0,
            additional_flight_attempts=0,bootstrap=0,production_enabled=False,decisions_enabled=False)
        report=output/'review.json'
        if report.exists():
            if json.loads(report.read_text())!=review:raise ValueError('completed review differs')
        else:refitter.atomic(report,review)
        refitter.atomic(output/'status.json',dict(state='complete',completed_cases=len(records),pid=os.getpid(),active_workers=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('refits',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.directory.resolve(),args.refits.resolve(),args.output.resolve())
