# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded motion-only diagnosis of the 61 preserved ILVIS0 recordings.

No gyro residuals, scientific selection change, original deletion, or Earth fit.
Longer-interval rates are sensitivity diagnostics, never replacements for the gate.
"""
import argparse
from collections import Counter
import datetime
import fcntl
import json
import math
import os
from pathlib import Path
import platform

import numpy as np

from . import applanix as ap,ilvis0 as il,ilvis0_followup as follow

VERSION='ilvis0-motion-diagnosis-v1'
SPANS=(2,6,12)
VTG_REFERENCE='https://receiverhelp.trimble.com/oem-gnss/nmea0183-messages-vtg.html'


def parse_vtg(fields):
    """Receiver ground track, not aircraft heading; reject invalid/estimated/simulated modes."""
    if len(fields)<9 or fields[2]!='T' or fields[6]!='N' or fields[8]!='K':
        raise ValueError('unsupported VTG fields or units')
    mode=fields[9] if len(fields)>9 else ''
    if mode not in ('','A','D','P','R','F'):
        raise ValueError('VTG is invalid, estimated, manual or simulated')
    course,speed=float(fields[1]),float(fields[7])/3.6
    if not math.isfinite(course) or not math.isfinite(speed) or not 0<=course<360 or speed<0:
        raise ValueError('invalid VTG values')
    return dict(course_deg=course,speed_mps=speed,mode=mode,
                source_kind='receiver_ground_track_not_aircraft_heading')


def local_slope(times,values,span_s,maximum_gap_s=2):
    """Linear regression on original points, using bounded prefix sums; no gap bridging."""
    t=np.asarray(times,float); y=np.asarray(values,float)
    result=np.full(len(t),np.nan)
    if len(t)<3 or np.any(np.diff(t)<=0) or not np.all(np.isfinite(t)) or not np.all(np.isfinite(y)):
        return result
    t=t-t[0]
    half=span_s/2
    # Binary time tags and nominal epochs differ by tiny floating/clock errors.
    # Permit 5% of one sample (capped at 1 ms), never a missing epoch or a real gap.
    tolerance=min(.001,float(np.median(np.diff(t)))*.05)
    left=np.searchsorted(t,t-half-tolerance,side='left'); right=np.searchsorted(t,t+half+tolerance,side='right')
    n=right-left
    def sums(a):
        prefix=np.concatenate(([0.],np.cumsum(a)))
        return prefix[right]-prefix[left]
    st,sy,stt,sty=(sums(a) for a in (t,y,t*t,t*y))
    gaps=np.concatenate(([0],np.cumsum(np.diff(t)>maximum_gap_s)))
    last=np.maximum(left,right-1)
    supported=(n>=3)&(t[left]<=t-half+tolerance)&(t[last]>=t+half-tolerance)&((gaps[last]-gaps[left])==0)
    denominator=n*stt-st*st
    supported &= denominator>1e-10
    result[supported]=(n[supported]*sty[supported]-st[supported]*sy[supported])/denominator[supported]
    return result


def window_ids(times,windows):
    ids=np.full(len(times),-1,int)
    for i,w in enumerate(windows):
        ids[(times>=w['start_s'])&(times<=w['end_s'])]=i
    return ids


def longest_span(times,good,ids,maximum_gap_s=2):
    start,last,window,longest=None,None,None,0.
    for t,ok,i in zip(times,good,ids):
        if not ok or i<0:
            start,last,window=None,None,None
            continue
        if last is None or i!=window or t-last>maximum_gap_s:
            start=t
        longest=max(longest,float(t-start));last,window=t,i
    return longest


def excursion_summary(times,bad,ids):
    """Approximate event durations include one native sample; no claim of exact crossings."""
    events=[];start,last,window=None,None,None
    step=float(np.median(np.diff(times))) if len(times)>1 else 0.
    for t,flag,i in zip(times,bad,ids):
        if start is not None and (not flag or i<0 or i!=window or t-last>2):
            events.append(float(last-start+step));start=None
        if flag and i>=0:
            if start is None:start=t
            last,window=t,i
    if start is not None:events.append(float(last-start+step))
    return dict(events=len(events),approximate_total_s=sum(events),
                events_under_1s=sum(x<1 for x in events),
                longest_s=max(events,default=0),median_s=float(np.median(events)) if events else None,
                p95_s=float(np.quantile(events,.95)) if events else None,
                timing_resolution_s=step)


def associate_vtg(rows,fixes):
    """VTG lacks UTC: uniquely nearest dated GGA within 0.5s, preserving association error."""
    times=np.array([r['utc_week_s'] for r in fixes]); matched=[];reasons=Counter()
    for row in rows:
        i=np.searchsorted(times,row['packet_utc_week_s'])
        choices=sorted((abs(times[j]-row['packet_utc_week_s']),j) for j in (i-1,i) if 0<=j<len(times))
        if not choices or choices[0][0]>.5 or (len(choices)>1 and abs(choices[0][0]-choices[1][0])<1e-6):
            reasons['no_unique_GGA_within_half_second']+=1;continue
        error,j=choices[0]
        matched.append(dict(row,utc_week_s=float(times[j]),association_error_s=float(error)))
    counts=Counter(r['utc_week_s'] for r in matched)
    reasons['duplicate_assigned_epochs']=sum(n for n in counts.values() if n>1)
    matched=[r for r in matched if counts[r['utc_week_s']]==1]
    if any(b['utc_week_s']<=a['utc_week_s'] for a,b in zip(matched,matched[1:])):
        raise ValueError('VTG timestamp association reversal; no sorting or repair')
    return matched,dict(reasons)


def read_motion(path,expected_hash):
    nav,gga,zda,vtg,cross=[],[],[],[],[]
    nmea=ap.NMEA();rejections=Counter()
    with il.open_source(path) as original:
        stream=follow.HashedReader(original)
        for frame in ap.frames(stream):
            if frame.tag!='$GRP':continue
            if frame.group==1:nav.append(ap.group1(frame))
            elif frame.group==10001:
                header=ap.time_header(frame)
                for sentence in nmea.feed(ap.group10001(frame)[1]):
                    if not sentence['valid']:continue
                    f=sentence['fields']
                    if f[0].endswith('ZDA'):
                        date=datetime.date(int(f[4]),int(f[3]),int(f[2]))
                        zda.append(dict(header,date=date.isoformat(),sod=follow.utc_sod(f[1])))
                    elif f[0].endswith('GGA') and int(f[6])>0:
                        if f[10]!='M' or (f[11] and f[12]!='M'):raise ValueError('unexpected GGA units')
                        gga.append(dict(header,sod=follow.utc_sod(f[1]),latitude_deg=ap.coordinate(f[2],f[3]),
                                        longitude_deg=ap.coordinate(f[4],f[5]),
                                        orthometric_height_m=float(f[9]) if f[9] else None,
                                        geoid_separation_m=float(f[11]) if f[11] else None))
                    elif f[0].endswith('VTG'):
                        try:row=parse_vtg(f)
                        except ValueError as error:rejections[str(error)]+=1;continue
                        vtg.append(dict(header,**row,receiver_stream_offset=sentence['stream_offset']))
            if frame.group in (1,4):
                header=ap.time_header(frame)
                if header['time_types']==33:cross.append(header['time1_s']-header['time2_s'])
            if max(map(len,(nav,gga,zda,vtg,cross)))>250000:raise ValueError('bounded context capacity exceeded')
    if stream.digest.hexdigest()!=expected_hash:raise ValueError('original SHA-256 mismatch')
    timing=follow.timing_check(zda,cross)
    if not timing['accepted']:raise ValueError('receiver/header timing checks failed')
    mapped,fixes=follow.mapped_context(nav,gga,timing)
    if any(b['utc_week_s']<=a['utc_week_s'] for a,b in zip(mapped,mapped[1:])):
        raise ValueError('navigation timestamp reversal')
    rows=[dict(r,packet_utc_week_s=follow.utc_tag(r,timing['gps_minus_utc_s'])) for r in vtg]
    matched,association_rejections=associate_vtg(rows,fixes)
    return mapped,matched,dict(source_sha256=expected_hash,source_bytes=stream.size,timing=timing,
        vtg_sentences=len(vtg),vtg_associated=len(matched),vtg_rejections=dict(rejections),
        vtg_association_rejections=association_rejections,nmea=nmea.finish(),
        vtg_reference=VTG_REFERENCE,
        vtg_timing='VTG has no time field; unique nearest GGA within 0.5s; association uncertainty retained, not fine-rate truth',
        vtg_mode_counts=dict(Counter(r['mode'] for r in matched)))


def diagnose(nav,vtg,windows):
    p=il.SCREEN_POLICY
    t=np.array([r['utc_week_s'] for r in nav]); ids=window_ids(t,windows)
    if len(t)<3:raise ValueError('insufficient navigation')
    course=np.rad2deg(np.unwrap(np.arctan2([r['velocity_east_mps'] for r in nav],
                                         [r['velocity_north_mps'] for r in nav])))
    native_rate=np.full(len(t),np.nan)
    dt1,dt2=np.diff(t)[:-1],np.diff(t)[1:]
    valid=np.zeros(len(t),bool);valid[1:-1]=(dt1>0)&(dt2>0)&(dt1<=2)&(dt2<=2)
    native_rate[1:-1]=(course[2:]-course[:-2])/(t[2:]-t[:-2])
    masks=dict(speed=np.array([r['speed_mps'] for r in nav])>=p['minimum_speed_mps'],
               roll=np.abs([r['roll_deg'] for r in nav])<=p['maximum_roll_deg'],
               climb=np.abs([r['velocity_down_mps'] for r in nav])<=p['maximum_vertical_speed_mps'],
               course=np.abs(native_rate)<=p['maximum_course_rate_deg_s'])
    eligible=valid&(ids>=0)
    base=masks['speed']&masks['roll']&masks['climb']&valid
    native=longest_span(t,base&masks['course'],ids)
    ignore={key:longest_span(t,np.logical_and.reduce([v for k,v in masks.items() if k!=key])&valid,ids)
            for key in masks}
    events={key:dict(samples_over_limit=int(np.sum(eligible&~mask)),
                     eligible_samples=int(eligible.sum()),
                     **excursion_summary(t,eligible&~mask,ids)) for key,mask in masks.items()}
    rates={str(span):local_slope(t,course,span) for span in SPANS}
    sensitivity={key:dict(longest_motion_compatible_s=longest_span(t,base&(np.abs(rate)<=p['maximum_course_rate_deg_s']),ids),
                          course_exceedance_samples=int(np.sum(eligible&np.isfinite(rate)&(np.abs(rate)>p['maximum_course_rate_deg_s']))))
                 for key,rate in rates.items()}
    gps_t=np.array([r['utc_week_s'] for r in vtg]);gps_ids=window_ids(gps_t,windows)
    gps_course=np.rad2deg(np.unwrap(np.deg2rad([r['course_deg'] for r in vtg])))
    gps_rates={str(span):local_slope(gps_t,gps_course,span) for span in SPANS}
    receiver={key:dict(longest_course_compatible_s=longest_span(gps_t,np.abs(rate)<=p['maximum_course_rate_deg_s'],gps_ids),
                       valid_samples_in_GPS_windows=int(np.sum((gps_ids>=0)&np.isfinite(rate)))) for key,rate in gps_rates.items()}
    recovered=any(r['longest_motion_compatible_s']>=60 for r in sensitivity.values())
    corroborated=any(r['longest_course_compatible_s']>=60 for r in receiver.values())
    if recovered:classification='course_rate_resolution_sensitive'
    elif ignore['course']<60:classification='additional_roll_or_climb_fragmentation'
    elif corroborated:classification='navigation_receiver_disagreement'
    else:classification='course_failure_persists_or_receiver_support_insufficient'
    # Preserve common-epoch comparison summaries; no interpolation or fitted lag.
    difference=[]
    for row in vtg:
        if not any(w['start_s']<=row['utc_week_s']<=w['end_s'] for w in windows):continue
        i=np.searchsorted(t,row['utc_week_s'])
        choices=[j for j in (i-1,i) if 0<=j<len(t)]
        if not choices:continue
        j=min(choices,key=lambda j:abs(t[j]-row['utc_week_s']))
        if abs(t[j]-row['utc_week_s'])>.1:continue
        difference.append(abs((course[j]-row['course_deg']+180)%360-180))
    return dict(classification=classification,native_longest_motion_s=native,
                ignore_one_criterion_longest_s=ignore,threshold_excursions=events,
                navigation_course_regression_seconds=sensitivity,receiver_course_regression_seconds=receiver,
                receiver_supports_60s_at_tested_resolution=corroborated,
                native_sample_interval_s=float(np.median(np.diff(t))),
                common_epoch_course_difference_deg=dict(samples=len(difference),median=float(np.median(difference)) if difference else None,
                                                       p95=float(np.quantile(difference,.95)) if difference else None),
                existing_limits=p,storage_decision='keep',scientific_eligible=False,
                interpretation='Resolution sensitivity can reflect real small corrections, estimator noise or both. Averaging does not prove artifact or create an accepted science window.')


def run(corpus,retention,output):
    corpus,retention,output=map(Path,(corpus,retention,output))
    old=json.loads((retention/'summary.json').read_text())
    targets=[r for r in old['results'] if r['storage_decision']=='keep' and r['fused_context']['longest_motion_compatible_span_s']<60]
    records={r['task_id']:r for r in map(json.loads,(corpus/'records.jsonl').read_text().splitlines())}
    sources=[Path(__file__),Path(ap.__file__),Path(il.__file__),Path(follow.__file__),
             Path(__file__).parents[1]/'tests'/'ilvis0_motion_worker.py']
    inputs=[corpus/'records.jsonl',retention/'summary.json',retention/'cleanup.jsonl']
    manifest=dict(version=VERSION,sources={str(p):il.sha256(p) for p in sources},inputs={str(p):il.sha256(p) for p in inputs},
                  tasks=[r['task_id'] for r in targets],python=platform.python_version(),numpy=np.__version__,
                  diagnostic_regression_spans_s=list(SPANS),unchanged_gate=il.SCREEN_POLICY,
                  threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
    if output.exists() and not (output/'manifest.json').is_file():raise ValueError('unmarked motion audit directory')
    output.mkdir(parents=True,exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'manifest.json').exists():
            if json.loads((output/'manifest.json').read_text())!=manifest:raise ValueError('motion source/environment/input mismatch')
        else:follow.atomic_json(output/'manifest.json',manifest)
        def frozen():
            for p in sources+inputs:
                if il.sha256(p)!=manifest['sources'].get(str(p),manifest['inputs'].get(str(p))):raise ValueError('frozen motion source/input changed')
        results=[]
        for i,target in enumerate(targets):
            frozen();task=target['task_id'];destination=output/(task+'.json')
            follow.atomic_json(output/'status.json',dict(state='running',pid=os.getpid(),completed=i,total=len(targets),task_id=task))
            if destination.exists():result=json.loads(destination.read_text())
            else:
                try:
                    nav,vtg,provenance=read_motion(follow.source_path(corpus,records[task]),target['source_sha256'])
                    result=dict(diagnose(nav,vtg,target['windows']),provenance=provenance)
                    result['native_span_difference_from_prior_s']=result['native_longest_motion_s']-target['fused_context']['longest_motion_compatible_span_s']
                except ValueError as error:result=dict(classification='audit_error_preserve',error=str(error),storage_decision='keep',scientific_eligible=False)
                result.update(task_id=task,filename=target['filename']);follow.atomic_json(destination,result)
            results.append(result)
        summary=dict(version=VERSION,state='complete',files=len(results),classifications=dict(Counter(r['classification'] for r in results)),
                     errors=sum('error' in r for r in results),originals_deleted=0,scientific_eligibility_changes=0,earth_model_fit_attempts=0,
                     results=results)
        frozen();follow.atomic_json(output/'summary.json',summary)
        compact={k:v for k,v in summary.items() if k!='results'}
        follow.atomic_json(output/'status.json',dict(compact,pid=os.getpid()));print(json.dumps(compact),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',type=Path,default=Path('data/ilvis0-ready'))
    parser.add_argument('--retention',type=Path,default=Path('data/ilvis0-retention-84-20261007'))
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-motion-61-20261007'))
    args=parser.parse_args();run(args.corpus,args.retention,args.output)


if __name__=='__main__':main()
