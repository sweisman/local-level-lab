# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive raw-stream analytics; no optimization or scientific decisions.

Fused attitude may describe a motion correction but never provides independent
Earth evidence. Ground-course proxies explicitly assume zero bank/pitch/crab.
"""
import math
from collections import defaultdict

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import ilvis0_installation as installation

VERSION = 'ilvis0-stretch-analytics-v1'
RADIUS_M = 6371000.
DPH = 180/math.pi*3600
ANGLE_SCALES = {8: 2.**-18, 21: 2.**-28}
TRACK_AXES = ('across_left', 'along', 'down')


def trajectory(fixes):
    t = np.array([r['time_s'] for r in fixes])
    phi = np.array([r['latitude_rad'] for r in fixes])
    lam = np.unwrap([r['longitude_rad'] for r in fixes])
    dt = np.diff(t)
    if len(dt) < 2 or not np.all(np.isfinite(np.r_[t, phi, lam])) or np.any(dt <= 0) or np.any(dt > 2):
        raise ValueError('unsupported receiver timestamps or gaps')
    middle_phi = (phi[1:]+phi[:-1])/2
    phi_dot, lam_dot = np.diff(phi)/dt, np.diff(lam)/dt
    vn, ve = RADIUS_M*phi_dot, RADIUS_M*np.cos(middle_phi)*lam_dot
    speed = np.hypot(vn, ve)
    course = np.unwrap(np.arctan2(ve, vn))
    middle_t = (t[1:]+t[:-1])/2
    course_rate = np.gradient(course, middle_t)
    average = lambda x: float(np.sum(np.asarray(x)*dt)/np.sum(dt))
    out = dict(mean_north_velocity_mps=average(vn), mean_east_velocity_mps=average(ve),
               mean_position_ground_speed_mps=average(speed), mean_latitude_rate_dph=average(phi_dot)*DPH,
               mean_longitude_rate_dph=average(lam_dot)*DPH,
               mean_course_turn_dph=average(course_rate)*DPH,
               sphere_transport_across_left_dph=average(speed/RADIUS_M)*DPH,
               sphere_transport_along_dph=0., sphere_transport_down_dph=average(-np.sin(middle_phi)*lam_dot)*DPH,
               disc_transport_across_left_dph=0., disc_transport_along_dph=0.,
               disc_transport_down_dph=-average(lam_dot)*DPH,
               mean_height_m=average((np.array([r['height_m'] for r in fixes])[1:]+
                                      np.array([r['height_m'] for r in fixes])[:-1])/2))
    samples = [dict(time_s=float(time), course_rad=float(psi), course_rate_rads=float(rate))
               for time, psi, rate in zip(middle_t, course, course_rate)]
    return out, samples


def attitude_matrix(row):
    return installation.rotation([row['roll_deg'], row['pitch_deg'], row['heading_deg']])


def attitude_rates(rows):
    """Euler-angle derivatives only; deliberately never read fused gyro channels."""
    times = np.array([r['time_s'] for r in rows])
    if len(times)<3 or np.any(np.diff(times)<=0):
        raise ValueError('unsupported attitude timestamps')
    angles = np.unwrap(np.deg2rad([[r[k] for k in ('roll_deg','pitch_deg','heading_deg')] for r in rows]), axis=0)
    rates = np.gradient(angles, times, axis=0)
    roll, pitch = angles[:,0], angles[:,1]
    dr, dp, dh = rates.T
    result = np.column_stack((dr-dh*np.sin(pitch), dp*np.cos(roll)+dh*np.sin(roll)*np.cos(pitch),
                              -dp*np.sin(roll)+dh*np.cos(roll)*np.cos(pitch)))
    for i,r in enumerate(rows):
        a,b=max(0,i-1),min(len(rows)-1,i+1)
        if times[b]-times[a]>4 or any(x.get('alignment_status')!=0 for x in rows[a:b+1]):
            result[i]=np.nan
    return result


def track_vector(ned, course):
    n,e,d = ned
    return np.array([math.sin(course)*n-math.cos(course)*e,
                     math.cos(course)*n+math.sin(course)*e,d])


def context_corrected(gyro_aircraft, attitude, aircraft_relative_rate, course):
    return track_vector(attitude_matrix(attitude)@(gyro_aircraft-aircraft_relative_rate), course)


def stop_reason(fit):
    if fit.get('error'): return 'execution_error'
    if fit.get('converged'): return 'passed'
    text = fit.get('message','').lower()
    if any(s in text for s in ('maximum','budget','evaluation limit','exhaust')): return 'budget'
    if 'stability' in text: return 'stability_check'
    if any(s in text for s in ('no decreasing','stall','no feasible','no progress')): return 'stall'
    if 'stationar' in text: return 'stationarity_check'
    return 'other_numerical_stop'


def shared_track(left, right):
    """Same UTC and close reported positions suggest a shared leg, not installation."""
    a = {r['time_s']:r for r in left['receiver_fixes']}
    b = {r['time_s']:r for r in right['receiver_fixes']}
    matched = sorted(set(a)&set(b))
    distances, heights = [], []
    for t in matched:
        x,y=a[t],b[t]
        h = math.sin((y['latitude_rad']-x['latitude_rad'])/2)**2 + math.cos(x['latitude_rad'])*math.cos(y['latitude_rad'])*math.sin((y['longitude_rad']-x['longitude_rad'])/2)**2
        distances.append(2*RADIUS_M*math.asin(math.sqrt(min(1.,max(0.,h)))))
        heights.append(abs(y['height_m']-x['height_m']))
    maximum = max(distances) if distances else None
    return dict(matched_receiver_epochs=len(matched), maximum_track_separation_m=maximum,
                maximum_height_separation_m=max(heights) if heights else None,
                same_track_candidate=bool(len(matched)>=3 and maximum<=1000 and max(heights)<=300))


def scan_windows(path, expected_hash, leap, windows):
    """One checksummed source pass, integer sums and fused-context records only."""
    bins = {w['segment_id']:{} for w in windows}
    nav = []
    previous = None
    signature, mount = '', None
    low=min(w['start_s'] for w in windows)-3
    high=max(w['end_s'] for w in windows)+3
    with il.open_source(path) as original:
        stream = follow.HashedReader(original)
        for frame in ap.frames(stream):
            if frame.tag=='$MSG' and frame.group in (1,20):
                signature=frame.packet[10:-4].hex()
                setting=installation.installation_message(frame)
                mount=setting.get('imu_to_aircraft_rotation') if setting['usable'] else None
            if frame.tag!='$GRP': continue
            if frame.group==1:
                r=ap.group1(frame); r['time_s']=follow.utc_tag(r,leap)
                if low<=r['time_s']<=high: nav.append(r)
            elif frame.group==4:
                r=ap.group4(frame); t=follow.utc_tag(r,leap)
                dt=None if previous is None else t-previous
                previous=t
                for w in windows:
                    if not w['start_s']<=t<=w['end_s']: continue
                    if dt is None or t-dt<w['start_s']: continue
                    if (not .0025<=dt<=.0075 or r['imu_type']!=w['imu_type'] or r['rate_code']!=2
                            or r['data_status'] or r['imu_status'] or signature!=w['signature']
                            or r['time_types']!=w['time_types']):
                        raise ValueError('selected raw completeness/configuration mismatch')
                    key=math.floor(t)
                    bin=bins[w['segment_id']].setdefault(key,dict(count=0,raw=[0]*6,header_s=0.,first_s=t-dt,last_s=t,mount=mount))
                    bin['count']+=1; bin['header_s']+=dt; bin['last_s']=t
                    for j,field in enumerate(ap.RAW_FIELDS): bin['raw'][j]+=r[field]
        if stream.digest.hexdigest()!=expected_hash: raise ValueError('original SHA256 mismatch')
    return bins,nav,dict(source_sha256=stream.digest.hexdigest(),source_bytes=stream.size)


def raw_summary(bins, kind):
    scale=ANGLE_SCALES[kind]
    count=sum(b['count'] for b in bins.values())
    if not count: raise ValueError('no selected increments')
    nominal=count*.005
    header=sum(b['header_s'] for b in bins.values())
    sums=np.array([sum(b['raw'][j] for b in bins.values()) for j in range(6)],float)
    out=dict(native_samples=count, nominal_duration_s=nominal, header_duration_s=header,
             cumulative_clock_difference_s=header-nominal,angle_scale_rad_per_count=scale,
             recorded_mount_available=all(b['mount'] is not None for b in bins.values()))
    for j,axis in enumerate('xyz'):
        out['raw_dtheta_'+axis+'_sum_counts']=int(sums[j+3])
        out['raw_native_mean_'+axis+'_dph']=sums[j+3]*scale/nominal*DPH
        out['header_native_mean_'+axis+'_dph']=sums[j+3]*scale/header*DPH
    if out['recorded_mount_available']:
        total=sum((np.asarray(b['mount'])@np.asarray(b['raw'][3:])*scale for b in bins.values()),start=np.zeros(3))
        out.update({'raw_aircraft_mean_'+axis+'_dph':total[j]/nominal*DPH for j,axis in enumerate('xyz')})
    return out


def nearest(rows, time, maximum):
    times=np.array([r['time_s'] for r in rows])
    i=int(np.searchsorted(times,time))
    choices=[j for j in (i-1,i) if 0<=j<len(rows)]
    if not choices: return None
    choices.sort(key=lambda j:abs(times[j]-time))
    if abs(times[choices[0]]-time)>maximum: return None
    if len(choices)>1 and abs(abs(times[choices[0]]-time)-abs(times[choices[1]]-time))<1e-8: return None
    return choices[0]


def motion_summary(bins, nav, course_samples, kind):
    rates=attitude_rates(nav) if len(nav)>=3 else None
    out={}; seconds={}; headings=[]; crabs=[]; durations=[]
    values=defaultdict(list)
    for second,b in bins.items():
        if b['count']<190 or b['mount'] is None: continue
        time=(b['first_s']+b['last_s'])/2
        ci=nearest(course_samples,time,.55)
        if ci is None: continue
        c=course_samples[ci]; duration=b['count']*.005
        gyro=np.asarray(b['mount'])@np.asarray(b['raw'][3:])*ANGLE_SCALES[kind]/duration
        proxy=np.array([-gyro[1],gyro[0],gyro[2]-c['course_rate_rads']])
        info=dict(duration_s=duration,level_course_proxy=proxy.tolist(),raw_aircraft=gyro.tolist())
        values['level_course_proxy'].append(proxy);values['proxy_weights'].append(duration)
        ni=nearest(nav,time,.55) if rates is not None else None
        if ni is not None and np.all(np.isfinite(rates[ni])):
            r=nav[ni]
            corrected=context_corrected(gyro,r,rates[ni],c['course_rad'])
            info['fused_context_corrected']=corrected.tolist()
            values['fused_context_corrected'].append(corrected);values['context_weights'].append(duration)
            heading=math.radians(r['heading_deg']);headings.append(heading)
            crabs.append((heading-c['course_rad']+math.pi)%(2*math.pi)-math.pi); durations.append(duration)
        seconds[second]=info
    total=sum(b['count']*.005 for b in bins.values())
    for label,weight in (('level_course_proxy','proxy_weights'),('fused_context_corrected','context_weights')):
        coverage=sum(values[weight])/total
        out[label+'_coverage_fraction']=coverage
        if coverage>=.95:
            mean=np.average(values[label],axis=0,weights=values[weight])*DPH
            out.update({label+'_mean_'+axis+'_dph':float(mean[i]) for i,axis in enumerate(TRACK_AXES)})
    if headings:
        circular=lambda x:math.atan2(sum(w*math.sin(v) for w,v in zip(durations,x)),sum(w*math.cos(v) for w,v in zip(durations,x)))
        out.update(fused_context_mean_heading_deg=math.degrees(circular(headings))%360,
                   fused_context_mean_crab_deg=math.degrees(circular(crabs)))
    out['independent_motion_corrected_rates_available']=False
    return out,seconds


def pair_difference(left, right):
    shared=sorted(set(left)&set(right))
    out=dict(matched_raw_seconds=len(shared))
    for label in ('raw_aircraft','level_course_proxy','fused_context_corrected'):
        keys=[k for k in shared if label in left[k] and label in right[k]]
        out[label+'_matched_seconds']=len(keys)
        if not keys: continue
        diff=np.array([np.array(left[k][label])-right[k][label] for k in keys])*DPH
        weights=[min(left[k]['duration_s'],right[k]['duration_s']) for k in keys]
        axes=('x','y','z') if label=='raw_aircraft' else TRACK_AXES
        for j,axis in enumerate(axes):
            out[label+'_difference_'+axis+'_dph']=float(np.average(diff[:,j],weights=weights))
            out[label+'_difference_rms_'+axis+'_dph']=float(np.sqrt(np.average(diff[:,j]**2,weights=weights)))
    return out
