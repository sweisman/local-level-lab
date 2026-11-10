# SPDX-License-Identifier: AGPL-3.0-or-later
"""Interval first derivatives for a future coupled static-calibration map.

These mathematical primitives do not yet enclose the complete source map or
qualify a prediction. All 27 physical and 24 common-error coordinates remain.
Arithmetic uses outward binary endpoints; this is not a whole-program proof.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math
from .ilvis0_force_bounds import _Box
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint


def _zero(a):return a.lo==a.hi==0.
def _add(a,b):return b if _zero(a) else a if _zero(b) else a+b
def _mul(a,b):return _Box(0.) if _zero(a) or _zero(b) else a*b


def _input_box(lower,upper=None):
    try:a=F(lower);b=a if upper is None else F(upper)
    except (ValueError,TypeError,OverflowError):raise ValueError('finite exact-compatible endpoints required') from None
    if a>b:raise ValueError('ordered input endpoints required')
    return _Box(endpoint(a,False),endpoint(b,True))


@dataclass(frozen=True)
class Jet:
    value:_Box
    derivative:tuple

    def __post_init__(self):
        if (not isinstance(self.value,_Box) or len(self.derivative)!=27
                or not all(isinstance(v,_Box) for v in self.derivative)):
            raise ValueError('complete value and all 27 interval derivatives required')

    @classmethod
    def constant(cls,value):
        box=value if isinstance(value,_Box) else _input_box(value)
        return cls(box,tuple(_Box(0.) for _ in range(27)))

    @classmethod
    def variable(cls,lower,upper,index):
        if type(index)!=int or not 0<=index<27:raise ValueError('one of all 27 physical coordinates required')
        return cls(_input_box(lower,upper),tuple(_Box(float(j==index)) for j in range(27)))

    @staticmethod
    def cast(value):return value if isinstance(value,Jet) else Jet.constant(value)

    def __add__(self,other):
        other=self.cast(other)
        return Jet(_add(self.value,other.value),tuple(_add(a,b) for a,b in zip(self.derivative,other.derivative)))

    __radd__=__add__

    def __neg__(self):return Jet(-self.value,tuple(-v for v in self.derivative))
    def __sub__(self,other):return self+-self.cast(other)
    def __rsub__(self,other):return self.cast(other)+-self

    def __mul__(self,other):
        other=self.cast(other)
        return Jet(_mul(self.value,other.value),tuple(_add(_mul(a,other.value),_mul(self.value,b))
            for a,b in zip(self.derivative,other.derivative)))

    __rmul__=__mul__

    def inverse(self):
        if self.value.lo<=0.<=self.value.hi:raise ValueError('inverse domain crosses zero')
        value=_Box(1.)/self.value;square=self.value.square()
        derivative=tuple(_Box(0.) if _zero(v) else -v/square for v in self.derivative)
        return Jet(value,derivative)

    def __truediv__(self,other):return self*self.cast(other).inverse()
    def __rtruediv__(self,other):return self.cast(other)*self.inverse()

    def square(self):
        return Jet(self.value.square(),tuple(_mul(_Box(2.)*self.value,v) for v in self.derivative))


def _matrix_product(a,b):
    return [[sum((a[i][k]*b[k][j] for k in range(3)),Jet.constant(0.)) for j in range(3)] for i in range(3)]


def exp_skew(vector):
    """Degree-12 exponential with separate analytic value/derivative tails.

    ||skew(v)||_2=||v||_2. For the omitted terms, bound the value tail from
    order 13 and the first Frechet derivative tail from order 12. Each scalar
    derivative retains the norm of the complete derivative of v with respect
    to that physical coordinate. No sampled derivative supplies the bound.
    """
    if len(vector)!=3 or not all(isinstance(v,Jet) for v in vector):
        raise ValueError('three complete interval-derivative coordinates required')
    a=F(sqrt_upper(sum((max(abs(F(v.value.lo)),abs(F(v.value.hi)))**2 for v in vector),F(0))))
    if a>8:raise ValueError('matrix exponential supports rotation norm at most eight')
    x,y,z=vector;zero=Jet.constant(0.)
    k=[[zero,-z,y],[z,zero,-x],[-y,x,zero]]
    term=[[Jet.constant(int(i==j)) for j in range(3)] for i in range(3)]
    result=[row[:] for row in term]
    for order in range(1,13):
        term=[[v/order for v in row] for row in _matrix_product(term,k)]
        result=[[result[i][j]+term[i][j] for j in range(3)] for i in range(3)]
    tail=a**13/F(math.factorial(13))/(1-a/14)
    derivative_tail=a**12/F(math.factorial(12))/(1-a/13)
    radius=endpoint(tail,True);derivative_radii=[]
    for column in range(27):
        norm=F(sqrt_upper(sum((max(abs(F(v.derivative[column].lo)),abs(F(v.derivative[column].hi)))**2
            for v in vector),F(0))))
        derivative_radii.append(endpoint(derivative_tail*norm,True))
    return [[Jet(_add(v.value,_Box(-radius,radius)),
        tuple(_add(g,_Box(-r,r)) for g,r in zip(v.derivative,derivative_radii))) for v in row] for row in result]


def couple(mapped,at_center,lower,upper,center):
    """Necessary mean-value inequalities, with no physical region discarded.

    The caller must qualify that mapped gradients enclose the SAME source map
    throughout the declared box, and at_center encloses that map at center.
    This primitive checks dimensions, not that source-level premise.
    """
    if (len(mapped)!=24 or len(at_center)!=24 or any(len(v)!=27 for v in (lower,upper,center))
            or not all(isinstance(v,Jet) for v in list(mapped)+list(at_center))):
        raise ValueError('all 27 physical and 24 common-error coordinates required')
    lo=list(map(F,lower));hi=list(map(F,upper));c=list(map(F,center))
    if any(not a<=v<=b for a,v,b in zip(lo,c,hi)):raise ValueError('box center must be in the complete physical region')
    distances=[max(v-a,b-v) for a,v,b in zip(lo,c,hi)];design=[];bounds=[];radii=[]
    for index,(function,origin) in enumerate(zip(mapped,at_center,strict=True)):
        slope=[float((F(g.lo)+F(g.hi))/2) for g in function.derivative]
        if not all(math.isfinite(v) for v in slope):raise ValueError('finite representable derivative midpoint required')
        error=[max(abs(F(v)-F(g.lo)),abs(F(g.hi)-F(v))) for v,g in zip(slope,function.derivative)]
        radius=sum((a*b for a,b in zip(error,distances)),F(0));radii.append(str(radius))
        shift=sum((F(v)*x for v,x in zip(slope,c)),F(0))
        left=F(origin.value.lo)-shift-radius;right=F(origin.value.hi)-shift+radius
        row=[-v for v in slope]+[float(j==index) for j in range(24)]
        design.extend((row,[-v for v in row]));bounds.extend((endpoint(right,True),endpoint(-left,True)))
    return dict(parameter_count=51,physical_parameter_count=27,common_error_count=24,
        physical_lower=list(lower),physical_upper=list(upper),center=list(center),design=design,upper=bounds,
        mean_value_radii=radii,source_map_qualified=False,observational_coverage_qualified=False,
        scientific_decision='abstain')
