# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact support for a position contrast with integrated velocity errors."""

from fractions import Fraction as F


def integrated_error_weights(times, taps, *, axes):
    """Map position taps to initial offsets and interval-average velocities.

    Weights are intervals in time-major order. For each axis, an interval's
    coefficient is its duration times the sum of all subsequent position
    taps. An error may change arbitrarily between velocity intervals.
    """
    times = list(map(F, times))
    if len(times) < 2 or any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError('strictly ordered times are required')
    if axes < 1 or len(taps) != axes*len(times):
        raise ValueError('one weight interval per time and axis is required')
    weights = [(F(lo), F(hi)) for lo, hi in taps]
    if any(lo > hi for lo, hi in weights):
        raise ValueError('weight intervals must be ordered')
    tail = [(F(0), F(0))]*axes
    velocities = [None]*(len(times)-1)
    for index in reversed(range(len(times))):
        values = weights[index*axes:(index+1)*axes]
        tail = [(lo+a, hi+b) for (lo, hi), (a, b) in zip(tail, values, strict=True)]
        if index:
            dt = times[index]-times[index-1]
            velocities[index-1] = [(lo*dt, hi*dt) for lo, hi in tail]
    return tail, [weight for row in velocities for weight in row]


def symmetric_support(weights, radii):
    """Outward absolute support over independently bounded symmetric inputs."""
    radii = list(map(F, radii))
    if any(radius < 0 for radius in radii):
        raise ValueError('radii must be nonnegative')
    return sum(max(abs(F(lo)), abs(F(hi)))*radius
               for (lo, hi), radius in zip(weights, radii, strict=True))


def contrast_allowances(times, taps, position_margin, *, axes, cut):
    """Limits for symmetric errors of two forecasts sharing the same allowances."""
    if not 0 < cut < len(times) or position_margin <= 0:
        raise ValueError('a chronological cut and positive certified margin are required')
    initial, rates = integrated_error_weights(times, taps, axes=axes)
    boundary = (cut-1)*axes
    groups = dict(independent_position=taps, initial_position=initial,
                  earlier_velocity=rates[:boundary], later_velocity=rates[boundary:])
    coefficients = {name: [symmetric_support(weights[axis::axes], [1]*len(weights[axis::axes]))
                           for axis in range(axes)] for name, weights in groups.items()}
    totals = {name: sum(values) for name, values in coefficients.items()}
    totals['uniform_velocity'] = totals['earlier_velocity']+totals['later_velocity']
    half_gap = F(position_margin)*totals['independent_position']
    if not half_gap:
        raise ValueError('the certified contrast must have nonzero weights')
    limits = {name: half_gap/weight if weight else None for name, weight in totals.items()}
    return coefficients, 2*half_gap, limits
