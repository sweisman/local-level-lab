# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact training-residual scale bounds under an explicitly supplied Gaussian law.

This qualifies arithmetic, not the law's applicability to real receiver errors.
Any coefficients in a fixed reference space are permitted. Counting all reference
columns gives conservative degrees of freedom even when they are dependent.
"""
from dataclasses import dataclass, field
from fractions import Fraction as F
import math
import time


class Unsupported(ValueError):
    """A cooperative computation limit or representable domain was exceeded."""


@dataclass
class Budget:
    maximum_steps: int = 1000
    maximum_bits: int = 131072
    maximum_seconds: float = 30.
    steps: int = field(default=0,init=False)
    started: float = field(default_factory=time.monotonic,init=False)

    def check(self, values=(), *, advance=False):
        if advance:self.steps+=1
        if self.steps>self.maximum_steps:raise Unsupported('step allowance exhausted')
        if time.monotonic()-self.started>=self.maximum_seconds:raise Unsupported('time allowance exhausted')
        if any(max(v.numerator.bit_length(),v.denominator.bit_length())>self.maximum_bits for v in values):
            raise Unsupported('precision allowance exhausted')

    def __post_init__(self):
        if (type(self.maximum_steps) is not int or self.maximum_steps<0
                or type(self.maximum_bits) is not int or self.maximum_bits<1
                or not math.isfinite(self.maximum_seconds) or self.maximum_seconds<0):
            raise ValueError('finite nonnegative work/time and positive precision limits required')


@dataclass(frozen=True)
class Covariance:
    rho: F
    white: F
    correlated: F
    offset: F
    drift: F

    def __post_init__(self):
        for name in ('rho','white','correlated','offset','drift'):
            object.__setattr__(self,name,F(getattr(self,name)))
        if not (0<=self.rho<=1 and self.white>0 and min(self.correlated,self.offset,self.drift)>=0):
            raise ValueError('rho in [0,1], positive white variance and nonnegative state variances required')


def residual_quadratic(residuals, law, *, budget):
    """Return exactly r' C^-1 r for uniform epochs with drift anchored to [0,1].

    C_ij = correlated*rho**abs(i-j) + offset + drift*t_i*t_j
           + white*1(i==j). State updates use rational scalar innovations.
    No observations outside the supplied training residuals are accepted.
    """
    if not isinstance(law,Covariance) or not isinstance(budget,Budget):
        raise ValueError('explicit covariance and cooperative budget required')
    n=len(residuals)
    if n<2:raise ValueError('at least two uniformly spaced training residuals required')
    budget.check((law.rho,law.white,law.correlated,law.offset,law.drift))
    p=[[F(0) for _ in range(3)] for _ in range(3)]
    for j,v in enumerate((law.correlated,law.offset,law.drift)):p[j][j]=v
    m=[F(0)]*3;total=F(0);transition=(law.rho,F(1),F(1))
    for i,value in enumerate(residuals):
        y=F(value);budget.check([y],advance=True)
        h=(F(1),F(1),F(i,n-1))
        ph=[sum((p[j][k]*h[k] for k in range(3)),F(0)) for j in range(3)]
        s=law.white+sum((h[j]*ph[j] for j in range(3)),F(0))
        if s<=0:raise Unsupported('nonpositive innovation variance')
        e=y-sum((h[j]*m[j] for j in range(3)),F(0))
        total+=e*e/s
        m=[transition[j]*(m[j]+ph[j]*e/s) for j in range(3)]
        p=[[transition[j]*transition[k]*(p[j][k]-ph[j]*ph[k]/s) for k in range(3)] for j in range(3)]
        p[0][0]+=law.correlated*(1-law.rho**2)
        budget.check([total,*m,*(v for row in p for v in row)])
    return total


def quantile_floor(degrees, alpha, *, maximum_moment=64, binary_digits=32):
    """A positive dyadic floor certified by an inverse-chi-square moment.

    Markov: P(X <= q) <= q**k / product(d-2*j), j=1..k.
    All selection and certification use integers, independent of observations.
    """
    alpha=F(alpha)
    if (type(degrees) is not int or not 2<degrees<=1000000 or not 0<alpha<1
            or type(maximum_moment) is not int or not 1<=maximum_moment<=64
            or type(binary_digits) is not int or not 1<=binary_digits<=64):
        raise ValueError('supported positive residual dimension, probability and finite moment grid required')
    scale=1<<binary_digits;best=0;best_k=0;product=1
    for k in range(1,min(maximum_moment,(degrees-1)//2)+1):
        product*=degrees-2*k
        target=(alpha.numerator*product*scale**k)//alpha.denominator
        left,right=0,degrees*scale+1
        while right-left>1:
            mid=(left+right)//2
            if mid**k<=target:left=mid
            else:right=mid
        if left>best:best,best_k=left,k
    if not best:raise Unsupported('positive quantile floor unrepresentable on declared dyadic grid')
    q=F(best,scale);denominator=math.prod(degrees-2*j for j in range(1,best_k+1))
    return dict(q=q,k=best_k,tail_bound=q**best_k/denominator,degrees=degrees,alpha=alpha)


def sqrt_upper(value):
    """Smallest finite binary64 upper square root, checked by exact squaring."""
    value=F(value)
    if value<0:raise ValueError('nonnegative square required')
    if not value:return 0.
    exponent=value.numerator.bit_length()-value.denominator.bit_length()
    exponent-=exponent%2
    scaled=value/(1<<exponent) if exponent>=0 else value*(1<<(-exponent))
    try:upper=math.ldexp(math.sqrt(float(scaled)),exponent//2)
    except OverflowError:raise Unsupported('scale exceeds finite endpoint range') from None
    if not math.isfinite(upper):raise Unsupported('scale exceeds finite endpoint range')
    while F(upper)**2<value:
        upper=math.nextafter(upper,math.inf)
        if not math.isfinite(upper):raise Unsupported('scale exceeds finite endpoint range')
    while upper and F(math.nextafter(upper,0.))**2>=value:upper=math.nextafter(upper,0.)
    return upper


def scale_upper(quadratic, *, observations, reference_columns, alpha):
    """Bound a common noise scale; every supplied reference column counts.

    The reference subspace and covariance must be fixed independently of errors.
    The caller must establish that the residual belongs to that declared model.
    """
    quadratic=F(quadratic)
    if (quadratic<0 or type(observations) is not int or type(reference_columns) is not int
            or reference_columns<1 or observations-reference_columns<=2):
        raise ValueError('nonnegative quadratic and more than two residual degrees required')
    quantile=quantile_floor(observations-reference_columns,alpha)
    return dict(upper=sqrt_upper(quadratic/quantile['q']),degrees=observations-reference_columns,
        quantile=quantile,quadratic=quadratic,reference_columns=reference_columns,
        covariance_shape_established=False,observational_coverage_qualified=False,scientific_decision='abstain')


def polynomial_residuals(values, coefficients):
    """Exact residuals for the fixed basis 1,t,... on uniform t in [-1,1]."""
    if len(values)<2 or not len(coefficients):raise ValueError('nonempty coefficients and at least two epochs required')
    coefficients=[F(v) for v in coefficients];result=[]
    for i,value in enumerate(values):
        t=F(2*i,len(values)-1)-1;reference=F(0)
        for coefficient in reversed(coefficients):reference=reference*t+coefficient
        result.append(F(value)-reference)
    return result
