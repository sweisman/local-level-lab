# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checkpoint six saved-state temporal sensitivity grids; no optimizer or synthesis."""
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
import temporal_measurement_covariance as temporal
from lll.attitude import epoch_of
from lll.format import read_session
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def prepare(directory,refits,row):
    folder=directory/'diagnostics'/row['task_id'];p,_=refitter.build(directory,row)
    inputs=observed.observed_inputs(folder);session=read_session(folder/'session.zip');f=session.phase('flight')
    gyro=session.slice(session.gyro_stream(),f['start_ns'],f['end_ns']);acc=session.slice('accel',f['start_ns'],f['end_ns'])
    analysis=json.loads((folder/'analysis.json').read_text())
    epochs=[dict(t0_s=-np.inf if e['t0_s'] is None else e['t0_s'],t1_s=np.inf if e['t1_s'] is None else e['t1_s']) for e in analysis['mount_epochs']]
    st,at=gyro['t_ns']/1e9,acc['t_ns']/1e9;ge,ae=epoch_of(st,epochs),epoch_of(at,epochs)
    g=np.column_stack([gyro[k] for k in ('x','y','z')]);a=np.column_stack([acc[k] for k in ('x','y','z')])
    matrices=inputs['bins']['mount_matrices']
    means,_,valid=matched.gyro_seconds(inputs['t'],st,g,ge,matrices,p.bias_fn)
    imu_cov,paired=continuous.paired_imu_covariance(inputs['t'],st,a,g,ge,matrices,p.bias_fn,force_t=at,force_epoch=ae)
    eq=continuous.ContinuousEquation(p,inputs,means,valid & paired)
    S=continuous.input_covariance(inputs,imu_cov)
    # Sensor-axis persistence may span a turn; the known mount transform rotates
    # that persistent error into the common reference, without acquiring turn data.
    epoch=epoch_of(inputs['t'],epochs);rotation=np.tile(np.eye(3),(len(epoch),1,1))
    active=epoch>=0;rotation[active]=matrices[epoch[active]]
    S[~active,5:,5:]=0.
    z=np.load(refits/row['task_id']/'free.npz',allow_pickle=False)['z']
    return eq,S,rotation,z


def evaluate(directory,refits,baseline,row,output):
    eq,S,rotation,z=prepare(directory,refits,row)
    prior=dict(np.load(baseline/(row['task_id']+'.npz'),allow_pickle=False))
    if not np.array_equal(eq.keep,prior['bin_mask']) or not np.array_equal(eq.bins['t'],prior['t']):raise ValueError('fixed support differs')
    B=eq.input_jacobians(z);responses,Q=temporal.latent_responses(B,S,rotation)
    gps=[temporal.temporal_covariance(responses[:5],eq.t,tau) for tau in temporal.POLICY['gps_correlation_seconds']]
    imu=[temporal.temporal_covariance(responses[5:],eq.t,tau) for tau in temporal.POLICY['imu_correlation_seconds']]
    expected=prior['covariance_augmented'];difference=np.linalg.norm(gps[0]+imu[0]-expected)/max(np.linalg.norm(expected),1e-30)
    if difference>1e-9:raise ValueError('independent-second baseline differs')
    # Separate dense temporal kernel on a finite input window, not the recurrence.
    first=int(eq.L.indices.min());idx=np.arange(first,min(first+240,len(eq.t)))
    kernel=np.exp(-abs(eq.t[idx,None]-eq.t[None,idx])/300.)
    reference=sum(r[:,idx].toarray()@kernel@r[:,idx].toarray().T for r in responses)
    check=temporal.temporal_covariance([r[:,idx] for r in responses],eq.t[idx],300.)
    error=float(np.linalg.norm(reference-check)/max(np.linalg.norm(reference),1e-30))
    if error>1e-10:raise ValueError('dense elapsed-time check differs')
    scenarios=[];n=len(prior['residual'])
    for i,gt in enumerate(temporal.POLICY['gps_correlation_seconds']):
        for j,it in enumerate(temporal.POLICY['imu_correlation_seconds']):
            scenarios.append(dict(gps_correlation_seconds=gt,imu_correlation_seconds=it,
                **temporal.scenario_metrics(gps[i]+imu[j],prior['residual_response'],prior['parameter_response'],n)))
    root_difference=float(np.max(abs(Q@Q.transpose(0,2,1)-S)))
    path=output/(row['task_id']+'.npz');temporary=path.with_suffix('.tmp.npz')
    np.savez_compressed(temporary,t=prior['t'],bin_mask=eq.keep,gps_covariances=np.array(gps),imu_covariances=np.array(imu),
        residual_response=prior['residual_response'],parameter_response=prior['parameter_response'],residual=prior['residual'])
    temporary.replace(path)
    return dict(task_id=row['task_id'],truth=row['truth'],crab_model=row['fit_options']['crab_model'],common_minutes=len(prior['t']),
        scenarios=scenarios,independent_baseline_relative_error=float(difference),dense_temporal_check_relative_error=error,
        root_covariance_max_absolute_error=root_difference,archive_sha256=refitter.sha(path))


def run(directory,refits,baseline,output):
    if any(os.environ.get(k)!='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')):raise ValueError('one numerical thread required')
    parent=json.loads((baseline/'plan.json').read_text());review=json.loads((baseline/'review.json').read_text())
    if not review['complete'] or len(review['cases'])!=6:raise ValueError('six completed baseline checks required')
    files=dict(parent['source_sha256'])
    for p in [Path(__file__),Path(temporal.__file__),baseline/'plan.json',baseline/'review.json',baseline/'verification.json']:
        files[str(p.relative_to(refitter.ROOT))]=refitter.sha(p)
    for c in review['cases']:
        p=baseline/(c['task_id']+'.npz')
        if refitter.sha(p)!=c['archive_sha256']:raise ValueError('baseline archive differs')
        files[str(p.relative_to(refitter.ROOT))]=refitter.sha(p)
    def verify():
        if implementation_hash()!=parent['scientific_implementation_hash'] or numerical_environment_hash()!=parent['numerical_environment_hash']:raise ValueError('source/environment differs')
        if any(refitter.sha(refitter.ROOT/k)!=v for k,v in files.items()):raise ValueError('frozen dependency changed')
    verify();rows=json.loads((directory/'campaign.json').read_text())['records'];output.mkdir(exist_ok=True)
    plan=dict(version='six-saved-temporal-sensitivity-1',policy=temporal.POLICY,source_sha256=files,
        scientific_implementation_hash=implementation_hash(),numerical_environment_hash=numerical_environment_hash(),
        task_ids=[r['task_id'] for r in rows],scenarios_per_case=36,optimizer_calls=0,additional_flight_attempts=0,bootstrap=0)
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
                start=time.monotonic();case=evaluate(directory,refits,baseline,row,output);case['elapsed_s']=time.monotonic()-start
                refitter.atomic(checkpoint,case)
            cases.append(case)
            values=[s['fixed_parameter_sigma_dph'] for s in case['scenarios']]
            print(json.dumps(dict(truth=case['truth'],crab=case['crab_model'],scenarios=len(values),fixed_parameter_sigma_dph_range=[min(values),max(values)])),flush=True)
        verify();result=dict(complete=True,cases=cases,plan_sha256=refitter.sha(path),optimizer_calls=0,additional_flight_attempts=0,bootstrap=0,
            production_enabled=False,decisions_enabled=False)
        report=output/'review.json'
        if report.exists():
            if json.loads(report.read_text())!=result:raise ValueError('completed review differs')
        else:refitter.atomic(report,result)
        refitter.atomic(output/'status.json',dict(state='complete',completed_cases=6,active_workers=0,pid=os.getpid()))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('refits',type=Path);parser.add_argument('baseline',type=Path)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    run(args.directory.resolve(),args.refits.resolve(),args.baseline.resolve(),args.output.resolve())
