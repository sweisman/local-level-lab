# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only ESA interval selection; no IMU values or model outcomes."""
from dataclasses import asdict,dataclass
import math

import numpy as np

VERSION='esa-receiver-selection-v1'


@dataclass(frozen=True)
class Policy:
    maximum_receiver_gap_s:float=.75
    window_s:float=10.
    maneuver_margin_s:float=30.
    minimum_duration_s:float=1200.
    minimum_speed_mps:float=50.
    minimum_distance_m:float=60000.
    maximum_median_vertical_mps:float=1.
    maximum_median_course_rate_deg_s:float=.02
    maximum_horizontal_sd_m:float=5.
    maximum_vertical_sd_m:float=10.
    maximum_pdop:float=4.
    minimum_satellites:int=8


def select(rows,*,imu_support,source_integrity_verified=False):
    """Use full supported receiver windows and maximal contiguous retained runs.

    imu_support describes a previously verified uninterrupted IMU time span.
    This function never reads gyro values or infers timing integrity itself.
    """
    policy=Policy();rows=list(rows);n=len(rows)
    if source_integrity_verified is not True:raise ValueError('verified source integrity required')
    if n<2:raise ValueError('at least two ordered receiver observations required')
    support=np.asarray(imu_support,float)
    if support.shape!=(2,) or not np.all(np.isfinite(support)) or support[1]<=support[0]:
        raise ValueError('finite uninterrupted IMU support required')
    keys=('time_s','latitude_deg','longitude_deg','height_m','north_mps','east_mps','up_mps','pdop')
    values=np.array([[r[k] for k in keys] for r in rows],float)
    if not np.all(np.isfinite(values)):raise ValueError('finite receiver measurements required')
    t=values[:,0];dt=np.diff(t);weeks=[r['gps_week'] for r in rows]
    if np.any(dt<=0.) or len(set(weeks))!=1:raise ValueError('strictly ordered single-week receiver times required')
    if np.any(abs(values[:,1])>90.) or np.any(abs(values[:,2])>180.) or np.any((t<0.)|(t>=604800.)):
        raise ValueError('unsupported coordinate/time range')
    sequence=np.asarray([r['sequence'] for r in rows]);satellites=np.asarray([r['satellites'] for r in rows],float)
    if (not np.all(np.isfinite(sequence)) or np.any(np.diff(sequence)<=0.)
            or not np.all(np.isfinite(satellites)) or np.any(satellites<0.) or np.any(satellites!=np.floor(satellites))):
        raise ValueError('ordered sequence and nonnegative integer satellite counts required')
    covariance=np.asarray([r['position_variance_m2'] for r in rows],float)
    if covariance.shape!=(n,3) or not np.all(np.isfinite(covariance)):raise ValueError('finite covariance diagonals required')
    reasons=[set() for _ in rows]
    speed=np.hypot(values[:,4],values[:,5]);course=np.arctan2(values[:,5],values[:,4])
    quality=(np.all(covariance>0.,axis=1)&(covariance[:,0]<=policy.maximum_horizontal_sd_m**2)
        &(covariance[:,1]<=policy.maximum_horizontal_sd_m**2)&(covariance[:,2]<=policy.maximum_vertical_sd_m**2)
        &(values[:,7]>0.)&(values[:,7]<=policy.maximum_pdop)&(satellites>=policy.minimum_satellites))
    for i in range(n):
        if speed[i]<policy.minimum_speed_mps:reasons[i].add('speed')
        if not quality[i]:reasons[i].add('receiver_quality')
        if not support[0]<=t[i]<=support[1]:reasons[i].add('imu_support')
    splits=np.flatnonzero((dt>policy.maximum_receiver_gap_s)|(np.diff(sequence)!=1))+1
    boundaries=np.r_[0,splits,n];blocks=[]
    half=policy.window_s/2.
    for start,end in zip(boundaries[:-1],boundaries[1:]):
        start=int(start);end=int(end);blocks.append(dict(first_index=start,last_index=end-1))
        bt=t[start:end];failed=[]
        rates=np.abs(np.rad2deg(np.arctan2(np.sin(np.diff(course[start:end])),np.cos(np.diff(course[start:end]))))/np.diff(bt))
        for i in range(start,end):
            lower=t[i]-half;upper=t[i]+half
            if lower<bt[0] or upper>bt[-1]:
                reasons[i].add('motion_window_edge');continue
            a=start+int(np.searchsorted(bt,lower,side='left'))
            b=start+int(np.searchsorted(bt,upper,side='right'))
            if b-a<2 or np.any(speed[a:b]==0.):
                reasons[i].add('undefined_course');failed.append((lower,upper));continue
            vertical=float(np.median(abs(values[a:b,6])))
            turn=float(np.median(rates[a-start:b-start-1]))
            if vertical>policy.maximum_median_vertical_mps or turn>policy.maximum_median_course_rate_deg_s:
                reasons[i].add('motion_window');failed.append((lower,upper))
        # Merge all exclusion intervals before marking; no quadratic expansion.
        merged=[]
        for lower,upper in failed:
            lower-=policy.maneuver_margin_s;upper+=policy.maneuver_margin_s
            if merged and lower<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],upper)
            else:merged.append([lower,upper])
        for lower,upper in merged:
            a=start+int(np.searchsorted(bt,lower,side='left'));b=start+int(np.searchsorted(bt,upper,side='right'))
            for i in range(a,b):reasons[i].add('maneuver_margin')
    eligible=[];rejected=[]
    for block in blocks:
        i=block['first_index'];last=block['last_index']+1
        while i<last:
            if reasons[i]:i+=1;continue
            start=i
            while i+1<last and not reasons[i+1]:i+=1
            end=i+1;indices=slice(start,end);duration=float(t[end-1]-t[start])
            distance=float(np.sum((speed[start:end-1]+speed[start+1:end])*.5*np.diff(t[indices])))
            direction=math.degrees(math.atan2(float(np.mean(np.sin(course[indices]))),float(np.mean(np.cos(course[indices])))))%360.
            row=dict(first_index=start,last_index=end-1,epochs=end-start,gps_week=weeks[start],
                first_time_s=float(t[start]),last_time_s=float(t[end-1]),duration_s=duration,distance_m=distance,
                first_utc_date=rows[start]['utc_date'],first_utc_time=rows[start]['utc_time'],
                last_utc_date=rows[end-1]['utc_date'],last_utc_time=rows[end-1]['utc_time'],
                minimum_speed_kmh=float(np.min(speed[indices])*3.6),mean_speed_kmh=float(np.mean(speed[indices])*3.6),
                maximum_speed_kmh=float(np.max(speed[indices])*3.6),mean_north_mps=float(np.mean(values[indices,4])),
                mean_east_mps=float(np.mean(values[indices,5])),mean_course_deg=direction,
                mean_latitude_deg=float(np.mean(values[indices,1])),minimum_height_m=float(np.min(values[indices,3])),
                maximum_height_m=float(np.max(values[indices,3])))
            failure=[]
            if duration<policy.minimum_duration_s:failure.append('duration')
            if distance<policy.minimum_distance_m:failure.append('distance')
            row['rejection_reasons']=failure
            (rejected if failure else eligible).append(row);i=end
    return dict(version=VERSION,policy=asdict(policy),blocks=blocks,eligible=eligible,rejected_runs=rejected,
        epoch_reasons=[sorted(value) for value in reasons],total_receiver_epochs=n,
        excluded_epochs=sum(bool(value) for value in reasons),gyro_used_for_selection=False,
        fused_navigation_used_for_selection=False,source_integrity_verified=True,
        receiver_covariance_calibrated=False,earth_model_fits=0,scientific_decision='abstain')
