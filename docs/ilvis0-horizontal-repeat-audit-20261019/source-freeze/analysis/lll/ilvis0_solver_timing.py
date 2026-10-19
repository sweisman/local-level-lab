# SPDX-License-Identifier: AGPL-3.0-or-later
"""Packet-aware bounded Gauss–Newton with an unchanged final acceptance gate."""
import numpy as np
from scipy.optimize import lsq_linear

from .ilvis0_estimator import EvaluationLimit
from .ilvis0_solver_refinement import POLICY as STOPPING,projected_stationarity
from . import ilvis0_solver_position as position,ilvis0_solver_boundary as boundary

VERSION='ilvis0-packet-aware-timing-candidate-v1'
POLICY=dict(position.POLICY,step_method='full bounded Gauss–Newton first; trust region after rejected full step',
            initial_radius=.25,maximum_radius=2.,minimum_radius=1e-12,
            timing_neighbor_offset_s=1e-9,
            initial_damping=1e-6,minimum_damping=1e-16,maximum_damping=1e12,
            acceptance_ratio=.1,linear_tolerance=1e-10,linear_maximum_iterations=100,
            stopping='unchanged undamped fresh stationarity, cost and actual-position check')


def interval_box(problem,point):
    """Intersection of the current receiver epochs' packet intervals, in u units."""
    names=list(problem.bounds.active)
    if 'time_offset' not in names:return None
    i=names.index('time_offset');scale=problem.bounds.limits['time_offset']
    times=np.asarray(problem.gps_times)+point[i]*scale
    ends=np.asarray(problem.ends);indices=np.searchsorted(ends,times,side='left')
    if np.any(times<0) or np.any(indices>=len(ends)):raise ValueError('time outside packet support')
    starts=np.r_[0.,ends[:-1]][indices]
    return i,float(np.max(starts-times)/scale),float(np.min(ends[indices]-times)/scale)


def refine_timing(problem,point,residual,jac,evaluate,available,history,evaluation):
    interval=interval_box(problem,point)
    if interval is None:return None
    i,lo,hi=interval;scale=problem.bounds.limits['time_offset']
    nudge=POLICY['timing_neighbor_offset_s']/scale
    anchors=[point]
    for step in (lo-nudge,hi+nudge):
        anchor=point.copy();anchor[i]+=step
        if abs(anchor[i])<=1 and not np.array_equal(anchor,point):anchors.append(anchor)
    original_cost=float(residual@residual)
    for n,anchor in enumerate(anchors):
        if n:
            if not available():break
            r,j,_=evaluate(anchor)
        else:r,j=residual,jac
        _,lower,upper=interval_box(problem,anchor)
        low=-1-anchor;high=1-anchor
        low[i]=max(low[i],lower);high[i]=min(high[i],upper)
        if np.any(low>=high):continue
        local=lsq_linear(j,-r,bounds=(low,high),method='bvls',tol=POLICY['linear_tolerance'],
                         max_iter=POLICY['linear_maximum_iterations'])
        if not local.success or not np.all(np.isfinite(local.x)):continue
        proposed=np.clip(anchor+local.x,-1.,1.)
        predicted=r+j@(proposed-anchor)
        reduction=original_cost-float(predicted@predicted)
        if reduction<=0 or np.array_equal(proposed,point) or not available():continue
        fresh,fresh_jac,_=evaluate(proposed);cost=float(fresh@fresh)
        actual=original_cost-cost;ratio=actual/reduction
        accepted=actual>0 and ratio>=POLICY['acceptance_ratio']
        history.append(dict(accepted=bool(accepted),cost=cost,method='timing_interval',
            anchor=n,timing_interval_lower=lower,timing_interval_upper=upper,
            predicted_reduction=reduction,actual_reduction=actual,agreement_ratio=ratio,
            normalized_step=float(np.linalg.norm(proposed-point))))
        if accepted:return proposed,fresh,fresh_jac,cost
    return None


def fit_candidate(problem,model,*,start,maximum_evaluations=200,physical_step=None):
    if type(maximum_evaluations) is not int or not 6<=maximum_evaluations<=600:
        raise ValueError('finite evaluation allowance in [6,600] required')
    original=np.array(start,dtype=float)
    if (original.shape!=(len(problem.bounds.active),) or not len(original)
            or not np.all(np.isfinite(original)) or np.any(abs(original)>1)):
        raise ValueError('explicit finite feasible start required')
    problem.bounds.decode(original);point=boundary.snap_bounds(original)
    transform=physical_step if physical_step is not None else lambda d:position.physical_residual_step(problem,d)
    calls=0;limit=maximum_evaluations-2;cache=None;trace=[];history=[]
    def evaluate(u,fresh=False):
        nonlocal calls,cache
        problem.bounds.decode(u)
        if not fresh and cache is not None and np.array_equal(u,cache[0]): return cache[1:]
        if calls>=limit: raise EvaluationLimit('tangent allowance exhausted')
        calls+=1
        residual,jac,edges=problem.residual_tangent(u,model)
        residual,jac=np.asarray(residual,float),np.asarray(jac,float)
        if (residual.ndim!=1 or jac.shape!=(len(residual),len(point))
                or not np.all(np.isfinite(residual)) or not np.all(np.isfinite(jac))):
            raise ValueError('invalid residual or tangent')
        cache=(u.copy(),residual,jac,edges)
        trace.append(dict(evaluation=calls,cost=float(residual@residual),fresh=bool(fresh)))
        return residual,jac,edges
    residual,jac,_=evaluate(point);initial_cost=cost=float(residual@residual)
    radius=POLICY['initial_radius'];damping=POLICY['initial_damping']
    message='evaluation allowance exhausted'
    try:
        while calls<limit:
            # An undamped solve decides whether the original gate is worth
            # checking. Damping never supplies a stopping or adequacy criterion.
            full=lsq_linear(jac,-residual,bounds=(-1-point,1-point),method='bvls',
                            tol=POLICY['linear_tolerance'],max_iter=POLICY['linear_maximum_iterations'])
            if not full.success or not np.all(np.isfinite(full.x)):
                message='undamped local solve unfinished';break
            predicted_full=residual+jac@full.x;full_cost=float(predicted_full@predicted_full)
            predicted_change=abs(full_cost-cost)/max(full_cost,cost,1.)
            predicted_step=float(np.linalg.norm(jac@full.x)/max(np.linalg.norm(residual),1.))
            if (projected_stationarity(point,residual,jac)[0]<=STOPPING['stationarity_tolerance']
                    and predicted_change<=STOPPING['relative_cost_tolerance']
                    and predicted_step<=STOPPING['relative_residual_step_tolerance']):
                message='undamped correction small; fresh verification required';break
            # Preserve progress along the complete local correction before
            # truncating its weak coordinates. A box-constrained short step can
            # point elsewhere in a curved, poorly conditioned valley.
            full_point=boundary.snap_bounds(np.clip(point+full.x,-1,1))
            full_reduction=cost-full_cost
            if full_reduction>0 and not np.array_equal(full_point,point):
                trial_residual,trial_jac,_=evaluate(full_point)
                trial_cost=float(trial_residual@trial_residual)
                reduction=cost-trial_cost;ratio=reduction/full_reduction
                accepted=reduction>0 and ratio>=POLICY['acceptance_ratio']
                history.append(dict(evaluation=calls,accepted=bool(accepted),cost=trial_cost,
                                    predicted_reduction=full_reduction,actual_reduction=reduction,
                                    agreement_ratio=ratio,method='full_bounded',radius=radius,
                                    damping=0.,damping_used=False,normalized_step=float(np.linalg.norm(full_point-point))))
                if accepted:
                    point,residual,jac,cost=full_point,trial_residual,trial_jac,trial_cost
                    continue
            revised=refine_timing(problem,point,residual,jac,evaluate,lambda:calls<limit,history,calls)
            if revised is not None:
                point,residual,jac,cost=revised
                continue
            step_bounds=(np.maximum(-1-point,-radius),np.minimum(1-point,radius))
            local=lsq_linear(jac,-residual,bounds=step_bounds,
                             method='bvls',tol=POLICY['linear_tolerance'],max_iter=POLICY['linear_maximum_iterations'])
            used_damping=False
            if not local.success or not np.all(np.isfinite(local.x)):
                scale=np.maximum(np.linalg.norm(jac,axis=0),1e-12)
                augmented=np.vstack((jac,np.diag(np.sqrt(damping)*scale)))
                right=np.r_[-residual,np.zeros(len(point))]
                local=lsq_linear(augmented,right,bounds=step_bounds,method='bvls',
                                 tol=POLICY['linear_tolerance'],max_iter=POLICY['linear_maximum_iterations'])
                used_damping=True
            if not local.success or not np.all(np.isfinite(local.x)):
                message='damped bounded step unfinished';break
            proposed=boundary.snap_bounds(np.clip(point+local.x,-1,1));step=proposed-point
            predicted=residual+jac@step;predicted_reduction=cost-float(predicted@predicted)
            if np.array_equal(proposed,point) or predicted_reduction<=0:
                # A tiny damped step cannot establish convergence. Reserve the
                # unchanged full correction check and report its actual result.
                message='no positive predicted decrease';break
            trial_residual,trial_jac,_=evaluate(proposed)
            trial_cost=float(trial_residual@trial_residual)
            actual_reduction=cost-trial_cost;ratio=actual_reduction/predicted_reduction
            accepted=actual_reduction>0 and ratio>=POLICY['acceptance_ratio']
            history.append(dict(evaluation=calls,accepted=bool(accepted),cost=trial_cost,
                                predicted_reduction=predicted_reduction,actual_reduction=actual_reduction,
                                agreement_ratio=ratio,radius=radius,damping=damping,damping_used=used_damping,
                                normalized_step=float(np.linalg.norm(step))))
            if accepted:
                point,residual,jac,cost=proposed,trial_residual,trial_jac,trial_cost
                if ratio>.75:
                    damping=max(damping*.3,POLICY['minimum_damping'])
                    if np.max(abs(step))>=.8*radius: radius=min(radius*2,POLICY['maximum_radius'])
                elif ratio<.25:
                    damping=min(damping*10,POLICY['maximum_damping']);radius=max(radius*.5,POLICY['minimum_radius'])
            else:
                damping=min(damping*10,POLICY['maximum_damping']);radius=max(radius*.5,POLICY['minimum_radius'])
                if radius<=POLICY['minimum_radius']:
                    message='trust region exhausted; fresh verification required';break
    except EvaluationLimit as error: message=str(error)
    limit=maximum_evaluations
    residual,jac,edges=evaluate(point,fresh=True)
    stationarity,gradient,projected,scaled=projected_stationarity(point,residual,jac)
    probe=position.verify_stability(point,residual,jac,evaluate,transform)
    converged=bool(probe['passed'] and stationarity<=STOPPING['stationarity_tolerance'])
    return dict(version=VERSION,model=model,parameters=problem.bounds.decode(point),
                normalized_parameters=point.tolist(),active_parameters=list(problem.bounds.active),
                residual_sum_squares=float(residual@residual),initial_cost=initial_cost,
                evaluations=calls,maximum_evaluations=maximum_evaluations,
                start_boundary_snap_maximum=float(np.max(abs(boundary.snap_bounds(original)-original))),
                converged=converged,stopping_rule_verified=converged,stability_verified=bool(probe['passed']),
                stability_probe=probe,stability_policy=dict(POLICY,maximum_evaluations=maximum_evaluations),
                message=message,termination='fresh_position_stability' if converged else 'unresolved',
                step_history=history,evaluation_trace=trace,
                exact_projected_gradient_relative=stationarity,stationarity_tolerance=STOPPING['stationarity_tolerance'],
                gradient=gradient.tolist(),projected_gradient=projected.tolist(),scaled_projected_gradient=scaled.tolist(),
                singular_values=np.linalg.svd(jac,compute_uv=False).tolist(),
                local_linearization=dict(active_parameters=list(problem.bounds.active),normalized_parameters=point.tolist(),
                                         residual=residual.tolist(),jacobian=jac.tolist(),
                                         convention='whitened residual derivative by normalized parameter'),
                active_bounds=[n for n,u in zip(problem.bounds.active,point) if abs(u)>=.999],
                gps_epochs_at_packet_boundaries=edges,scientific_eligible=False,scientific_decision='abstain',
                constant_bias_is_measured_drift=False,calibration_bounds_supported=False,
                processing_independence_established=False,receiver_covariance_calibrated=False,
                clock_independently_established=False)
