# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded mathematical calibration controls, not an archival observation fit."""
import numpy as np
from scipy.optimize import least_squares


class Problem:
    def __init__(self,body,force,limits):
        body,force,limits=(np.asarray(value,float) for value in (body,force,limits))
        if (body.ndim!=2 or body.shape[1]!=3 or not len(body) or force.shape!=body.shape
                or not np.all(np.isfinite(body)) or not np.all(np.isfinite(force))):
            raise ValueError('matching finite nonempty N by 3 force histories required')
        if (limits.shape!=(7,) or not np.all(np.isfinite(limits)) or np.any(limits<=0.)
                or np.any(limits[:3]>=1.)):
            raise ValueError('seven positive bounds with gain limits below one required')
        self.body=body.copy();self.force=force.copy();self.limits=limits.copy()
        for value in (self.body,self.force,self.limits):value.flags.writeable=False

    def quantities(self,point):
        point=np.asarray(point,float)
        if point.shape!=(7,) or not np.all(np.isfinite(point)) or np.any(abs(point)>1.):
            raise ValueError('seven finite normalized bound coordinates required')
        physical=point*self.limits;denominator=1.+physical[:3]
        corrected=(self.body-physical[3:6])/denominator
        target=self.force-np.array([0.,0.,physical[6]])
        measured=np.linalg.norm(corrected,axis=1);required=np.linalg.norm(target,axis=1)
        if not np.all(np.isfinite(measured)) or not np.all(np.isfinite(required)):
            raise ValueError('nonfinite force magnitude')
        return corrected,target,measured,required,denominator

    def residual(self,point):
        _,_,measured,required,_=self.quantities(point)
        return measured-required

    def jacobian(self,point):
        corrected,target,measured,required,denominator=self.quantities(point)
        if np.any(measured<=np.finfo(float).tiny) or np.any(required<=np.finfo(float).tiny):
            raise ValueError('nonzero magnitudes required for calibration derivatives')
        direction=corrected/measured[:,None]
        return np.column_stack((-direction*corrected/denominator,-direction/denominator,
            target[:,2]/required))*self.limits


def stationarity(point,gradient):
    """Normalized box-constrained projected-gradient infinity norm."""
    point,gradient=np.asarray(point,float),np.asarray(gradient,float)
    if point.shape!=gradient.shape or not np.all(np.isfinite(point)) or not np.all(np.isfinite(gradient)):
        raise ValueError('matching finite point and gradient required')
    return float(np.max(abs(point-np.clip(point-gradient,-1.,1.))))


def fit(problem,start,*,max_evaluations=200):
    """One finite start with analytic derivatives and fresh endpoint checks.

    No retry, adaptive budget, hidden clipping, column deletion or presumed
    global optimum. max_evaluations is the residual-call allowance during
    optimization; fresh residual and Jacobian each have one reserved call.
    """
    if not isinstance(max_evaluations,int) or isinstance(max_evaluations,bool) or max_evaluations<1:
        raise ValueError('positive integer evaluation allowance required')
    calls=dict(residual=0,jacobian=0);ceiling=2*max_evaluations+2
    def counted(kind,point):
        if sum(calls.values())>=ceiling:raise RuntimeError('mathematical call allowance exhausted')
        calls[kind]+=1
        return getattr(problem,kind)(point)
    result=least_squares(lambda x:counted('residual',x),start,
        jac=lambda x:counted('jacobian',x),bounds=(-np.ones(7),np.ones(7)),
        method='trf',x_scale=1.,ftol=1e-12,xtol=1e-12,gtol=2*np.finfo(float).eps,
        max_nfev=max_evaluations)
    residual=counted('residual',result.x);jacobian=counted('jacobian',result.x)
    gradient=jacobian.T@residual;stop=stationarity(result.x,gradient)
    return dict(point=result.x.tolist(),physical_point=(result.x*problem.limits).tolist(),
        residual_mps2=residual.tolist(),rms_mps2=float(np.linalg.norm(residual)/np.sqrt(len(residual))),
        cost=float(residual@residual/2),solver_status=int(result.status),message=result.message,
        stationarity=stop,passed=bool(result.success and stop<=1e-8),
        active_bounds=[int(i) for i in np.flatnonzero(abs(result.x)>=1.-1e-7)],
        residual_calls=calls['residual'],jacobian_calls=calls['jacobian'],calls=sum(calls.values()),
        maximum_calls=ceiling,fresh_endpoint_checked=True,global_optimum_established=False,
        observed_starts=0,scientific_decision='abstain')
