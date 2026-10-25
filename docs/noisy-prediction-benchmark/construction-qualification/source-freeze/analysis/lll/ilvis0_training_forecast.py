# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only setup and counted fitting for retrospective prediction studies."""
import math

import numpy as np


def initialize_training(times,gps,*,theta,dv,dt,model,maximum_interval_s,clock):
    """Initialize from explicitly supplied training observations, never fused data.

    The historical initializer supplies coordinates, speed and effective rotation.
    Its fixed-period force magnitude is replaced by summed increments / duration.
    The initial force direction is unchanged. This is initialization, not a new
    independent attitude measurement or an instrument calibration claim.
    """
    from .ilvis0_corpus_modeling import initialize
    from .ilvis0_exploratory import MODELS
    t,g,dv,theta,dt=(np.asarray(v,dtype=float) for v in (times,gps,dv,theta,dt))
    if (t.ndim!=1 or len(t)<2 or g.shape!=(len(t),3) or dt.ndim!=1 or not len(dt)
            or theta.shape!=(len(dt),3) or dv.shape!=(len(dt),3)
            or any(not np.all(np.isfinite(v)) for v in (t,g,dv,theta,dt))
            or np.any(np.diff(t)<=0) or t[0]<0 or np.count_nonzero(t<=t[0]+10)<2
            or model not in MODELS or clock not in ('header_elapsed','nominal_200Hz')
            or not math.isfinite(maximum_interval_s) or maximum_interval_s<=0
            or np.any(dt<=0) or np.any(dt>maximum_interval_s)
            or (clock=='nominal_200Hz' and not np.all(dt==.005))
            or t[-1]>np.sum(dt) or np.any(abs(g[:,0])>=math.pi/2-1e-6)):
        raise ValueError('finite supported training-only receiver and IMU observations required')
    count=min(2000,len(dt));force=np.sum(dv[:count],axis=0)/np.sum(dt[:count])
    gravity=float(np.linalg.norm(force))
    if not gravity>0:raise ValueError('nonzero initial specific force required')
    values=np.zeros((len(dt),15));values[:,2]=dt;values[:,12:15]=dv
    initial,_=initialize(t,g,values,model)
    return initial,gravity


def training_problem(times,gps,*,theta,dv,dt,covariance,model,limits,profile,clock,
                     maximum_interval_s,kernel,tangent_kernel,radius_m=6371000.):
    """Create a problem whose receiver arrays contain training observations only."""
    from .ilvis0_shape import TangentProblem
    from .ilvis0_estimator import Bounds
    initial,gravity=initialize_training(times,gps,theta=theta,dv=dv,dt=dt,model=model,
        maximum_interval_s=maximum_interval_s,clock=clock)
    return TangentProblem(theta,dv,dt,times,gps,covariance,initial,Bounds(limits),
        tangent_kernel=tangent_kernel,kernel=kernel,fit_earth_removal=profile,
        clock_hypothesis=clock,processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=maximum_interval_s,gravity_mps2=gravity,disc_radius_m=radius_m)


def fit_training(problem,model,*,start,maximum_evaluations,reserve,stopping='ordinary'):
    """Use the existing solver; reserve every real tangent before execution.

    A study owns start identities and their limits. This adapter does not retry,
    inspect withheld positions or alter the historical solver's stopping checks.
    """
    from .ilvis0_shape import TangentProblem
    if stopping=='ordinary':
        from .ilvis0_solver_trust_v2 import fit_candidate
    elif stopping=='near_zero':
        from .ilvis0_near_zero import fit_candidate
    else:raise ValueError('explicit ordinary or near_zero stopping policy required')
    if not isinstance(problem,TangentProblem) or not callable(reserve):
        raise ValueError('native training problem and reservation callback required')
    class Counted:
        calls=0
        def __getattr__(self,name):return getattr(problem,name)
        def residual_tangent(self,point,candidate):
            reserve(native_calls=1,packet_visits=len(problem.dt)*len(problem.gps_times))
            self.calls+=1
            return problem.residual_tangent(point,candidate)
    counted=Counted()
    fit=fit_candidate(counted,model,start=start,maximum_evaluations=maximum_evaluations)
    if counted.calls!=fit['evaluations']:raise ValueError('native evaluation accounting mismatch')
    fit.update(prediction_receiver_positions_used_in_training=False,
        forecast_spread_is_confidence_interval=False)
    return fit


def primary_index(fits):
    """Smallest converged training cost; exact ties retain declared start order."""
    eligible=[]
    for i,fit in enumerate(fits):
        if fit['converged']:
            cost=fit['residual_sum_squares']
            if not isinstance(cost,(int,float)) or not math.isfinite(cost) or cost<0:
                raise ValueError('finite nonnegative training cost required')
            eligible.append((cost,i))
    return min(eligible)[1] if eligible else None
