# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded proposals with shared calibration derived from physical coordinates."""

import numpy as np


class _ProposalLimit(Exception):
    pass


def propose(design, residual, objective, center, lower, upper, start, *,
            values, derivative, radius, iterations, evaluations):
    """Search the linked map. A returned point still needs an independent check."""
    from scipy.optimize import minimize

    center, lower, upper, start = (np.asarray(v,float) for v in (center,lower,upper,start))
    width = np.maximum(center-lower,upper-center)
    n = len(center)
    if (design.shape[0]<n or np.any(width<=0) or min(iterations,evaluations)<1):
        raise ValueError('full training design, nonzero physical ranges and positive limits required')
    compressed = np.linalg.qr(np.c_[residual,design],mode='r')
    r, d = compressed[:,0], compressed[:,1:]
    _, singular, rotation = np.linalg.svd(d[:,:n]*width,full_matrices=False)
    preconditioner = (width[:,None]*rotation.T)/np.maximum(singular,1e-3)
    inverse = np.maximum(singular,1e-3)[:,None]*rotation/width
    box_matrix = preconditioner/width[:,None]
    lo, hi = (lower-center)/width,(upper-center)/width
    goal_scale = max(1.,float(np.linalg.norm(objective)))
    baseline = np.linalg.norm(residual)
    margin = (radius+baseline)*(radius-baseline)
    loss_scale = max(1.,margin)
    calls = 0
    cache_x = None
    cache = None
    best = None

    def model(z):
        nonlocal cache, cache_x, calls, best
        if cache_x is not None and np.array_equal(z,cache_x):
            return cache
        if calls>=evaluations:
            raise _ProposalLimit
        calls += 1
        raw = center+preconditioner@z
        x = np.clip(raw,lower,upper)
        point = np.r_[x-center,values(x)]
        jac = np.vstack((np.eye(n),derivative(x)))@(
            preconditioner*((raw>=lower)&(raw<=upper))[:,None])
        change = d@point
        loss_gap = margin-(2*r+change)@change
        score = float(objective@point)
        cache = (x,score,loss_gap,objective@jac,-2*(r+change)@(d@jac))
        cache_x = np.array(z,copy=True)
        if loss_gap>=0. and (best is None or score>best[0]):
            best = score,x.copy()
        return cache

    def box_gap(z):
        value = box_matrix@z
        return np.r_[value-lo,hi-value]

    start = np.clip(start,lower,upper)
    seed = inverse@(start-center)
    success, status = False, 'evaluation_limit'
    try:
        fit = minimize(lambda z:-model(z)[1]/goal_scale,seed,method='SLSQP',
            jac=lambda z:-model(z)[3]/goal_scale,
            constraints=[dict(type='ineq',fun=lambda z:model(z)[2]/loss_scale,
                              jac=lambda z:model(z)[4]/loss_scale),
                         dict(type='ineq',fun=box_gap,jac=lambda _:np.r_[box_matrix,-box_matrix])],
            options=dict(maxiter=iterations,ftol=1e-11))
        final = np.clip(center+preconditioner@fit.x,lower,upper)
        success,status = bool(fit.success),str(fit.status)
    except _ProposalLimit:
        final = cache[0]
    return dict(point=final,best_approximate=None if best is None else best[1],
                success=success,status=status,evaluations=calls)
