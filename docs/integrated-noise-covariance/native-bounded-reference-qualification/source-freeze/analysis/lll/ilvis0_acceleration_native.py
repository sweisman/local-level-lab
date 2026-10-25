# SPDX-License-Identifier: AGPL-3.0-or-later
"""Candidate native propagation with a common acceleration polynomial.

All 15 auxiliary columns are mandatory. This component is not a qualified
observed-data adapter, whole-program roundoff bound or coverage statement.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math

import numpy as np
from scipy.linalg import expm_frechet
from . import ilvis0_shared_native as previous,ilvis0_relative_rotation as relative
from . import ilvis0_geographic_bounds as geo,ilvis0_history_bounds as history
from .ilvis0_local_step_bounds import (Value,Matrix,add,scale,scalar_product,matrix_vector,
    exponential,inverse_skew,OMEGA)
from .ilvis0_increment_remainders import calibrated_box
from .ilvis0_correlated_clock import PrefixClock
from .ilvis0_shared_reference_terms import ReferenceErrors,SharedCoefficients,_readonly,_skew,_upper
from .ilvis0_reference_acceleration import AccelerationTerms,AccelerationCoefficients

VERSION='ilvis0-common-acceleration-native-candidate-v1'


def _component_change(row,reference,remainder,full_change):
    displacements=[max(abs(F(float(x))-F(float(a))),abs(F(float(b))-F(float(x))))
        for a,b,x in zip(reference.lower,reference.upper,reference.center)]
    total=sum((abs(F(float(v)))*d for v,d in zip(row,displacements)),F(float(remainder)))
    return min(full_change,_upper(total))


def make_reference(configuration,theta,dv,dt,*,lower,upper,center):
    arrays,source=previous._data(configuration,theta,dv,dt)
    reference=ReferenceErrors(configuration,lower,upper,center,source_id=source)
    return AccelerationTerms(reference,arrays[1][0],float(arrays[2][0]),configuration['gravity'])


def _rates(position,initial_components,acceleration,common,residual_velocity,metric,model,radius):
    current=previous._metric(position,model,radius);full=[];rest=[]
    for axis,(m,fixed) in enumerate(zip(current,metric)):
        a=acceleration[axis];u=geo._component(residual_velocity,axis)
        base=geo.plus(initial_components[axis],geo.times(a,common))
        departure=geo.plus(geo.times(m,u),geo.times(geo.plus(m,geo.Scalar.fixed(-fixed)),base))
        rest.append(departure);full.append(geo.plus(geo.fixed_scale(base,fixed),departure))
    return tuple(full),tuple(rest)


def _increment(state,left,right,initial_r,theta,force_difference,reference_force,acceleration,
               latitude,transport,period,removal,model):
    phi=latitude.center
    standard=Value(OMEGA*np.array([math.cos(phi),0.,-math.sin(phi)]),
        geo._up(min(2*OMEGA,OMEGA*latitude.value.change)),
        geo._up(.5*OMEGA*latitude.value.change**2+OMEGA*latitude.value.remainder))
    earth=standard if model=='sphere_rotating' else Value(np.zeros(3))
    win=add(add(earth,transport),scale(scalar_product(removal.value,standard),-1.))
    argument=scalar_product(scale(period.value,.5),add(scale(earth,2.),transport))
    middle_left=relative.advance_left(left,exponential(scalar_product(scale(period.value,-.5),win)))
    middle_right=relative.advance_right(right,exponential(scale(theta,.5)))
    middle=relative.compose(middle_left,middle_right,initial_r)
    force_rest=add(relative.action(middle_left,middle_right,initial_r,reference_force),matrix_vector(middle,force_difference))
    rhs=add(scalar_product(period.value,force_rest),scale(previous._cross(argument,state.velocity),-2.))
    rhs=add(rhs,scale(scalar_product(period.value,previous._cross(argument,acceleration)),-1.))
    du=matrix_vector(inverse_skew(argument),rhs)
    next_left=relative.advance_left(left,exponential(scalar_product(scale(period.value,-1.),win)))
    next_right=relative.advance_right(right,exponential(theta))
    return next_left,next_right,du


@dataclass(frozen=True)
class AccelerationEnclosure:
    center:object
    unshared_remainder:object
    previous_coefficients:SharedCoefficients
    acceleration_coefficients:AccelerationCoefficients
    metadata:dict

    def __post_init__(self):
        for name in ('center','unshared_remainder'):
            a=np.asarray(getattr(self,name),float)
            if a.shape!=(3,) or not np.all(np.isfinite(a)) or (name=='unshared_remainder' and np.any(a<0)):
                raise ValueError('finite complete common-acceleration enclosure required')
            object.__setattr__(self,name,_readonly(a))

    def design(self,native_jacobian,reference):
        if not isinstance(reference,AccelerationTerms):raise ValueError('complete acceleration reference required')
        return reference.augment(native_jacobian,self.previous_coefficients,self.acceleration_coefficients)

    def report(self):
        return dict(self.metadata,version=VERSION,center=self.center.tolist(),unshared_remainder=self.unshared_remainder.tolist(),
            previous_coefficients=self.previous_coefficients.matrix.tolist(),shared_binding=self.previous_coefficients.binding,
            acceleration_coefficients=self.acceleration_coefficients.matrix.tolist(),acceleration_binding=self.acceleration_coefficients.binding,
            physical_parameter_count=27,enclosure_parameter_count=42,floating_point_enclosure_verified=False,
            observational_coverage_qualified=False,scientific_decision='abstain')


def enclose(configuration,theta,dv,dt,*,time,lower,upper,reference,maximum_seconds=30.):
    (theta,dv,dt),source=previous._data(configuration,theta,dv,dt)
    if not isinstance(reference,AccelerationTerms) or reference.reference.source_id!=source:
        raise ValueError('acceleration native source binding mismatch')
    r=reference.reference
    expected=make_reference(configuration,theta,dv,dt,lower=r.lower,upper=r.upper,center=r.center)
    if expected.binding!=reference.binding:raise ValueError('acceleration native expansion binding mismatch')
    lo=np.asarray(lower,float);hi=np.asarray(upper,float);z=r.center;limits=r.limits
    if (lo.shape!=(27,) or hi.shape!=lo.shape or not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi))
            or np.any(lo>hi) or np.any(lo<r.lower) or np.any(hi>r.upper) or not math.isfinite(time)):
        raise ValueError('complete physical subdomain required')
    blo=np.minimum(lo,z);bhi=np.maximum(hi,z);p=limits*z;plo=limits*blo;phi=limits*bhi
    delta=limits*np.maximum(z-blo,bhi-z)
    vector=lambda section:Value(p[section],float(np.linalg.norm(delta[section])),0.)
    model=previous.prior.MODELS[configuration['model']];radius=float(configuration['radius'])
    seed=geo.Coordinates(*(geo.Scalar.fixed(x) for x in configuration['initial_c']))
    offsets=geo.coordinate_map(seed,vector(slice(6,9)),model=model,disc_radius_m=radius)
    initial_position=geo.Coordinates(*(geo.plus(a,b) for a,b in zip((seed.latitude,seed.longitude,seed.height),offsets)))
    angle_delta=float(np.linalg.norm(delta[:3]));initial_r=Matrix(r._r_center,min(2.,angle_delta),.5*angle_delta**2,'rotation')
    initial_velocity=Value(np.asarray(configuration['initial_v'])+p[3:6],float(np.linalg.norm(delta[3:6])),0.)
    initial_components=tuple(geo.Scalar.interval(initial_velocity.center[i],configuration['initial_v'][i]+plo[3+i],
        configuration['initial_v'][i]+phi[3+i]) for i in range(3))
    acceleration=Value(reference.center,reference.change,reference.remainder)
    acceleration_changes=[_component_change(reference.jacobian[i],r,acceleration.remainder,acceleration.change) for i in range(3)]
    acceleration_components=tuple(geo.Scalar.interval(float(acceleration.center[i]),
        float(acceleration.center[i])-acceleration_changes[i],float(acceleration.center[i])+acceleration_changes[i],
        acceleration.remainder) for i in range(3))
    def correct(raw,period,bias,gain):
        a=calibrated_box(raw,period,bias_center=p[bias],gain_center=p[gain],bias_lower=plo[bias],
            bias_upper=phi[bias],gain_lower=plo[gain],gain_upper=phi[gain])
        return Value(a['center'],a['change_radius'],a['remainder_radius'])
    reference_force=scale(correct(dv[0],float(dt[0]),slice(12,15),slice(18,21)),1/float(dt[0]))
    angles=[correct(a,float(period),slice(9,12),slice(15,18)) for a,period in zip(theta,dt)]
    differences=[]
    for raw,period in zip(dv,dt):
        difference=raw/period-dv[0]/dt[0]
        c=calibrated_box(difference,1.,bias_center=np.zeros(3),gain_center=p[18:21],bias_lower=np.zeros(3),
            bias_upper=np.zeros(3),gain_lower=plo[18:21],gain_upper=phi[18:21])
        differences.append(Value(c['center'],c['change_radius'],c['remainder_radius']))
    starts=[];elapsed=0.
    for period in dt:starts.append(elapsed);elapsed+=float(period)
    query=geo.Scalar.interval(time+p[25],time+plo[25],time+phi[25])
    if query.lower<0 or query.upper>elapsed:raise ValueError('complete clock domain must lie within native support')
    removal=geo.Scalar.interval((p[26]+1)/2,(plo[26]+1)/2,(phi[26]+1)/2) if configuration['profile'] else geo.Scalar.fixed(0.)
    fractions=[history.packet_fraction(query,start=s,duration=float(period))[0] for s,period in zip(starts,dt)]
    fixed=geo.Coordinates(*(geo.Scalar.fixed(c) for c in initial_position.center))
    metric=tuple(v.center for v in previous._metric(fixed,model,radius))
    reference_rates=tuple(geo.fixed_scale(initial_components[i],m) for i,m in enumerate(metric))
    departures=geo.Coordinates(*(geo.plus(v,geo.Scalar.fixed(-c)) for v,c in zip(
        (initial_position.latitude,initial_position.longitude,initial_position.height),initial_position.center)))
    clock=PrefixClock(query.center,query.lower,query.upper,time_remainder=F(query.value.remainder),maximum_packets=len(dt),maximum_seconds=maximum_seconds)
    left=relative.Delta(np.zeros((3,3)));right=relative.Delta(np.zeros((3,3)))
    u=Value(np.zeros(3));common=geo.Scalar.fixed(0.);state=geo.State(initial_position,initial_velocity,initial_r)
    nominal=0.;slope=0.;used=[];prefix=None
    for index,(start,period,angle,difference,fraction) in enumerate(zip(starts,dt,angles,differences,fractions)):
        if start>query.upper:break
        prefix=clock.append(float(period),start=start)
        _,packet_slope=history.packet_fraction(query,start=start,duration=float(period))
        nominal+=fraction.center*period;slope+=packet_slope*period
        next_common=previous.prior._prefix_scalar(prefix,query,slope,nominal)
        if fraction.upper==0:continue
        used.append(index)
        actual_period=geo.Scalar(Value(fraction.center*period,geo._up(fraction.value.change*period),geo._up(fraction.value.remainder*period)),
            fraction.lower*period,fraction.upper*period)
        actual_angle=scalar_product(fraction.value,angle)
        rates,_=_rates(state.position,initial_components,acceleration_components,common,u,metric,model,radius)
        midpoint=geo._advance(state.position,rates,geo.fixed_scale(actual_period,.5))
        transport=geo.transport_context(midpoint.latitude,rates,model)
        _,_,estimate=_increment(state,left,right,initial_r,actual_angle,difference,reference_force,acceleration,
            midpoint.latitude,transport,actual_period,removal,model)
        mid_common=geo.plus(common,geo.fixed_scale(actual_period,.5));mid_u=add(u,scale(estimate,.5))
        revised,rest=_rates(midpoint,initial_components,acceleration_components,mid_common,mid_u,metric,model,radius)
        transport=geo.transport_context(midpoint.latitude,revised,model)
        left,right,increment=_increment(state,left,right,initial_r,actual_angle,difference,reference_force,acceleration,
            midpoint.latitude,transport,actual_period,removal,model)
        u=add(u,increment)
        departures=geo.Coordinates(*(geo.plus(value,geo.times(rate,actual_period)) for value,rate in zip(
            (departures.latitude,departures.longitude,departures.height),rest)))
        square=geo.times(next_common,next_common)
        position=geo.Coordinates(*(geo.plus(geo.plus(geo.plus(geo.Scalar.fixed(origin),geo.times(next_common,rate)),
            geo.times(geo.fixed_scale(acceleration_components[axis],m*.5),square)),rest_value)
            for axis,(origin,rate,m,rest_value) in enumerate(zip(initial_position.center,reference_rates,metric,
                (departures.latitude,departures.longitude,departures.height)))))
        velocity=add(add(initial_velocity,scalar_product(next_common.value,acceleration)),u)
        state=geo.State(position,velocity,relative.compose(left,right,initial_r));common=next_common
    factored=[];clock_terms=[]
    tau_delta=max(abs(time+plo[25]-query.center),abs(time+phi[25]-query.center))
    square=geo.times(common,common)
    for axis,(origin,rate,m,rest) in enumerate(zip(initial_position.center,reference_rates,metric,
            (departures.latitude,departures.longitude,departures.height))):
        velocity_full=geo.times(common,rate)
        if rate.value.remainder:raise ValueError('reference velocity must remain linear')
        velocity_remainder=geo._up((abs(rate.center)+rate.value.change)*common.value.remainder)
        velocity_part=geo.Scalar(Value(velocity_full.center,velocity_full.value.change,velocity_remainder),velocity_full.lower,velocity_full.upper)
        acceleration_full=geo.times(geo.fixed_scale(acceleration_components[axis],m*.5),square)
        amax=abs(float(acceleration.center[axis]))+acceleration.change;e=common.value.remainder
        acceleration_remainder=geo._up(abs(m)*amax*((abs(common.center)+abs(slope)*tau_delta)*e+.5*e*e))
        clock_terms.append(acceleration_remainder)
        acceleration_part=geo.Scalar(Value(acceleration_full.center,acceleration_full.value.change,acceleration_remainder),
            acceleration_full.lower,acceleration_full.upper)
        factored.append(geo.plus(geo.plus(geo.plus(geo.Scalar.fixed(origin),velocity_part),acceleration_part),rest))
    lever=vector(slice(21,24));initial_action=matrix_vector(initial_r,lever)
    lever_jacobian=np.zeros((3,27))
    for axis in range(3):
        direction=np.zeros(3);direction[axis]=limits[axis]
        lever_jacobian[:,axis]=r.initial_r@expm_frechet(_skew(p[:3]),_skew(direction),compute_expm=False)@lever.center
        lever_jacobian[:,21+axis]=r._r_center[:,axis]*limits[21+axis]
    lever_changes=[_component_change(lever_jacobian[i],r,r.caps[3+i],initial_action.change) for i in range(3)]
    initial_components_lever=tuple(geo.Scalar.interval(float(initial_action.center[i]),
        float(initial_action.center[i])-lever_changes[i],float(initial_action.center[i])+lever_changes[i],0.) for i in range(3))
    full_metric=previous._metric(state.position,model,radius)
    initial_offset=tuple(geo.times(m,v) for m,v in zip(full_metric,initial_components_lever))
    delta_offset=geo.coordinate_map(state.position,relative.action(left,right,initial_r,lever),model=model,disc_radius_m=radius)
    output=geo.Coordinates(*(geo.plus(geo.plus(position,a),b) for position,a,b in zip(factored,initial_offset,delta_offset)))
    current_metric=tuple(v.center for v in previous._metric(state.position,model,radius))
    old_coefficients=r.coefficients(metric,slope,current_metric)
    added=reference.coefficients(metric,clock_center=common.center,time_slope=slope)
    metadata=dict(source_id=source,normalized_center=z.tolist(),lower=lo.tolist(),upper=hi.tolist(),bound_lower=blo.tolist(),bound_upper=bhi.tolist(),
        time_s=time,used_packet_count=len(used),common_clock_center=common.center,time_slope=slope,clock_remainder_s=common.value.remainder,
        acceleration_clock_remainder=clock_terms,acceleration_caps=reference.caps.tolist(),previous_caps=r.caps.tolist(),
        position_unshared_remainder=[v.value.remainder for v in factored],
        lever_unshared_remainder=[a.value.remainder+b.value.remainder for a,b in zip(initial_offset,delta_offset)],
        reference_metric=metric,current_metric=current_metric,native_factorization_qualified=False)
    return AccelerationEnclosure(output.center,np.array([v.value.remainder for v in (output.latitude,output.longitude,output.height)]),
        old_coefficients,added,metadata)
