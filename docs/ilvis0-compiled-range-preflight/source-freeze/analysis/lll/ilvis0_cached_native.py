# SPDX-License-Identifier: AGPL-3.0-or-later
"""Component-preserving native propagation; separate from all frozen predecessors.

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
from . import ilvis0_shared_native as previous,ilvis0_cached_relative as relative
from . import ilvis0_component_geography as geo,ilvis0_history_bounds as history
from .ilvis0_local_step_bounds import Matrix,exponential,inverse_skew,OMEGA
from .ilvis0_cached_transport import Value,add,scale,scalar_product,matrix_vector,cross
from .ilvis0_increment_remainders import calibrated_box
from .ilvis0_correlated_clock import PrefixClock
from .ilvis0_shared_reference_terms import ReferenceErrors,SharedCoefficients,_readonly,_skew,_upper
from .ilvis0_reference_acceleration import AccelerationTerms,AccelerationCoefficients

VERSION='ilvis0-cached-component-native-v1'


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


def _increment(state,left,right,initial_r,theta,force_difference,raw_difference,reference_force,acceleration,matrix,
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
    force_rest=relative.action(middle_left,middle_right,initial_r,add(reference_force,force_difference))
    delta_g=scalar_product(period.value,Value(raw_difference))
    matrix_delta_g=relative.apply(matrix,delta_g)
    rhs=add(scalar_product(period.value,force_rest),scale(cross(argument,state.velocity),-2.))
    rhs=add(rhs,scale(scalar_product(period.value,cross(argument,acceleration)),-1.))
    rhs=add(rhs,scale(cross(argument,matrix_delta_g),-1.))
    dw=matrix_vector(inverse_skew(argument),rhs)
    next_left=relative.advance_left(left,exponential(scalar_product(scale(period.value,-1.),win)))
    next_right=relative.advance_right(right,exponential(theta))
    return next_left,next_right,dw


@dataclass(frozen=True)
class TransformEnclosure:
    center:object
    unshared_remainder:object
    previous_coefficients:SharedCoefficients
    acceleration_coefficients:AccelerationCoefficients
    transform_coefficients:ForceTransformCoefficients
    metadata:dict

    def __post_init__(self):
        for name in ('center','unshared_remainder'):
            a=np.asarray(getattr(self,name),float)
            if a.shape!=(3,) or not np.all(np.isfinite(a)) or (name=='unshared_remainder' and np.any(a<0)):
                raise ValueError('finite complete transform enclosure required')
            object.__setattr__(self,name,_readonly(a))

    def design(self,native_jacobian,reference):
        if not isinstance(reference,TransformReference) or self.metadata.get('reference_binding')!=reference.binding:
            raise ValueError('complete transform source/reference required')
        return reference.transform.augment(native_jacobian,reference.acceleration,self.previous_coefficients,self.acceleration_coefficients,self.transform_coefficients)

    def report(self):
        return dict(self.metadata,version=VERSION,center=self.center.tolist(),unshared_remainder=self.unshared_remainder.tolist(),
            previous_coefficients=self.previous_coefficients.matrix.tolist(),shared_binding=self.previous_coefficients.binding,
            acceleration_coefficients=self.acceleration_coefficients.matrix.tolist(),acceleration_binding=self.acceleration_coefficients.binding,
            transform_coefficients=self.transform_coefficients.matrix.tolist(),transform_binding=self.transform_coefficients.binding,
            physical_parameter_count=27,enclosure_parameter_count=51,floating_point_enclosure_verified=False,
            observational_coverage_qualified=False,scientific_decision='abstain')

def enclose(configuration,theta,dv,dt,*,time,lower,upper,reference,conditioning,maximum_seconds=30.):
    started=_timer.monotonic()
    if not math.isfinite(maximum_seconds) or maximum_seconds<0:raise ValueError('finite cooperative bound allowance required')
    (theta,dv,dt),source=previous._data(configuration,theta,dv,dt)
    if not isinstance(reference,TransformReference) or reference.parent.source_id!=source:
        raise ValueError('transform native source binding mismatch')
    refs=reference;r=refs.parent
    expected=make_reference(configuration,theta,dv,dt,lower=r.lower,upper=r.upper,center=r.center)
    if expected.binding!=refs.binding:raise ValueError('transform native source/reference mismatch')
    reference=refs.acceleration
    lo=np.asarray(lower,float);hi=np.asarray(upper,float);z=r.center;limits=r.limits
    if (lo.shape!=(27,) or hi.shape!=lo.shape or not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi))
            or np.any(lo>hi) or np.any(lo<r.lower) or np.any(hi>r.upper) or not math.isfinite(time)):
        raise ValueError('complete physical subdomain required')
    blo=np.minimum(lo,z);bhi=np.maximum(hi,z);p=limits*z;plo=limits*blo;phi=limits*bhi
    delta=limits*np.maximum(z-blo,bhi-z)
    vector=lambda section:Value(p[section],float(np.linalg.norm(delta[section])),0.,component_change=delta[section])
    model=previous.prior.MODELS[configuration['model']];radius=float(configuration['radius'])
    seed=geo.Coordinates(*(geo.Scalar.fixed(x) for x in configuration['initial_c']))
    offsets=geo.coordinate_map(seed,vector(slice(6,9)),model=model,disc_radius_m=radius)
    initial_position=geo.Coordinates(*(geo.plus(a,b) for a,b in zip((seed.latitude,seed.longitude,seed.height),offsets)))
    angle_delta=float(np.linalg.norm(delta[:3]));initial_r=Matrix(r._r_center,min(2.,angle_delta),.5*angle_delta**2,'rotation')
    initial_velocity=Value(np.asarray(configuration['initial_v'])+p[3:6],float(np.linalg.norm(delta[3:6])),0.,component_change=delta[3:6])
    initial_components=tuple(geo.Scalar.interval(initial_velocity.center[i],configuration['initial_v'][i]+plo[3+i],
        configuration['initial_v'][i]+phi[3+i]) for i in range(3))
    if not isinstance(conditioning,(ConditionedAcceleration,DirectionalAcceleration)):
        raise ValueError('verified training conditioning required')
    conditioned_change,component_changes=conditioning.match(refs.report(),lo,hi)
    acceleration=Value(reference.center,min(reference.change,conditioned_change),reference.remainder,component_change=component_changes)
    acceleration_changes=[min(component_changes[i],_component_change(
        reference.jacobian[i],r,acceleration.remainder,acceleration.change)) for i in range(3)]
    acceleration_components=tuple(geo.Scalar.interval(float(acceleration.center[i]),
        float(acceleration.center[i])-acceleration_changes[i],float(acceleration.center[i])+acceleration_changes[i],
        acceleration.remainder) for i in range(3))
    def correct(raw,period,bias,gain):
        a=calibrated_box(raw,period,bias_center=p[bias],gain_center=p[gain],bias_lower=plo[bias],
            bias_upper=phi[bias],gain_lower=plo[gain],gain_upper=phi[gain])
        return Value(a['center'],a['change_radius'],a['remainder_radius'],component_change=a['component_change'],component_remainder=a['component_remainder'])
    reference_force=scale(correct(dv[0],float(dt[0]),slice(12,15),slice(18,21)),1/float(dt[0]))
    angles=[correct(a,float(period),slice(9,12),slice(15,18)) for a,period in zip(theta,dt)]
    differences=[];raw_differences=[]
    for raw,period in zip(dv,dt):
        difference=raw/period-dv[0]/dt[0];raw_differences.append(difference)
        c=calibrated_box(difference,1.,bias_center=np.zeros(3),gain_center=p[18:21],bias_lower=np.zeros(3),
            bias_upper=np.zeros(3),gain_lower=plo[18:21],gain_upper=phi[18:21])
        differences.append(Value(c['center'],c['change_radius'],c['remainder_radius'],component_change=c['component_change'],component_remainder=c['component_remainder']))
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
    clock_profile=force_integrals(dt,raw_differences,
        center=F(time)+F(float(limits[25]))*F(float(z[25])),
        lower=F(time)+F(float(limits[25]))*F(float(r.lower[25])),
        upper=F(time)+F(float(limits[25]))*F(float(r.upper[25])),maximum_packets=len(dt),
        maximum_seconds=max(0.,maximum_seconds-(_timer.monotonic()-started)))
    clock_force=ClockedForceTransform(refs.transform,clock_profile,nominal_time=time,metric=metric)
    matrix=_matrix_bound(refs.transform,blo,bhi)
    clock=PrefixClock(query.center,query.lower,query.upper,time_remainder=F(query.value.remainder),maximum_packets=len(dt),
        maximum_seconds=max(0.,maximum_seconds-(_timer.monotonic()-started)))
    left=relative.Delta(np.zeros((3,3)));right=relative.Delta(np.zeros((3,3)))
    u=Value(np.zeros(3));raw_g=Value(np.zeros(3));raw_h=Value(np.zeros(3));common=geo.Scalar.fixed(0.);state=geo.State(initial_position,initial_velocity,initial_r)
    nominal=0.;slope=0.;used=[];prefix=None
    for index,(start,period,angle,difference,raw_difference,fraction) in enumerate(zip(starts,dt,angles,differences,raw_differences,fractions)):
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
        delta_g=scalar_product(actual_period.value,Value(raw_difference))
        rates,_=_rates(state.position,initial_components,acceleration_components,common,relative.apply(matrix,raw_g),u,metric,model,radius)
        midpoint=geo._advance(state.position,rates,geo.fixed_scale(actual_period,.5))
        transport=geo.transport_context(midpoint.latitude,rates,model)
        _,_,estimate=_increment(state,left,right,initial_r,actual_angle,difference,raw_difference,reference_force,acceleration,matrix,
            midpoint.latitude,transport,actual_period,removal,model)
        mid_common=geo.plus(common,geo.fixed_scale(actual_period,.5));mid_u=add(u,scale(estimate,.5));mid_g=add(raw_g,scale(delta_g,.5))
        revised,rest=_rates(midpoint,initial_components,acceleration_components,mid_common,relative.apply(matrix,mid_g),mid_u,metric,model,radius)
        transport=geo.transport_context(midpoint.latitude,revised,model)
        left,right,increment=_increment(state,left,right,initial_r,actual_angle,difference,raw_difference,reference_force,acceleration,matrix,
            midpoint.latitude,transport,actual_period,removal,model)
        u=add(u,increment);raw_h=add(raw_h,scalar_product(actual_period.value,mid_g));raw_g=add(raw_g,delta_g)
        departures=geo.Coordinates(*(geo.plus(value,geo.times(rate,actual_period)) for value,rate in zip(
            (departures.latitude,departures.longitude,departures.height),rest)))
        square=geo.times(next_common,next_common)
        matrix_h=relative.apply(matrix,raw_h)
        position=geo.Coordinates(*(geo.plus(geo.plus(geo.plus(geo.plus(geo.Scalar.fixed(origin),geo.times(next_common,rate)),
            geo.times(geo.fixed_scale(acceleration_components[axis],m*.5),square)),geo.fixed_scale(geo._component(matrix_h,axis),m)),rest_value)
            for axis,(origin,rate,m,rest_value) in enumerate(zip(initial_position.center,reference_rates,metric,
                (departures.latitude,departures.longitude,departures.height)))))
        velocity=add(add(add(initial_velocity,scalar_product(next_common.value,acceleration)),relative.apply(matrix,raw_g)),u)
        state=geo.State(position,velocity,relative.compose(left,right,initial_r));common=next_common
    factored=[];clock_terms=[];force_terms=[];force_center_differences=[]
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
        force_full=geo.fixed_scale(geo._component(relative.apply(matrix,raw_h),axis),m)
        center_difference=abs(force_full.center-float(clock_force.center[axis]))
        force_remainder=geo._up(float(clock_force.unshared_remainder[axis])+center_difference)
        force_part=geo.Scalar(Value(force_full.center,force_full.value.change,force_remainder),force_full.lower,force_full.upper)
        force_terms.append(force_remainder);force_center_differences.append(center_difference)
        factored.append(geo.plus(geo.plus(geo.plus(geo.plus(geo.Scalar.fixed(origin),velocity_part),acceleration_part),force_part),rest))
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
    metadata=dict(component_transport=True,cached_certificates=True,source_norm_interval_installed=False,conditioning=conditioning.report(),conditioned_acceleration_change=acceleration.change,
        retained_acceleration_remainder=reference.remainder,source_id=source,normalized_center=z.tolist(),lower=lo.tolist(),upper=hi.tolist(),bound_lower=blo.tolist(),bound_upper=bhi.tolist(),
        time_s=time,used_packet_count=len(used),common_clock_center=common.center,time_slope=slope,clock_remainder_s=common.value.remainder,
        acceleration_clock_remainder=clock_terms,acceleration_caps=reference.caps.tolist(),previous_caps=r.caps.tolist(),
        position_unshared_remainder=[v.value.remainder for v in factored],
        lever_unshared_remainder=[a.value.remainder+b.value.remainder for a,b in zip(initial_offset,delta_offset)],
        reference_metric=metric,current_metric=current_metric,native_factorization_qualified=False,
        reference_binding=refs.binding,transform_reference=refs.transform.report(),force_integrals=clock_profile.report(),
        clock_transform=clock_force.report(),force_unshared_remainder=force_terms,force_center_difference=force_center_differences,
        transform_matrix_change=matrix.change,transform_matrix_remainder=matrix.remainder)
    return TransformEnclosure(output.center,np.array([v.value.remainder for v in (output.latitude,output.longitude,output.height)]),
        old_coefficients,added,clock_force.coefficients,metadata)
