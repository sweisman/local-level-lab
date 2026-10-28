# SPDX-License-Identifier: AGPL-3.0-or-later
"""Complete-column bounded linear proposals inside one feasible timing cell."""
import numpy as np

TOLERANCE=1e-10
MAXIMUM_ITERATIONS=100


def bounded_step(residual,jacobian,point,lower,upper,*,active,reserve):
    # The public wrapper initializes from an unconstrained solution. On ill-conditioned
    # boxes that initialization can leave BVLS reporting success above a feasible
    # incumbent's cost. Its version-bound core accepts the feasible start explicitly.
    from scipy.optimize._lsq.bvls import bvls
    r,j,u,lo,hi=(np.asarray(v,float) for v in (residual,jacobian,point,lower,upper))
    names=list(active)
    if (not callable(reserve) or u.ndim!=1 or not 1<=len(u)<=27
            or len(names)!=len(u) or len(set(names))!=len(names) or any(not isinstance(n,str) or not n for n in names)
            or lo.shape!=u.shape or hi.shape!=u.shape or np.any(lo>hi) or np.any(u<lo) or np.any(u>hi)
            or r.ndim!=1 or not 1<=len(r)<=3600 or j.shape!=(len(r),len(u))
            or any(not np.all(np.isfinite(v)) for v in (r,j,u,lo,hi))):
        raise ValueError('finite complete columns, feasible anchor and nonempty physical box required')
    original=float(r@r)
    if not np.isfinite(original):raise ValueError('finite anchor objective required')
    reserve()
    free=lo<hi
    def solve(a,lower,upper):
        result=bvls(a,-r,np.zeros(a.shape[1]),lower,upper,TOLERANCE,MAXIMUM_ITERATIONS,0)
        result.success=bool(result.status>0)
        result.message={0:'maximum BVLS iterations reached',1:'BVLS first-order optimality satisfied',
                        2:'BVLS relative cost change satisfied'}.get(result.status,'BVLS stopped')
        return result
    if np.all(free):
        result=solve(j,lo-u,hi-u)
        step=result.x
    elif np.any(free):
        result=solve(j[:,free],(lo-u)[free],(hi-u)[free])
        step=np.zeros_like(u);step[free]=result.x
    else:
        from types import SimpleNamespace
        result=SimpleNamespace(success=True,message='every coordinate fixed by cell constraints',nit=0)
        step=np.zeros_like(u)
    proposed=u+step
    roundoff=64*np.finfo(float).eps*np.maximum(1.,np.maximum(abs(lo),abs(hi)))
    if (not np.all(np.isfinite(proposed)) or np.any(proposed<lo-roundoff) or np.any(proposed>hi+roundoff)):
        raise ValueError('linear solver returned an invalid or infeasible proposal')
    candidate=np.clip(proposed,lo,hi);predicted=r+j@(candidate-u);cost=float(predicted@predicted)
    if not np.isfinite(cost):raise ValueError('nonfinite linear prediction')
    monotone=cost<=original+64*np.finfo(float).eps*max(1.,cost,original)
    return dict(version='timing-cell-linear-step-v1',linear_success=bool(result.success and monotone),
        message=str(result.message),iterations=int(result.nit),maximum_iterations=MAXIMUM_ITERATIONS,
        tolerance=TOLERANCE,point=candidate.tolist(),step=(candidate-u).tolist(),
        active_parameters=names,predicted_residual=predicted.tolist(),predicted_cost=cost,anchor_cost=original,
        fixed_parameters=[names[i] for i in range(len(names)) if not free[i]],
        lower=lo.tolist(),upper=hi.tolist(),roundoff_clipped=bool(np.any(candidate!=proposed)),
        initialization='feasible_anchor',nonworsening=bool(monotone),solver_claimed_success=bool(result.success),
        parameter_bounds_reached=[names[i] for i in range(len(names)) if candidate[i]==lo[i] or candidate[i]==hi[i]],
        linear_solves=1,nonlinear_fit_starts=0,native_calls=0,scientific_decision='abstain',
        confidence_calibrated=False)
