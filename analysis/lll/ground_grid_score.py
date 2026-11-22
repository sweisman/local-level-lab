# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact fixed-score bounds from coordinate anchors and RMS acceleration."""
from bisect import bisect_right
from fractions import Fraction as F

from .shared_motion_gap import _inner_product


def score_sensitivity(times, taps, position_anchors):
    """Return the endpoint-error coefficient and squared RMS-acceleration coefficient.

    The first and last positions are fixed. The first coefficient multiplies a
    uniform bound on each coordinate of each interior anchor. The acceleration
    coefficient relaxes continuity of velocity between intervals.
    """
    times = list(map(F, times))
    if (len(times) < 2 or any(a >= b for a, b in zip(times, times[1:]))
            or len(taps) != len(times)-1 or any(len(row) != 3 for row in taps)):
        raise ValueError('an ordered score grid with one three-axis tap per later time is required')
    anchors = sorted(set(map(F, position_anchors)) | {times[0], times[-1]})
    if (anchors[0], anchors[-1]) != (times[0], times[-1]):
        raise ValueError('anchor times must lie inside the scoring interval')
    weights = [[F(0)]*3 for _ in anchors]
    intervals = [[] for _ in anchors[1:]]
    for t, tap in zip(times[1:-1], taps[:-1], strict=True):
        j = bisect_right(anchors, t)-1
        a, b = anchors[j:j+2]
        fraction = (t-a)/(b-a)
        for axis, value in enumerate(map(F, tap)):
            weights[j][axis] += (1-fraction)*value
            weights[j+1][axis] += fraction*value
        if fraction:
            intervals[j].append((t, tuple(map(F, tap))))

    integral = F(0)
    for a, b, values in zip(anchors[:-1], anchors[1:], intervals, strict=True):
        if not values:
            continue
        grid = [a, *(t for t, _ in values), b]
        widths = [t-s for s, t in zip(grid, grid[1:])]
        for axis in range(3):
            # The Green function for the fixed-position interval, with its
            # overall sign immaterial to the squared operator norm.
            kernel = [sum(w[axis]*(min(t,s)-a)*(b-max(t,s))/(b-a) for t, w in values) for s in grid]
            integral += _inner_product(kernel, kernel, widths)
    return sum(abs(x) for row in weights[1:-1] for x in row), integral*(times[-1]-times[0])
