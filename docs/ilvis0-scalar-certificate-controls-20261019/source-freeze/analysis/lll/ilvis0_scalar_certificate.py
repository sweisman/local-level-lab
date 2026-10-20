# SPDX-License-Identifier: AGPL-3.0-or-later
"""Feasible near-zero scalar construction before bounded nonlinear calibration.

This can demonstrate ambiguity of a scalar necessary constraint. It does not
identify orientation, establish a unique calibration or produce a model verdict.
The earlier nonlinear candidate remains unchanged.
"""
import numpy as np

from . import ilvis0_scalar_nonlinear as original


def fit(problem,start,*,max_evaluations=200):
    start=np.asarray(start,float)
    if start.shape!=(7,) or not np.all(np.isfinite(start)) or np.any(abs(start)>1.):
        raise ValueError('seven finite requested start coordinates inside bounds required')
    if not isinstance(max_evaluations,int) or isinstance(max_evaluations,bool) or max_evaluations<1:
        raise ValueError('positive integer evaluation allowance required')
    measured=np.linalg.norm(problem.body,axis=1);required=np.linalg.norm(problem.force,axis=1)
    denominator=float(required@required);point=None;rejection='nonzero finite history required'
    if np.all(np.isfinite(measured)) and np.all(np.isfinite(required)) and 0.<denominator<float('inf'):
        gain=float((required@measured)/denominator-1.)
        if np.isfinite(gain) and np.all(abs(gain)<=problem.limits[:3]):
            point=np.zeros(7);point[:3]=gain/problem.limits[:3]
        else:rejection='gain outside bounds'
    preflight=0
    if point is not None:
        residual=problem.residual(point);preflight+=1
        jacobian=problem.jacobian(point);preflight+=1
        rms=float(np.linalg.norm(residual)/np.sqrt(len(residual)))
        stop=original.stationarity(point,jacobian.T@residual)
        if rms<=1e-12 and float(np.max(abs(residual)))<=1e-11 and stop<=1e-8:
            residual=problem.residual(point);jacobian=problem.jacobian(point);preflight+=2
            rms=float(np.linalg.norm(residual)/np.sqrt(len(residual)))
            stop=original.stationarity(point,jacobian.T@residual);cost=float(residual@residual/2)
            passed=bool(rms<=1e-12 and float(np.max(abs(residual)))<=1e-11 and stop<=1e-8)
            return dict(point=point.tolist(),physical_point=(point*problem.limits).tolist(),
                residual_mps2=residual.tolist(),rms_mps2=rms,cost=cost,stationarity=stop,
                passed=passed,solver_status=None,message='feasible algebraic near-zero scalar construction',
                completion_method='algebraic_near_zero_certificate',optimizer_started=False,
                cost_lower_bound=0.,feasible_cost_upper_bound=cost,
                requested_start=start.tolist(),residual_calls=2,jacobian_calls=2,calls=4,
                maximum_calls=2*max_evaluations+4,magnitude_history_constructions=2,
                active_bounds=[int(i) for i in np.flatnonzero(abs(point)>=1.-1e-7)],
                fresh_endpoint_checked=True,global_optimum_established=False,
                observed_starts=0,scientific_decision='abstain')
        rejection='constant isotropic gain does not certify the complete history'
    result=original.fit(problem,start,max_evaluations=max_evaluations)
    result.update(completion_method='bounded_least_squares',optimizer_started=True,
        certificate_rejection=rejection,requested_start=start.tolist(),magnitude_history_constructions=2)
    result['calls']+=preflight;result['maximum_calls']+=2
    result['residual_calls']+=preflight//2;result['jacobian_calls']+=preflight//2
    return result
