# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resolve storage decisions for GPS-promising, alignment-blocked ILVIS0 logs.

Storage usefulness is separate from scientific acceptance. Never reject an original
merely for an unknown scale, an alignment label, or a failed gyro-reference fit.
Only redundant, hash-identical owned originals are automatically removed here.
"""
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
import fcntl
import json
import math
import os
from pathlib import Path
import platform

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import ilvis0_assessment as assessment

VERSION = 'ilvis0-storage-retention-v1'
OWNERSHIP = 'local-level-lab-ilvis0-v1'


def select_targets(previous, assessed):
    by_task = {r['task_id']:r for r in previous['results']}
    return [by_task[r['task_id']] for r in assessed['diagnostics']
            if r['prior_state']=='unresolved' and r.get('gps',{}).get('potential_windows')]


def duplicate_plan(contexts, target_ids):
    """Prefer the catalog entry consistent with the embedded date; never equate instruments."""
    hashes = defaultdict(list)
    for row in contexts:
        if row['screen']['state'] != 'no_level_window':
            hashes[row['inspection']['source_sha256']].append(row)
    plan = {}
    for members in hashes.values():
        # A target can be discarded only when its canonical copy is also in this audit.
        members = [r for r in members if r['task_id'] in target_ids]
        if len(members) < 2:
            continue
        ordered = sorted(members, key=lambda r:(r['date'] not in r['timing']['dates'], r['task_id']))
        canonical = ordered[0]
        for row in ordered[1:]:
            plan[row['task_id']] = canonical['task_id']
    return plan


def intersect_runs(runs, windows):
    result = []
    for window in windows:
        parts = [max(0., min(b, window['end_s'])-max(a, window['start_s'])) for a,b in runs]
        result.append(dict(window, longest_clean_imu_s=max(parts, default=0.),
                           clean_imu_seconds=sum(parts),
                           coverage_fraction=min(1.,sum(parts)/window['duration_s'])))
    return result


def navigation_context(nav, uncertainty, windows):
    """Descriptive fused motion/RMS diagnostics, with no claim of independent accuracy."""
    p = il.SCREEN_POLICY
    selected, good_times = [], []
    uncertainty_times = [r['utc_week_s'] for r in uncertainty]
    for before, row, after in zip(nav, nav[1:], nav[2:]):
        time = row['utc_week_s']
        window = next((i for i,w in enumerate(windows) if w['start_s'] <= time <= w['end_s']), None)
        if window is None:
            continue
        dt1, dt2 = time-before['utc_week_s'], after['utc_week_s']-time
        if min(dt1,dt2) <= 0 or max(dt1,dt2) > p['maximum_context_gap_s']:
            continue
        course = lambda r:math.degrees(math.atan2(r['velocity_east_mps'],r['velocity_north_mps']))
        rate = abs((course(after)-course(before)+180)%360-180)/(dt1+dt2)
        i = bisect_left(uncertainty_times,time)
        near = [uncertainty[j] for j in (i-1,i) if 0 <= j < len(uncertainty)]
        near = min(near,key=lambda r:abs(r['utc_week_s']-time)) if near else None
        metric = (near if near and near['usable'] and abs(near['utc_week_s']-time) <= 2 else None)
        observed = dict(time=time, alignment=row['alignment_status'], roll=row['roll_deg'], course_rate=rate,
                        vertical_speed=row['velocity_down_mps'], window=window)
        if metric:
            observed.update(roll_rms=metric['attitude_roll_rms_deg'], pitch_rms=metric['attitude_pitch_rms_deg'],
                            heading_rms=metric['attitude_heading_rms_deg'], layout=metric['layout_status'])
        selected.append(observed)
        good = (row['speed_mps'] >= p['minimum_speed_mps'] and abs(row['roll_deg']) <= p['maximum_roll_deg']
                and abs(row['velocity_down_mps']) <= p['maximum_vertical_speed_mps']
                and rate <= p['maximum_course_rate_deg_s'])
        good_times.append((window,time,good))
    longest, start, last, old_window = 0., None, None, None
    for window,time,good in good_times:
        if not good:
            start,last,old_window = None,None,None
            continue
        if old_window != window or last is None or time-last > p['maximum_context_gap_s']:
            start = time
        longest = max(longest,time-start)
        last,old_window = time,window
    statistics = {}
    for key in ('roll','course_rate','vertical_speed','roll_rms','pitch_rms','heading_rms'):
        values = [abs(r[key]) for r in selected if key in r]
        if values:
            statistics[key] = dict(median=float(np.median(values)), p95=float(np.quantile(values,.95)), max=max(values))
    return dict(samples=len(selected), alignment_counts=dict(Counter(r['alignment'] for r in selected)),
                samples_with_RMS=sum('roll_rms' in r for r in selected), statistics=statistics,
                longest_motion_compatible_span_s=longest,
                rms_layouts=dict(Counter(r['layout'] for r in selected if 'layout' in r)),
                interpretation='Group-1 motion and Group-2 internal RMS are descriptive fused context; no independent orientation proof',
                earth_model_eligible=False)


def audit_source(path, context, gps_windows):
    nav, uncertainty, runs, current, previous = [], [], [], None, None
    flags, types, rates = Counter(), Counter(), Counter()
    count = 0
    dt_values = []
    leap = context['timing']['gps_minus_utc_s']
    with il.open_source(path) as original:
        stream = follow.HashedReader(original)
        for frame in ap.frames(stream):
            if frame.tag != '$GRP':
                continue
            if frame.group == 1:
                row = ap.group1(frame)
                nav.append(dict(row,utc_week_s=follow.utc_tag(row,leap)))
            elif frame.group == 2:
                row = assessment.navigation_uncertainty(frame)
                uncertainty.append(dict(row,utc_week_s=follow.utc_tag(row,leap)))
            elif frame.group == 4:
                row = ap.group4(frame); time = follow.utc_tag(row,leap)
                # Only timing/status flags are used; the legacy converted columns are discarded.
                tagged = ap.increments(row, previous, supported=True)
                types[row['imu_type']] += 1; rates[row['rate_code']] += 1; count += 1
                if tagged['dt_s'] is not None:
                    dt_values.append(tagged['dt_s'])
                if tagged['flags']:
                    flags.update(tagged['flags'].split(';'))
                    if current is not None:
                        runs.append(current); current = None
                else:
                    current = ([follow.utc_tag(previous,leap), time] if current is None else [current[0],time])
                previous = row
            if max(len(nav),len(uncertainty),len(dt_values)) > 500000:
                raise ValueError('bounded context capacity exceeded')
    if current is not None:
        runs.append(current)
    actual_hash = stream.digest.hexdigest()
    if actual_hash != context['inspection']['source_sha256']:
        raise ValueError('original uncompressed SHA-256 mismatch')
    if any(b['utc_week_s'] < a['utc_week_s'] for rows in (nav,uncertainty) for a,b in zip(rows,rows[1:])):
        raise ValueError('context timestamp reversal; no sorting or repair')
    intersections = intersect_runs(runs,gps_windows)
    complete = [w for w in intersections if w['longest_clean_imu_s'] >= il.SCREEN_POLICY['minimum_window_s']]
    return dict(source_sha256=actual_hash,source_bytes=stream.size,imu_packets=count,
                imu_types=dict(types),rate_codes=dict(rates),checksum_failures=0,
                dt=dict(min=min(dt_values,default=None),median=float(np.median(dt_values)) if dt_values else None,
                        max=max(dt_values,default=None)), timing_status_flags=dict(flags),
                windows=intersections, windows_with_60s_clean_imu=len(complete),
                fused_context=navigation_context(nav,uncertainty,gps_windows),
                storage_decision='keep',
                reason=('GPS-selected trajectory and at least 60 seconds of complete raw IMU are useful for empirical development'
                        if complete else 'preserve for investigation: GPS geometry exists but clean IMU completeness is not established'),
                physical_interpretation=('IMU6 separate scale/mount interpretation pending' if set(types)=={6}
                                         else 'consult per-file/configuration physical reports'),
                scientific_eligible=False, scientific_blockers=['independent orientation','recorded correction behavior'])


def append_journal(path, row):
    with path.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(row,sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())


def remove_duplicate(corpus, output, rejected, canonical):
    """Only a verified byte-identical copy in the owned corpus; durable before/after journal."""
    corpus = Path(corpus)
    if json.loads((corpus/'ownership.json').read_text()).get('owner') != OWNERSHIP:
        raise ValueError('unowned corpus')
    if rejected['task_id']==canonical['task_id'] or rejected['source_sha256']!=canonical['source_sha256']:
        raise ValueError('not a distinct hash-identical duplicate')
    by = {r['task_id']:r for r in map(json.loads,(corpus/'records.jsonl').read_text().splitlines())}
    retained = follow.source_path(corpus,by[canonical['task_id']])
    journal = output/'cleanup.jsonl'
    entries = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    prepared = next((r for r in reversed(entries) if r['task_id']==rejected['task_id'] and r['state']=='prepared'),None)
    try:
        source = follow.source_path(corpus,by[rejected['task_id']])
    except ValueError:
        if not prepared or prepared['source_sha256']!=canonical['source_sha256'] or prepared['canonical_task_id']!=canonical['task_id']:
            raise
        source = Path(prepared['removed_path'])
        record = by[rejected['task_id']]
        expected = (corpus/record['task_id']/'decoded'/(record['filename']+'.gz'),
                    corpus/record['task_id']/(record['filename']+'.quarantine.gz'))
        if source not in expected or source.exists():
            raise ValueError('invalid interrupted deletion path')
    for path in (source,retained):
        if not path.resolve().is_relative_to(corpus.resolve()) or any(p.is_symlink() for p in (path,*path.parents)):
            raise ValueError('unsafe original path')
        if path==source and not path.exists() and prepared:
            continue
        with il.open_source(path) as stream:
            import hashlib
            digest = hashlib.sha256()
            for chunk in iter(lambda:stream.read(1024*1024),b''):
                digest.update(chunk)
        if digest.hexdigest()!=canonical['source_sha256']:
            raise ValueError('duplicate source changed')
    entry = dict(task_id=rejected['task_id'], canonical_task_id=canonical['task_id'],
                 source_sha256=canonical['source_sha256'], removed_path=str(source),
                 canonical_path=str(retained), reason='byte-identical duplicate; no additional measurements',
                 compressed_bytes=source.stat().st_size if source.exists() else prepared['compressed_bytes'])
    if source.exists():
        append_journal(output/'cleanup.jsonl',dict(entry,state='prepared'))
        source.unlink()
    descriptor = os.open(source.parent,os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)
    append_journal(output/'cleanup.jsonl',dict(entry,state='removed'))
    return entry


def run(corpus, prior, assessed, output, discard_duplicates=False):
    corpus, prior, assessed, output = map(Path,(corpus,prior,assessed,output))
    previous = json.loads((prior/'summary.json').read_text())
    assessment_summary = json.loads((assessed/'summary.json').read_text())
    targets = select_targets(previous,assessment_summary)
    contexts = {r['task_id']:r for r in targets}
    windows = {r['task_id']:r['gps']['potential_windows'] for r in assessment_summary['diagnostics'] if r['task_id'] in contexts}
    duplicate_of = duplicate_plan(previous['results'],set(contexts))
    records = {r['task_id']:r for r in map(json.loads,(corpus/'records.jsonl').read_text().splitlines())}
    sources = [Path(__file__),Path(ap.__file__),Path(il.__file__),Path(follow.__file__),Path(assessment.__file__)]
    sources.append(Path(__file__).parents[1]/'tests'/'ilvis0_retention_worker.py')
    inputs = [corpus/'records.jsonl',corpus/'ownership.json',prior/'summary.json',prior/'cleanup.jsonl',assessed/'summary.json']
    manifest = dict(version=VERSION,sources={str(p):il.sha256(p) for p in sources},
                    inputs={str(p):il.sha256(p) for p in inputs},python=platform.python_version(),numpy=np.__version__,
                    targets=[r['task_id'] for r in targets],duplicates=duplicate_of,
                    discard_duplicates=discard_duplicates,
                    threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
    if output.exists() and not (output/'manifest.json').is_file():
        raise ValueError('unmarked retention audit directory')
    output.mkdir(parents=True,exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        freeze = output/'manifest.json'
        if freeze.exists() and json.loads(freeze.read_text())!=manifest:
            raise ValueError('retention source/environment/input mismatch')
        if not freeze.exists(): follow.atomic_json(freeze,manifest)
        def frozen():
            for p in sources+inputs:
                if il.sha256(p)!=manifest['sources'].get(str(p),manifest['inputs'].get(str(p))):
                    raise ValueError('retention frozen source/input changed')
        results = {}
        for i,context in enumerate(targets):
            frozen(); task=context['task_id']; destination=output/(task+'.json')
            follow.atomic_json(output/'status.json',dict(state='running',pid=os.getpid(),completed=i,total=len(targets),task_id=task))
            if destination.exists(): result=json.loads(destination.read_text())
            else:
                try: result=audit_source(follow.source_path(corpus,records[task]),context,windows[task])
                except ValueError as error: result=dict(storage_decision='keep',reason='audit failure requires investigation',error=str(error),scientific_eligible=False)
                result.update(task_id=task,filename=context['filename'],actual_dates=context['timing']['dates'])
                follow.atomic_json(destination,result)
            results[task]=result
        removals = []
        for task,canonical_task in duplicate_of.items():
            frozen()
            rejected,canonical=results[task],results[canonical_task]
            if 'error' in rejected or 'error' in canonical:
                continue
            rejected.update(storage_decision='discard_duplicate',canonical_task_id=canonical_task,
                            reason='byte-identical duplicate; canonical original preserved')
            if discard_duplicates:
                # Recovery skips only a completed journaled deletion, never an unexplained missing file.
                journal=output/'cleanup.jsonl'
                entries=[json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
                completed=next((r for r in reversed(entries) if r['task_id']==task and r['state']=='removed'),None)
                if completed is not None: removals.append(completed)
                else: removals.append(remove_duplicate(corpus,output,rejected,canonical))
            follow.atomic_json(output/(task+'.json'),rejected)
        frozen()
        summary=dict(version=VERSION,state='complete',files=len(results),
                     decisions=dict(Counter(r['storage_decision'] for r in results.values())),
                     audit_errors=sum('error' in r for r in results.values()),
                     unique_kept_with_complete_IMU=sum(r['storage_decision']=='keep' and r.get('windows_with_60s_clean_imu',0)>0 for r in results.values()),
                     removed_duplicates=len(removals),reclaimed_bytes=sum(r['compressed_bytes'] for r in removals),
                     scientific_eligibility_changes=0,earth_model_fit_attempts=0,results=list(results.values()),removals=removals)
        follow.atomic_json(output/'summary.json',summary)
        compact={k:v for k,v in summary.items() if k not in ('results','removals')}
        follow.atomic_json(output/'status.json',dict(compact,pid=os.getpid()))
        print(json.dumps(compact),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',type=Path,default=Path('data/ilvis0-ready'))
    parser.add_argument('--prior',type=Path,default=Path('data/ilvis0-followup-20261007'))
    parser.add_argument('--assessed',type=Path,default=Path('data/ilvis0-imu21-assessment-20261007'))
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-retention-84-20261007'))
    parser.add_argument('--discard-duplicates',action='store_true')
    args=parser.parse_args()
    run(args.corpus,args.prior,args.assessed,args.output,args.discard_duplicates)


if __name__=='__main__': main()
