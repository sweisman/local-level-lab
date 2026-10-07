# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the joint research prediction at saved parameter states, without refitting."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))

import numpy as np
import acceleration_motion
import joint_acceleration_motion as joint
import review_acceleration_motion as observed
from lll.calib import RAD2DPH
from lll.inference import science_information
from lll.inference_policy import INFERENCE_POLICY
from lll.research_design import implementation_hash
from lll.wind_tas import WIND_TAS_POLICY


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def curvature(A):
    scale=np.maximum(np.linalg.norm(A,axis=0),1e-30)
    inverse=np.linalg.pinv(A/scale)
    return (inverse@inverse.T)/np.outer(scale,scale)


def review(directory, output):
    campaign_path=directory/'campaign.json'
    campaign=json.loads(campaign_path.read_text())
    if not campaign['execution']['complete'] or implementation_hash()!=campaign['implementation_hash']:
        raise ValueError('completed replay and its unchanged scientific implementation required')
    output.mkdir(exist_ok=False)
    sources={str(campaign_path.relative_to(ROOT)):sha(campaign_path)}
    cases=[]
    for row in campaign['records']:
        folder=directory/'diagnostics'/row['task_id']
        for name in ('session.zip','fit-input.npz','fit-rows.npz','analysis.json'):
            path=folder/name; sources[str(path.relative_to(ROOT))]=sha(path)
        inputs=observed.observed_inputs(folder)
        context=joint.MotionContext(inputs)
        analysis=json.loads((folder/'analysis.json').read_text())
        saved=dict(np.load(folder/'fit-rows.npz',allow_pickle=False))
        cal=analysis['calibration']
        b0,b1=(np.asarray(cal[k]['bias_dph'])/RAD2DPH for k in ('pre','post'))
        t0,t1=(cal[k]['t_mid_s'] for k in ('pre','post'))
        def bias(t): return b0+np.clip((np.asarray(t)-t0)/(t1-t0),0,1)[...,None]*(b1-b0)
        settings=dict(row['fit_options'])
        for key in ('bias_knot_seconds','bias_rw_sigma_dph_sqrth','crab_rate_sigma_dph'):
            if settings.get(key) is None: settings[key]=INFERENCE_POLICY[key]
        if settings.get('crab_knot_seconds') is None: settings['crab_knot_seconds']=INFERENCE_POLICY['wind_knot_seconds']
        if settings['crab_model']=='wind_tas': settings['wind_tas_policy']=dict(WIND_TAS_POLICY)
        problem=joint.JointAccelerationProblem(context,bias,np.asarray(analysis['bias_model']['prior_sigma_dph'])/RAD2DPH,settings)
        z=problem.expand_saved(saved['parameters'])
        lo,hi=problem.bounds()
        if np.any(z<lo) or np.any(z>hi):
            raise ValueError('saved reference outside prototype bounds; do not clip it or refit')
        sigma=np.asarray(analysis['fit']['noise']['sigma_by_bin_axis_dph'])[context.bin_mask]
        problem.w=(RAD2DPH/sigma.ravel())**2
        prediction,J=problem.prediction(z,True)
        P=problem.penalty()
        A=problem.objective_jacobian(z,P)
        covariance=curvature(A)
        keep=np.r_[np.arange(problem.error_slice.start),np.arange(problem.error_slice.stop,problem.npar)]
        conditional=curvature(A[:,keep])
        coupled=np.linalg.norm(covariance[:3,problem.error_slice])
        augmented,weights=problem.observation_information(z,J,problem.w)
        information=science_information(augmented,weights)['report']
        # An independent directional difference checks the full objective including priors/speed.
        direction=np.linspace(-.7,.7,problem.npar)
        if problem.wind_tas is not None: direction[problem.p:problem.p+problem.nc]*=5
        step=2e-5
        actual=(problem.objective_residual(z+step*direction,problem.y,P)-problem.objective_residual(z-step*direction,problem.y,P))/(2*step)
        expected=A@direction
        relative=float(np.linalg.norm(actual-expected)/max(np.linalg.norm(expected),1e-30))
        if relative>1e-3: raise ValueError('joint objective directional derivative differs')
        reference=context.bin_mask
        baseline_y=saved['y'].reshape(-1,3)[reference]
        # Original final prediction is reconstructed by the frozen predecessor helper.
        from audit_replay_residuals import saved_prediction
        original_residual,*_=saved_prediction(row,analysis,inputs['bins'],saved)
        residual=(problem.y-prediction).reshape(-1,3)
        archive=output/(row['task_id']+'.npz')
        np.savez_compressed(archive,bin_mask=reference,parameters=z,prediction=prediction,jacobian=J,
            covariance=covariance,covariance_errors_fixed=conditional,residual=residual,objective_jacobian=A)
        cases.append(dict(task_id=row['task_id'],truth=row['truth'],crab_model=settings['crab_model'],
            mode='saved reference evaluation; no refit',provenance=problem.provenance(),
            fixed_supported_minutes=len(context.bins['t']),original_minutes=len(reference),parameters=problem.npar,
            saved_reference_parameters=problem.original_npar,coherent_error_modes=6,
            baseline_residual_same_bins_dph=float(np.sqrt(np.mean(original_residual[reference]**2))*RAD2DPH),
            joint_prediction_residual_dph=float(np.sqrt(np.mean(residual**2))*RAD2DPH),
            local_science_sd=np.sqrt(np.maximum(np.diag(covariance)[:3],0)).tolist(),
            local_science_sd_errors_fixed=np.sqrt(np.maximum(np.diag(conditional)[:3],0)).tolist(),
            science_error_covariance_norm=float(coupled),objective_directional_derivative_relative_error=relative,
            nuisance_projection_diagnostic=information,
            archive=str(archive.relative_to(ROOT)),archive_sha256=sha(archive)))
        print(json.dumps({k:cases[-1][k] for k in ('truth','crab_model','fixed_supported_minutes','joint_prediction_residual_dph',
            'local_science_sd','local_science_sd_errors_fixed','objective_directional_derivative_relative_error')}),flush=True)
    helpers={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),Path(joint.__file__),Path(observed.__file__),
        Path(acceleration_motion.__file__),ROOT/'analysis/tests/audit_replay_residuals.py')}
    report=dict(scope='Joint wind/forward/force prediction and local curvature at frozen saved states; no new observations or fitting',
        scientific_implementation_hash=campaign['implementation_hash'],input_sha256=sources,helper_sha256=helpers,
        additional_flight_attempts=0,optimizer_calls=0,production_enabled=False,decisions_enabled=False,cases=cases,
        limitations=['Reference coefficients came from the earlier approximate pipeline; they are not optima of this new objective.',
            'Frozen earlier preliminary gyro weights are reused, not re-estimated or validated for corrected motion.',
            'Local penalized curvature is not coverage; six coherent measurement-error modes do not span all correlated or instrumental errors.',
            'Diagnostic nuisance projection is evaluated at saved data-dependent reference states, not an outcome-independent design envelope.',
            'Ground/TAS speed observation retains the existing conditional bin model; a fully joint GPS likelihood remains open.',
            'Scientific terms use the retained bin-average geometry; Coriolis/curvature acceleration systematics and filter bandwidth remain unresolved.',
            'No pair profile, selection gate, model winner, power, bootstrap or calibration output is produced.'])
    (output/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    review(args.directory.resolve(),args.output.resolve())
