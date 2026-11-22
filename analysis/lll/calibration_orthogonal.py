# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact score checks for a proposed calibration-resistant contrast."""

from fractions import Fraction as F
import math


def annihilate_quadratics(weights, later_times):
    """Adjust three taps per axis so all nine temporal moments are zero."""
    result = list(map(F, weights))
    times = list(map(F, later_times))
    first = len(result)-3*len(times)
    if (first < 0 or first % 3 or len(times) < 3
            or any(end <= start for start, end in zip(times, times[1:]))):
        raise ValueError('complete ordered position epochs are required')
    pivots = (0, len(times)//2, len(times)-1)
    for axis in range(3):
        original = result[first+axis::3]
        for pivot in pivots:
            others = [times[i] for i in pivots if i != pivot]
            correction = sum(weight*math.prod((time-other)/(times[pivot]-other) for other in others)
                             for weight, time in zip(original, times, strict=True))
            result[first+3*pivot+axis] -= correction
        for order in range(3):
            remaining = sum(weight*time**order
                            for weight, time in zip(result[first+axis::3], times, strict=True))
            if remaining:
                raise ArithmeticError('all three moments must be exactly zero')
    return result


def box_lower(coefficients, lower, higher):
    """Exact support floor using every supplied coefficient and bound."""
    total = F(0)
    for coefficient, lo, hi in zip(coefficients, lower, higher, strict=True):
        coefficient, lo, hi = map(F, (coefficient, lo, hi))
        if lo > hi:
            raise ValueError('ordered coefficient box required')
        total += min(coefficient*lo, coefficient*hi)
    return total
