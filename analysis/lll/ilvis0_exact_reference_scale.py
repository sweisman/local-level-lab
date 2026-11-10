# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact-rational training residuals under a declared Gaussian covariance.

This is a mathematical component, not an estimate of aircraft receiver noise.
All inputs are exact rational numbers or decimal strings; binary floats are
rejected so an implicit conversion cannot change the stated covariance law.
"""
from fractions import Fraction
from math import isfinite, isqrt, prod
from time import monotonic


class ResourceLimit(Exception):
    """A declared finite exact-arithmetic allowance was reached."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def _rational(value):
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError('exact rational or decimal-string input required')
    try:
        result = Fraction(value)
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError('exact rational or decimal-string input required') from error
    return result


def _check_bits(values, limit):
    if limit is not None and any(max(value.numerator.bit_length(), value.denominator.bit_length()) > limit
                                 for value in values):
        raise ResourceLimit('precision_limit')


def inverse_moment_floor(degrees, alpha, *, k, decimal_places=6):
    """Certified lower alpha-quantile floor for a central chi-square law.

    Markov's inequality on the k-th inverse moment gives
    P(chi-square_d <= q) <= q**k / product(d-2*j), j=1..k.
    All comparisons use integers. The result is maximal on the chosen
    decimal grid, rather than a floating quantile approximation.
    """
    if (type(degrees) is not int or type(k) is not int or type(decimal_places) is not int
            or k < 1 or degrees <= 2 * k or not 0 <= decimal_places <= 12):
        raise ValueError('positive inverse moment and supported grid required')
    probability = _rational(alpha)
    if not 0 < probability < 1:
        raise ValueError('alpha must be strictly between zero and one')
    scale = 10 ** decimal_places
    numerator = probability.numerator * prod(degrees - 2 * j for j in range(1, k + 1)) * scale ** k
    denominator = probability.denominator

    def certified(candidate):
        return candidate ** k * denominator <= numerator

    high = 1
    while certified(high):
        high *= 2
    low = high // 2
    while high - low > 1:
        middle = (low + high) // 2
        if certified(middle):
            low = middle
        else:
            high = middle
    return Fraction(low, scale)


def certify_scale(values, times, transitions, *, coefficients, ou, offset,
                  drift, white, alpha, k, source_id, covariance_id,
                  design_is_fixed, error_distribution,
                  decimal_places=6, max_bits=None, max_epochs=None,
                  max_seconds=None):
    """Conservative shared scale bound from training observations alone.

    A supplied polynomial coefficient vector need not fit the data optimally:
    its exact quadratic is at least the minimum over the fixed reference space.
    The coefficients may be estimated from training observations, but the
    polynomial design and covariance law must be fixed independently. For an
    arbitrary deterministic mean, the minimized quadratic is noncentral
    chi-square and stochastically dominates the central law. The inverse-moment
    lower quantile therefore gives a conservative scale upper bound under the
    *declared* covariance. It does not establish that covariance for aircraft.
    """
    if not isinstance(source_id, str) or not source_id or not isinstance(covariance_id, str) or not covariance_id:
        raise ValueError('nonempty source and covariance identities required')
    if type(design_is_fixed) is not bool or not isinstance(error_distribution, str):
        raise ValueError('explicit fixed-design and error-law declarations required')
    if type(k) is not int or k < 1:
        raise ValueError('positive inverse moment required')
    probability = _rational(alpha)
    if not 0 < probability < 1:
        raise ValueError('alpha must be strictly between zero and one')
    coefficients = tuple(map(_rational, coefficients))
    if len(coefficients) not in (4, 6, 8):
        raise ValueError('fixed polynomial degree 3, 5 or 7 required')
    observations = tuple(map(_rational, values))
    epochs = tuple(map(_rational, times))
    degrees = len(observations) - len(coefficients)
    base = dict(source_id=source_id, covariance_id=covariance_id,
                observation_count=len(observations), parameter_count=len(coefficients),
                residual_degrees_of_freedom=degrees, scale_upper=None,
                residual_quadratic=None, quantile_floor=None,
                observational_coverage_qualified=False, scientific_decision='abstain')
    if not design_is_fixed:
        return dict(base, reason='data_dependent_reference')
    if error_distribution != 'gaussian':
        return dict(base, reason='unsupported_error_distribution')
    if degrees <= 2 * k:
        return dict(base, reason='insufficient_residual_degrees_of_freedom')
    if len(epochs) != len(observations):
        raise ValueError('aligned observations and times required')
    if type(decimal_places) is not int or not 0 <= decimal_places <= 12:
        raise ValueError('supported decimal grid required')
    origin = epochs[0]
    relative_epochs = tuple(time - origin for time in epochs)
    residual = tuple(value - sum(coefficient * time ** power
                                 for power, coefficient in enumerate(coefficients))
                     for value, time in zip(observations, relative_epochs, strict=True))
    try:
        quadratic = ou_quadratic(residual, relative_epochs, transitions,
                                 ou=ou, offset=offset, drift=drift, white=white,
                                 max_bits=max_bits, max_epochs=max_epochs,
                                 max_seconds=max_seconds)
    except ResourceLimit as error:
        return dict(base, reason=error.reason)
    quantile = inverse_moment_floor(degrees, probability, k=k,
                                     decimal_places=decimal_places)
    try:
        _check_bits((quadratic, quantile), max_bits)
    except ResourceLimit as error:
        return dict(base, reason=error.reason)
    if quantile <= 0:
        return dict(base, reason='unrepresentable_quantile',
                    residual_quadratic=quadratic, quantile_floor=quantile)
    ratio = quadratic / quantile
    grid = 10 ** decimal_places
    floor = isqrt(ratio.numerator * grid * grid // ratio.denominator)
    if floor * floor * ratio.denominator < ratio.numerator * grid * grid:
        floor += 1
    return dict(base, reason='certified_under_declared_covariance',
                residual_quadratic=quadratic, quantile_floor=quantile,
                scale_upper=Fraction(floor, grid))


def ou_quadratic(values, times, transitions, *, ou, offset, drift, white,
                 max_bits=None, max_epochs=None, max_seconds=None):
    """Return ``r.T @ C^-1 @ r`` using rational innovations, without dense C.

    C has stationary OU covariance, a common offset, linear drift in ``times``
    and independent white variance. ``transitions[i]`` is the fixed OU
    correlation from time i to i+1. No interpolation or parameter estimation
    occurs here.
    """
    if max_bits is not None and (type(max_bits) is not int or max_bits < 1):
        raise ValueError('positive exact-rational bit limit required')
    if max_epochs is not None and (type(max_epochs) is not int or max_epochs < 1):
        raise ValueError('positive epoch limit required')
    if max_seconds is not None and (type(max_seconds) not in (int, float)
                                    or not isfinite(max_seconds) or max_seconds < 0):
        raise ValueError('finite nonnegative runtime limit required')
    deadline = monotonic() + max_seconds if max_seconds is not None else None
    residual = tuple(map(_rational, values))
    epochs = tuple(map(_rational, times))
    steps = tuple(map(_rational, transitions))
    if not residual or len(epochs) != len(residual) or len(steps) != len(residual) - 1:
        raise ValueError('aligned nonempty residuals, times and transitions required')
    if max_epochs is not None and len(residual) > max_epochs:
        raise ResourceLimit('work_limit')
    if any(right <= left for left, right in zip(epochs, epochs[1:])):
        raise ValueError('strictly increasing times required')
    if any(not 0 <= step < 1 for step in steps):
        raise ValueError('OU transitions must lie in [0, 1)')
    ou, offset, drift, white = map(_rational, (ou, offset, drift, white))
    if min(ou, offset, drift) < 0 or white <= 0:
        raise ValueError('nonnegative latent and positive white variances required')
    _check_bits((*residual, *epochs, *steps, ou, offset, drift, white), max_bits)

    mean = [Fraction(0)] * 3
    covariance = [[ou, Fraction(0), Fraction(0)],
                  [Fraction(0), offset, Fraction(0)],
                  [Fraction(0), Fraction(0), drift]]
    quadratic = Fraction(0)
    for index, (value, time) in enumerate(zip(residual, epochs, strict=True)):
        if deadline is not None and monotonic() >= deadline:
            raise ResourceLimit('time_limit')
        loading = (Fraction(1), Fraction(1), time)
        projected = [sum(covariance[row][column] * loading[column]
                         for column in range(3)) for row in range(3)]
        innovation_variance = white + sum(loading[row] * projected[row]
                                          for row in range(3))
        innovation = value - sum(loading[row] * mean[row] for row in range(3))
        quadratic += innovation * innovation / innovation_variance
        mean = [mean[row] + projected[row] * innovation / innovation_variance
                for row in range(3)]
        covariance = [[covariance[row][column]
                       - projected[row] * projected[column] / innovation_variance
                       for column in range(3)] for row in range(3)]
        if index < len(steps):
            step = steps[index]
            mean[0] *= step
            covariance = [[covariance[row][column]
                           * (step if row == 0 else 1)
                           * (step if column == 0 else 1)
                           for column in range(3)] for row in range(3)]
            covariance[0][0] += ou * (1 - step * step)
        _check_bits((quadratic, *mean, *(value for row in covariance for value in row)), max_bits)
    return quadratic
