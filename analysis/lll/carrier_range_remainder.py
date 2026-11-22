# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conservative rational remainder bounds for fixed-transmit carrier ranges."""
from fractions import Fraction
from math import isqrt


def position_cap(times, anchor_axis_m, acceleration_rms_mps2):
    """Bound every interior coordinate using the largest anchor interval."""
    times = list(map(Fraction, times))
    intervals = [b-a for a, b in zip(times, times[1:])]
    anchor, acceleration = map(Fraction, (anchor_axis_m, acceleration_rms_mps2))
    if not intervals or min(intervals) <= 0 or min(anchor, acceleration) < 0:
        raise ValueError('ordered anchors and nonnegative error caps required')
    squared = (times[-1]-times[0])*max(intervals)**3/48
    # Round the time factor up to a whole squared second before multiplication.
    factor = isqrt(squared.numerator//squared.denominator)
    return anchor+(factor+(factor**2 < squared))*acceleration


def bound_score_remainder(weights, counts, metric, base_height_m, max_axis_m):
    """Bound the nonlinear score error at the validated satellite radii."""
    metric = list(map(Fraction, metric))
    cap, height = map(Fraction, (max_axis_m, base_height_m))
    if len(metric) != 3 or min(metric) <= 0 or min(cap, height) < 0:
        raise ValueError('positive local metric and nonnegative position bounds required')
    lat, lon, up = (cap/scale for scale in metric)
    if height+up > 100000:
        raise ValueError('displaced altitude exceeds the derivative bound domain')
    if sum(counts) != len(weights) or not counts or min(counts) < 2:
        raise ValueError('the complete satellite blocks are required')

    # WGS84 prime-vertical and meridional radii plus |height| are below
    # 6.5 Mm in the validated range. The meridional radius derivative
    # is bounded by 70 km/rad. The ECEF norm is also <= 6.5 Mm there.
    speed = 6500000*(lat+lon)+up
    acceleration = 6500000*(lat+lon)**2+70000*lat**2+2*(lat+lon)*up
    # The final satellites are farther than 20 Mm from the centre and
    # within 40 Mm. Therefore the receiver range is at least 13 Mm,
    # and the norm of the Sagnac gradient is below 1e-5.
    endpoint_error = (speed**2/13000000+Fraction(100001, 100000)*acceleration)/2
    values = list(map(Fraction, weights))
    absolute_weight = Fraction()
    start = 0
    for size in counts:
        block = values[start:start+size]
        mean = sum(block)/size
        absolute_weight += sum(abs(value-mean) for value in block)
        start += size
    # Both endpoints contribute. Exact centering removes the receiver clock.
    return dict(max_score_remainder=2*absolute_weight*endpoint_error,
                endpoint_range_remainder_m=endpoint_error, absolute_centered_weight=absolute_weight)
