# SPDX-License-Identifier: AGPL-3.0-or-later
"""Common-clock/force regrouping of the unchanged mathematical native map.

Keep complete calibration boxes, field/transport physics and timing domains.
The existing global primitives supply mathematical bounds, not a complete
floating-point execution certificate or observational coverage.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math

import numpy as np
from scipy.linalg import expm
from . import ilvis0_geographic_bounds as geo,ilvis0_history_bounds as old
from .ilvis0_local_step_bounds import (Value,Matrix,add,scale,scalar_product,matrix_product,
    matrix_vector,exponential,inverse_skew,_cayley,OMEGA)
from .ilvis0_increment_remainders import calibrated_box
from .ilvis0_correlated_clock import PrefixClock

VERSION='ilvis0-regrouped-common-clock-history-v1'
MODELS=('sphere_rotating','sphere_still','flat_still')


def _endpoint(value,up):
    result=float(value)
    if (up and F(result)<value) or (not up and F(result)>value):result=math.nextafter(result,math.inf if up else -math.inf)
    if not math.isfinite(result):raise ValueError('finite regrouped endpoint required')
    return result


def _constant(value):
    value=F(value);center=float(value);error=_endpoint(abs(value-F(center)),True)
    return geo.Scalar(Value(center,error,error),_endpoint(value,False),_endpoint(value,True))


def _prefix_scalar(prefix,time,selected_slope,nominal):
    center=float(nominal);discrepancy=abs(F(center)-prefix.center)
    slope_difference=abs(F(float(selected_slope))-prefix.slope)
    extra=slope_difference*(F(time.value.change)+F(time.value.remainder))
    remainder=_endpoint(prefix.remainder+discrepancy+extra,True)
    change=_endpoint(prefix.change+discrepancy,True)
    # The legacy serial floating center can lie a few ulps outside the exact
    # prefix interval. Its discrepancy is already included above; retain both.
    return geo.Scalar(Value(center,change,remainder),min(center,_endpoint(prefix.lower,False)),
        max(center,_endpoint(prefix.upper,True)))


def _local(state,theta,force_rate,latitude,transport,period,removal,gravity,model):
    if period.lower<0 or removal.lower<0 or removal.upper>1 or gravity.lower<=0:
        raise ValueError('supported physical period, removal and gravity required')
    phi=latitude.center
    standard=Value(OMEGA*np.array([math.cos(phi),0.,-math.sin(phi)]),
        geo._up(min(2.*OMEGA,OMEGA*latitude.value.change)),geo._up(.5*OMEGA*latitude.value.change**2+OMEGA*latitude.value.remainder))
    earth=standard if model=='sphere_rotating' else Value(np.zeros(3))
    win=add(add(earth,transport),scale(scalar_product(removal.value,standard),-1.))
    argument=scalar_product(scale(period.value,.5),add(scale(earth,2.),transport))
    middle=matrix_product(matrix_product(exponential(scalar_product(scale(period.value,-.5),win)),state.attitude),exponential(scale(theta,.5)))
    attitude=matrix_product(matrix_product(exponential(scalar_product(scale(period.value,-1.),win)),state.attitude),exponential(theta))
    force=matrix_vector(middle,force_rate)
    gravity_vector=Value([0.,0.,gravity.center],gravity.value.change,gravity.value.remainder)
    # Preserve the common duration before bounding force/gravity cancellation.
    rhs=scalar_product(period.value,add(force,gravity_vector));inverse=inverse_skew(argument)
    velocity=add(matrix_vector(_cayley(argument,inverse),state.velocity),matrix_vector(inverse,rhs))
    return attitude,velocity


def _body(state,theta,force_rate,period,removal,gravity,model,radius):
    rates=geo.coordinate_map(state.position,state.velocity,model=model,disc_radius_m=radius)
    midpoint=geo._advance(state.position,rates,geo.fixed_scale(period,.5))
    transport=geo.transport_context(midpoint.latitude,rates,model)
    _,estimate=_local(state,theta,force_rate,midpoint.latitude,transport,period,removal,gravity,model)
    average=scale(add(state.velocity,estimate),.5)
    revised=geo.coordinate_map(midpoint,average,model=model,disc_radius_m=radius)
    transport=geo.transport_context(midpoint.latitude,revised,model)
    attitude,velocity=_local(state,theta,force_rate,midpoint.latitude,transport,period,removal,gravity,model)
    return attitude,velocity,revised


@dataclass(frozen=True)
class History:
    state:geo.State
    observation:geo.Coordinates
    packet_indices:tuple
    boundary_crossings:int
    reference_rates:tuple
    clock_remainder_s:float
    independent_clock_remainder_s:float


def history(*,initial,theta,dv,durations,starts,time,removal,gravity,lever,model,disc_radius_m,maximum_seconds=30.):
    durations=np.asarray(durations,float);starts=np.asarray(starts,float)
    if (durations.ndim!=1 or not len(durations) or starts.shape!=durations.shape or len(theta)!=len(durations)
            or len(dv)!=len(durations) or not np.all(np.isfinite(durations)) or np.any(durations<=0)):
        raise ValueError('complete contiguous positive increment clock required')
    expected=[];elapsed=0.
    for duration in durations:expected.append(elapsed);elapsed+=float(duration)
    if not np.array_equal(starts,expected) or not isinstance(time,geo.Scalar) or time.lower<0 or time.upper>elapsed:
        raise ValueError('complete unchanged clock and supported time interval required')
    if not isinstance(initial,geo.State) or any(not isinstance(v,Value) or v.center.shape!=(3,) for v in (*theta,*dv)):
        raise ValueError('complete bounded state and three-axis increments required')
    base=initial.position.center
    fixed=geo.Coordinates(*(geo.Scalar.fixed(v) for v in base))
    reference=tuple(v.center for v in geo.coordinate_map(fixed,Value(initial.velocity.center),model=model,disc_radius_m=disc_radius_m))
    residual=geo.Coordinates(*(geo.plus(v,geo.Scalar.fixed(-c)) for v,c in zip(
        (initial.position.latitude,initial.position.longitude,initial.position.height),base)))
    clock=PrefixClock(time.center,time.lower,time.upper,time_remainder=F(time.value.remainder),
        maximum_packets=len(durations),maximum_seconds=maximum_seconds)
    state=initial;used=[];selected_slope=0.;nominal=0.;prefix=None
    for index,(start,duration,angle,velocity) in enumerate(zip(starts,durations,theta,dv)):
        if start>time.upper:break
        prefix=clock.append(float(duration),start=float(start))
        fraction,slope=old.packet_fraction(time,start=float(start),duration=float(duration))
        selected_slope+=slope*duration;nominal+=fraction.center*duration
        common=_prefix_scalar(prefix,time,selected_slope,nominal)
        if fraction.upper==0:continue
        used.append(index)
        period=geo.Scalar(Value(fraction.center*duration,geo._up(fraction.value.change*duration),geo._up(fraction.value.remainder*duration)),
            fraction.lower*duration,fraction.upper*duration)
        reciprocal=_constant(F(1)/F(float(duration)))
        force_rate=scalar_product(reciprocal.value,velocity)
        attitude,next_velocity,rates=_body(state,scalar_product(fraction.value,angle),force_rate,period,removal,gravity,model,disc_radius_m)
        residual=geo.Coordinates(*(geo.plus(value,geo.times(geo.plus(rate,geo.Scalar.fixed(-fixed_rate)),period))
            for value,rate,fixed_rate in zip((residual.latitude,residual.longitude,residual.height),rates,reference)))
        position=geo.Coordinates(*(geo.plus(geo.plus(geo.Scalar.fixed(origin),geo.fixed_scale(common,fixed_rate)),value)
            for origin,fixed_rate,value in zip(base,reference,(residual.latitude,residual.longitude,residual.height))))
        state=geo.State(position,next_velocity,attitude)
    output=geo.observation(state,lever,model=model,disc_radius_m=disc_radius_m)
    return History(state,output,tuple(used),int(sum(time.lower<s<time.upper for s in starts[1:])),reference,
        float(prefix.remainder) if prefix else 0.,float(prefix.independent_remainder) if prefix else 0.)


def enclose(configuration,theta,dv,dt,*,time,lower,upper,center,maximum_seconds=30.):
    limits=np.asarray(configuration['limits'],float);lo=np.asarray(lower,float);hi=np.asarray(upper,float);z=np.asarray(center,float)
    theta=np.asarray(theta,float);dv=np.asarray(dv,float);dt=np.asarray(dt,float)
    c=np.asarray(configuration['initial_c'],float);v=np.asarray(configuration['initial_v'],float);r=np.asarray(configuration['initial_r'],float)
    model=configuration['model'];profile=configuration['profile'];gravity=float(configuration['gravity']);radius=float(configuration['radius'])
    if (any(x.shape!=(27,) or not np.all(np.isfinite(x)) for x in (limits,lo,hi,z))
            or np.any(limits<0) or np.any(lo< -1) or np.any(hi>1) or np.any(lo>hi) or np.any(z<lo) or np.any(z>hi)
            or model not in (0,1,2) or isinstance(model,bool) or type(profile) is not bool or limits[26]>1
            or c.shape!=(3,) or v.shape!=(3,) or r.shape!=(3,3) or not all(np.all(np.isfinite(x)) for x in (c,v,r))
            or not np.allclose(r.T@r,np.eye(3),rtol=0,atol=1e-10) or abs(np.linalg.det(r)-1)>1e-10
            or not math.isfinite(time) or not math.isfinite(gravity+radius) or gravity<=0 or radius<=0
            or dt.ndim!=1 or not len(dt) or theta.shape!=(len(dt),3) or dv.shape!=theta.shape
            or not all(np.all(np.isfinite(x)) for x in (theta,dv,dt)) or np.any(dt<=0)):
        raise ValueError('complete supported native configuration, increments and normalized box required')
    model_name=MODELS[model];p=limits*z;physical_lower=limits*lo;physical_upper=limits*hi;delta=limits*np.maximum(z-lo,hi-z)
    vector=lambda section:Value(p[section],float(np.linalg.norm(delta[section])),0.)
    seed=geo.Coordinates(*(geo.Scalar.fixed(x) for x in c))
    displacement=geo.coordinate_map(seed,vector(slice(6,9)),model=model_name,disc_radius_m=radius)
    position=geo.Coordinates(*(geo.plus(a,b) for a,b in zip((seed.latitude,seed.longitude,seed.height),displacement)))
    x,y,angle=p[:3];skew=np.array([[0.,-angle,y],[angle,0.,-x],[-y,x,0.]])
    rotation_radius=float(np.linalg.norm(delta[:3]))
    state=geo.State(position,Value(v+p[3:6],float(np.linalg.norm(delta[3:6])),0.),
        Matrix(r@expm(skew),min(2.,rotation_radius),.5*rotation_radius**2,'rotation'))
    def corrected(raw,period,bias,gain):
        result=calibrated_box(raw,period,bias_center=p[bias],gain_center=p[gain],bias_lower=physical_lower[bias],
            bias_upper=physical_upper[bias],gain_lower=physical_lower[gain],gain_upper=physical_upper[gain])
        return Value(result['center'],result['change_radius'],result['remainder_radius'])
    angles=[corrected(raw,period,slice(9,12),slice(15,18)) for raw,period in zip(theta,dt)]
    velocity=[corrected(raw,period,slice(12,15),slice(18,21)) for raw,period in zip(dv,dt)]
    starts=[];elapsed=0.
    for period in dt:starts.append(elapsed);elapsed+=float(period)
    query=geo.Scalar.interval(time+p[25],time+physical_lower[25],time+physical_upper[25])
    removal=geo.Scalar.interval((p[26]+1)/2,(physical_lower[26]+1)/2,(physical_upper[26]+1)/2) if profile else geo.Scalar.fixed(0.)
    result=history(initial=state,theta=angles,dv=velocity,durations=dt,starts=np.array(starts),time=query,removal=removal,
        gravity=geo.Scalar.interval(gravity+p[24],gravity+physical_lower[24],gravity+physical_upper[24]),
        lever=vector(slice(21,24)),model=model_name,disc_radius_m=radius,maximum_seconds=maximum_seconds)
    components=(result.observation.latitude,result.observation.longitude,result.observation.height)
    return dict(version=VERSION,center=result.observation.center,remainder=np.array([s.value.remainder for s in components]),
        change=np.array([s.value.change for s in components]),normalized_center=z.copy(),lower=lo.copy(),upper=hi.copy(),
        parameter_count=27,time_s=time,used_packet_count=len(result.packet_indices),boundary_crossings=result.boundary_crossings,
        reference_rates=result.reference_rates,clock_remainder_s=result.clock_remainder_s,
        independent_clock_remainder_s=result.independent_clock_remainder_s,force_gravity_regrouped=True,
        floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')
