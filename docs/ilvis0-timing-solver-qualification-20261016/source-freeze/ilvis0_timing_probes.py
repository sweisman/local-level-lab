# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite time-alignment checks at fixed endpoints; no optimization or decisions."""
import numpy as np
from .ilvis0_solver_position import physical_metric

VERSION='ilvis0-fixed-timing-probes-v1'
STEPS_S=(1e-7,1e-5,1e-3,4e-3)


def difference(a,b):
    delta=np.asarray(a)-np.asarray(b)
    wrap=abs(delta[:,1])>np.pi
    delta[wrap,1]=(delta[wrap,1]+np.pi)%(2*np.pi)-np.pi
    return delta


def rms(value):return np.sqrt(np.mean(np.asarray(value)**2,axis=0)).tolist()


def packet_context(problem,point):
    i=list(problem.bounds.active).index('time_offset')
    times=problem.gps_times+point[i]*problem.bounds.limits['time_offset']
    indices=np.searchsorted(problem.ends,times,side='left')
    if np.any(indices>=len(problem.ends)) or np.any(times<0):
        raise ValueError('time probe outside packet support')
    starts=np.r_[0.,problem.ends[:-1]][indices]
    ends=problem.ends[indices]
    return dict(packet_indices=indices.tolist(),minimum_boundary_distance_s=float(np.min(np.minimum(times-starts,ends-times))),
                minimum_interval_fraction=float(np.min((times-starts)/(ends-starts))),
                maximum_interval_fraction=float(np.max((times-starts)/(ends-starts))))


def inspect(problem,point,model,call,*,correction=None):
    point=np.array(point,float);i=list(problem.bounds.active).index('time_offset')
    scale=problem.bounds.limits['time_offset'];metric=physical_metric(problem.gps)
    points=[]
    for step in STEPS_S:
        minus=point.copy();minus[i]-=step/scale
        plus=point.copy();plus[i]+=step/scale
        points.extend((minus,plus))
    if correction is not None:
        correction=np.asarray(correction,float)
        points.extend(point+fraction*correction for fraction in (1.,.5))
    if any(p.shape!=point.shape or not np.all(np.isfinite(p)) or np.any(abs(p)>1) for p in [point,*points]):
        raise ValueError('all frozen perturbations must be feasible before native calls')
    contexts=[packet_context(problem,p) for p in [point,*points]]
    center,jac,boundaries=call(problem.prediction_tangent,point,model)
    again,_,_=call(problem.prediction_tangent,point,model)
    residual=problem.whiten(center-problem.gps);cost=float(residual@residual)
    derivative=jac[:,i].reshape(center.shape)/scale
    denominator=max(np.linalg.norm(derivative*metric),1e-30)
    results=[]
    for n,step in enumerate(STEPS_S):
        minus,jminus,bminus=call(problem.prediction_tangent,points[2*n],model)
        plus,jplus,bplus=call(problem.prediction_tangent,points[2*n+1],model)
        left=difference(center,minus)/step;right=difference(plus,center)/step
        central=(left+right)/2
        row=dict(step_s=step,centered_derivative_neu_rms_mps=rms(central*metric),
                 analytic_derivative_neu_rms_mps=rms(derivative*metric),
                 centered_derivative_error_neu_rms_mps=rms((central-derivative)*metric),
                 left_derivative_error_neu_rms_mps=rms((left-derivative)*metric),
                 right_derivative_error_neu_rms_mps=rms((right-derivative)*metric),
                 centered_derivative_relative_error=float(np.linalg.norm((central-derivative)*metric)/denominator),
                 left_right_derivative_relative_difference=float(np.linalg.norm((left-right)*metric)/denominator))
        for sign,value,j,b,context,signed in (
                ('minus',minus,jminus,bminus,contexts[2*n+1],-step),
                ('plus',plus,jplus,bplus,contexts[2*n+2],step)):
            r=problem.whiten(value-problem.gps);linear=problem.whiten((derivative*signed))
            row.update({sign+'_cost_change':float(r@r-cost),
                        sign+'_linearized_cost_change':float((residual+linear)@(residual+linear)-cost),
                        sign+'_changed_packet_epochs':sum(a!=b for a,b in zip(context['packet_indices'],contexts[0]['packet_indices'])),
                        sign+'_minimum_boundary_distance_s':context['minimum_boundary_distance_s'],
                        sign+'_native_boundary_epochs':b,
                        sign+'_tangent_change_relative':float(np.linalg.norm((j[:,i].reshape(center.shape)/scale-derivative)*metric)/denominator)})
        results.append(row)
    coupled=[]
    if correction is not None:
        for fraction,p in zip((1.,.5),points[-2:]):
            out,_,b=call(problem.prediction_tangent,p,model)
            r=problem.whiten(out-problem.gps);linear=problem.whiten((jac@(fraction*correction)).reshape(center.shape))
            coupled.append(dict(fraction=fraction,actual_cost_change=float(r@r-cost),
                linearized_cost_change=float((residual+linear)@(residual+linear)-cost),
                position_change_neu_rms_m=rms(difference(out,center)*metric),native_boundary_epochs=b,
                changed_packet_epochs=sum(a!=b for a,b in zip(packet_context(problem,p)['packet_indices'],contexts[0]['packet_indices']))))
    return dict(version=VERSION,center_cost=cost,time_offset_s=float(point[i]*scale),
        center_packet_context=contexts[0],center_native_boundary_epochs=boundaries,
        center_repeat_maximum_neu_m=np.max(abs(difference(again,center)*metric),axis=0).tolist(),
        time_probes=results,coupled_probes=coupled,native_evaluations=2+2*len(STEPS_S)+len(coupled),
        observed_fit_starts=0,original_labels_changed=False,scientific_decision='abstain')
