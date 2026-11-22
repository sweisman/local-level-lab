# SPDX-License-Identifier: AGPL-3.0-or-later
"""Outward coefficient bounds for a fixed innovations score direction."""

from decimal import Context, Decimal, ROUND_CEILING, ROUND_FLOOR
import math

import numpy as np

from .state_space_covariance import LinearInnovations


PRECISION = 384


def _directed_dot(down, up, coefficients, values):
    lo = hi = Decimal(0)
    for coefficient, (left, right) in zip(coefficients, values, strict=True):
        if coefficient and (left or right):
            factor = Decimal.from_float(float(coefficient))
            if coefficient < 0.:
                left, right = right, left
            lo = down.add(lo, down.multiply(factor, left))
            hi = up.add(hi, up.multiply(factor, right))
    return lo, hi


def whiten_intervals(operator, coordinates):
    """Outward whitening for rational coordinates and the saved linear factors."""
    from fractions import Fraction

    if not isinstance(operator, LinearInnovations):
        raise ValueError('a fixed linear innovations operator is required')
    d, n = operator.observation_dimension, operator.epoch_count
    values = tuple(map(Fraction, coordinates))
    if len(values) != d*n:
        raise ValueError('one rational value per chronological coordinate required')
    down = Context(prec=PRECISION, rounding=ROUND_FLOOR)
    up = Context(prec=PRECISION, rounding=ROUND_CEILING)
    mean = [(Decimal(0), Decimal(0))]*operator.state_dimension

    def dot(factors, box):
        return _directed_dot(down, up, factors, box)

    for epoch in range(n):
        innovations, whitened = [], []
        for axis, value in enumerate(values[epoch*d:(epoch+1)*d]):
            low, high = dot(operator._observation[epoch, axis], mean)
            a, b = Decimal(value.numerator), Decimal(value.denominator)
            low, high = down.subtract(down.divide(a, b), high), up.subtract(up.divide(a, b), low)
            innovations.append((low, high))
            factor = operator._lower[epoch, axis]
            shift_low, shift_high = dot(factor[:axis], whitened)
            divisor = Decimal.from_float(float(factor[axis]))
            left = down.divide(down.subtract(low, shift_high), divisor)
            right = up.divide(up.subtract(high, shift_low), divisor)
            whitened.append((left, right))
            yield math.nextafter(float(left), -math.inf), math.nextafter(float(right), math.inf)
        next_mean = []
        for transition, gain in zip(operator._transition[epoch], operator._gain[epoch], strict=True):
            lo, hi = dot(transition, mean)
            correction_lo, correction_hi = dot(gain, innovations)
            next_mean.append((down.add(lo, correction_lo), up.add(hi, correction_hi)))
        mean = next_mean


def adjoint_intervals(operator, direction):
    """Enclose W.T @ direction for the mathematical operator of stored factors."""
    if not isinstance(operator, LinearInnovations):
        raise ValueError('a fixed linear innovations operator is required')
    vector = np.asarray(direction, dtype=float)
    d = operator.observation_dimension
    n = operator.epoch_count
    if vector.shape != (n*d,) or not np.isfinite(vector).all():
        raise ValueError('one finite weight per chronological whitened coordinate required')
    vector = vector.reshape(n, d)
    down = Context(prec=PRECISION, rounding=ROUND_FLOOR)
    up = Context(prec=PRECISION, rounding=ROUND_CEILING)
    zero = Decimal(0), Decimal(0)

    def dot(coefficients, values):
        return _directed_dot(down, up, coefficients, values)

    future = [zero]*operator.state_dimension
    lower = np.empty((n, d))
    upper = np.empty_like(lower)
    for epoch in range(n-1, -1, -1):
        factor = operator._lower[epoch]
        solve = [zero]*d
        for axis in range(d-1, -1, -1):
            value = Decimal.from_float(float(vector[epoch, axis]))
            divisor = Decimal.from_float(float(factor[axis, axis]))
            lo, hi = dot(factor[axis+1:, axis], solve[axis+1:])
            solve[axis] = down.divide(down.subtract(value, hi), divisor), up.divide(up.subtract(value, lo), divisor)
        physical = []
        for (left, right), gain in zip(solve, operator._gain[epoch].T, strict=True):
            lo, hi = dot(gain, future)
            physical.append((down.add(left, lo), up.add(right, hi)))
        lower[epoch] = [math.nextafter(float(lo), -math.inf) for lo, _ in physical]
        upper[epoch] = [math.nextafter(float(hi), math.inf) for _, hi in physical]
        preceding = []
        for transition, observation in zip(operator._transition[epoch].T, operator._observation[epoch].T, strict=True):
            lo, hi = dot(transition, future)
            shift_lo, shift_hi = dot(observation, physical)
            preceding.append((down.subtract(lo, shift_hi), up.subtract(hi, shift_lo)))
        future = preceding
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise ValueError('unrepresentable adjoint bound')
    return lower.ravel(), upper.ravel()


def directional_bound(lower, upper, radii):
    """Upper bound for the absolute score under independent coordinate radii."""
    lo, hi, radii = (np.asarray(value, dtype=float) for value in (lower, upper, radii))
    if (lo.ndim != 1 or not len(lo) or hi.shape != lo.shape or radii.shape != lo.shape
            or np.any(lo > hi) or np.any(radii < 0.) or any(not np.isfinite(v).all() for v in (lo, hi, radii))):
        raise ValueError('finite ordered coefficient intervals and nonnegative radii required')
    magnitudes = np.maximum(abs(lo), abs(hi))
    mask = (magnitudes > 0.) & (radii > 0.)
    if not np.any(mask):
        return 0.
    terms = np.nextafter(magnitudes[mask]*radii[mask], np.inf)
    bound = math.nextafter(math.fsum(terms), math.inf)
    if not math.isfinite(bound):
        raise ValueError('unrepresentable directional bound')
    return bound
