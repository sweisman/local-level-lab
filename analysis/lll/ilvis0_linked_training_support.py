# SPDX-License-Identifier: AGPL-3.0-or-later
"""Directional bounds with physical and shared errors in one training constraint."""

from fractions import Fraction

import numpy as np
from scipy.optimize import minimize

from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint


def propose_point(design, residual, objective, lower, upper, radius):
    """Suggest a point whose score and feasibility require separate checks."""
    baseline = residual @ residual
    ceiling = (radius - np.sqrt(baseline)) * (radius + np.sqrt(baseline))
    linear = residual @ design
    recent = max(float(ceiling), 1e-12)
    scale = max(np.linalg.norm(objective), 1e-12)

    def gap(point):
        change = design @ point
        return (ceiling - 2 * linear @ point - change @ change) / recent

    result = minimize(
        lambda x: -(objective @ x) / scale, np.zeros(len(objective)),
        method='SLSQP', jac=lambda _: -objective / scale,
        bounds=list(zip(lower, upper, strict=True)),
        constraints=[dict(type='ineq', fun=gap,
                          jac=lambda x: -2 * (linear + design.T @ (design @ x)) / recent)],
        options=dict(maxiter=200, ftol=1e-10),
    )
    return np.clip(result.x, lower, upper), bool(result.success)


def propose_direction(design, residual, objective, lower, upper, radius):
    """Suggest a dual direction. Its quality has no bearing on validity."""
    point, success = propose_point(design, residual, objective, lower, upper, radius)
    return residual + design @ point, success


def training_upper(residual, direction, *, increase, unshared):
    """Right side of the necessary projected training inequality."""
    residual, direction = (tuple(map(Fraction, values)) for values in (residual, direction))
    increase, unshared = Fraction(increase), Fraction(unshared)
    if len(residual) != len(direction) or increase <= 0 or unshared < 0:
        raise ValueError('aligned training vectors and finite nonnegative budgets required')
    radius = Fraction(sqrt_upper(sum(v*v for v in residual) + increase)) + unshared
    bound = radius * Fraction(sqrt_upper(sum(v*v for v in direction)))
    return bound - sum(x*y for x, y in zip(residual, direction, strict=True))


def support(residual, direction, training, objective, lower, upper, *, increase, unshared):
    """Tighten an outward bound by checking its piecewise linear breakpoints.

    Training and objective coefficients are supplied as exact intervals. For
    any nonnegative multiplier, apply the projected training inequality and
    maximize the remaining linear form over the box.
    """
    bound = training_upper(residual, direction, increase=increase, unshared=unshared)
    lower, upper = (tuple(map(Fraction, values)) for values in (lower, upper))
    lines = []
    candidates = {Fraction(0)}
    for lo, hi, (a, b), (c, d) in zip(lower, upper, training, objective, strict=True):
        if not lo <= 0 <= hi or a > b or c > d:
            raise ValueError('ordered interval coefficients and box containing zero required')
        left, right = lo*c, hi*d
        left_slope, right_slope = -lo*b, -hi*a
        lines.append((left, right, left_slope, right_slope))
        if left_slope != right_slope:
            crossing = (right - left) / (left_slope - right_slope)
            if crossing > 0:
                candidates.add(crossing)

    def upper_at(multiplier):
        return multiplier * bound + sum(
            max(left + multiplier*left_slope, right + multiplier*right_slope)
            for left, right, left_slope, right_slope in lines
        )

    exact, multiplier = min((upper_at(value), value) for value in candidates)
    return dict(upper=endpoint(exact, True), exact_upper=str(exact),
                box_upper=endpoint(upper_at(0), True), multiplier=str(multiplier))


def split_support(training, objective, lower, upper, *, multiplier, bound, shared_start):
    """Keep the final shared coefficients together for a physical support calculation."""
    multiplier = Fraction(multiplier)
    if multiplier < 0 or not 0 < shared_start < len(lower):
        raise ValueError('nonnegative multiplier and nonempty shared block required')
    box = multiplier * Fraction(bound)
    shared = []
    for index, (lo, hi, (a, b), (c, d)) in enumerate(
            zip(lower, upper, training, objective, strict=True)):
        left, right = c - multiplier*b, d - multiplier*a
        if not lo <= 0 <= hi or a > b or c > d:
            raise ValueError('ordered interval coefficients and box containing zero required')
        if index < shared_start:
            box += max(Fraction(lo)*left, Fraction(hi)*right)
        else:
            if lo != -1 or hi != 1:
                raise ValueError('normalized shared coefficients must have unit box bounds')
            shared.append((left, right))
    return box, shared
