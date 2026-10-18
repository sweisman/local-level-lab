# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate affine-solver candidate; full nonlinear acceptance gates stay fixed."""
import numpy as np
from scipy.optimize import lsq_linear
from . import ilvis0_representable_boundary as prior

VERSION='ilvis0-scaled-affine-branch-v1'
LINEAR_STATIONARITY=1e-8
bracket=prior.bracket
probe_geometry=prior.probe_geometry


def scaled_lsq(a,b,*,bounds,method,tol,max_iter):
    a,b=np.asarray(a,float),np.asarray(b,float)
    lower,upper=(np.asarray(v,float) for v in bounds)
    if (a.ndim!=2 or b.ndim!=1 or not a.size or a.shape[0]!=len(b)
            or lower.shape!=(a.shape[1],) or upper.shape!=lower.shape
            or any(not np.all(np.isfinite(v)) for v in (a,b,lower,upper))
            or np.any(lower>=upper) or method!='bvls' or tol!=1e-10 or max_iter!=100):
        raise ValueError('finite compatible frozen affine box and budget required')
    scale=np.maximum(abs(lower),abs(upper))
    result=lsq_linear(a*scale,b,bounds=(lower/scale,upper/scale),method='bvls',
        tol=tol,max_iter=max_iter)
    point=np.clip(result.x*scale,lower,upper)
    residual=a@point-b;gradient=a.T@residual;projected=gradient.copy()
    tolerance=1e-6*scale
    projected[(point<=lower+tolerance)&(gradient>0)]=0.
    projected[(point>=upper-tolerance)&(gradient<0)]=0.
    stationarity=float(max(abs(projected*scale)/(np.maximum(np.linalg.norm(a*scale,axis=0),1.)*max(np.linalg.norm(residual),1.))))
    reference=np.clip(np.zeros(a.shape[1]),lower,upper)
    extended=a.astype(np.longdouble);target=b.astype(np.longdouble)
    old=extended@reference.astype(np.longdouble)-target;new=extended@point.astype(np.longdouble)-target
    old_cost=float(old@old);cost=float(new@new)
    reference_passed=cost<=old_cost+64*np.finfo(float).eps*max(old_cost,1.)
    result.x=point
    result.success=bool(result.success and reference_passed and stationarity<=LINEAR_STATIONARITY)
    result.affine_reference_passed=bool(reference_passed)
    result.affine_stationarity=stationarity
    result.affine_reference_cost=old_cost
    result.affine_cost=cost
    result.affine_solver_version=VERSION
    return result


def build_candidate():
    helper=prior.build_candidate()
    helper.adapter.stopping.lsq_linear=scaled_lsq
    helper.adapter.stopping.POLICY.update(affine_solver=VERSION,linear_stationarity_tolerance=LINEAR_STATIONARITY)
    return helper


def check_endpoint(*args,**kwargs):
    result=build_candidate().check_endpoint(*args,**kwargs)
    result.update(scaled_affine_version=VERSION,physical_bounds_changed=False,scientific_stopping_limits_changed=False)
    return result
