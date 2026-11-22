# SPDX-License-Identifier: AGPL-3.0-or-later
"""Combine the signed forecast gap with certified earlier-loss support limits."""

from fractions import Fraction as F


def margin_from_support(nominal, weight_norm, supports):
    """Return the strongest certified position allowance over the two signs.

    Each orientation lists one outward support from each independent box,
    with the sign already chosen to reduce the oriented separation.
    """
    orientation_limits = {sign: sign*F(nominal)-sum(map(F, supports[sign])) for sign in (1, -1)}
    if weight_norm <= 0:
        raise ValueError('positive upper weight norm required')
    orientation = max(orientation_limits, key=orientation_limits.__getitem__)
    return max(F(0), orientation_limits[orientation])/(2*F(weight_norm)), orientation, orientation_limits


def earlier_disposition(loss, residual, *, increase, unshared):
    """Judge the saved witness using an outer ceiling for a definite exclusion."""
    from .ilvis0_exact_scale import sqrt_upper

    increase, unshared = F(increase), F(unshared)
    ceiling = increase + 2*unshared*F(sqrt_upper(sum(F(float(value))**2 for value in residual)+increase)) + unshared**2
    if F(loss['loss_lower']) > ceiling:
        return 'excluded'
    return 'feasible' if loss['loss_passed'] else 'unresolved'
