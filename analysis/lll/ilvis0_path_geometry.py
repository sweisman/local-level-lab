# SPDX-License-Identifier: AGPL-3.0-or-later
"""Geographic path derivatives for ideal real-arithmetic mechanization.

Separate from frozen native engines. Numerical execution errors and clock
partitions are not established by these interval operations.
"""
from fractions import Fraction as F
import math
from .ilvis0_path_jets import Jet3 as J,ZERO
from .ilvis0_calibration_path import _add,_scale,_mul,_square

A=F(6378137)
E2=F(6.69437999014e-3)
OMEGA=F(7.2921150e-5)
HALF_PI=F(math.pi)/2


def sincos(value):
    """Scalar Taylor value enclosure and exact third-order chain rules."""
    if not isinstance(value,J):raise ValueError('complete path derivatives required')
    x,x1,x2,x3=value.exact;norm=max(map(abs,x))
    if norm>8:raise ValueError('trigonometric argument above eight is unsupported')
    def polynomial(cosine):
        result=ZERO
        for n in range(40,-1,-1):
            coefficient=F((-1)**(n//2),math.factorial(n)) if n%2==int(not cosine) else F(0)
            result=_add(_mul(result,x),(coefficient,coefficient))
        error=norm**41/F(math.factorial(41))
        return max(F(-1),result[0]-error),min(F(1),result[1]+error)
    si,co=polynomial(False),polynomial(True)
    x11=_square(x1);x111=_mul(x11,x1);x12=_mul(x1,x2)
    sine=J((si,_mul(co,x1),_add(_mul(co,x2),_scale(_mul(si,x11),-1)),
        _add(_add(_mul(co,x3),_scale(_mul(si,x12),-3)),_scale(_mul(co,x111),-1))))
    cosine=J((co,_scale(_mul(si,x1),-1),_scale(_add(_mul(si,x2),_mul(co,x11)),-1),
        _add(_scale(_add(_mul(si,x3),_scale(_mul(co,x12),3)),-1),_mul(si,x111))))
    return sine,cosine


def positive_sqrt(value):
    """Positive square root with dyadic value bounds and implicit derivatives."""
    if not isinstance(value,J) or value.exact[0][0]<=0:
        raise ValueError('strictly positive complete square-root domain required')
    def lower(q):return F(math.isqrt((q.numerator<<256)//q.denominator),1<<128)
    lo,hi=value.exact[0];left=lower(lo);right=lower(hi)
    if right*right<hi:right+=F(1,1<<128)
    if left<=0:raise ValueError('positive square-root endpoint unsupported at declared precision')
    inverse=(1/(2*right),1/(2*left));rows=[(left,right)]
    rows.append(_mul(value.exact[1],inverse))
    rows.append(_mul(_add(value.exact[2],_scale(_square(rows[1]),-2)),inverse))
    rows.append(_mul(_add(value.exact[3],_scale(_mul(rows[1],rows[2]),-6)),inverse))
    return J(tuple(rows))


def _domain(model,latitude):
    if type(model) is not int or model not in (0,1,2) or not isinstance(latitude,J):
        raise ValueError('supported physical candidate and latitude derivatives required')
    if max(map(abs,latitude.exact[0]))>F(157,100):
        raise ValueError('near-polar geographic domain unsupported')


def metric(model,latitude,height,radius):
    _domain(model,latitude)
    if not isinstance(height,J) or not isinstance(radius,J) or radius.exact[0][0]<=0:
        raise ValueError('height and positive radius derivative domains required')
    if model==2:north,east=radius,radius*(HALF_PI-latitude)
    else:
        si,co=sincos(latitude);d=1-E2*si.square();root=positive_sqrt(d)
        north=A*(1-E2)/(d*root)+height
        east=(A/root+height)*co
    if min(north.exact[0][0],east.exact[0][0])<=0:
        raise ValueError('nonpositive geographic metric domain')
    return north,east


def rates(model,coordinates,velocity,radius):
    if len(coordinates)!=3 or len(velocity)!=3 or not all(isinstance(v,J) for v in (*coordinates,*velocity)):
        raise ValueError('three complete coordinate and velocity derivatives required')
    north,east=metric(model,coordinates[0],coordinates[2],radius)
    return velocity[0]/north,velocity[1]/east,-velocity[2]


def context(model,latitude,coordinate_rates):
    _domain(model,latitude)
    if len(coordinate_rates)!=3 or not all(isinstance(v,J) for v in coordinate_rates):
        raise ValueError('three complete coordinate-rate derivatives required')
    si,co=sincos(latitude);zero=J.constant(0)
    earth=(OMEGA*co,zero,-OMEGA*si) if model==0 else (zero,zero,zero)
    transport=(zero,zero,-coordinate_rates[1]) if model==2 else (
        co*coordinate_rates[1],-coordinate_rates[0],-si*coordinate_rates[1])
    return earth,transport
