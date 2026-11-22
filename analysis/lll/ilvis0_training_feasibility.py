# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propose separating certificates for a calibration box and earlier loss ball."""

import numpy as np

from .ilvis0_affine_support import linear_proposal


def static_proposal(lower, upper, rows, limits):
    """Minimize one common slack in normalized inequalities."""
    rows, limits = np.asarray(rows,float), np.asarray(limits,float)
    scale = np.maximum(1e-20,np.maximum(np.max(abs(rows),axis=1),abs(limits)))
    a, b = rows/scale[:,None], limits/scale
    midpoint = (lower+upper)/2
    cap = max(0.,float(np.max(a@midpoint-b)))+1.
    fit = linear_proposal(np.r_[lower,0.],np.r_[upper,cap],np.c_[a,-np.ones(len(a))],
                          b,np.r_[np.zeros(len(lower)),-1.])
    if fit is None:
        return midpoint,np.zeros(len(rows)),None
    point, weights = fit
    return point[:-1],weights/scale,float(point[-1])


def loss_proposal(design, residual, lower, upper, rows, limits, start, *, iterations):
    """Propose a direction from minimum loss, with independent LP weights."""
    from scipy.optimize import minimize

    rows, limits = np.asarray(rows,float), np.asarray(limits,float)
    scale = np.maximum(1e-20,np.maximum(np.max(abs(rows),axis=1),abs(limits)))
    a, b = rows/scale[:,None], limits/scale
    compressed = np.linalg.qr(np.c_[residual,design],mode='r')
    r, d = compressed[:,0], compressed[:,1:]
    start = np.clip(start,lower,upper)
    magnitude = max(1.,float(np.linalg.norm(r+d@start)))

    def cost(x):
        value = (r+d@x)/magnitude
        return value@value

    result = minimize(cost,start,method='SLSQP',
        jac=lambda x: 2*(d.T@((r+d@x)/magnitude))/magnitude,
        bounds=list(zip(lower,upper,strict=True)),
        constraints=[dict(type='ineq',fun=lambda x:b-a@x,jac=lambda _:-a)],
        options=dict(maxiter=iterations,ftol=1e-12))
    point = np.clip(result.x,lower,upper)
    residual_at_point = residual+design@point
    norm = float(np.linalg.norm(residual_at_point))
    direction = residual_at_point/max(1.,norm)
    objective = -design.T@direction
    objective_scale = max(1.,float(np.max(abs(objective))))
    support = linear_proposal(lower,upper,a,b,objective/objective_scale)
    weights = (support[1]*objective_scale/scale if support is not None else np.zeros(len(rows)))
    return dict(direction=direction,weights=weights,proposed_norm=norm,point=point,
                success=bool(result.success),iterations=int(result.nit),tangent_proposed=support is not None)
