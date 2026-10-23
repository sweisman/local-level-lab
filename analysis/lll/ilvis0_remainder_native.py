# SPDX-License-Identifier: AGPL-3.0-or-later
"""Direct-source native candidate; frozen predecessors remain unchanged.

All 24 auxiliary columns are mandatory. This component is not a qualified
observed-data adapter, whole-program roundoff bound or coverage statement.
"""
from dataclasses import dataclass,field
from fractions import Fraction as F
import math
import hashlib
import json
import time as _timer

import numpy as np
from scipy.linalg import expm_frechet
from . import ilvis0_shared_native as previous,ilvis0_batched_relative as relative
from . import ilvis0_component_geography as geo,ilvis0_history_bounds as history
from .ilvis0_local_step_bounds import Matrix,exponential,inverse_skew,OMEGA
from .ilvis0_batched_transport import Value,add,scale,scalar_product,matrix_vector,cross
from .ilvis0_increment_remainders import calibrated_box
from .ilvis0_direct_source_taylor import SourceDirectStream as SourceValueStream
from .ilvis0_source_stream import SourceStream
from .ilvis0_direct_source_taylor import DirectBodyInterval as RoundedBodyInterval
from .ilvis0_correlated_clock import PrefixClock
from .ilvis0_shared_reference_terms import ReferenceErrors,SharedCoefficients,_readonly,_skew,_upper
from .ilvis0_reference_acceleration import AccelerationTerms,AccelerationCoefficients

VERSION='ilvis0-conditional-remainder-native-v1'


def _component_change(row,reference,remainder,full_change):
    displacements=[max(abs(F(float(x))-F(float(a))),abs(F(float(b))-F(float(x))))
        for a,b,x in zip(reference.lower,reference.upper,reference.center)]
    total=sum((abs(F(float(v)))*d for v,d in zip(row,displacements)),F(float(remainder)))
    return min(full_change,_upper(total))


from . import ilvis0_acceleration_native as antecedent
from .ilvis0_common_force_transform import ForceTransform,ForceTransformCoefficients
from .ilvis0_clocked_force_transform import ClockedForceTransform
from .ilvis0_force_integrals import enclose as force_integrals
from .ilvis0_shared_reference_terms import _norm


from .ilvis0_transform_native import TransformReference,make_reference
from .ilvis0_conditioned_acceleration import ConditionedAcceleration
from .ilvis0_directional_acceleration import DirectionalAcceleration


def _matrix_bound(transform,lower,upper):
    r=transform.reference;z=r.center;limits=r.limits
    lo=limits*np.minimum(lower,z);hi=limits*np.maximum(upper,z);p=limits*z
    delta=limits*np.maximum(z-np.minimum(lower,z),np.maximum(upper,z)-z)
    angle=_norm(F(float(v)) for v in delta[:3]);norm=F(relative.Delta(r.initial_r).norm);changes=[]
    for column in range(3):
        dc=1/(1+F(float(p[18+column])));left=1/(1+F(float(lo[18+column])));right=1/(1+F(float(hi[18+column])))
        offset=sum((abs(F(float(transform.center[axis,column]))-F(float(r._r_center[axis,column]))*dc) for axis in range(3)),F(0))
        changes.append(norm*(F(min(2.,angle))*abs(dc)+max(abs(left-dc),abs(right-dc)))+offset)
    caps=transform.caps.reshape(3,3)
    if not np.array_equal(caps[0],caps[1]) or not np.array_equal(caps[0],caps[2]):
        raise ValueError('qualified column-norm transform caps required')
    return relative.Delta(transform.center,_norm(changes),_norm(F(float(v)) for v in caps[0]))


def _rates(position,initial_components,acceleration,common,matrix_force,residual_velocity,metric,model,radius):
    current=previous._metric(position,model,radius);full=[];rest=[]
    for axis,(m,fixed) in enumerate(zip(current,metric)):
        a=acceleration[axis];u=geo._component(residual_velocity,axis)
        base=geo.plus(geo.plus(initial_components[axis],geo.times(a,common)),geo._component(matrix_force,axis))
        departure=geo.plus(geo.times(m,u),geo.times(geo.plus(m,geo.Scalar.fixed(-fixed)),base))
        rest.append(departure);full.append(geo.plus(geo.fixed_scale(base,fixed),departure))
    return tuple(full),tuple(rest)


def _recenter(value,center):
    center=np.asarray(center,float)
    shifts=[abs(F(float(c))-F(float(v))) for c,v in zip(center,value.center,strict=True)]
    norm=F(_norm(shifts))
    return Value(center,_upper(F(value.change)+norm),_upper(F(value.remainder)+norm),
        component_change=[_upper(F(float(d))+e) for d,e in zip(value.component_change,shifts,strict=True)],
        component_remainder=[_upper(F(float(d))+e) for d,e in zip(value.component_remainder,shifts,strict=True)])


def _increment(state,left,right,initial_r,theta,force_difference,raw_difference,reference_force,acceleration,matrix,
               latitude,transport,period,removal,model,source):
    phi=latitude.center
    standard=Value(OMEGA*np.array([math.cos(phi),0.,-math.sin(phi)]),
        geo._up(min(2*OMEGA,OMEGA*latitude.value.change)),
        geo._up(.5*OMEGA*latitude.value.change**2+OMEGA*latitude.value.remainder))
    earth=standard if model=='sphere_rotating' else Value(np.zeros(3))
    win=add(add(earth,transport),scale(scalar_product(removal.value,standard),-1.))
    argument=scalar_product(scale(period.value,.5),add(scale(earth,2.),transport))
    middle_left=relative.advance_left(left,exponential(scalar_product(scale(period.value,-.5),win)))
    middle_right=relative.advance_right(right,exponential(scale(theta,.5)))
    # (Q R P-R)f0 = (Q-I)(A+B)+B. Later force differences retain
    # their original treatment; the point expression keeps its old order.
    constant=add(relative.apply(middle_left,add(source.a,source.b)),source.b)
    force_rest=add(constant,relative.action(middle_left,middle_right,initial_r,force_difference))
    vector=reference_force.center+force_difference.center
    first=((middle_left.center@initial_r.center)@(middle_right.center+np.eye(3)))@vector
    second=(initial_r.center@middle_right.center)@vector
    force_rest=_recenter(force_rest,first+second)
    delta_g=scalar_product(period.value,Value(raw_difference))
    matrix_delta_g=relative.apply(matrix,delta_g)
    rhs=add(scalar_product(period.value,force_rest),scale(cross(argument,state.velocity),-2.))
    rhs=add(rhs,scale(scalar_product(period.value,cross(argument,acceleration)),-1.))
    rhs=add(rhs,scale(cross(argument,matrix_delta_g),-1.))
    dw=matrix_vector(inverse_skew(argument),rhs)
    next_left=relative.advance_left(left,exponential(scalar_product(scale(period.value,-1.),win)))
    next_right=relative.advance_right(right,exponential(theta))
    return next_left,next_right,dw


from .ilvis0_dyadic_native import TransformEnclosure

def enclose(configuration,theta,dv,dt,*,time,lower,upper,reference,conditioning,source_kernel,derivative_kernel,point_kernel,maximum_seconds=30.):
    from .ilvis0_native_prefix import _cold_enclose
    return _cold_enclose(configuration,theta,dv,dt,time=time,lower=lower,upper=upper,
        reference=reference,conditioning=conditioning,source_kernel=source_kernel,
        derivative_kernel=derivative_kernel,point_kernel=point_kernel,maximum_seconds=maximum_seconds)
