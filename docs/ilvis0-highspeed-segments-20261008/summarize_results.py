# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public summary of audited saved results; no original scans, predictions or fits."""
import argparse
from collections import Counter, defaultdict
import csv
import datetime
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import median
import subprocess
import sys
import time

MODELS=('sphere_rotating','sphere_still','flat_still')
CASES=('bias1_unsubtracted','bias1_profiled_removal')
LABELS=dict(sphere_rotating='Rotating globe',sphere_still='Still globe',flat_still='Flat disc',
    bias1_unsubtracted='No Earth-rate removal',bias1_profiled_removal='Possible Earth-rate removal')


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def load(path):
    if str(path).endswith('.gz'):
        with gzip.open(path,'rt') as f:return json.load(f)
    return json.loads(Path(path).read_text())


def fit_status(fit):
    if 'error' in fit:return 'failed'
    g=fit.get('exact_projected_gradient_relative')
    return 'converged' if fit.get('converged') and g is not None and math.isfinite(g) and g<=1e-4 else 'unresolved'


def partial_shape(fits):
    """Describe converged globe/disc pairs without promoting an incomplete family fit."""
    rows={f['model']:f for f in fits};out={};leans=[]
    for globe in MODELS[:2]:
        a=rows[globe];b=rows['flat_still'];delta=None
        if fit_status(a)==fit_status(b)=='converged':
            x=a.get('residual_sum_squares');y=b.get('residual_sum_squares')
            if isinstance(x,(float,int)) and isinstance(y,(float,int)) and math.isfinite(x) and math.isfinite(y):
                delta=y-x
                leans.append(LABELS[globe]+' fits better than flat' if delta>0 else
                    'Flat fits better than '+LABELS[globe].lower() if delta<0 else LABELS[globe]+' and flat tie')
        out[globe+'_disc_minus_globe_cost']=delta
    out['available_lean']='; '.join(leans) if leans else 'No converged shape pair'
    out['converged_models']=';'.join(m for m in MODELS if fit_status(rows[m])=='converged')
    out['unresolved_models']=';'.join(m for m in MODELS if fit_status(rows[m])!='converged')
    return out


def track_context(chosen,record):
    """Receiver-route description; spherical distance is descriptive, never a model test."""
    s=chosen['segment'];dates=[datetime.date.fromisoformat(d) for d in record.get('timing',{}).get('dates',[])]
    sundays={d-datetime.timedelta(days=(d.weekday()+1)%7) for d in dates}
    if len(sundays)>1:raise ValueError('ambiguous receiver UTC week')
    sunday=datetime.datetime.combine(next(iter(sundays)),datetime.time(),datetime.timezone.utc) if sundays else None
    def utc(t):return (sunday+datetime.timedelta(seconds=t)).isoformat().replace('+00:00','Z') if sunday else ''
    fixes=s.get('receiver_fixes',[]);distance=0.
    for a,b in zip(fixes,fixes[1:]):
        h=math.sin((b['latitude_rad']-a['latitude_rad'])/2)**2+math.cos(a['latitude_rad'])*math.cos(b['latitude_rad'])*math.sin((b['longitude_rad']-a['longitude_rad'])/2)**2
        distance+=2*6371.*math.asin(math.sqrt(min(1.,max(0.,h))))
    out=dict(filename=chosen.get('filename',''),source_sha256=record.get('source_sha256',''),
        source_bytes=record.get('source_bytes'),record_type='Applanix Group 4',imu_type=s['imu_type'],
        nominal_imu_hz=200,time_types=s.get('time_types'),mounting_epoch=s.get('signature',''),
        start_utc=utc(s.get('start_s',0)),end_utc=utc(s.get('end_s',0)),duration_min=s['duration_s']/60,
        minimum_speed_kmh=s.get('minimum_receiver_ground_speed_kmh'),
        median_speed_kmh=s['median_receiver_ground_speed_kmh'],gps_track_km=distance if len(fixes)>1 else None,
        receiver_epochs=len(fixes))
    points=[dict(segment_id=s.get('segment_id',''),time_utc=utc(f['time_s']),
        latitude_deg=math.degrees(f['latitude_rad']),longitude_deg=math.degrees(f['longitude_rad']),
        height_m=f['height_m']) for f in fixes]
    return dict(out,track_points=points)


def load_evidence(dest):
    receipt=dest/'evidence-receipt.json'
    if not receipt.exists():raise ValueError('completed audited publication required')
    r=load(receipt)
    if r['state']!='complete':raise ValueError('completed audited publication required')
    for name,digest in r['artifacts'].items():
        if Path(name).name!=name or sha(dest/name)!=digest:raise ValueError('published evidence integrity mismatch')
    completion=load(dest/'completion.json');manifest=load(dest/'fit-manifest.json')
    if (completion['state']!='complete' or completion['summary_sha256']!=sha(dest/'summary.json.gz')
            or completion['fit_manifest_sha256']!=sha(dest/'fit-manifest.json')
            or manifest['selection_sha256']!=sha(dest/'selection.json.gz')):
        raise ValueError('published completion mismatch')
    return load(dest/'summary.json.gz'),load(dest/'selection.json.gz'),dict(
        starts=completion['starts'],maximum_starts=manifest['maximum_starts'])


def tabulate(summary,selection):
    chosen={r['segment']['segment_id']:r for r in selection['selected']}
    selected={sid:r['segment'] for sid,r in chosen.items()}
    records={r['task']:r for r in selection.get('records',[])}
    results=summary['results']
    if len(selected)!=len(selection['selected']) or len(results)!=len(selected) or {r['segment_id'] for r in results}!=set(selected):
        raise ValueError('missing or duplicate stretch identity')
    counts=Counter(converged=0,unresolved=0,failed=0);by_case=defaultdict(lambda:defaultdict(Counter))
    groups=defaultdict(list);fits=[];stretches=[];preferences=Counter();rotation=Counter();cases=[];tracks=[]
    for r in results:
        sid=r['segment_id'];s=selected[sid];statuses=[]
        if r['state']=='fitted':
            if len(r['cases'])!=2 or {c['case_id'] for c in r['cases']}!=set(CASES):raise ValueError('incomplete processing grid')
            for case in r['cases']:
                if len(case['fits'])!=3 or {f['model'] for f in case['fits']}!=set(MODELS):raise ValueError('incomplete model grid')
                cases.append(dict(segment_id=sid,filename=r['filename'],case_id=case['case_id'],
                    stretch_shape_preference=r['profile']['conditional_shape_preference'],**partial_shape(case['fits'])))
                for f in case['fits']:
                    status=fit_status(f);statuses.append(status);counts[status]+=1
                    by_case[case['case_id']][f['model']][status]+=1
                    fits.append(dict(segment_id=sid,filename=r['filename'],case_id=case['case_id'],
                        model=f['model'],status=status,evaluations=f.get('evaluations'),
                        conditional_cost=f.get('residual_sum_squares'),
                        stationarity=f.get('exact_projected_gradient_relative'),
                        rms_neu_m=json.dumps(f.get('residual_rms_neu_m')),
                        active_bounds=';'.join(f.get('active_bounds',[])),error=f.get('error',''),
                        solver_message=f.get('message','')))
            group='fully converged' if all(x=='converged' for x in statuses) else 'unresolved'
            p=r['profile'];preference=p['conditional_shape_preference'];preferences[preference]+=1
            if group!='fully converged' and (preference in ('globe','flat') or p['rotation_diagnostics'] is not None):
                raise ValueError('unresolved stretch exposed a decision')
            for d in p['rotation_diagnostics'] or []:
                value=d['conditional_still_minus_rotating_cost']
                rotation['rotating' if value>0 else 'still' if value<0 else 'tied']+=1
        else:group='unsupported';preference='unsupported';preferences[preference]+=1
        groups[group].append(s)
        context=track_context(chosen[sid],records.get(chosen[sid].get('task'),{}));tracks.extend(context.pop('track_points'))
        provenance=r.get('provenance',{})
        stretches.append(dict(segment_id=sid,**context,group=group,conditional_shape_preference=preference,
            native_packets=provenance.get('native_packets'),
            physical_conversion_status=provenance.get('physical_conversion_status',''),
            angle_scale_rad_per_count=provenance.get('angle_scale_rad_per_count'),
            velocity_scale_mps_per_count=provenance.get('velocity_scale_mps_per_count')))
    stats={name:dict(stretches=len(rows),minutes=sum(s['duration_s'] for s in rows)/60,
        median_duration_min=median(s['duration_s']/60 for s in rows),
        median_speed_kmh=median(s['median_receiver_ground_speed_kmh'] for s in rows),
        imu_types=dict(Counter(s['imu_type'] for s in rows))) for name,rows in groups.items()}
    return dict(fit_counts=dict(counts),by_case_model=by_case,group_stats=stats,fit_rows=fits,
        stretch_rows=stretches,case_rows=cases,track_rows=tracks,
        shape_preferences=dict(preferences),rotation_case_counts=dict(rotation))


def render(out,budget):
    c=out['fit_counts'];n=len(out['stretch_rows'])
    p=out['shape_preferences'];unknown=p.get('unresolved',0)+p.get('ambiguous',0)
    lines=['# Final selected-stretch analysis summary','',
        f"Of {n} selected stretches, the completed conditional shape comparisons favored globe "
        f"in {p.get('globe',0)} and flat in {p.get('flat',0)}. "
        f"{unknown} remained unknown; {p.get('unsupported',0)} were unsupported.",'',
        'The shape question comes first. These are conditional comparisons under assumed calibration '
        'and processing, not calibrated scientific detections. Overlapping instrument streams '
        'are not independent flights.','',
        '## Shape and rotation','',
        '| Conditional shape outcome | Stretches |','|---|---:|']
    for key,label in [('globe','Globe'),('flat','Flat'),('unresolved','Unknown: unresolved fits'),
            ('ambiguous','Unknown: conflicting or tied comparisons'),('unsupported','Unsupported')]:
        lines.append(f"| {label} | {out['shape_preferences'].get(key,0)} |")
    lines+=['','Rotation is exposed only for resolved globe stretches. Across their processing cases, '
        f"{out['rotation_case_counts'].get('rotating',0)} favored rotating globe, "
        f"{out['rotation_case_counts'].get('still',0)} favored still globe and "
        f"{out['rotation_case_counts'].get('tied',0)} tied. These are matched case comparisons, not independent votes.",'',
        '## Which calculations finished?','',
        'The following counts measure solver completion, not model support. A flat-disc '
        'calculation can finish while describing the flight much worse than a globe. '
        'The quality of matched fits determines the comparison; counting finished calculations '
        'does not.','',
        f"{c['converged']} calculations passed the stopping checks, {c['unresolved']} remained "
        f"numerically unresolved and {c['failed']} returned an explicit error. "
        f"{budget['starts']} starts were charged against the {budget['maximum_starts']}-start limit.",'',
        '| Processing assumption | Model | Passed stopping checks | Unresolved | Error |',
        '|---|---|---:|---:|---:|']
    for case in CASES:
        for model in MODELS:
            r=out['by_case_model'][case][model]
            lines.append(f"| {LABELS[case]} | {LABELS[model]} | {r['converged']} | {r['unresolved']} | {r['failed']} |")
    lines+=['','Convergence requires the numerical stopping and stationarity checks. A low residual '
        'alone is insufficient; an unresolved optimization cannot rule out its model.','',
        '## Fully converged versus unresolved stretches','',
        'A fully converged stretch has all six required fits. Any unresolved or failed fit leaves '
        'its stretch in the unresolved group. Geometry was selected before any model comparison.','',
        '| Group | Stretches | Total minutes | Median duration (min) | Median ground speed (km/h) | IMU types (stretch counts) |',
        '|---|---:|---:|---:|---:|---|']
    for name in ('fully converged','unresolved','unsupported'):
        r=out['group_stats'].get(name)
        if r:
            types=', '.join(f'{k}: {v}' for k,v in sorted(r['imu_types'].items()))
            lines.append(f"| {name} | {r['stretches']} | {r['minutes']:.1f} | {r['median_duration_min']:.1f} | {r['median_speed_kmh']:.1f} | {types} |")
        else:lines.append(f'| {name} | 0 | 0 | — | — | — |')
    lines+=['','These are descriptive comparisons, not evidence that speed, duration or instrument '
        'type caused convergence. All selected stretches remain in the report.','',
        '## Source recordings and tracks','',
        'Every stretch uses Applanix Group-4 IMU increments at nominal 200 Hz. IMU type is the '
        'logged type code, not a confirmed manufacturer/model. Exact original filenames, SHA-256 '
        'fingerprints, UTC bounds, mounting epochs and conversion details are in '
        '[the stretch ledger](stretch-summary.csv). [Receiver track points](tracks.csv) retain '
        'the dated positions without interpolation.','',
        '| Stretch | UTC start | IMU type | Minutes | Ground speed min/median (km/h) | GPS track (km) | Shape |',
        '|---|---|---:|---:|---:|---:|---|']
    for r in out['stretch_rows']:
        speed=f"{r['minimum_speed_kmh']:.1f}/{r['median_speed_kmh']:.1f}" if r['minimum_speed_kmh'] is not None else '—'
        distance=f"{r['gps_track_km']:.1f}" if r['gps_track_km'] is not None else '—'
        lines.append(f"| {r['segment_id']} | {r['start_utc']} | {r['imu_type']} | {r['duration_min']:.1f} | {speed} | {distance} | {r['conditional_shape_preference']} |")
    lines+=['','Track distance sums receiver-position steps using a 6,371 km spherical coordinate '
        'convention. It is a route description, not evidence for a globe. Ground speed is receiver '
        'speed; it is not true airspeed.','',
        '## Partial comparisons in indeterminate stretches','',
        'These rows show only matched globe/disc pairs whose two fits converged. An unfinished '
        'fit is never treated as a losing model. A pairwise lean does not resolve the whole stretch '
        'or unlock a rotation decision. Numerical costs have no calibrated significance here.','',
        '| Stretch | Processing assumption | Converged models | Available shape lean |',
        '|---|---|---|---|']
    partial=[r for r in out['case_rows'] if r['stretch_shape_preference'] in ('unresolved','ambiguous')]
    for r in partial:
        names=', '.join(LABELS[m] for m in r['converged_models'].split(';') if m) or 'None'
        lines.append(f"| {r['segment_id']} | {LABELS[r['case_id']]} | {names} | {r['available_lean']} |")
    if not partial:lines.append('| — | — | — | No indeterminate fitted stretches |')
    lines+=['','[Case-by-case details](case-summary.csv) preserve the available cost differences '
        'and unresolved models; [fit details](fit-summary.csv) also preserve unfinished costs '
        'as diagnostics. They are not used to rank models whose fits have not converged.','',
        '## Residuals and limits','',
        '| Fit group | Fits touching a parameter limit | Fits using 200 evaluations | Median RMS N/E/up (m) |',
        '|---|---:|---:|---|']
    for status in ('converged','unresolved','failed'):
        rows=[r for r in out['fit_rows'] if r['status']==status]
        residuals=[json.loads(r['rms_neu_m']) for r in rows if json.loads(r['rms_neu_m']) is not None]
        rms='/'.join(f'{median(x[i] for x in residuals):.2f}' for i in range(3)) if residuals else '—'
        lines.append(f"| {status} | {sum(bool(r['active_bounds']) for r in rows)} | "
            f"{sum(r['evaluations']==200 for r in rows)} | {rms} |")
    lines+=['','Residuals from unresolved fits describe unfinished solutions; they do not support '
        'model rejection. A converged fit at a parameter limit can still be sensitive to the '
        'assumed bounds. Smaller sections are fixed-parameter consistency checks, not extra trials.','',
        'Calibration offsets, onboard corrections, the integration clock and receiver uncertainty '
        'remain partly assumed. Numerical convergence does not establish model adequacy, a global '
        'optimum or a validated error rate. All scientific decisions still abstain.','',
        '[Every stretch](stretch-summary.csv) and [every fit](fit-summary.csv) retain unresolved '
        'outcomes, solver messages and diagnostics. See [selection criteria](ELIGIBILITY.md), '
        '[methods](README.md) and [pilot findings](../ilvis0-refinement-20261008/PROVISIONAL.md).','']
    return '\n'.join(lines)


def atomic_text(path,text):
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as f:f.write(text);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def package(dest):
    summary,selection,budget=load_evidence(dest);out=tabulate(summary,selection)
    for filename,key in [('fit-summary.csv','fit_rows'),('stretch-summary.csv','stretch_rows'),
                         ('case-summary.csv','case_rows'),('tracks.csv','track_rows')]:
        rows=out[key];tmp=dest/(filename+'.tmp')
        with tmp.open('w',newline='') as f:
            if rows:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,dest/filename)
    atomic_text(dest/'FINAL_SUMMARY.md',render(out,budget))
    names=['FINAL_SUMMARY.md','fit-summary.csv','stretch-summary.csv','case-summary.csv','tracks.csv',
        'summarize_results.py','evidence-receipt.json']
    atomic_text(dest/'public-summary-receipt.json',json.dumps(dict(state='complete',
        artifacts={n:sha(dest/n) for n in names}),sort_keys=True,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch',action='store_true');parser.add_argument('--detach',action='store_true')
    args=parser.parse_args();dest=Path(__file__).resolve().parent;root=dest.parents[1]
    source=root/'data/ilvis0-highspeed-segments-v2-20261008'
    if args.detach:
        with (root/'data/ilvis0-public-summary-20261009.log').open('ab',buffering=0) as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--watch'],cwd=root,
                stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
        print(json.dumps(dict(pid=child.pid)))
    else:
        with (source/'public-summary.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);deadline=time.monotonic()+7*24*3600
            while args.watch and not (dest/'evidence-receipt.json').exists():
                if time.monotonic()>deadline:raise RuntimeError('summary wait expired; analysis untouched')
                time.sleep(30)
            package(dest)
            print('Final public summary published from audited results.',flush=True)
