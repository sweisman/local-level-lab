# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-endpoint diagnostics and independent gate controls; no native predictions."""
import numpy as np
from scipy.optimize import lsq_linear
from . import ilvis0_solver_position as position
from .ilvis0_solver_refinement import projected_stationarity

VERSION='ilvis0-saved-stopping-boundary-audit-v1'


def known_controls():
    rows=[]
    for case in ('cusp_left','cusp_right','smooth_minimum','constrained_minimum','smooth_nonminimum'):
        point=np.array([1. if case=='constrained_minimum' else .8 if case=='smooth_nonminimum' else 0.])
        calls=[]
        def evaluate(u,fresh=False):
            x=float(u[0])
            if case.startswith('cusp'):
                r=np.array([1+.001*abs(x),40.]);d=-.001 if x<0 or (x==0 and case=='cusp_left') else .001
            elif case=='constrained_minimum':r=np.array([1+.001*(1-x),40.]);d=-.001
            else:r=np.array([.005*x,40.]);d=.005
            calls.append((x,r.copy()))
            return r,np.array([[d],[0.]]),0
        r,j,_=evaluate(point)
        # An explicit arbitrary unit conversion, not an instrument specification.
        physical=lambda delta:np.column_stack((2*np.asarray(delta),np.zeros((len(delta),2))))
        gate=position.verify_stability(point,r,j,evaluate,physical)
        stationarity=projected_stationarity(point,r,j)[0]
        known_minimum=case!='smooth_nonminimum'
        expected_pass=case in ('smooth_minimum','constrained_minimum')
        rows.append(dict(case=case,known_global_minimum=known_minimum,
            proof='minimize (1+0.001*abs(u))^2+1600 on [-1,1]' if case.startswith('cusp') else
                  'monotone residual minimized at upper bound' if case=='constrained_minimum' else
                  'minimize (0.005*u)^2+1600 on [-1,1]',
            original_gate=gate,stationarity=stationarity,stationarity_passed=stationarity<=1e-4,
            signed_actual_cost_change=float(calls[-1][1]@calls[-1][1]-r@r),
            center_cost=float(r@r),probe_parameter=calls[-1][0],analytic_evaluations=len(calls),
            expectation_met=bool(gate['passed'])==expected_pass,native_predictions=0,observed_fit_starts=0))
    return rows


def packet_screen(times,packet_count,offset_s,time_scale_s):
    times=np.asarray(times,float)
    if (times.ndim!=1 or not len(times) or not np.all(np.isfinite(times)) or np.any(np.diff(times)<=0)
            or type(packet_count) is not int or packet_count<1 or not np.isfinite(offset_s)
            or not np.isfinite(time_scale_s) or time_scale_s<=0):raise ValueError('valid saved timing geometry required')
    ends=np.cumsum(np.full(packet_count,.005));shifted=times+offset_s
    indices=np.searchsorted(ends,shifted,side='left')
    if np.any(shifted<0) or np.any(indices>=packet_count):raise ValueError('saved epochs outside native support')
    starts=np.r_[0.,ends[:-1]][indices];left=shifted-starts;right=ends[indices]-shifted
    distance=np.minimum(left,right)
    return dict(receiver_epochs=len(times),minimum_packet_distance_ns=float(np.min(distance)*1e9),
        median_packet_distance_ns=float(np.median(distance)*1e9),maximum_packet_distance_ns=float(np.max(distance)*1e9),
        epochs_within_100ns=int(np.sum(distance<=1e-7)),epochs_within_1us=int(np.sum(distance<=1e-6)),
        epochs_within_10us=int(np.sum(distance<=1e-5)),
        changed_packet_epochs_minus_100ns=int(np.sum(np.searchsorted(ends,shifted-1e-7,side='left')!=indices)),
        changed_packet_epochs_plus_100ns=int(np.sum(np.searchsorted(ends,shifted+1e-7,side='left')!=indices)),
        lower_normalized_time_step=float(-np.min(left)/time_scale_s),
        upper_normalized_time_step=float(np.min(right)/time_scale_s))


def affine_slices(point,residual,jac,time_index,lower_time,upper_time):
    point,residual,jac=map(lambda x:np.asarray(x,float),(point,residual,jac))
    if (jac.shape!=(len(residual),len(point)) or not 0<=time_index<len(point)
            or lower_time>0 or upper_time<0 or not all(np.all(np.isfinite(x)) for x in (point,residual,jac))):
        raise ValueError('finite compatible saved system required')
    rows=[];before=float(residual@residual)
    for method in ('full','current_packet_interval','fixed_time'):
        columns=list(range(len(point)));lower=-1-point;upper=1-point
        if method=='fixed_time':columns.remove(time_index)
        elif method=='current_packet_interval':
            lower[time_index]=max(lower[time_index],lower_time)
            upper[time_index]=min(upper[time_index],upper_time)
            if lower[time_index]>=upper[time_index]:columns.remove(time_index)
        fit=lsq_linear(jac[:,columns],-residual,bounds=(lower[columns],upper[columns]),
                       method='bvls',tol=1e-10,max_iter=100)
        step=np.zeros(len(point));step[columns]=fit.x
        predicted=residual+jac@step;after=float(predicted@predicted)
        rows.append(dict(method=method,success=bool(fit.success),predicted_cost_change=after-before,
            normalized_time_step=float(step[time_index]),normalized_step=float(np.linalg.norm(step)),
            feasible=bool(np.all(abs(point+step)<=1+4*np.finfo(float).eps)),
            native_predictions=0,observed_fit_starts=0))
    return rows


def signed_saved_probe(fit):
    reason=fit.get('stability_probe',{}).get('reason')
    if reason not in ('fresh_position_probe_not_stable','fresh_position_stability_verified'):return None
    fresh=[r for r in fit['evaluation_trace'] if r.get('fresh')]
    if len(fresh)<2 or abs(fresh[-2]['cost']-fit['residual_sum_squares'])>1e-10*max(fit['residual_sum_squares'],1.):
        raise ValueError('saved fresh probe center does not reproduce')
    return float(fresh[-1]['cost']-fit['residual_sum_squares'])
