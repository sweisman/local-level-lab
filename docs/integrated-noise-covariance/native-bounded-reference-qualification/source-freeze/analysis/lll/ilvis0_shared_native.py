# SPDX-License-Identifier: AGPL-3.0-or-later
"""Candidate native enclosure with shared velocity/time and initial-lever errors.

Unshared remainders MUST be used with all six source-bound auxiliary columns.
Physical dynamics and all 27 calibration coordinates are unchanged. This is
not a complete floating-point certificate or an observational decision policy.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
import math

import numpy as np
from . import ilvis0_geographic_bounds as geo,ilvis0_history_bounds as old
from . import ilvis0_regrouped_history as prior
from .ilvis0_local_step_bounds import (Value,Matrix,add,scale,scalar_product,matrix_product,
    matrix_vector,exponential,inverse_skew,OMEGA)
from .ilvis0_increment_remainders import calibrated_box
from .ilvis0_correlated_clock import PrefixClock
from .ilvis0_shared_reference_terms import ReferenceErrors,SharedCoefficients

VERSION='ilvis0-shared-reference-native-candidate-v1'


def _data(configuration,theta,dv,dt):
    arrays=[np.ascontiguousarray(a,dtype=float) for a in (theta,dv,dt)]
    th,vel,periods=arrays
    if (periods.ndim!=1 or not len(periods) or th.shape!=(len(periods),3) or vel.shape!=th.shape
            or any(not np.all(np.isfinite(a)) for a in arrays) or np.any(periods<=0)):
        raise ValueError('complete finite positive-period native inputs required')
    fields={k:np.asarray(configuration[k],float).tolist() for k in ('initial_c','initial_v','initial_r','limits')}
    fields.update({k:configuration[k] for k in ('model','profile','gravity','radius')})
    if (np.shape(fields['initial_c'])!=(3,) or np.shape(fields['initial_v'])!=(3,) or np.shape(fields['initial_r'])!=(3,3)
            or np.shape(fields['limits'])!=(27,) or fields['model'] not in (0,1,2) or isinstance(fields['model'],bool)
            or type(fields['profile']) is not bool or not math.isfinite(fields['gravity']+fields['radius'])
            or fields['gravity']<=0 or fields['radius']<=0 or fields['limits'][26]>1
            or any(not np.all(np.isfinite(fields[k])) for k in ('initial_c','initial_v','initial_r','limits'))):
        raise ValueError('complete supported native configuration required')
    digest=hashlib.sha256(json.dumps(fields,sort_keys=True,allow_nan=False).encode())
    for a in arrays:digest.update(a.tobytes())
    return arrays,digest.hexdigest()


def make_reference(configuration,theta,dv,dt,*,lower,upper,center):
    _,source=_data(configuration,theta,dv,dt)
    return ReferenceErrors(configuration,lower,upper,center,source_id=source)


def _cross(a,b):
    return Value(np.cross(a.center,b.center),geo._up(a.norm*b.change+b.norm*a.change+a.change*b.change),
        geo._up(a.norm*b.remainder+b.norm*a.remainder+a.change*b.change))


def _local_increment(state,theta,force_rate,latitude,transport,period,removal,gravity,model):
    phi=latitude.center
    standard=Value(OMEGA*np.array([math.cos(phi),0.,-math.sin(phi)]),
        geo._up(min(2*OMEGA,OMEGA*latitude.value.change)),geo._up(.5*OMEGA*latitude.value.change**2+OMEGA*latitude.value.remainder))
    earth=standard if model=='sphere_rotating' else Value(np.zeros(3))
    win=add(add(earth,transport),scale(scalar_product(removal.value,standard),-1.))
    argument=scalar_product(scale(period.value,.5),add(scale(earth,2.),transport))
    middle=matrix_product(matrix_product(exponential(scalar_product(scale(period.value,-.5),win)),state.attitude),exponential(scale(theta,.5)))
    attitude=matrix_product(matrix_product(exponential(scalar_product(scale(period.value,-1.),win)),state.attitude),exponential(theta))
    force=matrix_vector(middle,force_rate)
    g=Value([0.,0.,gravity.center],gravity.value.change,gravity.value.remainder)
    rhs=add(scalar_product(period.value,add(force,g)),scale(_cross(argument,state.velocity),-2.))
    return attitude,matrix_vector(inverse_skew(argument),rhs)


def _metric(position,model,radius):return geo.coordinate_map(position,Value([1.,1.,1.]),model=model,disc_radius_m=radius)


def _rates(position,initial_components,delta_velocity,reference_metric,model,radius):
    metric=_metric(position,model,radius);full=[];residual=[]
    for axis,(m,fixed) in enumerate(zip(metric,reference_metric)):
        initial=initial_components[axis];delta=geo._component(delta_velocity,axis)
        rest=geo.plus(geo.times(m,delta),geo.times(geo.plus(m,geo.Scalar.fixed(-fixed)),initial))
        residual.append(rest);full.append(geo.plus(geo.fixed_scale(initial,fixed),rest))
    return tuple(full),tuple(residual)


def _advance(state,initial_components,delta_velocity,theta,force_rate,period,removal,gravity,model,radius,reference_metric):
    rates,_=_rates(state.position,initial_components,delta_velocity,reference_metric,model,radius)
    midpoint=geo._advance(state.position,rates,geo.fixed_scale(period,.5))
    transport=geo.transport_context(midpoint.latitude,rates,model)
    _,estimate_increment=_local_increment(state,theta,force_rate,midpoint.latitude,transport,period,removal,gravity,model)
    average_delta=scale(add(delta_velocity,add(delta_velocity,estimate_increment)),.5)
    revised,residual=_rates(midpoint,initial_components,average_delta,reference_metric,model,radius)
    transport=geo.transport_context(midpoint.latitude,revised,model)
    attitude,increment=_local_increment(state,theta,force_rate,midpoint.latitude,transport,period,removal,gravity,model)
    return attitude,add(delta_velocity,increment),residual


def _rotation_cap(initial,angles,velocities,periods,fractions,gravity,removal,model,radius):
    duration=0.;body=0.;impulse=0.
    for a,v,dt,f in zip(angles,velocities,periods,fractions):
        duration=geo._up(duration+geo._up(f.upper*dt))
        body=geo._up(body+geo._up(f.upper*(a.norm+a.change)))
        impulse=geo._up(impulse+geo._up(f.upper*(v.norm+v.change)))
    if not duration:return 0.
    speed=geo._up(initial.velocity.norm+initial.velocity.change+impulse+gravity.upper*duration)
    height_min=initial.position.height.lower-speed*duration
    north=radius if model=='flat_still' else geo.A*(1-geo.E2)+height_min
    if north<=0:raise ValueError('rotation-path geographic metric is unsupported')
    phi=max(abs(initial.position.latitude.lower),abs(initial.position.latitude.upper))+speed*duration/north
    if phi>=math.pi/2-1e-6:raise ValueError('rotation-path global latitude is unsupported')
    if model=='flat_still':
        east=radius*(math.pi/2-(initial.position.latitude.upper+speed*duration/north))
        if east<=0:raise ValueError('rotation-path flat metric is unsupported')
        transport=speed/east
    else:
        east=north*math.cos(phi)
        transport=speed*math.sqrt(1/north**2+1/east**2)
    coefficient=max(abs(1-removal.lower),abs(1-removal.upper)) if model=='sphere_rotating' else max(abs(removal.lower),abs(removal.upper))
    return min(2.,geo._up(body+geo._up((OMEGA*coefficient+transport)*duration)))


@dataclass(frozen=True)
class SharedEnclosure:
    center:object
    unshared_remainder:object
    coefficients:SharedCoefficients
    metadata:dict

    def __post_init__(self):
        for name in ('center','unshared_remainder'):
            value=np.array(getattr(self,name),float,copy=True)
            if value.shape!=(3,) or not np.all(np.isfinite(value)) or (name=='unshared_remainder' and np.any(value<0)):
                raise ValueError('complete finite shared native output required')
            value.setflags(write=False);object.__setattr__(self,name,value)

    def design(self,native_jacobian,reference):return reference.augment(native_jacobian,self.coefficients)

    def report(self):
        return dict(self.metadata,version=VERSION,center=self.center.tolist(),unshared_remainder=self.unshared_remainder.tolist(),
            shared_coefficients=self.coefficients.matrix.tolist(),shared_binding=self.coefficients.binding,
            physical_parameter_count=27,enclosure_parameter_count=33,
            floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def enclose(configuration,theta,dv,dt,*,time,lower,upper,reference,maximum_seconds=30.):
    (theta,dv,dt),source=_data(configuration,theta,dv,dt)
    if not isinstance(reference,ReferenceErrors) or source!=reference.source_id:
        raise ValueError('shared native source binding mismatch')
    expected=ReferenceErrors(configuration,reference.lower,reference.upper,reference.center,source_id=source)
    if expected.binding!=reference.binding:raise ValueError('shared native expansion binding mismatch')
    lo=np.asarray(lower,float);hi=np.asarray(upper,float);z=reference.center;limits=reference.limits
    if (lo.shape!=(27,) or hi.shape!=lo.shape or not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi))
            or np.any(lo>hi) or np.any(lo<reference.lower) or np.any(hi>reference.upper) or not math.isfinite(time)):
        raise ValueError('requested physical region must remain inside its bound reference')
    # An expansion need not be feasible after contraction. The bound uses the
    # containing hull, while the support calculation may keep the smaller set.
    blo=np.minimum(lo,z);bhi=np.maximum(hi,z);p=limits*z;plo=limits*blo;phi=limits*bhi
    delta=limits*np.maximum(z-blo,bhi-z)
    vector=lambda section:Value(p[section],float(np.linalg.norm(delta[section])),0.)
    model=prior.MODELS[configuration['model']];radius=float(configuration['radius'])
    seed=geo.Coordinates(*(geo.Scalar.fixed(x) for x in configuration['initial_c']))
    offsets=geo.coordinate_map(seed,vector(slice(6,9)),model=model,disc_radius_m=radius)
    initial_position=geo.Coordinates(*(geo.plus(a,b) for a,b in zip((seed.latitude,seed.longitude,seed.height),offsets)))
    angle_radius=float(np.linalg.norm(delta[:3]));initial_attitude=Matrix(reference._r_center,min(2.,angle_radius),.5*angle_radius**2,'rotation')
    initial_velocity=Value(np.asarray(configuration['initial_v'])+p[3:6],float(np.linalg.norm(delta[3:6])),0.)
    initial_components=tuple(geo.Scalar.interval(initial_velocity.center[i],configuration['initial_v'][i]+plo[3+i],
        configuration['initial_v'][i]+phi[3+i]) for i in range(3))
    initial=geo.State(initial_position,initial_velocity,initial_attitude);lever=vector(slice(21,24))
    def corrected(raw,period,bias,gain):
        result=calibrated_box(raw,period,bias_center=p[bias],gain_center=p[gain],bias_lower=plo[bias],
            bias_upper=phi[bias],gain_lower=plo[gain],gain_upper=phi[gain])
        return Value(result['center'],result['change_radius'],result['remainder_radius'])
    angles=[corrected(a,period,slice(9,12),slice(15,18)) for a,period in zip(theta,dt)]
    velocities=[corrected(v,period,slice(12,15),slice(18,21)) for v,period in zip(dv,dt)]
    starts=[];elapsed=0.
    for period in dt:starts.append(elapsed);elapsed+=float(period)
    query=geo.Scalar.interval(time+p[25],time+plo[25],time+phi[25])
    if query.lower<0 or query.upper>elapsed:raise ValueError('whole shared time interval must stay inside native support')
    removal=geo.Scalar.interval((p[26]+1)/2,(plo[26]+1)/2,(phi[26]+1)/2) if configuration['profile'] else geo.Scalar.fixed(0.)
    gravity=geo.Scalar.interval(configuration['gravity']+p[24],configuration['gravity']+plo[24],configuration['gravity']+phi[24])
    if gravity.lower<=0:raise ValueError('positive complete gravity interval required')
    fractions=[old.packet_fraction(query,start=float(s),duration=float(d))[0] for s,d in zip(starts,dt)]
    rotation_cap=_rotation_cap(initial,angles,velocities,dt,fractions,gravity,removal,model,radius)
    fixed=geo.Coordinates(*(geo.Scalar.fixed(c) for c in initial_position.center))
    reference_metric=tuple(s.center for s in _metric(fixed,model,radius))
    reference_rates=tuple(geo.fixed_scale(initial_components[i],m) for i,m in enumerate(reference_metric))
    residual=geo.Coordinates(*(geo.plus(a,geo.Scalar.fixed(-c)) for a,c in zip(
        (initial_position.latitude,initial_position.longitude,initial_position.height),initial_position.center)))
    clock=PrefixClock(query.center,query.lower,query.upper,time_remainder=F(query.value.remainder),maximum_packets=len(dt),maximum_seconds=maximum_seconds)
    state=initial;delta_velocity=Value(np.zeros(3));used=[];nominal=0.;slope_sum=0.;common=geo.Scalar.fixed(0.);prefix=None
    for index,(start,period,angle,velocity,fraction) in enumerate(zip(starts,dt,angles,velocities,fractions)):
        if start>query.upper:break
        prefix=clock.append(float(period),start=start)
        _,slope=old.packet_fraction(query,start=start,duration=float(period))
        nominal+=fraction.center*period;slope_sum+=slope*period
        common=prior._prefix_scalar(prefix,query,slope_sum,nominal)
        if fraction.upper==0:continue
        used.append(index)
        physical_period=geo.Scalar(Value(fraction.center*period,geo._up(fraction.value.change*period),geo._up(fraction.value.remainder*period)),
            fraction.lower*period,fraction.upper*period)
        force_rate=scalar_product(prior._constant(F(1)/F(float(period))).value,velocity)
        attitude,delta_velocity,delta_rates=_advance(state,initial_components,delta_velocity,scalar_product(fraction.value,angle),
            force_rate,physical_period,removal,gravity,model,radius,reference_metric)
        residual=geo.Coordinates(*(geo.plus(value,geo.times(rate,physical_period)) for value,rate in zip(
            (residual.latitude,residual.longitude,residual.height),delta_rates)))
        position=geo.Coordinates(*(geo.plus(geo.plus(geo.Scalar.fixed(origin),geo.times(common,rate)),rest)
            for origin,rate,rest in zip(initial_position.center,reference_rates,(residual.latitude,residual.longitude,residual.height))))
        state=geo.State(position,add(initial_velocity,delta_velocity),attitude)
    factored_position=[]
    for origin,rate,rest in zip(initial_position.center,reference_rates,(residual.latitude,residual.longitude,residual.height)):
        full=geo.times(common,rate)
        if rate.value.remainder!=0:raise ValueError('reference rate must retain its declared linear structure')
        remainder=geo._up((abs(rate.center)+rate.value.change)*common.value.remainder)
        factored=geo.Scalar(Value(full.center,full.value.change,remainder),full.lower,full.upper)
        factored_position.append(geo.plus(geo.plus(geo.Scalar.fixed(origin),factored),rest))
    initial_action=matrix_vector(initial_attitude,lever)
    common_action=Value(initial_action.center,initial_action.change,0.)
    initial_offset=geo.coordinate_map(state.position,common_action,model=model,disc_radius_m=radius)
    delta_center=(state.attitude.center-initial_attitude.center)@lever.center
    delta_norm=float(np.linalg.norm(delta_center));lever_max=lever.norm+lever.change
    derivative_delta=state.attitude.change+state.attitude.remainder+initial_attitude.change+initial_attitude.remainder
    if rotation_cap==0:delta_action=Value(np.zeros(3))
    else:
        delta_action=Value(delta_center,geo._up(rotation_cap*lever_max+delta_norm),
            geo._up(rotation_cap*lever_max+delta_norm+derivative_delta*lever.norm+rotation_cap*lever.change))
    delta_offset=geo.coordinate_map(state.position,delta_action,model=model,disc_radius_m=radius)
    output=geo.Coordinates(*(geo.plus(geo.plus(position,a),b) for position,a,b in zip(factored_position,initial_offset,delta_offset)))
    current_metric=tuple(s.center for s in _metric(state.position,model,radius))
    coefficients=reference.coefficients(reference_metric,slope_sum,current_metric)
    metadata=dict(source_id=source,shared_caps=reference.caps.tolist(),normalized_center=z.tolist(),lower=lo.tolist(),upper=hi.tolist(),
        bound_lower=blo.tolist(),bound_upper=bhi.tolist(),time_s=time,used_packet_count=len(used),
        boundary_crossings=int(sum(query.lower<s<query.upper for s in starts[1:])),rotation_motion_cap=rotation_cap,
        clock_remainder_s=float(prefix.remainder) if prefix else 0.,reference_metric=reference_metric,current_metric=current_metric,
        position_unshared_remainder=[v.value.remainder for v in factored_position],
        lever_unshared_remainder=[a.value.remainder+b.value.remainder for a,b in zip(initial_offset,delta_offset)],
        velocity_increment_change=delta_velocity.change,initial_velocity_change=initial_velocity.change)
    return SharedEnclosure(output.center,np.array([s.value.remainder for s in (output.latitude,output.longitude,output.height)]),coefficients,metadata)
