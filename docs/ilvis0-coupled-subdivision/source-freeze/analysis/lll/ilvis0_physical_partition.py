# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic closed-box covers retaining every physical coordinate."""
from fractions import Fraction as F
import itertools
import math


def _inputs(lower,upper,axes):
    if (len(lower)!=27 or len(upper)!=27 or not 1<=len(axes)<=2 or len(set(axes))!=len(axes)
            or any(type(j)!=int or not 0<=j<27 for j in axes)):
        raise ValueError('all 27 coordinates and up to two distinct physical axes required')
    try:lo=list(map(float,lower));hi=list(map(float,upper))
    except (ValueError,TypeError,OverflowError):raise ValueError('finite binary endpoints required') from None
    if (not all(math.isfinite(v) for v in lo+hi) or any(a>b for a,b in zip(lo,hi))
            or any(isinstance(v,bool) or F(v)!=F(f) for v,f in zip(list(lower)+list(upper),lo+hi))):
        raise ValueError('ordered exact binary endpoints required; no silent domain conversion')
    return lo,hi


def split(lower,upper,*,axes):
    lo,hi=_inputs(lower,upper,axes);midpoints={}
    for axis in axes:
        middle=float((F(lo[axis])+F(hi[axis]))/2)
        if lo[axis]<middle<hi[axis]:midpoints[str(axis)]=middle
    active=[j for j in axes if str(j) in midpoints];children=[]
    for index,bits in enumerate(itertools.product((0,1),repeat=len(active))):
        a=lo.copy();b=hi.copy()
        for axis,bit in zip(active,bits):
            if bit:a[axis]=midpoints[str(axis)]
            else:b[axis]=midpoints[str(axis)]
        children.append(dict(index=index,lower=a,upper=b))
    return dict(physical_parameter_count=27,lower=lo,upper=hi,axes=list(axes),split_axes=active,
        midpoints=midpoints,children=children,known_truth_used=False)


def audit(partition,lower,upper,*,axes):
    """Independent Cartesian-cover reconstruction, including every boundary."""
    lo,hi=_inputs(lower,upper,axes)
    if (partition['physical_parameter_count']!=27 or partition['lower']!=lo or partition['upper']!=hi
            or partition['axes']!=list(axes) or partition['known_truth_used']):
        raise ValueError('complete unchanged parent and outcome-blind partition required')
    active=[];middle={}
    for coordinate in axes:
        value=float((F(lo[coordinate])+F(hi[coordinate]))/2)
        if F(lo[coordinate])<F(value)<F(hi[coordinate]):active.append(coordinate);middle[str(coordinate)]=value
    if (partition['split_axes']!=active or partition['midpoints']!=middle
            or len(partition['children'])!=2**len(active)):
        raise ValueError('complete physical cover required')
    for index,child in enumerate(partition['children']):
        left=lo.copy();right=hi.copy()
        for order,coordinate in enumerate(active):
            if (index>>(len(active)-1-order))&1:left[coordinate]=middle[str(coordinate)]
            else:right[coordinate]=middle[str(coordinate)]
        if child!=dict(index=index,lower=left,upper=right):
            raise ValueError('child domain changed, missing, duplicated or outside its parent')
    return dict(passed=True,children=len(partition['children']),physical_parameter_count=27,
        coverage='closed Cartesian product cover; shared boundaries retained',known_truth_used=False)
