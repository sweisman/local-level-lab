# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recorded roundoff correction for coupled probes; physical bounds stay fixed."""
import numpy as np
from . import ilvis0_timing_probes as original

VERSION='ilvis0-fixed-timing-probes-v2'
STEPS_S=original.STEPS_S
MAXIMUM_BOUND_ROUNDOFF=4*np.finfo(float).eps


def inspect(problem,point,model,call,*,correction=None):
    point=np.asarray(point,float);adjustments=[]
    if correction is not None:
        correction=np.array(correction,float,copy=True)
        if (point.shape!=correction.shape or not np.all(np.isfinite(point))
                or not np.all(np.isfinite(correction)) or np.any(abs(point)>1)):
            raise ValueError('coupled center and correction must be finite and feasible')
        endpoint=point+correction
        if np.any(abs(endpoint)>1+MAXIMUM_BOUND_ROUNDOFF):
            raise ValueError('coupled perturbation must be feasible; material overshoot')
        for i in np.flatnonzero(abs(endpoint)>1):
            target=float(np.sign(endpoint[i]))
            adjustments.append(dict(parameter=problem.bounds.active[i],fraction=1.,
                computed_value=float(endpoint[i]),evaluated_value=target,
                normalized_adjustment=target-float(endpoint[i])))
            correction[i]=target-point[i]
    result=original.inspect(problem,point,model,call,correction=correction)
    result.update(version=VERSION,coupled_roundoff_adjustments=adjustments,
                  maximum_normalized_bound_roundoff=float(MAXIMUM_BOUND_ROUNDOFF))
    return result
