# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project a saved integration's position remainder without cancellation in the arithmetic."""

from fractions import Fraction as F


def summarize_error(displacement, baseline, affine, metric, times, taps, *, cut):
    """Return exact score intervals and per-axis position and velocity magnitudes."""
    t = list(map(F, times))
    metric = list(map(F, metric))
    axes = len(metric)
    if not 1 < cut < len(t):
        raise ValueError('a cut with earlier and later intervals is required')
    if any(a >= b for a, b in zip(t, t[1:])):
        raise ValueError('strictly ordered times are required')
    if not axes or any(scale <= 0 for scale in metric):
        raise ValueError('positive physical coordinate scales are required')
    if (any(len(path) != len(t) or any(len(row) != axes for row in path)
            for path in (displacement, baseline, affine)) or len(taps) != axes*len(t)):
        raise ValueError('one coordinate vector per epoch and tap per coordinate required')
    position = [[(F(a)-F(b)-F(c))*scale for a, b, c, scale in zip(*rows, metric, strict=True)]
                for rows in zip(displacement, baseline, affine, strict=True)]
    velocity = [[abs((now-prev)/dt) for now, prev in zip(position[i], position[i-1], strict=True)]
                for i, dt in enumerate((b-a for a, b in zip(t, t[1:])), start=1)]
    score_lo = score_hi = F(0)
    for value, (lo, hi) in zip((value for row in position for value in row), taps, strict=True):
        if lo > hi:
            raise ValueError('weight intervals must be ordered')
        terms = value*F(lo), value*F(hi)
        score_lo += min(terms)
        score_hi += max(terms)

    def peak(values):
        return [max(map(abs, column)) for column in zip(*values, strict=True)]

    return dict(score_bounds=(score_lo, score_hi), earlier_position_max=peak(position[:cut]),
                later_position_max=peak(position[cut:]), earlier_velocity_max=peak(velocity[:cut-1]),
                later_velocity_max=peak(velocity[cut-1:]))
