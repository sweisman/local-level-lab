# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded numerical proposals for affine constraints with a full residual ball."""

import math
from fractions import Fraction as F


class EvaluationLimit(Exception):
    """Return the best evaluated point when its fixed allowance is used."""


def projected_loss_budget(residual, fixed_direction, columns, lower, upper, *, increase):
    """Subtract energy guaranteed along one measured residual direction."""
    vector = tuple(map(F, fixed_direction))
    norm_squared = sum(value*value for value in vector)
    if not norm_squared or F(increase) <= 0:
        raise ValueError('nonzero direction and positive loss allowance required')
    offset = sum(F(r)*w for r, w in zip(residual, vector, strict=True))
    left = right = offset
    intervals = [tuple(map(F, interval)) for interval in columns]
    for (a, b), lo, hi in zip(intervals, lower, upper, strict=True):
        lo, hi = F(lo), F(hi)
        if a > b or lo > hi:
            raise ValueError('ordered parameter and projection bounds required')
        products = (a*lo, a*hi, b*lo, b*hi)
        left += min(products)
        right += max(products)
    guaranteed = max(F(0), left, -right)**2/norm_squared
    total = sum(F(value)**2 for value in residual)+F(increase)
    return dict(direction=vector, norm_squared=norm_squared, columns=intervals, offset=offset,
                fixed_range=(left, right), guaranteed=guaranteed, squared=total-guaranteed)


def projected_loss_row(residual, direction, columns, budget):
    """Bound a direction orthogonal to the already budgeted residual energy."""
    from .ilvis0_exact_scale import sqrt_upper

    vector = tuple(map(F, direction))
    if budget['squared'] < 0:
        raise ValueError('the certified lower energy excludes the box')
    fixed_dot = sum(a*b for a, b in zip(vector, budget['direction'], strict=True))
    factor = fixed_dot/budget['norm_squared']
    norm = sum(a*a for a in vector)-factor*fixed_dot
    shifted = []
    for (lo, hi), (a, b) in zip(columns, budget['columns'], strict=True):
        a, b = factor*a, factor*b
        shifted.append((F(lo)-max(a, b), F(hi)-min(a, b)))
    offset = sum(F(r)*a for r, a in zip(residual, vector, strict=True))-factor*budget['offset']
    return shifted, F(sqrt_upper(norm*budget['squared']))-offset


def full_loss_proposals(lower, upper, rows, limits, objective, residual, design, loss_limit, *,
                        maximum, reserve=lambda: None, check_continue=lambda: None):
    """Propose a minimum-loss and a maximum-score point, with no claim of proof."""
    import numpy as np
    from scipy.optimize import minimize

    lo, hi, matrix, limits, c, r, design = (np.asarray(a, float) for a in
                                           (lower, upper, rows, limits, objective, residual, design))
    if (lo.ndim != 1 or hi.shape != lo.shape or c.shape != lo.shape or np.any(lo > hi)
            or matrix.ndim != 2 or matrix.shape[1] != len(lo) or limits.shape != (len(matrix),)
            or r.ndim != 1 or not len(r) or design.shape != (len(r), len(lo))
            or any(not np.isfinite(a).all() for a in (lo, hi, matrix, limits, c, r, design))
            or not math.isfinite(loss_limit) or loss_limit < 0. or type(maximum) is not int or maximum < 1):
        raise ValueError('finite aligned constraints and bounded proposal work required')
    width = (hi-lo)/2.
    center = lo+width
    active = width > 0.
    a = matrix[:, active]*width[active]
    b = limits-matrix@center
    clip_bounds = [(-1., 1.)]*int(active.sum())
    row_scale = np.maximum(1e-20, np.maximum(abs(b), np.max(abs(a), axis=1, initial=0.)))
    a, b = a/row_scale[:, None], b/row_scale
    origin = r+design@center
    tangent = design[:, active]*width[active]
    loss_scale = max(1., loss_limit)
    score = c[active]*width[active]
    score /= max(1., float(np.max(abs(score), initial=0.)))

    def expand(z):
        full = center.copy()
        full[active] += z*width[active]
        return np.clip(full, lo, hi)

    def solve(z0, *, maximize):
        reserve()
        previous, best, count = None, None, 0

        def at(z):
            nonlocal previous, best, count
            if previous is not None and np.array_equal(z, previous[0]):
                return previous[1:]
            if count >= maximum:
                raise EvaluationLimit
            check_continue()
            count += 1
            e = origin+tangent@z
            loss, gradient = float(e@e), 2.*(tangent.T@e)
            if not math.isfinite(loss) or not np.isfinite(gradient).all():
                raise ValueError('nonfinite affine residual proposal')
            linear_error = max(0., float(np.max(a@z-b, initial=0.))-1e-9)
            violation = max(linear_error, (loss-loss_limit)/loss_scale-1e-9) if maximize else linear_error
            key = (violation, -float(score@z) if maximize else loss)
            if best is None or key < best[0]:
                best = key, z.copy(), loss
            previous = z.copy(), loss, gradient
            return loss, gradient

        def affine(z):
            return b-a@z

        constraints = [dict(type='ineq', fun=affine, jac=lambda _: -a)] if len(a) else []
        if maximize:
            constraints.append(dict(type='ineq', fun=lambda z: (loss_limit-at(z)[0])/loss_scale,
                                    jac=lambda z: -at(z)[1]/loss_scale))
        at(z0)
        status = 'fixed_box'
        if clip_bounds:
            try:
                function = (lambda z: -float(score@z)) if maximize else (lambda z: at(z)[0]/loss_scale)
                jac = (lambda _: -score) if maximize else (lambda z: at(z)[1]/loss_scale)
                result = minimize(function, z0, jac=jac, method='SLSQP', bounds=clip_bounds,
                                  constraints=constraints, options=dict(maxiter=maximum+1, ftol=1e-12))
                at(result.x)
                status = int(result.status)
            except EvaluationLimit:
                status = 'evaluation_limit'
        _, point, loss = best
        return point, dict(point=expand(point).tolist(), loss=loss, evaluations=count, status=status)

    center_proposal, near = solve(np.zeros(len(score)), maximize=False)
    _, best = solve(center_proposal, maximize=True)
    return dict(min_loss=near, max_score=best)
