# SPDX-License-Identifier: AGPL-3.0-or-later
"""Enclose mean force predicted by a quadratic GPS path on common packet support."""

import numpy as np

from .ilvis0_force_bounds import _Box, force_bounds


def bound_average(jet, support_s, *, offset_bounds_s, subdivisions, model,
                  background_rate_rads, gravity_mps2, disc_radius_m):
    """Bound the continuous mean over one contiguous union of retained packets.

    All times are relative to the fitted quadratic's center. The common timing
    offset translates the union without changing its duration. Within each
    subdivision, coordinate, rate and acceleration bounds are propagated
    together. Relaxing the shared offset to an interval in every subdivision
    makes the overall enclosure conservative. This bounds the supplied path,
    without bounding GPS errors, model truncation or the instrument response.
    """
    jet = np.asarray(jet, float)
    support = np.asarray(support_s, float)
    offset = np.asarray(offset_bounds_s, float)
    if (jet.shape != (3, 3) or support.shape != (2,) or offset.shape != (2,)
            or not all(np.isfinite(a).all() for a in (jet, support, offset))
            or support[0] >= support[1] or offset[0] > offset[1]
            or type(subdivisions) is not int or not 1 <= subdivisions <= 256):
        raise ValueError('finite quadratic jet, contiguous support and bounded partition required')
    intervals = np.linspace(*support, subdivisions+1)
    translation = _Box(*offset)
    position, rate, acceleration = jet.tolist()
    integral = _Box(0.)
    total = _Box(support[1])-_Box(support[0])
    for left, right in zip(intervals[:-1], intervals[1:], strict=True):
        if not left < right:
            raise ValueError('subdivision has no representable duration')
        time = _Box(left, right)+translation
        squared = time.square()
        positions = [p+v*time+a*.5*squared for p, v, a in zip(position, rate, acceleration, strict=True)]
        rates = [v+a*time for v, a in zip(rate, acceleration, strict=True)]
        boxes = [[value.lo, value.hi] for value in (*positions, *rates)]
        boxes.extend([value, value] for value in acceleration)
        magnitude = force_bounds(boxes, model=model, include_matched_disc=True,
            background_rate_bounds_rads=(background_rate_rads, background_rate_rads),
            gravity_bounds_mps2=(gravity_mps2, gravity_mps2), disc_radius_m=disc_radius_m)
        integral += _Box(*magnitude['magnitude_bounds_mps2'])*(_Box(right)-_Box(left))
    mean = integral/total
    return max(0., mean.lo), mean.hi
