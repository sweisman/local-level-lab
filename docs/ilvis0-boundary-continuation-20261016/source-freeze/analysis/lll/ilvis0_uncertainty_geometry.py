# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research diagnostics for nonlinear/bounded uncertainty, never confidence sets.

Consumes supplied predictions, derivatives and costs; performs no integration or
optimization. Bound parameters remain in the full Jacobian. Finite grid support
does not establish continuous extrema, a global optimum or confidence coverage.
"""
import math

import numpy as np
from scipy.linalg import solve_triangular

from . import ilvis0_error_model as error

VERSION='ilvis0-uncertainty-geometry-controls-v1'


def bounds(lower,upper):
    lo=np.asarray(lower,dtype=float);hi=np.asarray(upper,dtype=float)
    if (lo.ndim!=1 or not len(lo) or hi.shape!=lo.shape or not np.all(np.isfinite(lo))
            or not np.all(np.isfinite(hi)) or np.any(hi<=lo)):
        raise ValueError('finite ordered parameter bounds required')
    return lo,hi


def points(values,lo,hi):
    p=np.asarray(values,dtype=float)
    if (p.ndim!=2 or not len(p) or p.shape[1]!=len(lo) or not np.all(np.isfinite(p))
            or np.any(p<lo) or np.any(p>hi)):
        raise ValueError('finite feasible parameter probes required; no clipping')
    return p


def predictions(values,n):
    p=np.asarray(values,dtype=float)
    if p.ndim!=2 or p.shape[0]!=n or not p.shape[1] or not np.all(np.isfinite(p)):
        raise ValueError('aligned finite predictions required')
    return p


def assess(center,lower,upper,jacobian,covariance,probe_parameters,probe_predictions,
        center_prediction,relative_rank_cutoff=1e-10):
    lo,hi=bounds(lower,upper);span=hi-lo
    center=np.asarray(center,dtype=float)
    if center.shape!=lo.shape:raise ValueError('aligned center required')
    points(center[None,:],lo,hi)
    probes=points(probe_parameters,lo,hi);values=predictions(probe_predictions,len(probes))
    f=np.asarray(center_prediction,dtype=float);j=np.asarray(jacobian,dtype=float)
    if f.shape!=(values.shape[1],) or not np.all(np.isfinite(f)) or j.shape!=(len(f),len(center)) or not np.all(np.isfinite(j)):
        raise ValueError('aligned finite derivatives and center prediction required')
    if not math.isfinite(relative_rank_cutoff) or not 0<relative_rank_cutoff<1:
        raise ValueError('relative rank cutoff must be between zero and one')
    lower_factor=error.factor(covariance)
    if len(lower_factor)!=len(f):raise ValueError('prediction/covariance dimensions disagree')
    displacement=(probes-center)/span
    center_rows=np.flatnonzero(np.all(abs(displacement)<=1e-12,axis=1))
    if not len(center_rows):raise ValueError('center must be included in probe ledger')
    difference=solve_triangular(lower_factor,(values[center_rows]-f).T,lower=True)
    if np.max(abs(difference))>1e-10:raise ValueError('center prediction disagrees with probe ledger')
    whitened=solve_triangular(lower_factor,j,lower=True)*span
    _,s,v=np.linalg.svd(whitened,full_matrices=False)
    cutoff=relative_rank_cutoff*s[0] if len(s) else 0.
    rank=int(np.sum(s>cutoff));p=len(center)
    active=[]
    for k in range(p):
        if (center[k]-lo[k])/span[k]<=1e-8:active.append(dict(parameter=k,side='lower'))
        if (hi[k]-center[k])/span[k]<=1e-8:active.append(dict(parameter=k,side='upper'))
    cov=None;distance=None
    if rank==p:
        inverse=span[:,None]*(v.T/s)
        cov=inverse@inverse.T
        distance=float(np.min(np.minimum(center-lo,hi-center)/np.sqrt(np.diag(cov))))
    remainder=values-f-(probes-center)@j.T
    wr=solve_triangular(lower_factor,remainder.T,lower=True).T
    return dict(version=VERSION,rank=rank,parameters=p,unidentifiable_dimensions=p-rank,
        relative_rank_cutoff=relative_rank_cutoff,active_bounds=active,
        unconstrained_local_covariance=None if cov is None else cov.tolist(),
        minimum_bound_distance_in_local_sd=distance,
        local_gaussian_boundary_compatible=not active and rank==p,
        maximum_whitened_remainder=float(np.max(np.linalg.norm(wr,axis=1))),
        probe_count=len(probes),probed_parameter_rank=int(np.linalg.matrix_rank(displacement,tol=relative_rank_cutoff)),
        confidence_calibrated=False,scientific_decision='abstain')


def grid_support(parameter_points,costs,future_predictions,lower,upper,*,cost_allowance):
    """Descriptive sampled support; caller supplies allowance, never a default test."""
    lo,hi=bounds(lower,upper);probes=points(parameter_points,lo,hi)
    values=predictions(future_predictions,len(probes));cost=np.asarray(costs,dtype=float)
    if cost.shape!=(len(probes),) or not np.all(np.isfinite(cost)) or np.any(cost<0):
        raise ValueError('aligned finite nonnegative costs required')
    if not math.isfinite(cost_allowance) or cost_allowance<0:
        raise ValueError('explicit finite nonnegative cost allowance required')
    minimum=float(np.min(cost));accepted=np.flatnonzero(cost-minimum<=cost_allowance)
    return dict(version=VERSION,accepted_indices=accepted.tolist(),grid_minimum_cost=minimum,
        cost_allowance=float(cost_allowance),prediction_minimum=np.min(values[accepted],axis=0).tolist(),
        prediction_maximum=np.max(values[accepted],axis=0).tolist(),
        sampled_support_only=True,continuous_extrema_established=False,
        confidence_calibrated=False,scientific_decision='abstain')
