# SPDX-License-Identifier: AGPL-3.0-or-later
"""All geometry-selected high-speed level segments, before model-dependent fits.

Receiver VTG measures ground speed. Fused Group1 supplies screening context only;
its attitude/rates are never observations in the subsequent Earth profiles.
No interpolation, course smoothing, relaxed alignment or original deletion.
"""
from collections import Counter
import datetime
import hashlib
import json
import math

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import ilvis0_installation as installation, ilvis0_motion_diagnosis as motion
from . import ilvis0_corpus_modeling as corpus

VERSION='ilvis0-all-highspeed-level-segments-v1'
POLICY=dict(il.SCREEN_POLICY,minimum_window_s=240.,minimum_speed_mps=700/3.6,
    diagnostic_section_s=600.,receiver_association_s=.5,native_guard_s=.2,
    version=VERSION,speed_source='checksummed primary receiver VTG, unique dated GGA association')

# Prospective receiver/motion inventory only. Fifty kilometres slightly exceeds
# the original 4-minute/700-km/h minimum path length (46.7 km). The 180-km/h
# sample floor excludes ground movement; this is not a model-fit eligibility gate.
DISTANCE_INVENTORY_POLICY=dict(POLICY,
    version='ilvis0-distance-duration-inventory-v1',
    minimum_window_s=600.,minimum_speed_mps=180/3.6,
    minimum_distance_m=50000.)

RECEIVER_RAW_INVENTORY_POLICY=dict(DISTANCE_INVENTORY_POLICY,
    version='ilvis0-receiver-raw-inventory-v1',
    selection_mode='receiver_raw_support')

ALIGNMENT_ABLATION_POLICY=dict(DISTANCE_INVENTORY_POLICY,
    version='ilvis0-alignment-status-ablation-v1',
    require_alignment_status=False)


def tile(start,end):
    duration=end-start
    if not math.isfinite(duration) or duration<240:raise ValueError('segment must span at least240s')
    n=int(math.ceil(duration/600))
    edges=[start+duration*i/n for i in range(n)]+[end]
    return list(zip(edges,edges[1:]))


def select_segments(nav,receiver,raw_runs,rejections=None,*,policy=None):
    """Maximal eligible intervals, with diagnostic sections and a joint primary fit.

    Exact legacy central course rate and alignment/roll/climb/buffer rules remain.
    Every receiver speed sample matters; short failures split the interval, and
    receiver gaps above2s are unsupported. Nothing is selected on gyro outcomes.
    """
    p=POLICY if policy is None else policy
    minimum_window=p['minimum_window_s']
    minimum_distance=p.get('minimum_distance_m')
    if (not math.isfinite(minimum_window) or minimum_window<240 or
            (minimum_distance is not None and
             (not math.isfinite(minimum_distance) or minimum_distance<=0))):
        raise ValueError('invalid prospective duration or distance policy')
    if len(nav)<3 or len(receiver)<2:return []
    nt=np.array([r['utc_week_s'] for r in nav]);rt=np.array([r['utc_week_s'] for r in receiver])
    speed=np.array([r['speed_mps'] for r in receiver])
    fields=np.array([[r[k] for k in ('velocity_north_mps','velocity_east_mps','velocity_down_mps','roll_deg')]
                     for r in nav])
    if (not all(np.all(np.isfinite(a)) for a in (nt,rt,speed,fields))
            or np.any(np.diff(nt)<=0) or np.any(np.diff(rt)<=0) or np.any(speed<0)):
        raise ValueError('invalid/reversed/duplicate motion or receiver epochs')
    # A unique closest receiver sample, within the half-second association tolerance.
    i=np.searchsorted(rt,nt);a=np.clip(i-1,0,len(rt)-1);b=np.clip(i,0,len(rt)-1)
    da,db=abs(rt[a]-nt),abs(rt[b]-nt);closest=np.where(da<db,a,b)
    unique=(a==b)|(abs(da-db)>1e-6)
    associated=unique&(np.minimum(da,db)<=p['receiver_association_s'])
    # Never span missing receiver epochs even if a nearby sample is available.
    gaps=np.flatnonzero(np.diff(rt)>p['maximum_context_gap_s'])
    for j in gaps:associated[(nt>rt[j])&(nt<rt[j+1])]=False
    course=np.degrees(np.arctan2(fields[:,1],fields[:,0]))
    rate=np.full(len(nt),np.inf)
    rate[1:-1]=abs((course[2:]-course[:-2]+180)%360-180)/(nt[2:]-nt[:-2])
    complete=np.zeros(len(nt),bool)
    complete[1:-1]=(np.diff(nt)[:-1]<=2)&(np.diff(nt)[1:]<=2)
    alignment=np.array([r['alignment_status']==0 for r in nav])
    good=(complete&associated&(speed[closest]>=p['minimum_speed_mps'])
          &(abs(fields[:,2])<=p['maximum_vertical_speed_mps'])
          &(abs(fields[:,3])<=p['maximum_roll_deg'])
          &(rate<=p['maximum_course_rate_deg_s'])
          &(alignment if p.get('require_alignment_status',True) else np.ones(len(nav),bool)))
    if rejections is not None:
        for name,bad in dict(missing_motion_context=~complete,missing_receiver_support=~associated,
                below_ground_speed=speed[closest]<p['minimum_speed_mps'],
                excessive_vertical_speed=abs(fields[:,2])>p['maximum_vertical_speed_mps'],
                excessive_roll=abs(fields[:,3])>p['maximum_roll_deg'],
                excessive_course_rate=rate>p['maximum_course_rate_deg_s'],
                incomplete_alignment=~alignment).items():
            rejections[name]+=int(np.sum(bad))
    spans=[];start=None;last=None
    for t,ok in zip(nt,good):
        if ok:
            if start is None:start=float(t)
            last=float(t)
        elif start is not None:
            spans.append((start,last));start=None
    if start is not None:spans.append((start,last))
    receiver_spans=[];start=None;last=None
    for t,v in zip(rt,speed):
        if start is not None and (v<p['minimum_speed_mps'] or t-last>p['maximum_context_gap_s']):
            receiver_spans.append((start,last));start=None
        if v>=p['minimum_speed_mps']:
            if start is None:start=float(t)
            last=float(t)
    if start is not None:receiver_spans.append((start,last))
    spans=[(max(a,c),min(b,d)) for a,b in spans for c,d in receiver_spans if max(a,c)<=min(b,d)]
    out=[];buffer=p['maneuver_buffer_s'];guard=p['native_guard_s']
    for first,last in spans:
        first+=buffer;last-=buffer
        for run in raw_runs:
            begin=max(first,run['start_s']+guard);end=min(last,run['end_s']-guard)
            if end-begin<minimum_window:
                if rejections is not None:rejections['short_after_buffers_or_raw_intersection']+=1
                continue
            # Strictly verify all speed observations inside this candidate, including
            # those not selected as closest to a navigation observation.
            used=(rt>=begin)&(rt<=end)
            if not np.any(used) or np.any(speed[used]<p['minimum_speed_mps']):continue
            distance=None
            if minimum_distance is not None:
                times=rt[used];speeds=speed[used]
                if len(times)<2:continue
                # No endpoint extrapolation or interpolation across receiver gaps.
                distance=float(np.sum(np.minimum(speeds[:-1],speeds[1:])*np.diff(times)))
                if distance<minimum_distance:
                    if rejections is not None:rejections['below_sampled_receiver_distance']+=1
                    continue
            row=dict(start_s=begin,end_s=end,duration_s=end-begin,
                **{k:run[k] for k in ('signature','imu_type','time_types')},
                minimum_receiver_ground_speed_kmh=float(np.min(speed[used])*3.6),
                median_receiver_ground_speed_kmh=float(np.median(speed[used])*3.6),
                diagnostic_sections=[dict(start_s=a,end_s=b) for a,b in tile(begin,end)],
                last_section=True,level_context_source='Group1 fused motion, screening only',
                raw_guard_s=guard,scientific_eligible=False)
            if distance is not None:row['receiver_distance_m']=distance
            out.append(row)
    return sorted(out,key=lambda r:(r['start_s'],r['end_s'],r['signature']))


def select_receiver_raw_segments(receiver,raw_runs,rejections=None,*,policy):
    """Broad receiver/raw continuity inventory, with no fused motion veto.

    This selects candidate trajectories only. It neither establishes level
    flight nor uses gyro increments or Earth-model residuals.
    """
    if policy.get('selection_mode')!='receiver_raw_support':
        raise ValueError('receiver/raw inventory policy required')
    times=np.array([r['utc_week_s'] for r in receiver],float)
    speeds=np.array([r['speed_mps'] for r in receiver],float)
    if len(times)<2:return []
    if (not np.all(np.isfinite(times)) or
            not np.all(np.isfinite(speeds)) or np.any(np.diff(times)<=0) or
            np.any(speeds<0)):
        raise ValueError('ordered finite receiver speed samples required')
    floor=policy['minimum_speed_mps'];maximum_gap=policy['maximum_context_gap_s']
    minimum_window=policy['minimum_window_s'];minimum_distance=policy['minimum_distance_m']
    if (not all(math.isfinite(x) and x>0 for x in
            (floor,maximum_gap,minimum_window,minimum_distance)) or
            minimum_window<240):
        raise ValueError('finite positive receiver/raw inventory limits required')
    if rejections is not None:
        rejections['below_ground_speed']+=int(np.sum(speeds<floor))
    spans=[];start=None;last=None
    for t,speed in zip(times,speeds):
        if start is not None and (speed<floor or t-last>maximum_gap):
            spans.append((start,last));start=None
        if speed>=floor:
            if start is None:start=float(t)
            last=float(t)
    if start is not None:spans.append((start,last))
    out=[];buffer=policy['maneuver_buffer_s'];guard=policy['native_guard_s']
    for first,last in spans:
        first+=buffer;last-=buffer
        for run in raw_runs:
            begin=max(first,run['start_s']+guard)
            end=min(last,run['end_s']-guard)
            if end-begin<minimum_window:
                if rejections is not None:rejections['short_after_buffers_or_raw_intersection']+=1
                continue
            used=(times>=begin)&(times<=end)
            selected_times=times[used];selected_speeds=speeds[used]
            if (len(selected_times)<2 or
                    np.any(np.diff(selected_times)>maximum_gap) or
                    np.any(selected_speeds<floor)):
                raise ValueError('candidate receiver support differs from span')
            distance=float(np.sum(np.minimum(selected_speeds[:-1],selected_speeds[1:])*
                                  np.diff(selected_times)))
            if distance<minimum_distance:
                if rejections is not None:rejections['below_sampled_receiver_distance']+=1
                continue
            out.append(dict(start_s=begin,end_s=end,duration_s=end-begin,
                **{k:run[k] for k in ('signature','imu_type','time_types')},
                minimum_receiver_ground_speed_kmh=float(np.min(selected_speeds)*3.6),
                median_receiver_ground_speed_kmh=float(np.median(selected_speeds)*3.6),
                receiver_distance_m=distance,
                diagnostic_sections=[dict(start_s=a,end_s=b) for a,b in tile(begin,end)],
                last_section=True,level_context_source='none; level motion unverified',
                raw_guard_s=guard,scientific_eligible=False,
                selection_used_group1_motion=False,motion_screened=False))
    return sorted(out,key=lambda r:(r['start_s'],r['end_s'],r['signature']))


def scan(path,context,*,policy=None):
    """Strict streaming context/raw completeness inventory; no physical residuals."""
    p=POLICY if policy is None else policy
    if not context['timing']['accepted']:raise ValueError('unsupported UTC mapping')
    leap=context['timing']['gps_minus_utc_s'];expected=context['inspection']['source_sha256']
    nav=[];gga=[];zda=[];vtg=[];cross=[];runs=[];current=None;previous=None;signature=''
    nmea=ap.NMEA();rejections=Counter();counts=Counter()
    with il.open_source(path) as original:
        stream=follow.HashedReader(original)
        for frame in ap.frames(stream):
            counts[f'{frame.tag}:{frame.group}']+=1
            if frame.tag=='$MSG' and frame.group in (1,20):signature=frame.packet[10:-4].hex()
            if frame.tag!='$GRP':continue
            if frame.group==1:nav.append(ap.group1(frame))
            elif frame.group==4:
                row=ap.group4(frame);t=follow.utc_tag(row,leap)
                key=(signature,row['imu_type'],row['time_types'])
                interval=None if previous is None else t-previous[0]
                good=(interval is not None and .0025<=interval<=.0075 and row['rate_code']==2
                    and not row['data_status'] and not row['imu_status'] and key==previous[1])
                if not good:
                    if current:runs.append(current);current=None
                    rejections['unsupported_native_interval_status_or_epoch']+=1
                else:
                    if current is None:current=dict(start_s=t-interval,end_s=t,signature=signature,
                        imu_type=row['imu_type'],time_types=row['time_types'])
                    else:current['end_s']=t
                previous=(t,key)
            elif frame.group==10001:
                header=ap.time_header(frame)
                for sentence in nmea.feed(ap.group10001(frame)[1]):
                    if not sentence['valid']:continue
                    f=sentence['fields']
                    if f[0].endswith('ZDA'):
                        date=datetime.date(int(f[4]),int(f[3]),int(f[2]))
                        zda.append(dict(header,date=date.isoformat(),sod=follow.utc_sod(f[1])))
                    elif f[0].endswith('GGA'):
                        if int(f[6]) not in (1,2,4,5):rejections['unsupported_GGA_quality']+=1;continue
                        if not f[9] or not f[11]:rejections['missing_GGA_height']+=1;continue
                        if f[10]!='M' or f[12]!='M':raise ValueError('unsupported GPS height units')
                        gga.append(dict(header,sod=follow.utc_sod(f[1]),latitude_deg=ap.coordinate(f[2],f[3]),
                            longitude_deg=ap.coordinate(f[4],f[5]),fix_quality=int(f[6]),
                            orthometric_height_m=float(f[9]),geoid_separation_m=float(f[11])))
                    elif f[0].endswith('VTG'):
                        try:r=motion.parse_vtg(f)
                        except ValueError as error:rejections[str(error)]+=1;continue
                        vtg.append(dict(header,**r,receiver_stream_offset=sentence['stream_offset']))
            if frame.group in (1,4):
                header=ap.time_header(frame)
                if header['time_types']==33:cross.append(header['time1_s']-header['time2_s'])
            if max(map(len,(nav,gga,zda,vtg,cross)))>250000:raise ValueError('bounded context capacity exceeded')
    if current:runs.append(current)
    if stream.digest.hexdigest()!=expected:raise ValueError('original SHA256 mismatch')
    timing=follow.timing_check(zda,cross)
    if not timing['accepted'] or timing['gps_minus_utc_s']!=leap:raise ValueError('actual receiver timing did not reproduce')
    mapped,fixes=follow.mapped_context(nav,gga,timing)
    # Reject duplicate/conflicting position epochs, rather than silently choosing one.
    if any(b['utc_week_s']<=a['utc_week_s'] for a,b in zip(fixes,fixes[1:])):
        raise ValueError('duplicate/reversed receiver position epochs')
    matched,association_rejections=motion.associate_vtg(
        [dict(r,packet_utc_week_s=follow.utc_tag(r,leap)) for r in vtg],fixes)
    if p.get('selection_mode')=='receiver_raw_support':
        segments=select_receiver_raw_segments(matched,runs,rejections,policy=p)
    else:
        segments=select_segments(mapped,matched,runs,rejections,policy=p)
    for r in segments:
        r['receiver_fixes']=[dict(time_s=f['utc_week_s'],latitude_rad=math.radians(f['latitude_deg']),
            longitude_rad=math.radians(f['longitude_deg']),height_m=f['orthometric_height_m']+f['geoid_separation_m'])
            for f in fixes if r['start_s']<=f['utc_week_s']<r['end_s']
            or (r['last_section'] and f['utc_week_s']==r['end_s'])]
        r['segment_id']=hashlib.sha256(json.dumps(dict(source_sha256=expected,start=r['start_s'],end=r['end_s'],
            signature=r['signature'],imu_type=r['imu_type'],version=p['version']),sort_keys=True).encode()).hexdigest()[:24]
    empty_state=('no_qualifying_segment' if matched and
                 (mapped or p.get('selection_mode')=='receiver_raw_support')
                 else 'unresolved_context')
    return dict(policy=p,segments=segments,source_sha256=expected,source_bytes=stream.size,
        frame_counts=dict(counts),native_runs=len(runs),receiver_speed_samples=len(matched),
        receiver_association_rejections=association_rejections,rejections=dict(rejections),timing=timing,
        state='segments_available' if segments else empty_state,
        nmea=nmea.finish(),selection_used_gyro_residuals=False,original_preserved=True,scientific_eligible=False)


def extract_segment(path,context,segment):
    """Native raw/converted increments for one independently inventoried section."""
    kind=segment['imu_type']
    if kind not in corpus.SCALES:raise ValueError('unsupported physical conversion hypothesis')
    scale_angle,scale_velocity=corpus.SCALES[kind]
    start=segment['start_s']-segment['raw_guard_s'];end=segment['end_s']+segment['raw_guard_s']
    leap=context['timing']['gps_minus_utc_s'];rows=[];previous=None;signature='';mount=np.eye(3)
    with il.open_source(path) as original:
        stream=follow.HashedReader(original)
        for frame in ap.frames(stream):
            if frame.tag=='$MSG' and frame.group in (1,20):
                signature=frame.packet[10:-4].hex();s=installation.installation_message(frame)
                mount=np.array(s['imu_to_aircraft_rotation']) if s['usable'] else np.eye(3)
            if frame.tag!='$GRP' or frame.group!=4:continue
            row=ap.group4(frame);t=follow.utc_tag(row,leap);dt=None if previous is None else t-previous
            if start<=t<=end and dt is not None and t-dt>=start-1e-9:
                if (signature!=segment['signature'] or row['imu_type']!=kind or row['time_types']!=segment['time_types']
                        or not .0025<=dt<=.0075 or row['data_status'] or row['imu_status'] or row['rate_code']!=2):
                    raise ValueError('selected native completeness/configuration mismatch')
                raw=np.array([row[k] for k in ap.RAW_FIELDS],dtype=np.int64)
                rows.append((frame.offset,t,dt,*raw,*(mount@raw[3:]*scale_angle),*(mount@raw[:3]*scale_velocity)))
            previous=t
    if stream.digest.hexdigest()!=context['inspection']['source_sha256']:raise ValueError('original SHA256 mismatch')
    values=np.array(rows,float)
    if not len(values) or np.any(abs(np.diff(values[:,1])-values[1:,2])>1e-8):raise ValueError('selected native gap')
    initial_time=values[0,1]-values[0,2]
    fixes=segment['receiver_fixes'];times=np.array([r['time_s'] for r in fixes])-initial_time
    gps=np.array([[r['latitude_rad'],r['longitude_rad'],r['height_m']] for r in fixes])
    if len(times)<2 or np.any(np.diff(times)<=0) or np.any(np.diff(times)>2):raise ValueError('receiver completeness failure')
    if times[0]-.15<0 or times[-1]+.15>min(len(values)*.005,float(np.sum(values[:,2]))):
        raise ValueError('receiver epochs lack full latency/clock support')
    return values,times,gps,dict(segment_id=segment['segment_id'],source_sha256=stream.digest.hexdigest(),
        source_bytes=stream.size,first_packet_offset=int(values[0,0]),last_packet_offset=int(values[-1,0]),
        native_packets=len(values),receiver_epochs=len(times),first_interval_start_utc_s=initial_time,
        duration_header_s=float(np.sum(values[:,2])),duration_nominal_s=len(values)*.005,
        angle_scale_rad_per_count=scale_angle,velocity_scale_mps_per_count=scale_velocity,
        physical_conversion_status='empirical conditional hypothesis, not scientific promotion',
        group1_observations_used=False,all_original_integers_preserved=True)
