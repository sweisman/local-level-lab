# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact interval derivatives through order three, separate from frozen engines."""
from dataclasses import dataclass
from fractions import Fraction as F
import math
from .ilvis0_calibration_path import _box,_add,_mul,_scale,_square,_outward
from .ilvis0_piecewise_trapezoid import _number
from .ilvis0_exact_scale import sqrt_upper

ZERO=(F(0),F(0))


@dataclass(frozen=True)
class Jet3:
    exact:tuple

    def __post_init__(self):
        try:
            if len(self.exact)!=4:raise ValueError('orders zero through three required')
            values=tuple(_box(row) for row in self.exact)
        except (ValueError,TypeError):raise ValueError('four complete finite actual-derivative intervals required') from None
        object.__setattr__(self,'exact',values)

    @classmethod
    def constant(cls,value):
        box=_box(value) if isinstance(value,(tuple,list)) else (_number(value),)*2
        return cls((box,ZERO,ZERO,ZERO))

    @classmethod
    def affine(cls,center,slope,path):
        c=_number(center);b=_box(slope);s=_box(path)
        return cls((_add((c,c),_mul(b,s)),b,ZERO,ZERO))

    @staticmethod
    def cast(value):return value if isinstance(value,Jet3) else Jet3.constant(value)

    def __add__(self,other):
        other=self.cast(other);return Jet3(tuple(_add(a,b) for a,b in zip(self.exact,other.exact)))
    __radd__=__add__

    def __neg__(self):return Jet3(tuple(_scale(a,-1) for a in self.exact))
    def __sub__(self,other):return self+-self.cast(other)
    def __rsub__(self,other):return self.cast(other)+-self

    def __mul__(self,other):
        other=self.cast(other);rows=[]
        for n in range(4):
            value=ZERO
            for k in range(n+1):value=_add(value,_scale(_mul(self.exact[k],other.exact[n-k]),F(math.comb(n,k))))
            rows.append(value)
        return Jet3(tuple(rows))
    __rmul__=__mul__

    def square(self):
        value=self*self;return Jet3((_square(self.exact[0]),)+value.exact[1:])

    def inverse(self):
        lo,hi=self.exact[0]
        if lo<=0<=hi:raise ValueError('reciprocal derivative domain crosses zero')
        inverse=tuple(sorted((1/lo,1/hi)));rows=[inverse]
        for n in range(1,4):
            value=ZERO
            for k in range(1,n+1):value=_add(value,_scale(_mul(self.exact[k],rows[n-k]),F(math.comb(n,k))))
            rows.append(_scale(_mul(value,inverse),-1))
        return Jet3(tuple(rows))

    def __truediv__(self,other):return self*self.cast(other).inverse()
    def __rtruediv__(self,other):return self.cast(other)*self.inverse()

    def __pow__(self,n):
        if type(n) is not int or not 0<=n<=64:raise ValueError('bounded nonnegative integer power required')
        if n==0:return Jet3.constant(1)
        if n==1:return self
        if n%2:return self*(self**(n-1))
        return (self**(n//2)).square()

    def rounded(self,*,binary_bits=96):
        """Round every endpoint outward to a fixed dyadic grid."""
        if type(binary_bits) is not int or not 32<=binary_bits<=256:
            raise ValueError('dyadic precision from thirty-two to 256 bits required')
        scale=1<<binary_bits;rows=[]
        for lo,hi in self.exact:
            floor=(lo.numerator*scale)//lo.denominator
            ceiling=-((-hi.numerator*scale)//hi.denominator)
            rows.append((F(floor,scale),F(ceiling,scale)))
        return Jet3(tuple(rows))

    def report(self):
        return dict(version='ilvis0-exact-third-order-path-jet-v1',
            exact_derivatives=[list(map(str,row)) for row in self.exact],derivatives=_outward(self.exact),
            derivative_order=3,actual_derivatives_not_factorial_coefficients=True,
            input_derivative_bounds_assumed=True,component_arithmetic_verified=True,
            native_motion_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def _product(a,b):
    return tuple(tuple(sum((a[i][k]*b[k][j] for k in range(3)),Jet3.constant(0)) for j in range(3)) for i in range(3))


@dataclass(frozen=True)
class Rotation:
    matrix:tuple
    terms:int
    argument_norms:tuple
    derivative_tails:tuple
    rotation_norms:tuple

    def report(self):
        return dict(version='ilvis0-third-order-skew-exponential-v1',terms=self.terms,
            matrix=[[v.report() for v in row] for row in self.matrix],
            argument_derivative_norms=list(map(str,self.argument_norms)),
            derivative_tail_bounds=list(map(str,self.derivative_tails)),
            rotation_derivative_norms=list(map(str,self.rotation_norms)),
            native_motion_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def exp_skew(vector,*,terms=24):
    """Enclose exp(skew(v)) and its first three path derivatives.

The power-series tail includes every derivative placement in each matrix
product. Rotation norm identities tighten entries without assuming independent
coordinates. This is not a complete native-mechanization derivative bound.
"""
    if (len(vector)!=3 or not all(isinstance(v,Jet3) for v in vector)
            or type(terms) is not int or not 12<=terms<=48):
        raise ValueError('three complete jets and a finite series degree from twelve to forty-eight required')
    norms=tuple(F(sqrt_upper(sum((max(abs(v.exact[n][0]),abs(v.exact[n][1]))**2 for v in vector),F(0)))) for n in range(4))
    a0,a1,a2,a3=norms
    if a0>8:raise ValueError('rotation argument norm above eight is unsupported')
    def tail(degree):
        n=degree+1
        return a0**n/F(math.factorial(n))/(1-a0/F(n+1))
    tails=(tail(terms),a1*tail(terms-1),
        a2*tail(terms-1)+a1*a1*tail(terms-2),
        a3*tail(terms-1)+3*a1*a2*tail(terms-2)+a1**3*tail(terms-3))
    rotation_norms=(F(1),a1,a2+a1*a1,a3+3*a1*a2+a1**3)
    x,y,z=vector;zero=Jet3.constant(0);k=((zero,-z,y),(z,zero,-x),(-y,x,zero))
    term=tuple(tuple(Jet3.constant(int(i==j)) for j in range(3)) for i in range(3));result=term
    for order in range(1,terms+1):
        term=tuple(tuple(v/F(order) for v in row) for row in _product(term,k))
        result=tuple(tuple(a+b for a,b in zip(row,addition)) for row,addition in zip(result,term))
    matrix=[]
    for row in result:
        entries=[]
        for value in row:
            bounds=[]
            for (lo,hi),radius,norm in zip(value.exact,tails,rotation_norms):
                left=max(lo-radius,-norm);right=min(hi+radius,norm)
                if left>right:raise ValueError('series and rotation-norm restrictions disagree')
                bounds.append((left,right))
            entries.append(Jet3(tuple(bounds)))
        matrix.append(tuple(entries))
    return Rotation(tuple(matrix),terms,norms,tails,rotation_norms)
