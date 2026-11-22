# SPDX-License-Identifier: AGPL-3.0-or-later
"""Outward score range for a single linked static calibration map."""

from fractions import Fraction as F

from .ilvis0_coupled_map import _left_matrix
from .ilvis0_force_bounds import _Box
from .ilvis0_interval_calibration import Jet, exp_skew
from .ilvis0_saved_prediction_audit import endpoint


def _dot(weights, terms):
    return sum((Jet.cast(w)*v for w, v in zip(weights, terms, strict=True)), Jet.constant(0))


def _linked_expression(model, lower, upper, weights):
    ref = model.reference
    r, a, m = ref.parent, ref.acceleration, ref.transform
    c, limits = tuple(map(F, r.center)), tuple(map(F, r.limits))
    p0 = [v*t for v, t in zip(c, limits, strict=True)]
    x = [Jet.variable(lo, hi, j) for j, (lo, hi) in enumerate(zip(lower, upper, strict=True))]
    dx = [v-C for v, C in zip(x, c, strict=True)]
    step = [v*t for v, t in zip(dx, limits, strict=True)]
    rotation = _left_matrix(r.initial_r, exp_skew([x[j]*limits[j] for j in range(3)]))
    normalized = [w/F(cap) if cap else F(0) for w, cap in zip(weights[27:], model.caps, strict=True)]
    velocity, lever, square, cross, accel = [normalized[j:j+3] for j in range(0, 15, 3)]
    force_weight = [normalized[j:j+3] for j in (15, 18, 21)]
    clock = step[25]
    clock_weights = [s*clock.square()/2 + t*clock for s, t in zip(square, cross, strict=True)]
    accel_weights = [b+w for b, w in zip(accel, clock_weights, strict=True)]
    f0 = [F(value)/F(a.period)-p0[12+j] for j, value in enumerate(a.raw_delta_v)]
    result = _dot(weights[:27], dx) + _dot(velocity, step[3:6])*clock
    result += _dot(square, a.center)*clock.square()/2

    for i in range(3):
        lever_change = _dot(
            [rotation[i][j]-float(r._r_center[i,j]) for j in range(3)],
            [p0[21+j]+step[21+j] for j in range(3)],
        )
        lever_first = [F(float(jac[i] @ r._lever_center)) for jac in model.rotation_jacobian]
        result += lever[i]*(lever_change-_dot(lever_first, dx[:3]))

        # A = M(f0 - delta_bias) + gravity. Collect both appearances
        # of each M remainder before evaluating their product intervals.
        center_error = sum(F(m.center[i,j])*f0[j] for j in range(3))-F(a.center[i])
        if i == 2:
            center_error += F(a.gravity)+p0[24]
        slope = [sum(F(m.jacobian[i,j,k])*f0[j] for j in range(3)) for k in range(27)]
        for j in range(3):
            slope[12+j] -= F(m.center[i,j])*limits[12+j]
        if i == 2:
            slope[24] += limits[24]
        discrepancy = [w-F(v) for w, v in zip(slope, a.jacobian[i], strict=True)]
        result += accel_weights[i]*(center_error+_dot(discrepancy, dx))
        result += clock_weights[i]*_dot(a.jacobian[i], dx)
        for j in range(3):
            matrix = rotation[i][j]/(1+x[18+j]*limits[18+j])
            change = matrix-float(m.center[i,j])
            remainder = change-_dot(m.jacobian[i,j], dx)
            weight = (force_weight[i][j]+accel[i]*f0[j])+clock_weights[i]*f0[j]
            result += weight*remainder-accel_weights[i]*change*step[12+j]
    return result


def directional_bound(model, lower, upper, coefficients):
    """Enclose dot(c, [x-center, shared(x)]) for interval coefficients c.

    The normalized shared coordinates retain the original unit caps. The
    source map's declared numeric allowance still applies. This bounds the
    static representation and does not qualify the integration remainder.
    """
    r = model.reference.parent
    if (len(lower) != 27 or len(upper) != 27 or len(coefficients) != 51
            or any(not a <= lo <= hi <= b for a, lo, hi, b in
                   zip(r.lower, lower, upper, r.upper, strict=True))):
        raise ValueError('complete source-contained box and all 51 coefficient intervals required')
    pairs = [tuple(map(F, pair)) for pair in coefficients]
    if any(lo > hi for lo, hi in pairs):
        raise ValueError('ordered score coefficient intervals required')
    weights = [(lo+hi)/2 for lo, hi in pairs]
    radii = [(hi-lo)/2 for lo, hi in pairs]
    displacement = [max(abs(F(lo)-F(c)), abs(F(hi)-F(c))) for lo, hi, c in
                    zip(lower, upper, r.center, strict=True)]
    coefficient_error = sum(w*v for w, v in zip(radii[:27], displacement, strict=True))
    coefficient_error += sum(w for w, cap in zip(radii[27:], model.caps, strict=True) if cap)
    numeric_error = F(model.numerical_allowance)*sum(
        abs(w) for w, cap in zip(weights[27:], model.caps, strict=True) if cap)
    padding = coefficient_error + numeric_error

    value = _linked_expression(model, lower, upper, weights)
    midpoint = [float((F(lo)+F(hi))/2) for lo, hi in zip(lower, upper, strict=True)]
    at_midpoint = _linked_expression(model, midpoint, midpoint, weights).value
    left, right = F(at_midpoint.lo), F(at_midpoint.hi)
    for lo, hi, mid, gradient in zip(lower, upper, midpoint, value.derivative, strict=True):
        products = [F(g)*(F(v)-F(mid)) for g in (gradient.lo, gradient.hi) for v in (lo, hi)]
        left += min(products)
        right += max(products)
    return _Box(endpoint(max(left, F(value.value.lo))-padding, False),
                endpoint(min(right, F(value.value.hi))+padding, True))
