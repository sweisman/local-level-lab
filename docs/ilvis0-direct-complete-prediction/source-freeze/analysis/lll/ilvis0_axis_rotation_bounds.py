# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact component bounds for exp([w]x) acting on a coordinate unit vector.

These rotation-vector coordinates are NOT Euler angles. The component along
the chosen vector loses at most half the squared perpendicular rotation-vector
length, regardless of the parallel rotation-vector coordinate. This primitive
does not replace or qualify any native propagation bound.
"""
from fractions import Fraction as F


def bound(lower,upper,*,axis):
    if type(axis)!=int or axis not in (0,1,2) or len(lower)!=3 or len(upper)!=3:
        raise ValueError('one coordinate axis and all three rotation-vector coordinates required')
    try:lo=list(map(F,lower));hi=list(map(F,upper))
    except (ValueError,OverflowError,TypeError):raise ValueError('finite rational rotation-vector bounds required') from None
    if any(a>b for a,b in zip(lo,hi)):raise ValueError('ordered rotation-vector box required')
    perpendicular=sum((max(abs(a),abs(b))**2 for j,(a,b) in enumerate(zip(lo,hi)) if j!=axis),F(0))
    parallel_low=max(F(-1),1-perpendicular/2)
    return dict(axis=axis,parallel_lower=str(parallel_low),parallel_upper='1',
        transverse_squared_upper=str(min(F(1),perpendicular)),
        displacement_squared_upper=str(min(F(4),perpendicular)),
        perpendicular_rotation_vector_squared_upper=str(perpendicular),
        coordinates='rotation vector in radians, not Euler angles',
        native_propagation_qualified=False,observational_coverage_qualified=False,
        scientific_decision='abstain')
