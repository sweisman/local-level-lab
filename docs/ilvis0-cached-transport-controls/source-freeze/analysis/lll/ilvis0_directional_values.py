# SPDX-License-Identifier: AGPL-3.0-or-later
"""Componentwise change/Taylor bounds, separate from every frozen engine.

Centers are binary64 reference values. Bounds use exact rational arithmetic
and outward exports, including rounding of each operation's new center.
Input change and remainder bounds must already be justified. No derivative,
measurement-error law or complete native propagation is supplied here.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math
import numpy as np
from .ilvis0_saved_prediction_audit import endpoint
from .ilvis0_exact_scale import sqrt_upper


def _radii(values,shape):
    raw=np.asarray(values,dtype=object)
    if raw.shape!=shape:raise ValueError('component radii must match the center shape')
    try:exact=[F(v) for v in raw.flat]
    except (ValueError,OverflowError,TypeError):raise ValueError('finite rational radii required') from None
    if any(v<0 for v in exact):raise ValueError('nonnegative radii required')
    result=np.array([endpoint(v,True) for v in exact]).reshape(shape);result.setflags(write=False)
    return result


@dataclass(frozen=True)
class Value:
    center:object
    change:object
    remainder:object

    def __post_init__(self):
        c=np.array(self.center,dtype=float,copy=True)
        if c.shape not in ((),(3,)) or not np.all(np.isfinite(c)):raise ValueError('finite scalar or three-vector center required')
        c.setflags(write=False);object.__setattr__(self,'center',c)
        object.__setattr__(self,'change',_radii(self.change,c.shape))
        object.__setattr__(self,'remainder',_radii(self.remainder,c.shape))

    def component(self,axis):
        if self.center.shape!=(3,) or type(axis)!=int or not 0<=axis<3:raise ValueError('one vector coordinate required')
        return Value(float(self.center[axis]),float(self.change[axis]),float(self.remainder[axis]))

    def legacy(self):
        from .ilvis0_local_step_bounds import Value as NormValue
        change=sqrt_upper(sum((F(v)**2 for v in self.change.flat),F(0)))
        remainder=sqrt_upper(sum((F(v)**2 for v in self.remainder.flat),F(0)))
        return NormValue(self.center,change,remainder)

    def report(self):
        return dict(center=self.center.tolist(),component_change=self.change.tolist(),
            component_remainder=self.remainder.tolist(),input_bounds_require_qualification=True,
            native_propagation_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def _require(value,shape=None):
    if not isinstance(value,Value) or (shape is not None and value.center.shape!=shape):
        raise ValueError('typed directional value with the required shape needed')


def _output(center,change,remainder):
    shape=np.asarray(center).shape
    return Value(center,np.array(change,dtype=object).reshape(shape),np.array(remainder,dtype=object).reshape(shape))


def add(a,b):
    _require(a);_require(b,a.center.shape);center=a.center+b.center;change=[];remainder=[]
    for x,y,c,dx,dy,rx,ry in zip(a.center.flat,b.center.flat,center.flat,a.change.flat,b.change.flat,a.remainder.flat,b.remainder.flat):
        error=abs(F(c)-F(x)-F(y));change.append(F(dx)+F(dy)+error);remainder.append(F(rx)+F(ry)+error)
    return _output(center,change,remainder)


def scale(a,number):
    _require(a)
    if not math.isfinite(number):raise ValueError('finite fixed scalar required')
    s=F(number);center=a.center*float(number);change=[];remainder=[]
    for x,c,dx,rx in zip(a.center.flat,center.flat,a.change.flat,a.remainder.flat):
        error=abs(F(c)-F(x)*s);change.append(abs(s)*F(dx)+error);remainder.append(abs(s)*F(rx)+error)
    return _output(center,change,remainder)


def _product_bounds(x,y,dx,dy,rx,ry):
    # Bounds for a product before rounding its exported center.
    return abs(F(x))*F(dy)+abs(F(y))*F(dx)+F(dx)*F(dy),abs(F(x))*F(ry)+abs(F(y))*F(rx)+F(dx)*F(dy)


def scalar_product(a,b):
    _require(a,());_require(b,(3,));center=a.center*b.center;change=[];remainder=[]
    for j in range(3):
        d,r=_product_bounds(a.center.item(),b.center[j],a.change.item(),b.change[j],a.remainder.item(),b.remainder[j])
        error=abs(F(center[j])-F(a.center.item())*F(b.center[j]));change.append(d+error);remainder.append(r+error)
    return _output(center,change,remainder)


def cross(a,b):
    _require(a,(3,));_require(b,(3,));center=np.cross(a.center,b.center);change=[];remainder=[]
    for axis,(j,k) in enumerate(((1,2),(2,0),(0,1))):
        d1,r1=_product_bounds(a.center[j],b.center[k],a.change[j],b.change[k],a.remainder[j],b.remainder[k])
        d2,r2=_product_bounds(a.center[k],b.center[j],a.change[k],b.change[j],a.remainder[k],b.remainder[j])
        error=abs(F(center[axis])-(F(a.center[j])*F(b.center[k])-F(a.center[k])*F(b.center[j])))
        change.append(d1+d2+error);remainder.append(r1+r2+error)
    return _output(center,change,remainder)
