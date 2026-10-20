# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local, resumable context audit of the completed ILVIS0 corpus.

The original corpus and its dispositions are immutable. No downloads, synthetic
campaigns, model fits, or automatic deletion of previously unresolved originals.
"""
import argparse
from bisect import bisect_left
from collections import Counter
import datetime as dt
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys

import numpy as np

from . import applanix as ap, ilvis0 as il
from . import models

VERSION = 'ilvis0-context-followup-v1'
TIME_SOURCES = [ap.ICD_URL, 'https://www.nist.gov/pml/time-and-frequency-division/time-realization/leap-seconds']
# Bounded to the archive's dates, not a perpetually current time service.
LEAPS = [('2009-01-01', 15), ('2012-07-01', 16), ('2015-07-01', 17), ('2017-01-01', 18)]


def leap_seconds(date):
    date = dt.date.fromisoformat(date) if isinstance(date, str) else date
    if not dt.date(2009, 1, 1) <= date < dt.date(2018, 1, 1):
        raise ValueError('date outside validated archive leap-second table')
    return max(n for start, n in LEAPS if dt.date.fromisoformat(start) <= date)


def utc_sod(value):
    h, m, s = int(value[:2]), int(value[2:4]), float(value[4:])
    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError('invalid UTC or leap-second epoch requires separate handling')
    return h * 3600 + m * 60 + s


def utc_tag(header, leap):
    kind = header['time_types'] & 15
    if kind not in (1, 2):
        raise ValueError('unsupported time1 basis')
    return header['time1_s'] - (leap if kind == 1 else 0)


def timing_check(zda, cross_checks):
    """Use dated receiver UTC and documented tag types, never fit a time shift."""
    if len(zda) < 30:
        return dict(accepted=False, reason='fewer than 30 checksummed ZDA anchors')
    offsets = {leap_seconds(row['date']) for row in zda}
    if len(offsets) != 1:
        return dict(accepted=False, reason='leap transition requires separate processing')
    leap = offsets.pop()
    errors = []
    for row in zda:
        date = dt.date.fromisoformat(row['date'])
        expected = ((date.weekday() + 1) % 7) * 86400 + row['sod']
        error = (utc_tag(row, leap) - expected + 302400) % 604800 - 302400
        errors.append(error)
    cross = [(value - leap + 302400) % 604800 - 302400 for value in cross_checks]
    accepted = (max(abs(x) for x in errors) <= il.SCREEN_POLICY['maximum_context_gap_s']
                and all(abs(x) <= 0.001 for x in cross))
    return dict(accepted=accepted, gps_minus_utc_s=leap, zda_anchors=len(zda),
                dates=sorted({r['date'] for r in zda}), method='documented tag basis, dated leap table, checked receiver UTC; no fitted offset',
                packet_minus_receiver_utc_median_s=float(np.median(errors)),
                packet_minus_receiver_utc_max_abs_s=max(abs(x) for x in errors),
                dual_gps_utc_header_checks=len(cross),
                dual_header_max_abs_residual_s=max(map(abs, cross), default=None),
                reason=None if accepted else 'receiver UTC/header timing disagreement', sources=TIME_SOURCES)


class HashedReader:
    def __init__(self, stream):
        self.stream, self.digest, self.size = stream, hashlib.sha256(), 0

    def read(self, n):
        data = self.stream.read(n)
        self.digest.update(data)
        self.size += len(data)
        return data


def read_context(path, expected_hash):
    """Strict streaming scan; retain bounded navigation/receiver context only."""
    nav, gga, zda, cross = [], [], [], []
    counts, types, rates, versions = (Counter() for _ in range(4))
    nmea = ap.NMEA()
    with il.open_source(path) as original:
        stream = HashedReader(original)
        for frame in ap.frames(stream):
            counts[f'{frame.tag}:{frame.group}'] += 1
            if frame.tag != '$GRP':
                continue
            if frame.group == 1:
                nav.append(ap.group1(frame))
            elif frame.group == 4:
                row = ap.group4(frame)
                types[row['imu_type']] += 1
                rates[row['rate_code']] += 1
            elif frame.group == 99:
                versions[ap.group99(frame)] += 1
            elif frame.group == 10001:
                header = ap.time_header(frame)
                for sentence in nmea.feed(ap.group10001(frame)[1]):
                    if not sentence['valid']:
                        continue
                    fields = sentence['fields']
                    if fields[0].endswith('ZDA'):
                        date = dt.date(int(fields[4]), int(fields[3]), int(fields[2]))
                        zda.append(dict(header, date=date.isoformat(), sod=utc_sod(fields[1])))
                    elif fields[0].endswith('GGA') and int(fields[6]) > 0:
                        if fields[10] != 'M' or (fields[11] and fields[12] != 'M'):
                            raise ValueError('unexpected GGA height units')
                        gga.append(dict(header, sod=utc_sod(fields[1]), latitude_deg=ap.coordinate(fields[2], fields[3]),
                                        longitude_deg=ap.coordinate(fields[4], fields[5]), fix_quality=int(fields[6]),
                                        orthometric_height_m=float(fields[9]) if fields[9] else None,
                                        geoid_separation_m=float(fields[11]) if fields[11] else None))
            # When both time fields are explicitly GPS/UTC, test the same leap shift.
            if frame.group in (1, 4):
                h = ap.time_header(frame)
                if h['time_types'] == 33:
                    cross.append(h['time1_s'] - h['time2_s'])
            if max(len(nav), len(gga), len(zda), len(cross)) > 250000:
                raise ValueError('context exceeds bounded scan capacity')
    if stream.digest.hexdigest() != expected_hash:
        raise ValueError('original uncompressed SHA-256 mismatch')
    return nav, gga, zda, cross, dict(frame_counts=dict(counts), imu_types=dict(types), rate_codes=dict(rates),
                                    versions=dict(versions), source_sha256=expected_hash, source_bytes=stream.size,
                                    nmea=nmea.finish(), checksum_failures=0)


def mapped_context(nav, gga, timing):
    if not timing['accepted']:
        return [], []
    leap = timing['gps_minus_utc_s']
    navigation = [dict(r, native_time1_s=r['time1_s'], utc_week_s=utc_tag(r, leap)) for r in nav]
    fixes = []
    for row in gga:
        time = utc_tag(row, leap)
        measurement = round((time - row['sod']) / 86400) * 86400 + row['sod']
        if abs(measurement - time) > il.SCREEN_POLICY['maximum_context_gap_s']:
            continue
        fixes.append(dict(row, utc_week_s=measurement))
    if any(b['utc_week_s'] < a['utc_week_s'] for a, b in zip(fixes, fixes[1:])):
        raise ValueError('receiver timestamp reversal; no sorting or repair')
    return navigation, fixes


def screen_context(nav, fixes):
    """Same geometry/status limits as the original screen, with explicit UTC tags."""
    p = il.SCREEN_POLICY
    reasons, alignment, time_types = Counter(), Counter(), Counter()
    for row in nav:
        alignment[row['alignment_status']] += 1
        time_types[row['time_types']] += 1
    times = [r['utc_week_s'] for r in fixes]
    spans, current, valid, qualified = [], None, 0, 0
    for before, row, after in zip(nav, nav[1:], nav[2:]):
        time = row['utc_week_s']
        dt1, dt2 = time - before['utc_week_s'], after['utc_week_s'] - time
        if dt1 <= 0 or dt2 <= 0:
            return dict(state='unresolved', reason='navigation timestamp reversal', windows=[], alignment_counts=dict(alignment))
        i = bisect_left(times, time)
        gps_ok = any(abs(times[j] - time) <= p['maximum_context_gap_s'] for j in (i - 1, i) if 0 <= j < len(times))
        failures = []
        if not gps_ok:
            failures.append('missing_nearby_GPS')
        if max(dt1, dt2) > p['maximum_context_gap_s']:
            failures.append('navigation_gap')
        if row['alignment_status'] != 0:
            failures.append('navigation_not_fully_aligned')
        reasons.update(failures)
        supported = not failures
        valid += supported
        course = lambda r: math.degrees(math.atan2(r['velocity_east_mps'], r['velocity_north_mps']))
        rate = abs((course(after) - course(before) + 180) % 360 - 180) / (dt1 + dt2)
        good = (supported and row['speed_mps'] >= p['minimum_speed_mps']
                and abs(row['velocity_down_mps']) <= p['maximum_vertical_speed_mps']
                and abs(row['roll_deg']) <= p['maximum_roll_deg'] and rate <= p['maximum_course_rate_deg_s'])
        qualified += good
        if good:
            current = [time, time] if current is None else [current[0], time]
        elif current is not None:
            spans.append(current); current = None
    if current is not None:
        spans.append(current)
    buffer = p['maneuver_buffer_s']
    windows = [dict(start_s=a + buffer, end_s=b - buffer, duration_s=b - a - 2 * buffer)
               for a, b in spans if b - a - 2 * buffer >= p['minimum_window_s']]
    count = max(0, len(nav) - 2)
    coverage = valid / count if count else 0
    no_level = valid >= 60 and coverage >= p['minimum_context_coverage_for_discard']
    return dict(state='retain' if windows else 'no_level_window' if no_level else 'unresolved', windows=windows,
                policy=dict(p, time_support=VERSION), context_samples=count, valid_context_samples=valid,
                context_coverage_fraction=coverage, qualifying_context_samples=qualified,
                alignment_counts=dict(alignment), original_time_type_counts=dict(time_types), context_failures=dict(reasons),
                earth_model_eligible=False, selection_basis='GPS synchronization and fused motion context; no gyro fit')


def window_performance(nav, window):
    rows = [r for r in nav if window['start_s'] <= r['utc_week_s'] <= window['end_s']]
    lat = np.deg2rad([r['latitude_deg'] for r in rows])
    h = np.array([r['altitude_m'] for r in rows])
    vn, ve = (np.array([r[k] for r in rows]) for k in ('velocity_north_mps', 'velocity_east_mps'))
    transport = models.transport_rate(lat, h, vn, ve)
    factor = 180 / np.pi * 3600
    horizontal = np.linalg.norm(transport[:, :2], axis=1) * factor
    heading = np.arctan2(ve, vn)
    def summary(a):
        return dict(min=float(np.min(a)), median=float(np.median(a)), max=float(np.max(a)))
    return dict(**window, samples=len(rows), speed_mps=summary(np.hypot(vn, ve)), latitude_deg=summary(np.rad2deg(lat)),
                altitude_m=summary(h), horizontal_globe_transport_deg_h=summary(horizontal),
                rotating_globe_earth_rate_horizontal_deg_h=summary(models.OMEGA_E * np.cos(lat) * factor),
                heading_concentration=float(abs(np.mean(np.exp(1j * heading)))),
                occupied_45deg_course_bins=len(set(((np.rad2deg(heading) % 360) // 45).astype(int))),
                expected_signal_only=True, motion_source='Group-1 fused context, not independent Earth evidence',
                interpretation='Horizontal globe transport is a predicted tilt scale; proportional to speed. Bias, aircraft motion and projection determine usable contrast.')


def audit_file(path, record):
    nav, gga, zda, cross, inspection = read_context(path, record['source_sha256'])
    timing = timing_check(zda, cross)
    mapped, fixes = mapped_context(nav, gga, timing)
    if mapped:
        screen = screen_context(mapped, fixes)
    else:
        screen = dict(state='unresolved', reason=timing['reason'], windows=[],
                      alignment_counts=dict(Counter(r['alignment_status'] for r in nav)))
    return dict(task_id=record['task_id'], filename=record['filename'], date=record['date'],
                original_state=record['state'], inspection=inspection, timing=timing, screen=screen,
                performance=[window_performance(mapped, w) for w in screen['windows']],
                physical_accepted_in_original=record.get('physical_accepted',False), earth_model_eligible=False)


def physical_diagnostic(path, context):
    """Test a configuration empirically; never inherit another IMU's conversion."""
    samples,total=il.matched_samples(path,limit=4000,imu_types=(6,8,21))
    reference_status='full_navigation'
    if len(samples)<60:
        samples,total=il.matched_samples(path,limit=4000,imu_types=(6,8,21),alignment_statuses=(1,))
        reference_status='fine_alignment_diagnostic_only'
    result=dict(matched_total=total,retained_validation_samples=len(samples),reference_status=reference_status,
                configuration=context['inspection'],conversion_authorized=False,
                reference='Group-1 fused dynamics; decoder validation only, not independent science')
    if len(samples)<60:
        return dict(result,physical_channel_checks_pass=False,reason='fewer than 60 time-matched usable dynamics samples')
    gyro=il.validate_arrays([r['gyro'] for r in samples],[r['gyro_reference'] for r in samples],ap.DELTA_ANGLE_SCALE)
    accel=il.validate_arrays([r['force'] for r in samples],[r['acceleration_reference'] for r in samples],
                             ap.DELTA_V_SCALE,[r['gravity'] for r in samples])
    result.update(gyro=gyro,accelerometer=accel,
                  physical_channel_checks_pass=bool(gyro['accepted'] and accel['accepted']),
                  time_match_max_abs_s=max(abs(r['error']) for r in samples),
                  processing=il.PROCESSING,empirical_scale_table_only=True)
    return result


def gyro_characterization(path, context, physical):
    """Observed gyro variability includes aircraft motion; not an intrinsic noise spec."""
    if not physical['physical_channel_checks_pass'] or not context['screen']['windows']:
        return dict(state='unavailable',reason='need geometry-selected windows and independently supported scales')
    leap=context['timing']['gps_minus_utc_s']; windows=context['screen']['windows']
    levels=(1,10,60); bins={level:{} for level in levels}
    previous=None; dt_values=[]; count=0
    factor=180/math.pi*3600
    for frame in il.groups(path,4):
        row=ap.group4(frame); value=ap.increments(row,previous,True); previous=row
        if value['flags']:continue
        time=utc_tag(row,leap)
        w=next((i for i,v in enumerate(windows) if v['start_s']<=time<=v['end_s']),None)
        if w is None:continue
        interval=value['dt_s'];dt_values.append(interval);count+=1
        increment=np.array([row[f'raw_dtheta_{axis}'] for axis in 'xyz'])*ap.DELTA_ANGLE_SCALE
        for level in levels:
            index=int((time-windows[w]['start_s'])//level)
            summed,duration=bins[level].setdefault((w,index),[np.zeros(3),0.])
            bins[level][(w,index)]=[summed+increment,duration+interval]
    reports={}
    for level,blocks in bins.items():
        means={key:vector/duration*factor for key,(vector,duration) in blocks.items()
               if level*.99<=duration<=level*1.01}
        values=np.array(list(means.values()))
        diffs=np.array([means[(w,i+1)]-v for (w,i),v in means.items() if (w,i+1) in means])
        reports[str(level)]=dict(complete_blocks=len(means),adjacent_pairs=len(diffs),
            mean_deg_h=np.mean(values,axis=0).tolist() if len(values) else None,
            standard_deviation_deg_h=np.std(values,axis=0).tolist() if len(values)>1 else None,
            adjacent_block_allan_deviation_deg_h=np.sqrt(np.mean(diffs**2,axis=0)/2).tolist() if len(diffs) else None)
    median=float(np.median(dt_values)) if dt_values else None
    return dict(state='observed_variability_characterized',samples=count,dt_median_s=median,
                delta_angle_lsb_rad=ap.DELTA_ANGLE_SCALE,
                instantaneous_rate_lsb_deg_h=ap.DELTA_ANGLE_SCALE/median*factor if median else None,
                averaging_seconds=reports,
                interpretation='Body-axis variability and adjacent-block Allan deviation include aircraft motion, vibration, sensor noise and processing; not isolated IMU noise or calibrated significance.',
                independence='No fused gyro or attitude is subtracted; geometry is selected before these statistics.')


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as out:
        out.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
        out.flush(); os.fsync(out.fileno())
    temp.replace(path)


def source_path(root, record):
    paths = [root / record['task_id'] / 'decoded' / (record['filename'] + '.gz'),
             root / record['task_id'] / (record['filename'] + '.quarantine.gz')]
    found = [p for p in paths if p.is_file() and not p.is_symlink()]
    if len(found) != 1:
        raise ValueError('missing or ambiguous retained original')
    return found[0]


def run(corpus, output):
    corpus, output = Path(corpus), Path(output)
    records = {}
    for line in (corpus / 'records.jsonl').read_text().splitlines():
        row = json.loads(line); records[row['task_id']] = row
    selected = [r for r in records.values() if r['state'] in ('retained', 'unresolved')]
    if output.exists() and not (output/'manifest.json').is_file():
        raise ValueError('refusing unmarked existing follow-up directory')
    output.mkdir(parents=True, exist_ok=True)
    source_files = [Path(__file__), Path(ap.__file__), Path(il.__file__), Path(models.__file__)]
    source_files.append(Path(__file__).parents[1]/'tests'/'ilvis0_followup_worker.py')
    manifest = dict(version=VERSION, sources={str(p): il.sha256(p) for p in source_files},
                    original_records_sha256=il.sha256(corpus/'records.jsonl'), selected_task_ids=[r['task_id'] for r in selected],
                    python=platform.python_version(), numpy=np.__version__, policy=il.SCREEN_POLICY,
                    threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
    with (output / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        freeze=output/'manifest.json'
        if freeze.exists() and json.loads(freeze.read_text()) != manifest:
            raise ValueError('follow-up source/environment mismatch; use a new output directory')
        if not freeze.exists(): atomic_json(freeze,manifest)
        def check_frozen():
            if il.sha256(corpus/'records.jsonl')!=manifest['original_records_sha256']:
                raise ValueError('original ledger changed during follow-up')
            for source in source_files:
                if il.sha256(source)!=manifest['sources'][str(source)]:
                    raise ValueError('source changed during follow-up')
        results=[]
        for record in selected:
            check_frozen()
            task=record['task_id']; destination=output/(task+'.json')
            atomic_json(output/'status.json',dict(state='running',pid=os.getpid(),completed=len(results),total=len(selected),task_id=task))
            if destination.exists():
                result=json.loads(destination.read_text())
            else:
                try: result=audit_file(source_path(corpus,record),record)
                except ValueError as error:
                    result=dict(task_id=task,filename=record['filename'],original_state=record['state'],
                                screen=dict(state='unresolved',reason=str(error),windows=[]),performance=[])
                atomic_json(destination,result)
            results.append(result)
        # Choose at most two dates per exact observed firmware/IMU/rate configuration.
        # Ordering uses motion context, never model-dependent gyro residuals.
        configurations={}
        by_task={r['task_id']:r for r in selected}
        for result in results:
            if 'inspection' not in result:continue
            inspection=result['inspection']
            key=json.dumps([sorted(inspection['versions']),sorted(inspection['imu_types']),sorted(inspection['rate_codes'])])
            configurations.setdefault(key,[]).append(result)
        checks=[]
        for key,members in sorted(configurations.items()):
            members=sorted(members,key=lambda r:(sum(w['duration_s'] for w in r['screen']['windows']),
                           r['screen'].get('alignment_counts',{}).get('0',r['screen'].get('alignment_counts',{}).get(0,0)),r['date']),reverse=True)
            representatives=[members[0]]
            representatives.extend(next(([r] for r in members[1:] if r['date']!=members[0]['date']),[]))
            tests=[]
            for context in representatives:
                check_frozen()
                task=context['task_id']; p=output/(task+'.physical.json')
                atomic_json(output/'status.json',dict(state='running',phase='configuration_validation',task_id=task,pid=os.getpid()))
                if p.exists():test=json.loads(p.read_text())
                else:
                    test=physical_diagnostic(source_path(corpus,by_task[task]),context)
                    atomic_json(p,test)
                tests.append(dict(task_id=task,date=context['date'],report=p.name,
                                  checks_pass=test['physical_channel_checks_pass'],reference_status=test['reference_status']))
            checks.append(dict(configuration=key,files=len(members),tests=tests,
                               reproduced_on_two_dates=len(tests)==2 and all(t['checks_pass'] for t in tests)))
        # Characterize all qualifying windows only where this file's physical check passes.
        performance_count=0
        for context in results:
            if not context['screen']['windows']:continue
            check_frozen()
            task=context['task_id']; physical_path=output/(task+'.physical.json')
            if physical_path.exists():physical=json.loads(physical_path.read_text())
            else:
                atomic_json(output/'status.json',dict(state='running',phase='window_units_validation',task_id=task,pid=os.getpid()))
                physical=physical_diagnostic(source_path(corpus,by_task[task]),context)
                atomic_json(physical_path,physical)
            noise_path=output/(task+'.noise.json')
            if noise_path.exists():noise=json.loads(noise_path.read_text())
            else:
                noise=gyro_characterization(source_path(corpus,by_task[task]),context,physical)
                atomic_json(noise_path,noise)
            performance_count+=noise['state']=='observed_variability_characterized'
        summary=dict(state='complete',version=VERSION,files=len(results),
                     states=dict(Counter(r['screen']['state'] for r in results)),
                     newly_retained=sum(r['original_state']=='unresolved' and r['screen']['state']=='retain' for r in results),
                     timing_accepted=sum(r.get('timing',{}).get('accepted',False) for r in results),
                     qualifying_seconds=sum(w['duration_s'] for r in results for w in r['screen']['windows']),
                     files_with_any_full_navigation=sum(bool(r['screen'].get('alignment_counts',{}).get('0',r['screen'].get('alignment_counts',{}).get(0,0))) for r in results),
                     configurations=checks,window_variability_files=performance_count,
                     results=results,earth_model_fit_attempts=0,original_corpus_modified=False)
        check_frozen()
        atomic_json(output/'summary.json',summary)
        atomic_json(output/'status.json',{k:v for k,v in summary.items() if k not in ('results','configurations')})
        print(json.dumps({k:v for k,v in summary.items() if k not in ('results','configurations')}),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',type=Path,default=Path('data/ilvis0-ready'))
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-followup-20261007'))
    args=parser.parse_args()
    run(args.corpus,args.output)


if __name__=='__main__':
    main()
