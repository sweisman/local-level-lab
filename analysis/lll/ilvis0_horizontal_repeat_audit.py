# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved full-column affine witnesses; never propagates or relabels a flight."""
import math
import numpy as np
from scipy.optimize import lsq_linear
from .ilvis0_scaled_branch import scaled_lsq


def endpoint(row,saved):
    fit=row['fit'];names=fit['active_parameters'];point=np.asarray(fit['normalized_parameters'],float)
    r=np.asarray(saved['residual'],float);j=np.asarray(saved['jacobian'],float)
    if (saved['active_parameters']!=names or saved['normalized_parameters']!=fit['normalized_parameters']
            or point.ndim!=1 or len(point)!=len(names) or r.ndim!=1 or j.shape!=(len(r),len(point))
            or np.any(abs(point)>1) or any(not np.all(np.isfinite(v)) for v in (point,r,j))):
        raise ValueError('exact finite full-column saved endpoint required')
    cost=float(r@r)
    if abs(cost-fit['residual_sum_squares'])>1e-10*max(cost,fit['residual_sum_squares'],1.):raise ValueError('saved cost mismatch')
    results=[]
    for name,solve in (('original',lsq_linear),('range_scaled',scaled_lsq)):
        result=solve(j,-r,bounds=(-1-point,1-point),method='bvls',tol=1e-10,max_iter=100)
        step=np.asarray(result.x);linear=r.astype(np.longdouble)+j.astype(np.longdouble)@step.astype(np.longdouble)
        value=float(linear@linear);zero=float(np.asarray(r,np.longdouble)@np.asarray(r,np.longdouble))
        results.append(dict(method=name,solver_success=bool(result.success),step=step.tolist(),affine_cost=value,
            zero_cost=zero,predicted_reduction=zero-value,
            affine_not_worse_than_zero=bool(value<=zero+64*np.finfo(float).eps*max(zero,1.)),
            feasible=bool(np.all(point+step>=-1-1e-14) and np.all(point+step<=1+1e-14)),
            maximum_normalized_step=float(np.max(abs(step))),
            largest_steps=[dict(parameter=names[i],step=float(step[i])) for i in np.argsort(abs(step))[::-1][:5]]))
    offset=fit['parameters'].get('time_offset',0.)
    distance=min(min((t+offset)%.005,.005-(t+offset)%.005) for t in saved['times_s'])
    return dict(identity=row['identity'],columns=len(point),saved_rank=fit['numerical_rank'],
        original_fit_passed=row['passed'],cost=cost,corrections=results,time_offset_s=offset,
        nearest_nominal_clock_boundary_s=distance,stop_message=fit.get('message'),
        exhausted=fit['evaluations']>=fit['maximum_evaluations'],native_evaluations=0,fit_labels_changed=False)


def pair(a,b,sa,sb):
    ua=np.asarray(sa['normalized_parameters']);ub=np.asarray(sb['normalized_parameters'])
    if sa['active_parameters']!=sb['active_parameters'] or len(ua)!=len(ub):raise ValueError('matched parameter order required')
    ra=np.asarray(sa['residual']);rb=np.asarray(sb['residual']);j=np.asarray(sa['jacobian'])
    if ra.shape!=rb.shape:raise ValueError('matched residual layout required')
    delta=ub-ua;predicted=ra+j@delta
    return dict(primary_identity=a['identity'],repeat_identity=b['identity'],
        timing_difference_s=b['fit']['parameters']['time_offset']-a['fit']['parameters']['time_offset'],
        primary_predicts_repeat_cost=float(predicted@predicted),actual_repeat_cost=float(rb@rb),
        linear_vs_actual_residual_norm=float(np.linalg.norm(predicted-rb)),
        maximum_normalized_parameter_difference=float(np.max(abs(delta))),
        largest_parameter_differences=[dict(parameter=sa['active_parameters'][i],difference=float(delta[i]))
                                      for i in np.argsort(abs(delta))[::-1][:5]])
