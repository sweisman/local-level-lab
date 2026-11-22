# SPDX-License-Identifier: AGPL-3.0-or-later
"""Directional support of a box and an affine earlier squared-loss constraint."""

import math


def support(design, residual, objective, lower, upper, *, budget):
    """Return a feasible witness and a convex upper bound for one contrast."""
    import numpy as np
    from scipy.optimize import minimize

    design, residual, objective, lower, upper = (np.asarray(v, float) for v in
                                               (design, residual, objective, lower, upper))
    if (objective.ndim != 1 or residual.ndim != 1 or not len(objective)
            or design.shape != (len(residual), len(objective))
            or lower.shape != objective.shape or upper.shape != objective.shape
            or np.any(lower > 0) or np.any(upper < 0) or np.any(lower > upper)
            or not math.isfinite(budget) or budget <= 0
            or any(not np.all(np.isfinite(v)) for v in (design, residual, objective, lower, upper))):
        raise ValueError('finite aligned arrays, a box containing zero and positive budget required')
    first = 2*(residual @ design)

    def increase(point):
        v = design@point
        return float(first@point+v@v)

    def gradient(point):
        return first+2*(design.T@(design@point))

    magnitude = max(float(np.sum(np.abs(objective)*np.maximum(-lower, upper))), 1e-12)
    origin = np.zeros_like(objective)
    fit = minimize(lambda x: -float(objective@x)/magnitude, origin, method='SLSQP',
                   jac=lambda x: -objective/magnitude, bounds=list(zip(lower, upper)),
                   constraints=[dict(type='ineq', fun=lambda x: (budget-increase(x))/budget,
                                     jac=lambda x: -gradient(x)/budget)],
                   options=dict(maxiter=200, ftol=1e-12))
    trial = np.clip(fit.x, lower, upper) if np.all(np.isfinite(fit.x)) else origin
    if increase(trial) > budget:
        lo, hi = 0., 1.
        for _ in range(50):
            mid = (lo+hi)/2
            if increase(mid*trial) <= budget:
                lo = mid
            else:
                hi = mid
        trial *= lo
    if objective@trial < 0 or increase(trial) > budget:
        trial = origin
    cost = increase(trial)
    achieved = float(objective@trial)
    normal = gradient(trial)
    # Convexity bounds the exact affine-loss feasible set by the tangent
    # half-space at trial. Minimize its box support bound over lambda >= 0.
    positive = (normal != 0) & (np.sign(objective) == np.sign(normal))
    candidates = [0., *(objective[positive]/normal[positive])]
    certified = math.inf
    for multiplier in candidates:
        if not math.isfinite(multiplier):
            continue
        tilt = objective-multiplier*normal
        lift = np.maximum(tilt*(lower-trial), tilt*(upper-trial))
        upper_estimate = achieved+multiplier*max(0., budget-cost)+float(lift.sum())
        roundoff = (64*np.finfo(float).eps*max(design.shape)
                    * (1+abs(achieved)+float(abs(lift).sum())+abs(multiplier)*
                       (budget+abs(cost)+float(abs(normal)@np.maximum(-lower, upper)))))
        certified = min(certified, upper_estimate+roundoff)
    return dict(point=trial.tolist(), loss_increase=cost, achieved=achieved,
                upper_bound=max(achieved, certified), solver_success=bool(fit.success),
                iterations=int(fit.nit))
