# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared cold/batched remainder orchestration, with complete prefix state.

This is an efficiency candidate. Frozen source/cold comparisons and useful
whole-period prediction uncertainty remain separate qualification requirements.
"""
from copy import copy,deepcopy
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
import math
import time as _timer
from types import SimpleNamespace

from .ilvis0_remainder_native import (
    np,geo,previous,relative,Matrix,Value,calibrated_box,scale,add,scalar_product,
    matrix_vector,expm_frechet,_skew,_component_change,_matrix_bound,_rates,_increment,
    TransformReference,TransformEnclosure,make_reference,ConditionedAcceleration,
    DirectionalAcceleration,SourceValueStream,SourceStream,RoundedBodyInterval,
    PrefixClock,force_integrals,ClockedForceTransform,history)

VERSION='ilvis0-complete-native-prefix-candidate-v1'


def _prepare(configuration,theta,dv,dt,*,lower,upper,reference,conditioning,maximum_seconds):
    started=_timer.monotonic()
    if not math.isfinite(maximum_seconds) or maximum_seconds<0:raise ValueError('finite cooperative bound allowance required')
    configuration=deepcopy(configuration)
    (theta,dv,dt),source=previous._data(configuration,theta,dv,dt)
    theta,dv,dt=(np.array(v,copy=True) for v in (theta,dv,dt))
    for value in (theta,dv,dt):value.setflags(write=False)
    if not isinstance(reference,TransformReference) or reference.parent.source_id!=source:
        raise ValueError('transform native source binding mismatch')
    refs=reference;r=refs.parent
    expected=make_reference(configuration,theta,dv,dt,lower=r.lower,upper=r.upper,center=r.center)
    if expected.binding!=refs.binding:raise ValueError('transform native source/reference mismatch')
    reference=refs.acceleration
    lo=np.asarray(lower,float);hi=np.asarray(upper,float);z=r.center;limits=r.limits
    if (lo.shape!=(27,) or hi.shape!=lo.shape or not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi))
            or np.any(lo>hi) or np.any(lo<r.lower) or np.any(hi>r.upper)):
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
    from .ilvis0_conditional_remainder import enclose as remainder_bound
    conditional_remainder=remainder_bound(reference.jacobian,lo,hi,z,component_changes,reference.remainder)
    acceleration=Value(reference.center,min(reference.change,conditioned_change),conditional_remainder['remainder_upper'],component_change=component_changes)
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
    removal=geo.Scalar.interval((p[26]+1)/2,(plo[26]+1)/2,(phi[26]+1)/2) if configuration['profile'] else geo.Scalar.fixed(0.)
    fixed=geo.Coordinates(*(geo.Scalar.fixed(c) for c in initial_position.center))
    metric=tuple(v.center for v in previous._metric(fixed,model,radius))
    reference_rates=tuple(geo.fixed_scale(initial_components[i],m) for i,m in enumerate(metric))
    departures=geo.Coordinates(*(geo.plus(v,geo.Scalar.fixed(-c)) for v,c in zip(
        (initial_position.latitude,initial_position.longitude,initial_position.height),initial_position.center)))
    matrix=_matrix_bound(refs.transform,blo,bhi)
    lo=np.array(lo,copy=True);hi=np.array(hi,copy=True)
    lo.setflags(write=False);hi.setflags(write=False)
    material=locals()
    context=SimpleNamespace(**{name:material[name] for name in ['configuration', 'theta', 'dv', 'dt', 'source', 'refs', 'r', 'reference', 'lo', 'hi', 'z', 'limits', 'blo', 'bhi', 'p', 'plo', 'phi', 'delta', 'vector', 'model', 'radius', 'initial_position', 'initial_r', 'initial_velocity', 'initial_components', 'acceleration', 'acceleration_components', 'reference_force', 'angles', 'differences', 'raw_differences', 'starts', 'elapsed', 'removal', 'metric', 'reference_rates', 'departures', 'matrix', 'conditional_remainder', 'conditioning', 'started', 'maximum_seconds']})
    binding=dict(version=VERSION,source=source,reference=refs.binding,conditioning=conditioning.report(),
        lower=lo.tolist(),upper=hi.tolist(),center=z.tolist())
    context.binding=hashlib.sha256(json.dumps(binding,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    context.work=None
    return context


@dataclass
class Cursor:
    time:float
    query:object
    clock:object
    source_values:object
    source_rows:object
    source_intervals:object
    left:object
    right:object
    u:object
    raw_g:object
    raw_h:object
    common:object
    state:object
    departures:object
    used:list
    binding:str
    index:int=0
    source_prefixes:int=0
    nominal:float=0.
    slope:float=0.
    source_physical_upper:float=0.
    clock_profile:object=None
    clock_force:object=None

    def close(self):
        self.source_values.close();self.source_rows.close()


def _remaining(context):
    return max(0.,context.maximum_seconds-(_timer.monotonic()-context.started))


def _query(context,time):
    if not math.isfinite(time):raise ValueError('finite declared query required')
    query=geo.Scalar.interval(time+context.p[25],time+context.plo[25],time+context.phi[25])
    if query.lower<0 or query.upper>context.elapsed:
        raise ValueError('complete clock domain must lie within native support')
    return query


def _force_profile(context,time):
    c=context
    if c.work is not None:c.work.add('force_profile_packets',len(c.dt))
    profile=force_integrals(c.dt,c.raw_differences,
        center=F(time)+F(float(c.limits[25]))*F(float(c.z[25])),
        lower=F(time)+F(float(c.limits[25]))*F(float(c.r.lower[25])),
        upper=F(time)+F(float(c.limits[25]))*F(float(c.r.upper[25])),
        maximum_packets=len(c.dt),maximum_seconds=_remaining(c))
    force=ClockedForceTransform(c.refs.transform,profile,nominal_time=time,metric=c.metric)
    return profile,force


def _new_cursor(context,time,*,cold_kernels=None,prefix_kernels=None,profile=True):
    c=context;query=_query(c,time);n=len(c.dt)
    clock_profile,clock_force=_force_profile(c,time) if profile else (None,None)
    clock=PrefixClock(query.center,query.lower,query.upper,time_remainder=F(query.value.remainder),
        maximum_packets=n,maximum_seconds=_remaining(c))
    source_case=dict(configuration=c.configuration,theta=c.theta,dv=c.dv,dt=c.dt)
    if prefix_kernels is None:
        source_values=SourceValueStream(source_case,c.refs,c.lo,c.hi,time,maximum_packets=n,
            derivative_kernel=cold_kernels['derivative_kernel'],point_kernel=cold_kernels['point_kernel'])
        source_rows=SourceStream(cold_kernels['source_kernel'],source_case,c.z,time,maximum_packets=n)
    else:
        from .ilvis0_source_prefix import make_stream
        source_values=SourceValueStream(source_case,c.refs,c.lo,c.hi,time,maximum_packets=n,
            derivative_kernel=prefix_kernels['interval'],point_kernel=prefix_kernels['point'])
        arguments=dict(lower=c.lo,upper=c.hi,reference_binding=c.refs.binding,maximum_packets=n)
        source_values.derivatives.close();source_values.direct.points.close()
        source_values.derivatives=make_stream(prefix_kernels,'interval',source_case,c.z,time,**arguments)
        source_values.direct.points=make_stream(prefix_kernels,'point',source_case,c.z,time,**arguments)
        source_rows=make_stream(prefix_kernels,'reference',source_case,c.z,time,**arguments)
    source_intervals=RoundedBodyInterval(c.refs,c.conditioning,c.lo,c.hi,
        direct_source_binding=source_values.direct.source_binding)
    return Cursor(time,query,clock,source_values,source_rows,source_intervals,
        relative.Delta(np.zeros((3,3))),relative.Delta(np.zeros((3,3))),
        Value(np.zeros(3)),Value(np.zeros(3)),Value(np.zeros(3)),geo.Scalar.fixed(0.),
        geo.State(c.initial_position,c.initial_velocity,c.initial_r),c.departures,[],c.binding,
        clock_profile=clock_profile,clock_force=clock_force)


def _fork(context,parent,time,kernels):
    from .ilvis0_source_prefix import fork_stream
    c=context;query=_query(c,time)
    if parent.binding!=c.binding or parent.slope!=0. or parent.clock._slope!=0 or parent.clock._independent:
        raise ValueError('unchanged, complete, query-independent native prefix required')
    if parent.index:
        previous_index=parent.index-1
        earliest=min(F(query.lower),F(time)+F(float(c.limits[25]))*F(float(min(c.lo[25],c.z[25]))))
        end=max(F(c.starts[previous_index])+F(float(c.dt[previous_index])),parent.clock._physical)
        if not end<earliest:raise ValueError('native fork reaches a clipped or exact-boundary packet')
    child=_new_cursor(c,time,prefix_kernels=kernels,profile=True)
    child.source_rows.close();child.source_rows=fork_stream(parent.source_rows,time,reference_binding=c.refs.binding)
    values=child.source_values;old=parent.source_values
    values.derivatives.close();values.direct.points.close()
    values.derivatives=fork_stream(old.derivatives,time,reference_binding=c.refs.binding)
    values.direct.points=fork_stream(old.direct.points,time,reference_binding=c.refs.binding)
    values.body=old.body;values.visits=old.visits;values.elapsed=old.elapsed
    for name in ('visits','elapsed','prefix_d','prefix_r','prefix_n'):
        setattr(values.direct,name,getattr(old.direct,name))
    child.clock=copy(parent.clock);child.clock._values=list(parent.clock._values)
    child.clock.center=F(query.center);child.clock.lower=F(query.lower);child.clock.upper=F(query.upper)
    child.clock.time_remainder=F(query.value.remainder)
    for name in ('left','right','u','raw_g','raw_h','common','state','departures',
                 'index','source_prefixes','nominal','slope','source_physical_upper'):
        setattr(child,name,getattr(parent,name))
    child.used=list(parent.used)
    return child


def _advance(context,cursor):
    if cursor.index>=len(context.dt) or context.starts[cursor.index]>cursor.query.upper:return False
    if _remaining(context)<=0:raise ValueError('native batch time allowance exhausted')
    index=cursor.index;start=context.starts[index];period=context.dt[index];removal=context.removal
    initial_velocity=context.initial_velocity
    angle=context.angles[index];difference=context.differences[index];raw_difference=context.raw_differences[index]
    fraction=history.packet_fraction(cursor.query,start=start,duration=float(period))[0]
    initial_components,acceleration_components,matrix,metric,model,radius,initial_r,reference_force,acceleration,initial_position,reference_rates=(context.initial_components,context.acceleration_components,context.matrix,context.metric,context.model,context.radius,context.initial_r,context.reference_force,context.acceleration,context.initial_position,context.reference_rates)
    query,clock,source_values,source_rows,source_intervals,nominal,slope,state,left,right,u,raw_g,raw_h,common,departures,used,source_prefixes=(cursor.query,cursor.clock,cursor.source_values,cursor.source_rows,cursor.source_intervals,cursor.nominal,cursor.slope,cursor.state,cursor.left,cursor.right,cursor.u,cursor.raw_g,cursor.raw_h,cursor.common,cursor.departures,cursor.used,cursor.source_prefixes)
    prefix=clock.append(float(period),start=start)
    cursor.source_physical_upper=math.nextafter(cursor.source_physical_upper+float(period),math.inf)
    physical_source=source_values.append();reference_source=source_rows.append()
    _,packet_slope=history.packet_fraction(query,start=start,duration=float(period))
    nominal+=fraction.center*period;slope+=packet_slope*period
    next_common=previous.prior._prefix_scalar(prefix,query,slope,nominal)
    if fraction.upper==0:
        cursor.nominal=nominal;cursor.slope=slope;cursor.index=index+1
        return True
    used.append(index)
    source_bound=source_intervals.bound(physical_source['phases'][0],reference_source,phase=0)
    source_prefixes+=1
    actual_period=geo.Scalar(Value(fraction.center*period,geo._up(fraction.value.change*period),geo._up(fraction.value.remainder*period)),
        fraction.lower*period,fraction.upper*period)
    actual_angle=scalar_product(fraction.value,angle)
    delta_g=scalar_product(actual_period.value,Value(raw_difference))
    rates,_=_rates(state.position,initial_components,acceleration_components,common,relative.apply(matrix,raw_g),u,metric,model,radius)
    midpoint=geo._advance(state.position,rates,geo.fixed_scale(actual_period,.5))
    transport=geo.transport_context(midpoint.latitude,rates,model)
    _,_,estimate=_increment(state,left,right,initial_r,actual_angle,difference,raw_difference,reference_force,acceleration,matrix,
        midpoint.latitude,transport,actual_period,removal,model,source_bound)
    mid_common=geo.plus(common,geo.fixed_scale(actual_period,.5));mid_u=add(u,scale(estimate,.5));mid_g=add(raw_g,scale(delta_g,.5))
    revised,rest=_rates(midpoint,initial_components,acceleration_components,mid_common,relative.apply(matrix,mid_g),mid_u,metric,model,radius)
    transport=geo.transport_context(midpoint.latitude,revised,model)
    left,right,increment=_increment(state,left,right,initial_r,actual_angle,difference,raw_difference,reference_force,acceleration,matrix,
        midpoint.latitude,transport,actual_period,removal,model,source_bound)
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
    cursor.nominal=nominal
    cursor.slope=slope
    cursor.state=state
    cursor.left=left
    cursor.right=right
    cursor.u=u
    cursor.raw_g=raw_g
    cursor.raw_h=raw_h
    cursor.common=common
    cursor.departures=departures
    cursor.used=used
    cursor.source_prefixes=source_prefixes
    cursor.index=index+1
    return True


def _finish(context,cursor):
    if cursor.clock_profile is None:cursor.clock_profile,cursor.clock_force=_force_profile(context,cursor.time)
    plo,phi,initial_position,reference_rates,metric,acceleration_components,acceleration,vector,initial_r,limits,r,p,model,radius,reference,conditional_remainder,source,z,lo,hi,blo,bhi,refs,conditioning,matrix=(context.plo,context.phi,context.initial_position,context.reference_rates,context.metric,context.acceleration_components,context.acceleration,context.vector,context.initial_r,context.limits,context.r,context.p,context.model,context.radius,context.reference,context.conditional_remainder,context.source,context.z,context.lo,context.hi,context.blo,context.bhi,context.refs,context.conditioning,context.matrix)
    time,query,common,slope,raw_h,state,left,right,source_values,source_rows,source_intervals,source_prefixes,used,departures,clock_profile,clock_force=(cursor.time,cursor.query,cursor.common,cursor.slope,cursor.raw_h,cursor.state,cursor.left,cursor.right,cursor.source_values,cursor.source_rows,cursor.source_intervals,cursor.source_prefixes,cursor.used,cursor.departures,cursor.clock_profile,cursor.clock_force)
    source_values.close();source_rows.close()
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
    metadata=dict(conditional_acceleration_remainder=conditional_remainder,source_direct_remainder_installed=True,source_direct_steps=source_values.direct.visits,source_mean_value_interval_installed=True,source_derivative_steps=source_values.derivatives.visits,batched_bound_operations=True,component_transport=True,compiled_outward_arithmetic=True,source_norm_interval_installed=True,rounded_source_prefixes=source_prefixes,source_reference_steps=source_rows.visits,source_initial_padding=list(map(str,source_intervals.padding)),conditioning=conditioning.report(),conditioned_acceleration_change=acceleration.change,
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


def _cold_enclose(configuration,theta,dv,dt,*,time,lower,upper,reference,conditioning,
                  source_kernel,derivative_kernel,point_kernel,maximum_seconds=30.):
    context=_prepare(configuration,theta,dv,dt,lower=lower,upper=upper,reference=reference,
        conditioning=conditioning,maximum_seconds=maximum_seconds)
    kernels=dict(source_kernel=source_kernel,derivative_kernel=derivative_kernel,point_kernel=point_kernel)
    cursor=_new_cursor(context,time,cold_kernels=kernels)
    try:
        while _advance(context,cursor):pass
        return _finish(context,cursor)
    finally:cursor.close()


class Work:
    def __init__(self,maximum,reserve):
        self.maximum=maximum;self.reserve=reserve
        self.counts=dict(preparation_packets=0,force_profile_packets=0,prefix_packet_steps=0,
            tail_packet_steps=0,cursor_copies=0,source_state_copies=0,source_query_checks=0)
    def add(self,resource,amount):
        self.reserve(**{resource:amount});self.counts[resource]+=amount
    def step(self,kind):
        used=self.counts['prefix_packet_steps']+self.counts['tail_packet_steps']
        if used>=self.maximum:raise ValueError('finite native packet-step allowance exhausted')
        self.reserve(packet_steps=1,**{kind:1});self.counts[kind]+=1


def enclose_many(configuration,theta,dv,dt,*,times,lower,upper,reference,conditioning,
                 prefix_kernels,maximum_packet_steps,reserve,maximum_seconds=30.,on_report=None):
    if on_report is not None and not callable(on_report):
        raise ValueError('report observer must be callable')
    times=np.array(times,float,copy=True)
    if (times.ndim!=1 or not 1<=len(times)<=4096 or not np.all(np.isfinite(times))
            or np.any(np.diff(times)<=0.) or type(maximum_packet_steps) is not int
            or maximum_packet_steps<=0 or not callable(reserve)):
        raise ValueError('fixed ordered queries, finite packet allowance and reservation callback required')
    work=Work(maximum_packet_steps,reserve);work.add('preparation_packets',len(dt))
    c=_prepare(configuration,theta,dv,dt,lower=lower,upper=upper,reference=reference,
        conditioning=conditioning,maximum_seconds=maximum_seconds);c.work=work
    queries=[_query(c,float(t)) for t in times]
    parent=_new_cursor(c,float(times[-1]),prefix_kernels=prefix_kernels,profile=False);bounds=[]
    try:
        for time,query in zip(times,queries,strict=True):
            from .ilvis0_source_prefix import fork_floor
            earliest=min(F(query.lower),F(float(time))+F(float(c.limits[25]))*F(float(min(c.lo[25],c.z[25]))))
            for stream in (parent.source_rows,parent.source_values.derivatives,parent.source_values.direct.points):
                work.add('source_query_checks',1)
                earliest=min(earliest,F(fork_floor(stream,float(time),reference_binding=c.refs.binding)))
            while parent.index<len(c.dt):
                i=parent.index
                source_end=math.nextafter(parent.source_physical_upper+float(c.dt[i]),math.inf)
                end=max(F(c.starts[i])+F(float(c.dt[i])),parent.clock._physical+F(float(c.dt[i])),F(source_end))
                if not end<earliest:break
                work.step('prefix_packet_steps')
                if not _advance(c,parent):raise ValueError('canonical prefix reached its terminal query')
            work.add('cursor_copies',1);work.add('source_state_copies',3)
            child=_fork(c,parent,float(time),prefix_kernels)
            try:
                while child.index<len(c.dt) and c.starts[child.index]<=child.query.upper:
                    work.step('tail_packet_steps');_advance(c,child)
                bounds.append(_finish(c,child))
                if on_report is not None:
                    on_report(len(bounds)-1,deepcopy(bounds[-1].report()))
            finally:child.close()
        return dict(bounds=bounds,work=dict(work.counts),binding=c.binding,
            whole_native_prefix_qualified=False,observational_coverage_qualified=False,
            scientific_decision='abstain')
    finally:parent.close()
