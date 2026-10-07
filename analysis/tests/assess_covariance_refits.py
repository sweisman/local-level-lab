# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent arithmetic, support and boundary audit of the bounded GLS refits."""
import argparse
import itertools
import json
from pathlib import Path
import time

import numpy as np
from scipy.linalg import cho_solve

import refit_covariance_measurement as refits
import refit_joint_acceleration_motion as saved
import review_temporal_measurement_covariance as preparation
from lll import models
from lll.calib import RAD2DPH
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment_hash


def relative(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(a),np.linalg.norm(b),1e-30))


def pair_diagnostics(J,C):
    """Local data-only projection, without priors or any eligibility threshold."""
    sigma=np.sqrt(np.diag(C));L=np.linalg.cholesky(C/sigma[:,None]/sigma[None,:])
    from scipy.linalg import solve_triangular
    WJ=solve_triangular(L,J/sigma[:,None],lower=True)
    nuisance=WJ[:,3:];scales=np.maximum(np.linalg.norm(nuisance,axis=0),1e-30)
    coefficients=np.linalg.lstsq(nuisance/scales,WJ[:,:3],rcond=1e-10)[0]
    retained=WJ[:,:3]-(nuisance/scales)@coefficients
    result={}
    for a,b in itertools.combinations(models.EXPECTED_K,2):
        contrast=np.asarray(models.EXPECTED_K[a])-models.EXPECTED_K[b]
        before=WJ[:,:3]@contrast;after=retained@contrast
        total=float(before@before);information=float(after@after)
        result[a+'__'+b]=dict(information=information,retained_fraction=information/total if total>0 else None)
    return result


def assess(output):
    plan_path=output/'plan.json';plan=json.loads(plan_path.read_text());review_path=output/'review.json';review=json.loads(review_path.read_text())
    if not review['complete'] or len(review['cases'])!=24:raise ValueError('24 completed comparisons required')
    if saved.sha(plan_path)!=review['plan_sha256']:raise ValueError('plan hash differs')
    if implementation_hash()!=plan['scientific_implementation_hash'] or numerical_environment_hash()!=plan['numerical_environment_hash']:raise ValueError('frozen environment/source differs')
    if any(saved.sha(saved.ROOT/k)!=v for k,v in plan['source_sha256'].items()):raise ValueError('frozen dependency differs')
    # Audit only complete lines. Repair, if needed, is the worker's responsibility.
    journal=(output/'attempts.jsonl').read_bytes()
    if not journal.endswith(b'\n'):raise ValueError('journal has unfinished last write')
    events=[json.loads(line) for line in journal.splitlines()];starts=[e for e in events if e['event']=='started'];completed=[e for e in events if e['event']=='complete']
    if [e['attempt'] for e in starts]!=list(range(1,len(starts)+1)) or len(starts)!=review['optimizer_starts'] or len(starts)>120:raise ValueError('start budget/sequence differs')
    by_attempt={e['attempt']:e for e in starts};done={e['attempt']:e for e in completed}
    if len(done)!=len(completed):raise ValueError('duplicate completion')
    for event in completed:
        original=by_attempt[event['attempt']]
        if (original['case_id'],original['fit'])!=(event['case_id'],event['fit']):raise ValueError('completion identity differs')
    repairs=[e for e in starts if e['fit']=='nesting-repair']
    if len({e['case_id'] for e in repairs})!=len(repairs):raise ValueError('more than one repair per comparison')
    rows={r['task_id']:r for r in json.loads((refits.ORIGINAL/'campaign.json').read_text())['records']}
    cases=[];files={};checkpoint_attempts=set();max_residual_error=max_score_error=max_direction_error=0.;primary_count=0;failed=0;boundary_fits=0;near_boundary_fits=0
    for task_id,row in rows.items():
        eq,_,_,_=preparation.prepare(refits.ORIGINAL,refits.JOINT,row);lo,hi=eq.problem.bounds();P=eq.problem.penalty()
        for case in [c for c in review['cases'] if c['task_id']==task_id]:
            pair=case['correlation_seconds'];case_id=refits.identity(row,pair)
            if case_id!=case['case_id']:raise ValueError('case identity differs')
            folder=output/case_id;cov_path=folder/'covariance.npz';files[str(cov_path.relative_to(saved.ROOT))]=saved.sha(cov_path)
            if saved.sha(cov_path)!=case['covariance_sha256']:raise ValueError('covariance hash differs')
            cov_archive=dict(np.load(cov_path,allow_pickle=False));C=cov_archive['covariance']
            if not np.array_equal(cov_archive['bin_mask'],eq.keep) or not np.array_equal(cov_archive['t'],eq.bins['t']):raise ValueError('support differs')
            prior=np.load(refits.TEMPORAL/(task_id+'.npz'),allow_pickle=False)
            gi=refits.temporal.POLICY['gps_correlation_seconds'].index(pair[0]);ii=refits.temporal.POLICY['imu_correlation_seconds'].index(pair[1])
            expected=refits.discrepancy.add_discrepancy(prior['gps_covariances'][gi]+prior['imu_covariances'][ii],3*len(eq.bins['t']),case['crab_model'])
            if not np.array_equal(C,expected):raise ValueError('covariance changed between comparisons')
            sigma=np.sqrt(np.diag(C));factor=np.linalg.cholesky(C/sigma[:,None]/sigma[None,:]);fits={}
            for name,meta in case['fits'].items():
                path=folder/(name+'.json');files[str(path.relative_to(saved.ROOT))]=saved.sha(path)
                if json.loads(path.read_text())!=meta:raise ValueError('summary/metadata differ')
                if 'attempt' in meta:
                    attempt=meta['attempt'];original=by_attempt[attempt]
                    if (original['case_id'],original['fit'])!=(case_id,name) or attempt in checkpoint_attempts:raise ValueError('checkpoint start identity differs')
                    checkpoint_attempts.add(attempt)
                primary_count+=name in refits.POLICY['primary_fits_per_case'];failed+=not meta['success']
                if not meta.get('archive'):continue
                archive=folder/meta['archive'];files[str(archive.relative_to(saved.ROOT))]=saved.sha(archive)
                if saved.sha(archive)!=meta['archive_sha256']:raise ValueError('archive hash differs')
                state=dict(np.load(archive,allow_pickle=False));z=state['z']
                if not np.isfinite(z).all() or np.any(z<lo-1e-10) or np.any(z>hi+1e-10):raise ValueError('parameters outside frozen bounds')
                if name in models.EXPECTED_K and not np.array_equal(z[:3],models.EXPECTED_K[name]):raise ValueError('fixed science differs')
                if meta['nfev']>200:raise ValueError('evaluation limit exceeded')
                finite=np.isfinite(lo)&np.isfinite(hi);margins=np.minimum(z[finite]-lo[finite],hi[finite]-z[finite])/(hi[finite]-lo[finite])
                boundary_fits+=bool(np.any(margins<=1e-5));near_boundary_fits+=bool(np.any(margins<=.01))
                raw=np.r_[eq.residual(z),eq.auxiliary(z)]
                rerr=relative(raw,state['raw_residual']);max_residual_error=max(max_residual_error,rerr)
                standardized=raw/sigma;data=float(standardized@cho_solve((factor,True),standardized));penalty=float(np.sum((P@z)**2))
                score=data+penalty;serr=abs(score-meta['scores']['penalized_least_squares'])/max(1.,abs(score));max_score_error=max(max_score_error,serr)
                if rerr>1e-10 or serr>1e-9:raise ValueError('independent residual/objective differs')
                if meta['attempt'] in done and done[meta['attempt']]['success']!=meta['success']:raise ValueError('journal convergence differs')
                fits[name]=dict(objective=score,residual_rms_dph=meta['residual_rms_dph'],minimum_relative_bound_margin=float(min(margins)),
                    boundary=bool(np.any(margins<=1e-5)),near_boundary=bool(np.any(margins<=.01)),k=z[:3].tolist(),
                    conditional_sampling_k_sd=np.sqrt(np.maximum(np.diag(state['sampling_covariance'])[:3],0)).tolist(),
                    data_quadratic=data,penalty_quadratic=penalty,success=meta['success'],nfev=meta['nfev'])
            free=case['selected_free_fit'];local=None
            if free in fits:
                state=dict(np.load(folder/case['fits'][free]['archive'],allow_pickle=False));z=state['z'];p=eq.problem
                direction=np.full(p.npar,1e-7);direction[:3]=[.02,-.03,.01];direction[p.p:p.p+p.nc]=.002 if p.wind_tas is not None else 1e-4
                direction[p.error_slice]=.001;direction[-1]=1e-4
                h=1e-3
                # Use an interior direction at finite parameter boundaries.
                direction[(z-h*abs(direction)<lo)|(z+h*abs(direction)>hi)]=0.
                direct=(np.r_[eq.residual(z+h*direction),eq.auxiliary(z+h*direction)]-np.r_[eq.residual(z-h*direction),eq.auxiliary(z-h*direction)])/(2*h)
                derr=relative(direct,state['raw_jacobian']@direction);max_direction_error=max(max_direction_error,derr)
                if derr>2e-3:raise ValueError('saved full-equation Jacobian direction differs')
                local=pair_diagnostics(state['raw_jacobian'],C)
            nested=bool(free in fits and all(k in fits and fits[free]['objective']<=fits[k]['objective']+1e-6 for k in models.EXPECTED_K))
            if nested!=case['nested']:raise ValueError('nesting summary differs')
            fixed_differences={a+'__'+b:fits[a]['objective']-fits[b]['objective'] for a,b in itertools.combinations(models.EXPECTED_K,2) if a in fits and b in fits}
            cases.append(dict(case_id=case_id,truth=case['truth'],crab_model=case['crab_model'],correlation_seconds=pair,
                comparison_converged=case['selected_comparison_converged'],nested=nested,selected_free_fit=free,fits=fits,
                signed_fixed_objective_differences=fixed_differences,local_data_only_pair_projection=local))
    if primary_count!=96 or {c['case_id'] for c in cases}!={t['case_id'] for t in plan['tasks']}:raise ValueError('finite primary scope differs')
    for p in [plan_path,review_path,output/'attempts.jsonl',Path(__file__)]:files[str(p.relative_to(saved.ROOT))]=saved.sha(p)
    values=[f['residual_rms_dph'] for c in cases for name,f in c['fits'].items() if name==c['selected_free_fit']]
    if not set(done).issubset(checkpoint_attempts):raise ValueError('journal completion lacks a durable checkpoint')
    report=dict(complete=True,cases=cases,primary_fits=primary_count,optimizer_starts=len(starts),completed_starts=len(checkpoint_attempts),
        journal_completion_events=len(completed),checkpoint_completions_without_journal_event=len(checkpoint_attempts-set(done)),
        interrupted_starts=len(starts)-len(checkpoint_attempts),nesting_repair_starts=len(repairs),nonconverged_or_failed_fits=failed,
        converged_comparisons=sum(c['comparison_converged'] for c in cases),nested_comparisons=sum(c['nested'] for c in cases),
        boundary_fits=boundary_fits,within_one_percent_bound_fits=near_boundary_fits,
        free_residual_rms_dph_range=[min(values),max(values)] if values else None,
        summed_completed_optimizer_seconds=sum(f['elapsed_s'] for c in review['cases'] for f in c['fits'].values() if 'attempt' in f),
        max_independent_residual_relative_error=max_residual_error,max_independent_objective_relative_error=max_score_error,
        max_full_equation_direction_relative_error=max_direction_error,artifact_sha256=files,
        additional_flight_attempts=0,bootstrap=0,production_enabled=False,decisions_enabled=False,
        limitations=['Covariance frozen at previous free states; scales/correlations and physical discrepancy remain provisional.',
            'Conditional on recovered references, calibration and assumed nuisance penalties; no hardware coverage established.',
            'Local data-only projections use normalized least squares rcond 1e-10 without priors; no acceptance thresholds applied.',
            'Raw objective differences are uncalibrated and provide no rejection, power or winner claim.'])
    path=output/'verification.json'
    if path.exists():
        if json.loads(path.read_text())!=report:raise ValueError('completed assessment differs')
    else:saved.atomic(path,report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('cases','artifact_sha256','limitations')},indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=refits.OUTPUT);parser.add_argument('--wait',action='store_true')
    args=parser.parse_args();output=args.output.resolve()
    if args.wait:
        while not (output/'review.json').exists():
            status=json.loads((output/'status.json').read_text()) if (output/'status.json').exists() else {}
            if status.get('state')=='stopped':raise RuntimeError('Worker stopped: '+str(status.get('error')))
            time.sleep(30)
    assess(output)
