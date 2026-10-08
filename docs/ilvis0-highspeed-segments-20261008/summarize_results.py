# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public summary of audited saved results; no original scans, predictions or fits."""
import argparse
from collections import Counter, defaultdict
import csv
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
    selected={r['segment']['segment_id']:r['segment'] for r in selection['selected']}
    results=summary['results']
    if len(selected)!=len(selection['selected']) or len(results)!=len(selected) or {r['segment_id'] for r in results}!=set(selected):
        raise ValueError('missing or duplicate stretch identity')
    counts=Counter(converged=0,unresolved=0,failed=0);by_case=defaultdict(lambda:defaultdict(Counter))
    groups=defaultdict(list);fits=[];stretches=[];preferences=Counter();rotation=Counter()
    for r in results:
        sid=r['segment_id'];s=selected[sid];statuses=[]
        if r['state']=='fitted':
            if len(r['cases'])!=2 or {c['case_id'] for c in r['cases']}!=set(CASES):raise ValueError('incomplete processing grid')
            for case in r['cases']:
                if len(case['fits'])!=3 or {f['model'] for f in case['fits']}!=set(MODELS):raise ValueError('incomplete model grid')
                for f in case['fits']:
                    status=fit_status(f);statuses.append(status);counts[status]+=1
                    by_case[case['case_id']][f['model']][status]+=1
                    fits.append(dict(segment_id=sid,filename=r['filename'],case_id=case['case_id'],
                        model=f['model'],status=status,evaluations=f.get('evaluations'),
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
        stretches.append(dict(segment_id=sid,filename=r.get('filename',''),group=group,
            duration_min=s['duration_s']/60,median_speed_kmh=s['median_receiver_ground_speed_kmh'],
            imu_type=s['imu_type'],conditional_shape_preference=preference))
    stats={name:dict(stretches=len(rows),minutes=sum(s['duration_s'] for s in rows)/60,
        median_duration_min=median(s['duration_s']/60 for s in rows),
        median_speed_kmh=median(s['median_receiver_ground_speed_kmh'] for s in rows),
        imu_types=dict(Counter(s['imu_type'] for s in rows))) for name,rows in groups.items()}
    return dict(fit_counts=dict(counts),by_case_model=by_case,group_stats=stats,fit_rows=fits,
        stretch_rows=stretches,shape_preferences=dict(preferences),rotation_case_counts=dict(rotation))


def render(out,budget):
    c=out['fit_counts'];n=len(out['stretch_rows'])
    lines=['# Final selected-stretch analysis summary','',
        f"{n} selected stretches: {c['converged']} model fits converged, {c['unresolved']} remained "
        f"numerically unresolved, and {c['failed']} returned an explicit error. "
        f"{budget['starts']} starts were charged against the {budget['maximum_starts']}-start limit.",'',
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
        '## Which fits converged?','',
        '| Processing assumption | Model | Converged | Unresolved | Error |',
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
    for filename,key in [('fit-summary.csv','fit_rows'),('stretch-summary.csv','stretch_rows')]:
        rows=out[key];tmp=dest/(filename+'.tmp')
        with tmp.open('w',newline='') as f:
            if rows:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,dest/filename)
    atomic_text(dest/'FINAL_SUMMARY.md',render(out,budget))
    names=['FINAL_SUMMARY.md','fit-summary.csv','stretch-summary.csv','summarize_results.py','evidence-receipt.json']
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
