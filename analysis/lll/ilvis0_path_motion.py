# SPDX-License-Identifier: AGPL-3.0-or-later
"""Third-order interval midpoint step; not full-history native qualification.

Encloses ideal real arithmetic using the native rotation branch expressions.
Outward dyadic rounding controls rational denominator growth. Floating native
execution and complete clock-boundary coverage remain separate requirements.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from .ilvis0_path_jets import Jet3 as J
from .ilvis0_path_geometry import sincos,positive_sqrt,rates,context


def _q(value):return value.rounded(binary_bits=96)


def _product(a,b):
    return tuple(tuple(_q(sum((a[i][k]*b[k][j] for k in range(3)),J.constant(0)))
        for j in range(3)) for i in range(3))


def _mv(a,v):
    return tuple(_q(sum((a[i][k]*v[k] for k in range(3)),J.constant(0))) for i in range(3))


def _cross(a,b):
    return tuple(_q(a[i]*b[j]-a[j]*b[i]) for i,j in ((1,2),(2,0),(0,1)))


def exponential(vector):
    """Native Rodrigues branches, including its small-angle polynomial.

A domain crossing the native switch must be split before this operation.
The polynomial branch is not silently replaced by an exact rotation.
"""
    if len(vector)!=3 or not all(isinstance(v,J) for v in vector):
        raise ValueError('three complete angular increment derivatives required')
    x,y,z=map(_q,vector);q=_q(x.square()+y.square()+z.square());threshold=F(1e-4)
    if q.exact[0][1]<threshold:
        q2=q.square();q3=q2*q
        a=_q(1-q/6+q2/120-q3/5040)
        b=_q(F(1,2)-q/24+q2/720-q3/40320)
    elif q.exact[0][0]>=threshold:
        root=_q(positive_sqrt(q));si,co=sincos(root)
        a=_q(si/root);b=_q((1-co)/q)
    else:raise ValueError('rotation domain crosses native exponential branch; split required')
    zero=J.constant(0);k=((zero,-z,y),(z,zero,-x),(-y,x,zero));kk=_product(k,k)
    return tuple(tuple(_q(int(i==j)+a*k[i][j]+b*kk[i][j]) for j in range(3)) for i in range(3))


@dataclass(frozen=True)
class State:
    coordinates:tuple
    velocity:tuple
    attitude:tuple

    def __post_init__(self):
        if (len(self.coordinates)!=3 or len(self.velocity)!=3 or len(self.attitude)!=3
                or any(len(row)!=3 for row in self.attitude)
                or not all(isinstance(v,J) for v in (*self.coordinates,*self.velocity,
                    *(v for row in self.attitude for v in row)))):
            raise ValueError('complete three-axis coordinate, velocity and matrix derivatives required')

    def report(self):
        return dict(version='ilvis0-third-order-midpoint-state-v1',
            coordinates=[v.report() for v in self.coordinates],velocity=[v.report() for v in self.velocity],
            attitude=[[v.report() for v in row] for row in self.attitude],
            derivative_order=3,dyadic_bits=96,ideal_native_step_expressions=True,
            floating_point_execution_covered=False,clock_partition_verified=False,
            native_history_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def _local(state,theta,dv,period,earth,transport,latitude,removal,gravity):
    standard,_=context(0,latitude,(J.constant(0),)*3)
    win=tuple(_q(e+t-removal*s) for e,t,s in zip(earth,transport,standard))
    argument=tuple(_q((2*e+t)*period/2) for e,t in zip(earth,transport))
    left=exponential([_q(-w*period/2) for w in win]);right=exponential([_q(v/2) for v in theta])
    middle=_product(_product(left,state.attitude),right);force=_mv(middle,dv)
    full_left=exponential([_q(-w*period) for w in win]);full_right=exponential(theta)
    attitude=_product(_product(full_left,state.attitude),full_right)
    av=_cross(argument,state.velocity)
    rhs=tuple(_q(v-a+f+(gravity*period if i==2 else 0))
        for i,(v,a,f) in enumerate(zip(state.velocity,av,force)))
    ar=_cross(argument,rhs);dot=_q(sum((a*b for a,b in zip(argument,rhs)),J.constant(0)))
    den=_q(1+sum((a.square() for a in argument),J.constant(0)))
    velocity=tuple(_q((r-c+a*dot)/den) for r,c,a in zip(rhs,ar,argument))
    return attitude,velocity


def step(model,state,theta,dv,period,gravity,radius,removal):
    """Two local solves and the revised-rate coordinate update of native step."""
    if (not isinstance(state,State) or len(theta)!=3 or len(dv)!=3
            or not all(isinstance(v,J) for v in (*theta,*dv,period,gravity,radius,removal))
            or period.exact[0][0]<0 or gravity.exact[0][0]<=0
            or not 0<=removal.exact[0][0]<=removal.exact[0][1]<=1):
        raise ValueError('complete step derivatives and physical period/gravity/removal required')
    rate=tuple(map(_q,rates(model,state.coordinates,state.velocity,radius)))
    middle=tuple(_q(c+r*period/2) for c,r in zip(state.coordinates,rate))
    earth,transport=context(model,middle[0],rate)
    _,estimate=_local(state,theta,dv,period,earth,transport,middle[0],removal,gravity)
    average=tuple(_q((v+e)/2) for v,e in zip(state.velocity,estimate))
    revised=tuple(map(_q,rates(model,middle,average,radius)))
    earth,transport=context(model,middle[0],revised)
    attitude,velocity=_local(state,theta,dv,period,earth,transport,middle[0],removal,gravity)
    coordinates=tuple(_q(c+r*period) for c,r in zip(state.coordinates,revised))
    return State(coordinates,velocity,attitude)
