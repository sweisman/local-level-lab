# SPDX-License-Identifier: AGPL-3.0-or-later
"""Global mathematical geographic-step bounds under declared input regions.

Scalar intervals preserve asymmetric domains. Vector/matrix Taylor bounds reuse
the separately qualified local primitives. No archive inputs or decisions.
Packet-boundary support and a whole-record rounding enclosure remain open.
"""
from dataclasses import dataclass
import math

import numpy as np

from .ilvis0_local_step_bounds import (Value,Matrix,add,scale,scalar_product,matrix_product,matrix_vector,
    exponential,inverse_skew,_cayley,OMEGA)

VERSION='ilvis0-geographic-global-step-bounds-v1'
A=6378137.;E2=6.69437999014e-3


def _up(x):
    x=float(x)
    if not math.isfinite(x) or x<0.:raise ValueError('finite nonnegative global radius required')
    return float(np.nextafter(x,np.inf)) if x else 0.


def _ends(lo,hi):return float(np.nextafter(lo,-np.inf)),float(np.nextafter(hi,np.inf))


@dataclass(frozen=True)
class Scalar:
    value:Value
    lower:float
    upper:float

    def __post_init__(self):
        if not isinstance(self.value,Value) or self.value.center.shape!=():raise ValueError('bounded scalar required')
        c=float(self.value.center);lo=float(self.lower);hi=float(self.upper)
        if not math.isfinite(lo+hi) or not lo<=c<=hi:raise ValueError('finite physical interval containing center required')
        if self.value.change:
            a,b=_ends(c-self.value.change,c+self.value.change);lo=max(lo,a);hi=min(hi,b)
        else:lo=hi=c
        change=min(self.value.change,_up(max(abs(lo-c),abs(hi-c))))
        object.__setattr__(self,'lower',lo);object.__setattr__(self,'upper',hi)
        object.__setattr__(self,'value',Value(c,change,self.value.remainder))

    @classmethod
    def interval(cls,center,lower,upper,remainder=0.):
        return cls(Value(center,_up(max(abs(lower-center),abs(upper-center))),remainder),lower,upper)

    @classmethod
    def fixed(cls,center):return cls(Value(center),center,center)

    @property
    def center(self):return float(self.value.center)

    def report(self):return dict(self.value.report(),lower=self.lower,upper=self.upper)


def _result(center,change,remainder,lo,hi):return Scalar(Value(center,_up(change),_up(remainder)),*_ends(lo,hi))


def plus(a,b):
    return _result(a.center+b.center,a.value.change+b.value.change,a.value.remainder+b.value.remainder,
        a.lower+b.lower,a.upper+b.upper)


def times(a,b):
    corners=[x*y for x in (a.lower,a.upper) for y in (b.lower,b.upper)]
    change=abs(a.center)*b.value.change+abs(b.center)*a.value.change+a.value.change*b.value.change
    error=abs(a.center)*b.value.remainder+abs(b.center)*a.value.remainder+a.value.change*b.value.change
    return _result(a.center*b.center,change,error,min(corners),max(corners))


def fixed_scale(a,number):
    if not math.isfinite(number):raise ValueError('finite fixed scalar required')
    ends=[a.lower*number,a.upper*number]
    return _result(a.center*number,abs(number)*a.value.change,abs(number)*a.value.remainder,min(ends),max(ends))


def inverse(a):
    if a.lower<=0.<=a.upper:raise ValueError('inverse domain crosses zero')
    center=1./a.center;ends=[1./a.lower,1./a.upper];minimum=min(abs(a.lower),abs(a.upper))
    error=a.value.change**2/(a.center**2*minimum)+a.value.remainder/a.center**2
    return _result(center,max(abs(x-center) for x in ends),error,min(ends),max(ends))


def power(a,exponent):
    if a.lower<=0. or not math.isfinite(exponent):raise ValueError('positive finite power domain required')
    center=a.center**exponent;ends=[a.lower**exponent,a.upper**exponent]
    derivative=exponent*a.center**(exponent-1.)
    hessian=abs(exponent*(exponent-1.))*max(a.lower**(exponent-2.),a.upper**(exponent-2.))
    error=.5*hessian*a.value.change**2+abs(derivative)*a.value.remainder
    return _result(center,max(abs(x-center) for x in ends),error,min(ends),max(ends))


def _trig(a,cosine):
    f=math.cos if cosine else math.sin;center=f(a.center)
    if a.upper-a.lower>=2.*math.pi:lo,hi=-1.,1.
    else:
        phase=0. if cosine else math.pi/2.;values=[f(a.lower),f(a.upper)]
        for k in range(math.ceil((a.lower-phase)/math.pi),math.floor((a.upper-phase)/math.pi)+1):values.append(1. if k%2==0 else -1.)
        lo,hi=min(values),max(values)
    derivative=-math.sin(a.center) if cosine else math.cos(a.center)
    error=.5*a.value.change**2+abs(derivative)*a.value.remainder
    return _result(center,max(abs(lo-center),abs(hi-center)),error,lo,hi)


def sine(a):return _trig(a,False)
def cosine(a):return _trig(a,True)


def _pack(values):
    return Value([v.center for v in values],_up(np.linalg.norm([v.value.change for v in values])),
        _up(np.linalg.norm([v.value.remainder for v in values])))


def _component(vector,axis):
    center=float(vector.center[axis]);lo,hi=_ends(center-vector.change,center+vector.change)
    return Scalar(Value(center,vector.change,vector.remainder),lo,hi)


@dataclass(frozen=True)
class Coordinates:
    latitude:Scalar
    longitude:Scalar
    height:Scalar

    def __post_init__(self):
        if not all(isinstance(v,Scalar) for v in (self.latitude,self.longitude,self.height)):raise ValueError('separate scalar coordinate bounds required')
        if self.latitude.lower<=-math.pi/2+1e-6 or self.latitude.upper>=math.pi/2-1e-6:raise ValueError('global polar coordinate domain unsupported')

    @property
    def center(self):return np.array([v.center for v in (self.latitude,self.longitude,self.height)])

    def report(self):
        return dict(latitude=self.latitude.report(),longitude=self.longitude.report(),height=self.height.report(),
            units=['rad','rad','m'],longitude_wrapped=False)


@dataclass(frozen=True)
class State:
    position:Coordinates
    velocity:Value
    attitude:Matrix

    def __post_init__(self):
        if (not isinstance(self.position,Coordinates) or not isinstance(self.velocity,Value) or self.velocity.center.shape!=(3,)
                or not isinstance(self.attitude,Matrix) or self.attitude.structure!='rotation'):
            raise ValueError('complete geographic/velocity/rotation bounds required')

    def report(self):
        return dict(version=VERSION,position=self.position.report(),velocity=self.velocity.report(),attitude=self.attitude.report(),
            native_full_map_covered=False,packet_boundary_crossing_covered=False,floating_point_enclosure_verified=False,
            scientific_decision='abstain')


def coordinate_map(position,vector,*,model,disc_radius_m):
    """Inverse candidate metric on a local velocity or lever displacement."""
    if not isinstance(position,Coordinates) or not isinstance(vector,Value) or vector.center.shape!=(3,):raise ValueError('coordinate and local vector bounds required')
    if not math.isfinite(disc_radius_m) or disc_radius_m<=0.:raise ValueError('explicit positive disc radius required')
    phi=position.latitude;height=position.height
    if model=='flat_still':
        north=Scalar.fixed(disc_radius_m);east=fixed_scale(plus(Scalar.fixed(math.pi/2),fixed_scale(phi,-1.)),disc_radius_m)
    elif model in ('sphere_rotating','sphere_still'):
        s=sine(phi);d=plus(Scalar.fixed(1.),fixed_scale(times(s,s),-E2))
        north=plus(fixed_scale(power(d,-1.5),A*(1.-E2)),height)
        east=times(plus(fixed_scale(power(d,-.5),A),height),cosine(phi))
    else:raise ValueError('supported physical candidate required')
    if min(north.lower,east.lower)<=0.:raise ValueError('nonpositive geographic metric domain')
    return (times(_component(vector,0),inverse(north)),times(_component(vector,1),inverse(east)),fixed_scale(_component(vector,2),-1.))


def transport_context(latitude,rates,model):
    if model=='flat_still':return _pack((Scalar.fixed(0.),Scalar.fixed(0.),fixed_scale(rates[1],-1.)))
    return _pack((times(cosine(latitude),rates[1]),fixed_scale(rates[0],-1.),fixed_scale(times(sine(latitude),rates[1]),-1.)))


def _local(state,theta,dv,latitude,transport,period,removal,gravity,model):
    # New interface identity: explicit physical intervals are distinct from
    # symmetric change balls. Reuse the frozen operator primitives unchanged.
    if period.lower<0. or removal.lower<0. or removal.upper>1. or gravity.lower<=0.:
        raise ValueError('valid physical period/removal/gravity intervals required')
    phi=latitude.center
    standard=Value(OMEGA*np.array([math.cos(phi),0.,-math.sin(phi)]),
        _up(min(2.*OMEGA,OMEGA*latitude.value.change)),_up(.5*OMEGA*latitude.value.change**2+OMEGA*latitude.value.remainder))
    earth=standard if model=='sphere_rotating' else Value(np.zeros(3))
    win=add(add(earth,transport),scale(scalar_product(removal.value,standard),-1.))
    argument=scalar_product(scale(period.value,.5),add(scale(earth,2.),transport))
    middle=matrix_product(matrix_product(exponential(scalar_product(scale(period.value,-.5),win)),state.attitude),exponential(scale(theta,.5)))
    attitude=matrix_product(matrix_product(exponential(scalar_product(scale(period.value,-1.),win)),state.attitude),exponential(theta))
    force=matrix_vector(middle,dv)
    g=Value([0.,0.,gravity.center],gravity.value.change,gravity.value.remainder)
    rhs=add(force,scalar_product(period.value,g));b=inverse_skew(argument)
    velocity=add(matrix_vector(_cayley(argument,b),state.velocity),matrix_vector(b,rhs))
    return attitude,velocity


def _advance(position,rates,period):
    return Coordinates(*(plus(v,times(rate,period)) for v,rate in zip((position.latitude,position.longitude,position.height),rates)))


def step(state,theta,dv,*,period,removal,gravity,model,disc_radius_m):
    if not all(isinstance(x,Scalar) for x in (period,removal,gravity)):raise ValueError('explicit scalar physical domains required')
    rates=coordinate_map(state.position,state.velocity,model=model,disc_radius_m=disc_radius_m)
    midpoint=_advance(state.position,rates,fixed_scale(period,.5))
    transport=transport_context(midpoint.latitude,rates,model)
    _,estimate=_local(state,theta,dv,midpoint.latitude,transport,period,removal,gravity,model)
    average=scale(add(state.velocity,estimate),.5)
    revised=coordinate_map(midpoint,average,model=model,disc_radius_m=disc_radius_m)
    transport=transport_context(midpoint.latitude,revised,model)
    attitude,velocity=_local(state,theta,dv,midpoint.latitude,transport,period,removal,gravity,model)
    return State(_advance(state.position,revised,period),velocity,attitude)


def observation(state,lever,*,model,disc_radius_m):
    local=matrix_vector(state.attitude,lever)
    offsets=coordinate_map(state.position,local,model=model,disc_radius_m=disc_radius_m)
    return Coordinates(*(plus(v,o) for v,o in zip((state.position.latitude,state.position.longitude,state.position.height),offsets)))


def partial_packet(state,theta,dv,*,packet_dt,fraction,removal,gravity,model,disc_radius_m):
    if (not isinstance(fraction,Scalar) or fraction.lower<0. or fraction.upper>1.
            or not math.isfinite(packet_dt) or packet_dt<=0.):
        raise ValueError('fraction must remain inside one supported positive-duration packet')
    return step(state,scalar_product(fraction.value,theta),scalar_product(fraction.value,dv),
        period=fixed_scale(fraction,packet_dt),removal=removal,gravity=gravity,model=model,disc_radius_m=disc_radius_m)
