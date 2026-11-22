# SPDX-License-Identifier: AGPL-3.0-or-later
"""Proposal and certificate for a loss ball with static calibration cuts."""

from fractions import Fraction as F

import numpy as np

from .ilvis0_affine_support import linear_proposal
from .ilvis0_linked_training_support import training_upper
from .ilvis0_saved_prediction_audit import endpoint


def translate_rows(rows, bounds, center):
    """Translate cuts on absolute parameters to displacements from the fit."""
    center = tuple(map(F, center))
    return [endpoint(F(b)-sum(F(a)*c for a, c in zip(row, center, strict=True)), True)
            for row, b in zip(rows, bounds, strict=True)]


def propose(design, residual, lower, upper, objective, static, static_upper, *,
            radius, iterations, seed):
    """Generate loss-ball cuts in floating point and return proposal weights."""
    cuts, limits = list(static), list(static_upper)
    vectors = []
    candidate = np.asarray(seed, float)
    best = dict(approximate_upper=float('inf'), direction=np.zeros_like(residual),
                weights=np.zeros(len(static)), iterations=0)
    for _ in range(iterations):
        row = design.T @ candidate
        scale = max(1., np.max(abs(row)))
        vectors.append(candidate/scale)
        cuts.append(row/scale)
        limits.append((radius*np.linalg.norm(candidate)-residual@candidate)/scale)
        fit = linear_proposal(lower, upper, cuts, limits, objective)
        if fit is None:
            break
        x, dual = fit
        norm_direction = np.asarray(vectors).T @ dual[len(static):]
        weights = dual[:len(static)]
        # Bound proposal quality after combining the norm directions. The
        # certificate will rebuild this bound using exact coefficient intervals.
        remaining = objective - np.asarray(static).T@weights - design.T@norm_direction
        score = (radius*np.linalg.norm(norm_direction) - residual@norm_direction
                 + np.asarray(static_upper)@weights
                 + np.maximum(remaining*lower, remaining*upper).sum())
        if score < best['approximate_upper']:
            best.update(approximate_upper=float(score), direction=norm_direction, weights=weights)
        best['iterations'] += 1
        candidate = residual + design@np.clip(x, lower, upper)
        if np.linalg.norm(candidate) <= radius:
            break
    return best


def direct_proposal(design, residual, lower, upper, objective, static, static_upper, *,
                    radius, start, iterations, scaled_tangent=False):
    """Solve the full loss constraint, then propose dual weights at its tangent."""
    from scipy.optimize import minimize

    rows, limits = np.asarray(static, float), np.asarray(static_upper, float)
    row_scale = np.maximum(1e-12, np.maximum(np.max(abs(rows), axis=1), abs(limits)))
    scaled_rows, scaled_limits = rows/row_scale[:, None], limits/row_scale
    # Compress the least-squares norm to the design's column space.
    # This affects the proposal only. The certificate uses the archived factors.
    compressed = np.linalg.qr(np.c_[residual, design], mode='r')
    base, matrix = compressed[:, 0], compressed[:, 1:]
    linear = base@matrix
    original = np.linalg.norm(residual)
    increase = (radius-original)*(radius+original)
    scale = max(1., increase)
    score_scale = max(np.linalg.norm(objective), 1e-12)

    def gap(point):
        change = matrix@point
        return (increase-2*linear@point-change@change)/scale

    fit = minimize(lambda x: -(objective@x)/score_scale, start, method='SLSQP',
        jac=lambda _: -objective/score_scale, bounds=list(zip(lower, upper, strict=True)),
        constraints=[dict(type='ineq', fun=gap,
                          jac=lambda x: -2*(linear+matrix.T@(matrix@x))/scale),
                     dict(type='ineq', fun=lambda x: scaled_limits-scaled_rows@x,
                          jac=lambda _: -scaled_rows)],
        options=dict(maxiter=iterations, ftol=1e-11))
    point = np.clip(fit.x, lower, upper)
    tangent = tangent_proposal(design,residual,lower,upper,objective,rows,limits,
                               radius=radius,point=point,scaled=scaled_tangent)
    return dict(tangent,point=point,iterations=int(fit.nit),success=bool(fit.success),status=int(fit.status))


def tangent_proposal(design, residual, lower, upper, objective, rows, limits, *, radius, point, scaled=False):
    """Propose a support at a fixed residual direction, with optional LP row scaling."""
    rows, limits = np.asarray(rows,float), np.asarray(limits,float)
    row_scale = (np.maximum(1e-20,np.maximum(np.max(abs(rows),axis=1),abs(limits)))
                 if scaled else np.ones(len(rows)))
    objective_scale = max(1.,float(np.max(abs(objective)))) if scaled else 1.
    vector = residual+design@point
    tangent = design.T@vector
    normalization = max(1., np.max(abs(tangent)))
    support = linear_proposal(lower,upper,[*(rows/row_scale[:,None]),tangent/normalization],
        [*(limits/row_scale),(radius*np.linalg.norm(vector)-residual@vector)/normalization],
        objective/objective_scale)
    if support is None:
        direction, weights = np.zeros_like(residual), np.zeros(len(rows))
    else:
        dual = support[1]
        direction = (dual[-1]*objective_scale/normalization)*vector
        weights = dual[:-1]*objective_scale/row_scale
    return dict(direction=direction,weights=weights,tangent_proposed=support is not None)


def certify(residual, direction, training, objective, lower, upper,
            static, static_upper, weights, *, increase, unshared):
    """Check dual numbers using only outward coefficients and exact arithmetic."""
    weights = tuple(map(F, weights))
    if any(weight<0 for weight in weights) or len(weights)!=len(static):
        raise ValueError('nonnegative weight for every static inequality required')
    result = training_upper(residual, direction, increase=increase, unshared=unshared)
    result += sum(weight*F(bound) for weight, bound in zip(weights, static_upper, strict=True))
    for i, (lo, hi, (a, b), (c, d)) in enumerate(zip(lower, upper, training, objective, strict=True)):
        if lo>hi or a>b or c>d:
            raise ValueError('ordered interval coefficients and box required')
        shift = sum(weight*F(row[i]) for weight, row in zip(weights, static, strict=True) if weight)
        left, right = c-b-shift, d-a-shift
        result += max(F(x)*v for x in (lo, hi) for v in (left, right))
    return result
