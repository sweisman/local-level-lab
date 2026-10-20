# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive raw pitch-axis comparison under explicit orientation scenarios.

Receiver positions construct predictions, not an independent aircraft attitude.
Fused navigation and fitted nuisance values never enter this module.
"""
import math

import numpy as np

VERSION='raw-gyro-geographic-companion-v1'
MODELS=('sphere_rotating','sphere_still','flat_still')
OMEGA=7.2921150e-5;DPH=180./math.pi*3600.;RADIUS_M=6371000.


def geographic_vector(model,latitude,latitude_rate,longitude_rate,*,removal):
    if model not in MODELS:raise ValueError('declared physical candidate required')
    phi,pd,ld,removed=np.broadcast_arrays(latitude,latitude_rate,longitude_rate,removal)
    if not all(np.all(np.isfinite(x)) for x in (phi,pd,ld,removed)) or np.any((removed<0.)|(removed>1.)):
        raise ValueError('finite geometry and removal fraction in [0,1] required')
    zero=np.zeros_like(phi);standard=OMEGA*np.stack((np.cos(phi),zero,-np.sin(phi)),axis=-1)
    transport=np.stack((zero,zero,-ld),axis=-1) if model=='flat_still' else np.stack((np.cos(phi)*ld,-pd,-np.sin(phi)*ld),axis=-1)
    physical=standard if model=='sphere_rotating' else np.zeros_like(standard)
    return transport+physical-removed[...,None]*standard


def right_axis(heading,*,roll,pitch):
    psi,r,p=np.broadcast_arrays(heading,roll,pitch)
    if not all(np.all(np.isfinite(x)) for x in (psi,r,p)):raise ValueError('finite declared aircraft angles required')
    return np.stack((np.cos(psi)*np.sin(p)*np.sin(r)-np.sin(psi)*np.cos(r),
        np.sin(psi)*np.sin(p)*np.sin(r)+np.cos(psi)*np.cos(r),np.cos(p)*np.sin(r)),axis=-1)


def course_pitch_rate(course_rate,*,roll,pitch):
    return np.asarray(course_rate)*np.sin(roll)*np.cos(pitch)


def receiver_geometry(fixes):
    if len(fixes)<3:raise ValueError('at least three independent receiver fixes required')
    # Whitelist receiver fields; no fused navigation is consumed.
    data=np.asarray([[r[k] for k in ('time_s','latitude_rad','longitude_rad','height_m')] for r in fixes],float)
    t,phi,lam,height=data.T;dt=np.diff(t)
    if (not np.all(np.isfinite(data)) or np.any(dt<=0.) or np.any(dt>2.)
            or np.any(abs(phi)>=math.pi/2-1e-6)):
        raise ValueError('unsupported receiver timestamps, gaps or coordinate domain')
    lam=np.unwrap(lam);pd=np.diff(phi)/dt;ld=np.diff(lam)/dt
    midphi=(phi[1:]+phi[:-1])/2.;midh=(height[1:]+height[:-1])/2.;midt=(t[1:]+t[:-1])/2.
    d=1.-6.69437999014e-3*np.sin(midphi)**2
    north=6378137.*(1.-6.69437999014e-3)/d**1.5+midh
    east=(6378137./np.sqrt(d)+midh)*np.cos(midphi)
    courses={};rates={};velocities={}
    for model in MODELS:
        n,e=(RADIUS_M,RADIUS_M*(math.pi/2-midphi)) if model=='flat_still' else (north,east)
        if np.any(np.asarray(n)<=0.) or np.any(np.asarray(e)<=0.):raise ValueError('unsupported candidate metric')
        vn,ve=n*pd,e*ld
        if np.any(np.hypot(vn,ve)<=.01):raise ValueError('receiver course unavailable at negligible speed')
        psi=np.unwrap(np.arctan2(ve,vn));courses[model]=psi;rates[model]=np.gradient(psi,midt)
        velocities[model]=np.stack((vn,ve),axis=-1)
    return dict(times_s=midt,latitude_rad=midphi,latitude_rate_rads=pd,longitude_rate_rads=ld,
        height_m=midh,courses=courses,course_rates=rates,velocities_mps=velocities)


def nearest_unique(times,time,maximum):
    times=np.asarray(times,float)
    if not len(times) or not math.isfinite(time) or not math.isfinite(maximum) or maximum<0.:
        raise ValueError('finite receiver centers, time and matching tolerance required')
    difference=abs(times-time);index=int(np.argmin(difference))
    if difference[index]>maximum or np.count_nonzero(abs(difference-difference[index])<=1e-9)!=1:return None
    return index


def matched_bins(bins,geometry,*,recorded_mount_available):
    if recorded_mount_available is not True:return dict(supported=False,reason='recorded_mount_unavailable')
    ordered=sorted((int(k),v) for k,v in bins.items())
    if not ordered or len({k for k,_ in ordered})!=len(ordered):raise ValueError('nonempty unique UTC-second bins required')
    indices=[];raw=[];durations=[];seconds=[];errors=[];excluded=[];total=0.
    for second,row in ordered:
        duration=float(row['duration_s']);gyro=np.asarray(row['raw_aircraft'],float)
        if (not math.isfinite(duration) or not 0.<duration<=1.+1e-9 or gyro.shape!=(3,) or not np.all(np.isfinite(gyro))):
            raise ValueError('invalid raw gyro bin; no repair or channel substitution')
        total+=duration
        index=nearest_unique(geometry['times_s'],second+.5,.55)
        if index is None:
            excluded.append(dict(utc_second=second,reason='no_unique_receiver_interval_within_0.55s',duration_s=duration));continue
        indices.append(index);raw.append(gyro);durations.append(duration);seconds.append(second)
        errors.append(abs(geometry['times_s'][index]-second-.5))
    if not indices:return dict(supported=False,reason='no_common_receiver_gyro_support',excluded=excluded)
    return dict(supported=True,receiver_indices=np.asarray(indices,int),raw_aircraft=np.asarray(raw),
        durations_s=np.asarray(durations),utc_seconds=np.asarray(seconds,int),association_errors_s=np.asarray(errors),
        total_cached_duration_s=total,excluded=excluded,midpoint_assumption='UTC-second center; no raw interpolation')


def summarize(geometry,support,*,model,crab_deg,roll_deg,pitch_deg,removal):
    if not support.get('supported'):return dict(supported=False,reason=support['reason'],scientific_decision='abstain')
    if model not in MODELS:raise ValueError('declared physical candidate required')
    index=support['receiver_indices'];weights=support['durations_s'];duration=float(sum(weights))
    average=lambda x:float(np.average(x,weights=weights))
    heading=geometry['courses'][model][index]+math.radians(crab_deg)
    roll,pitch=math.radians(roll_deg),math.radians(pitch_deg)
    axis=right_axis(heading,roll=roll,pitch=pitch)
    vector=geographic_vector(model,geometry['latitude_rad'][index],geometry['latitude_rate_rads'][index],
        geometry['longitude_rate_rads'][index],removal=removal)
    geographic=np.einsum('ij,ij->i',axis,vector)
    aircraft=course_pitch_rate(geometry['course_rates'][model][index],roll=roll,pitch=pitch)
    observed=-support['raw_aircraft'][:,1];predicted=-(geographic+aircraft)
    course=geometry['courses'][model][index];velocity=geometry['velocities_mps'][model][index]
    mean_course=math.degrees(math.atan2(average(np.sin(course)),average(np.cos(course))))%360.
    return dict(supported=True,model=model,crab_deg=float(crab_deg),roll_deg=float(roll_deg),pitch_deg=float(pitch_deg),removal=float(removal),
        matched_bins=len(index),matched_duration_s=duration,matched_fraction_of_cached_duration=duration/support['total_cached_duration_s'],
        excluded_bins=len(support['excluded']),maximum_association_error_s=float(max(support['association_errors_s'])),
        observed_nose_down_dph=average(observed)*DPH,predicted_nose_down_dph=average(predicted)*DPH,
        geographic_nose_down_dph=-average(geographic)*DPH,declared_course_motion_nose_down_dph=-average(aircraft)*DPH,
        observed_minus_scenario_dph=average(observed-predicted)*DPH,
        observed_nose_down_deg=average(observed)*duration*180./math.pi,
        predicted_nose_down_deg=average(predicted)*duration*180./math.pi,
        mean_candidate_course_deg=mean_course,mean_latitude_deg=math.degrees(average(geometry['latitude_rad'][index])),
        mean_north_velocity_mps=average(velocity[:,0]),mean_east_velocity_mps=average(velocity[:,1]),
        mean_candidate_speed_mps=average(np.linalg.norm(velocity,axis=1)),
        independent_aircraft_pitch_removed=False,orientation_assumed=True,fused_attitude_used=False,
        field_magnitude_fitted=False,scientific_decision='abstain')
