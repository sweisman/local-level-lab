# SPDX-License-Identifier: AGPL-3.0-or-later
"""Scalar affine-error bounds and a conditional norm-preserving rotation closure.

Inputs must use compatible reference linear maps. The rotation closure requires
a source proof of the norm identity and matching linearization; a box alone
does not prove either premise. No native engine uses this prototype.
"""
from fractions import Fraction as F
import math
from .ilvis0_directional_values import Value,add,scale,_product_bounds
from .ilvis0_exact_scale import sqrt_upper


def _scalar(value):
    if not isinstance(value,Value) or value.center.shape!=():raise ValueError('typed scalar bound required')
    return F(value.center.item()),F(value.change.item()),F(value.remainder.item())


def multiply(a,b):
    x,dx,rx=_scalar(a);y,dy,ry=_scalar(b);center=float(a.center)*float(b.center)
    d,r=_product_bounds(x,y,dx,dy,rx,ry);error=abs(F(center)-x*y)
    return Value(center,d+error,r+error)


def reciprocal(value):
    c,d,r=_scalar(value);left=c-d;right=c+d
    if left<=0<=right:raise ValueError('reciprocal domain crosses zero')
    minimum=min(abs(left),abs(right));center=1./float(c);error=abs(F(center)-1/c)
    change=d/(abs(c)*minimum)+error
    remainder=r/c**2+d**2/(c**2*minimum)+error
    return Value(center,change,remainder)


def _roots(value):
    if value<=0:raise ValueError('positive square-root domain required')
    upper=F(sqrt_upper(value));lower=upper if upper**2==value else F(math.nextafter(float(upper),0.))
    if lower<=0:raise ValueError('square-root derivative scale is not representable')
    return lower,upper


def square_root(value):
    c,d,r=_scalar(value);minimum=c-d
    low,_=_roots(minimum);lc,uc=_roots(c);center=math.sqrt(float(c))
    error=max(abs(F(center)-lc),abs(F(center)-uc))
    change=d/(lc+low)+error
    remainder=r/(2*lc)+d**2/(2*lc*(lc+low)**2)+error
    return Value(center,change,remainder)


def recenter(value,center):
    c,d,r=_scalar(value)
    if not math.isfinite(center):raise ValueError('finite target reference required')
    target=float(center);shift=abs(c-F(target))
    return Value(target,d+shift,r+shift)


def vertical_departure(a,b,*,norm_identity=False,linearization_consistent=False):
    """Bound b_z when ||a+b||=||a|| and the vertical sign does not flip.

    The stable identity is b_z=-E/(a_z+s*sqrt(a_z²-E)), with
    E=2*a_h dot b_h+||b_h||² and s=sign(a_z). Its reference linear map
    must match that of b_z before this remainder can replace an existing one.
    Both source premises are explicit requirements, never inferred from probes.
    """
    if norm_identity is not True:raise ValueError('a proven norm identity is required')
    if linearization_consistent is not True:raise ValueError('a compatible reference linearization is required')
    if not isinstance(a,Value) or not isinstance(b,Value) or a.center.shape!=(3,) or b.center.shape!=(3,):
        raise ValueError('two typed vectors required')
    az=a.component(2);bz=b.component(2);c,d,_=_scalar(az);q,e,_=_scalar(bz)
    if c-d>0 and c+q-d-e>0:sign=1
    elif c+d<0 and c+q+d+e<0:sign=-1
    else:raise ValueError('vertical sign branch is not established over the full domain')
    cross=add(multiply(a.component(0),b.component(0)),multiply(a.component(1),b.component(1)))
    square=add(multiply(b.component(0),b.component(0)),multiply(b.component(1),b.component(1)))
    numerator=add(scale(cross,2.),square)
    argument=add(multiply(az,az),scale(numerator,-1.))
    denominator=add(az,scale(square_root(argument),sign))
    result=scale(multiply(numerator,reciprocal(denominator)),-1.)
    return recenter(result,float(bz.center))
