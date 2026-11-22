# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact power-of-two arithmetic for binary source-radius calculations.

Integer pairs represent n / 2**e. No floating addition, product or subtraction
is used to form a bound. General rational value endpoints remain exact; rows
with nonbinary denominators use the original Fraction reference.
"""
from fractions import Fraction as F
from functools import lru_cache
import numpy as np
from .ilvis0_saved_prediction_audit import endpoint
from .ilvis0_source_reference import affine_radius as _general_affine


class _Nonbinary(ValueError):pass


def _number(value):
    n,d=value.as_integer_ratio() if hasattr(value,'as_integer_ratio') else F(value).as_integer_ratio()
    if d&(d-1):raise _Nonbinary('nonbinary denominator')
    return n,d.bit_length()-1


def _subtract(a,b):
    e=max(a[1],b[1])
    return (a[0]<<(e-a[1]))-(b[0]<<(e-b[1])),e


def _absolute(a):return abs(a[0]),a[1]


def _maximum(a,b):
    e=max(a[1],b[1])
    return a if (a[0]<<(e-a[1]))>=(b[0]<<(e-b[1])) else b


def _width(lo,hi,z):
    return _maximum(_absolute(_subtract(lo,z)),_absolute(_subtract(hi,z)))


def _multiply(a,b):return a[0]*b[0],a[1]+b[1]


def _sum(terms):
    e=max((v[1] for v in terms),default=0)
    return F(sum(n<<(e-p) for n,p in terms),1<<e)


@lru_cache(maxsize=8)
def _widths(lower,upper,center):
    return tuple(_width(_number(a),_number(b),_number(c))
                 for a,b,c in zip(lower,upper,center,strict=True))


def _mismatch(value,ends):
    return _width(_number(float(ends[0])),_number(float(ends[1])),_number(float(value)))


def transfer_radius(values,rows,points,derivatives,*,lower,upper,center,remainders):
    """Transfer a source bound to stated values and all stated derivative rows.

    The callers validate the finite array shapes and interval ordering. Only the
    final sum is rounded, even when the ideal remainder is a general rational.
    """
    try:
        widths=_widths(tuple(lower),tuple(upper),tuple(center))
    except _Nonbinary:
        rational_widths=[max(abs(F(a)-F(c)),abs(F(b)-F(c)))
                         for a,b,c in zip(lower,upper,center,strict=True)]
        widths=None
    result=np.empty((2,3))
    for source in range(2):
        base=F(remainders[source])
        if base<0:raise ValueError('nonnegative ideal source remainder required')
        for axis in range(3):
            value_interval=points[source,axis]
            derivative_intervals=derivatives[source,axis]
            stated_rows=rows[source,axis]
            value=values[source,axis]
            if widths is None:
                offset=max(abs(F(float(v))-F(float(value))) for v in value_interval)
                affine=sum((d*max(abs(F(float(v))-F(float(row))) for v in ends)
                            for ends,row,d in zip(derivative_intervals,stated_rows,rational_widths,strict=True)),F(0))
            else:
                offset=F(0)
                terms=[_mismatch(value,value_interval)]
                terms.extend(_multiply(_mismatch(row,ends),width)
                             for row,ends,width in zip(stated_rows,derivative_intervals,widths,strict=True))
                affine=_sum(terms)
            result[source,axis]=endpoint(base+offset+affine,True)
    result.setflags(write=False)
    return result


def affine_radius(lower_value,upper_value,center,jacobian,lower,upper,reference):
    low,high,c=map(F,(lower_value,upper_value,center))
    if low>high:raise ValueError('ordered value interval required')
    vectors=tuple(tuple(v) for v in (jacobian,lower,upper,reference))
    terms=[]
    try:
        for j,lo,hi,z in zip(*vectors,strict=True):
            if lo>hi:raise ValueError('ordered parameter domain required')
            terms.append(_multiply(_absolute(_number(j)),_width(_number(lo),_number(hi),_number(z))))
    except _Nonbinary:
        return _general_affine(lower_value,upper_value,center,*vectors)
    linear=_sum(terms);value=max(abs(low-c),abs(high-c));total=value+linear
    return dict(value_radius=str(value),linear_radius=str(linear),affine_radius=str(total),
        upper_float=endpoint(total,True))


def mean_value_radius(frame,values,rows,*,phase):
    if type(phase) is not int or phase not in (0,1):raise ValueError('source phase required')
    arrays=[np.asarray(v,float) for v in (frame['point_values'],frame['jacobian'],values,rows)]
    point,derivatives,values,rows=arrays
    if (tuple(a.shape for a in arrays)!=((2,2,3,2),(2,2,3,27,2),(2,2,3),(2,2,3,27))
            or not all(np.all(np.isfinite(a)) for a in arrays)
            or np.any(point[...,0]>point[...,1]) or np.any(derivatives[...,0]>derivatives[...,1])):
        raise ValueError('finite ordered intervals and all 27 supplied rows required')
    z,lo,hi=(np.asarray(frame[key],float) for key in ('center','lower','upper'))
    if any(a.shape!=(27,) or not np.all(np.isfinite(a)) for a in (z,lo,hi)) or np.any(lo>hi):
        raise ValueError('complete finite source domain required')
    return transfer_radius(values[phase],rows[phase],point[phase],derivatives[phase],
                           lower=lo,upper=hi,center=z,remainders=(0,0))
