# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate, resumable units/uncertainty/GPS audit of preserved ILVIS0 sources.

No acquisition, deletion, scientific eligibility promotion, or Earth-model fit.
Group 1/2 are fused references, not independent inertial observations.
"""
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
import csv
import datetime
import fcntl
import gzip
import io
import json
import math
import os
from pathlib import Path
import platform
import struct

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow, models

VERSION = 'ilvis0-imu21-assessment-v1'
ANGLE_SCALE = 2.0 ** -28
VELOCITY_SCALE = 0.3048 * 2.0 ** -21
GPS_POLICY = dict(version='ilvis0-gps-potential-v1', altitude_half_window_s=15,
                  velocity_half_window_s=5, course_half_window_s=5,
                  maximum_gap_s=2, minimum_speed_mps=50, maximum_vertical_speed_mps=1.5,
                  maximum_course_rate_deg_s=0.05, maneuver_buffer_s=10, minimum_window_s=60)
UNCERTAINTY_FIELDS = tuple(f'{kind}_{axis}_rms_{unit}' for kind, axes, unit in (
    ('position', ('north', 'east', 'down'), 'm'),
    ('velocity', ('north', 'east', 'down'), 'mps'),
    ('attitude', ('roll', 'pitch', 'heading'), 'deg')) for axis in axes)


def navigation_uncertainty(frame):
    """Preserve bytes; label the older nine-float prefix as inferred, not authoritative."""
    if frame.tag != '$GRP' or frame.group != 2:
        raise ValueError('expected Group 2')
    row = dict(ap.time_header(frame), packet_size=len(frame.packet),
               payload_hex=frame.packet[34:-4].hex(), source_kind='fused_navigation_uncertainty',
               authoritative_reference=ap.ICD_URL, usable=False)
    if len(frame.packet) not in (76, 88):
        return dict(row, layout_status='unsupported_size_preserved')
    values = struct.unpack_from('<9f', frame.packet, 34)
    row.update(zip(UNCERTAINTY_FIELDS, values))
    row.update(layout_status=('documented_v6_12_float_layout' if len(frame.packet) == 88
                              else 'inferred_legacy_9_float_prefix'),
               usable=all(math.isfinite(v) and v > 0 for v in values))
    if len(frame.packet) == 88:
        row.update(zip(('ellipse_major_m', 'ellipse_minor_m', 'ellipse_orientation_deg'),
                       struct.unpack_from('<3f', frame.packet, 70)))
    return row


def gps_geometry(fixes):
    """Position/height only; local regressions never interpolate inertial measurements.

    The smoothed geometry cannot establish aircraft roll, heading, mount orientation,
    alignment or short maneuvers. No absence of these windows permits deletion.
    """
    p = GPS_POLICY
    result = dict(policy=p, selection_basis='checksummed GGA positions/heights only; no gyro or fused attitude',
                  scientific_eligible=False, confirmed_level_flight=False, potential_windows=[])
    times = np.array([r['utc_week_s'] for r in fixes], float)
    if len(times) < 3 or np.any(np.diff(times) <= 0):
        return dict(result, reason='insufficient or non-increasing GPS times')
    lat = np.deg2rad([r['latitude_deg'] for r in fixes])
    lon = np.unwrap(np.deg2rad([r['longitude_deg'] for r in fixes]))
    heights = np.array([r['orthometric_height_m'] + (r['geoid_separation_m'] or 0)
                        if r['orthometric_height_m'] is not None else np.nan for r in fixes])
    # Local WGS84 displacement, relative to each window's center. No global projection.
    speed, heading, vertical, scatter = (np.full(len(times), np.nan) for _ in range(4))
    for i, time in enumerate(times):
        for half, kind in ((p['altitude_half_window_s'], 'height'), (p['velocity_half_window_s'], 'motion')):
            left, right = np.searchsorted(times, [time-half, time+half], side='left')
            right = min(right+1, len(times))
            t = times[left:right]-time
            if (len(t) < 3 or t[0] > -half+1e-6 or t[-1] < half-1e-6
                    or np.max(np.diff(t)) > p['maximum_gap_s']):
                continue
            design = np.column_stack((t, np.ones(len(t))))
            if kind == 'height' and np.all(np.isfinite(heights[left:right])):
                fit = np.linalg.lstsq(design, heights[left:right], rcond=None)[0]
                vertical[i] = fit[0]
                scatter[i] = np.sqrt(np.mean((design@fit-heights[left:right])**2))
            elif kind == 'motion':
                meridian, prime = models.radii(np.array([lat[i]]))
                north = (lat[left:right]-lat[i])*float(meridian[0])
                east = (lon[left:right]-lon[i])*float(prime[0])*math.cos(lat[i])
                vn = np.linalg.lstsq(design, north, rcond=None)[0][0]
                ve = np.linalg.lstsq(design, east, rcond=None)[0][0]
                speed[i], heading[i] = math.hypot(vn, ve), math.atan2(ve, vn)
    course_rate = np.full(len(times), np.nan)
    for i, time in enumerate(times):
        half = p['course_half_window_s']
        left, right = np.searchsorted(times, [time-half, time+half], side='left')
        right = min(right+1, len(times))
        if (right-left < 3 or times[left] > time-half+1e-6 or times[right-1] < time+half-1e-6
                or not np.all(np.isfinite(heading[left:right]))
                or np.max(np.diff(times[left:right])) > p['maximum_gap_s']):
            continue
        course_rate[i] = math.degrees(np.linalg.lstsq(
            np.column_stack((times[left:right]-time, np.ones(right-left))),
            np.unwrap(heading[left:right]), rcond=None)[0][0])
    valid = np.isfinite(speed) & np.isfinite(vertical) & np.isfinite(course_rate)
    good = (valid & (speed >= p['minimum_speed_mps'])
            & (np.abs(vertical) <= p['maximum_vertical_speed_mps'])
            & (np.abs(course_rate) <= p['maximum_course_rate_deg_s']))
    spans, start = [], None
    for i in range(len(times)+1):
        qualifies = i < len(times) and good[i]
        if start is not None and (not qualifies or times[i]-times[i-1] > p['maximum_gap_s']):
            first = times[start]+p['maneuver_buffer_s']
            last = times[i-1]-p['maneuver_buffer_s']
            if last-first >= p['minimum_window_s']:
                selected = (times >= first) & (times <= last)
                spans.append(dict(start_s=float(first), end_s=float(last), duration_s=float(last-first),
                                  median_speed_mps=float(np.median(speed[selected])),
                                  maximum_height_regression_rms_m=float(np.max(scatter[selected]))))
            start = None
        if qualifies and start is None:
            start = i
    return dict(result, potential_windows=spans, gps_samples=len(times), geometry_samples=int(valid.sum()),
                reason=None if spans else 'no GPS-only potential window; orientation and brief motion untested')


def read_diagnostics(path, expected_hash):
    nav, uncertainty, gga, zda, cross = [], [], [], [], []
    nmea = ap.NMEA()
    with il.open_source(path) as original:
        stream = follow.HashedReader(original)
        for frame in ap.frames(stream):
            if frame.tag != '$GRP':
                continue
            if frame.group == 1:
                nav.append(ap.group1(frame))
            elif frame.group == 2:
                uncertainty.append(navigation_uncertainty(frame))
            elif frame.group == 10001:
                header = ap.time_header(frame)
                for sentence in nmea.feed(ap.group10001(frame)[1]):
                    if not sentence['valid']:
                        continue
                    f = sentence['fields']
                    if f[0].endswith('ZDA'):
                        date = datetime.date(int(f[4]), int(f[3]), int(f[2]))
                        zda.append(dict(header, date=date.isoformat(), sod=follow.utc_sod(f[1])))
                    elif f[0].endswith('GGA') and int(f[6]) > 0:
                        if f[10] != 'M' or (f[11] and f[12] != 'M'):
                            raise ValueError('unexpected GGA height units')
                        gga.append(dict(header, sod=follow.utc_sod(f[1]),
                                        latitude_deg=ap.coordinate(f[2], f[3]),
                                        longitude_deg=ap.coordinate(f[4], f[5]),
                                        orthometric_height_m=float(f[9]) if f[9] else None,
                                        geoid_separation_m=float(f[11]) if f[11] else None))
            if frame.group in (1, 4):
                h = ap.time_header(frame)
                if h['time_types'] == 33:
                    cross.append(h['time1_s']-h['time2_s'])
            if max(map(len, (nav, uncertainty, gga, zda, cross))) > 250000:
                raise ValueError('context exceeds bounded scan capacity')
    if stream.digest.hexdigest() != expected_hash:
        raise ValueError('original uncompressed SHA-256 mismatch')
    timing = follow.timing_check(zda, cross)
    _, fixes = follow.mapped_context(nav, gga, timing)
    nav_times = [r['time1_s'] for r in nav]
    for row in uncertainty:
        i = bisect_left(nav_times, row['time1_s'])
        near = [nav[j] for j in (i-1, i) if 0 <= j < len(nav_times)]
        near = min(near, key=lambda r:abs(r['time1_s']-row['time1_s'])) if near else None
        if (near and abs(near['time1_s']-row['time1_s']) <= 2
                and (near['time_types'] & 15) == (row['time_types'] & 15)):
            row['alignment_status'] = near['alignment_status']
        else:
            row['alignment_status'] = None
    statistics = {}
    for status in sorted({str(r['alignment_status']) for r in uncertainty}):
        rows = [r for r in uncertainty if str(r['alignment_status']) == status and r['usable']]
        statistics[status] = dict(samples=len(rows), **{
            field:dict(median=float(np.median([r[field] for r in rows])),
                       p95=float(np.quantile([r[field] for r in rows], .95)))
            for field in UNCERTAINTY_FIELDS if rows})
    return dict(timing=timing, source_sha256=expected_hash, source_bytes=stream.size,
                group2=dict(count=len(uncertainty), layouts=dict(Counter(r['layout_status'] for r in uncertainty)),
                            by_alignment=statistics, interpretation='internal fused RMS estimates; not independently verified accuracy'),
                gps=gps_geometry(fixes), earth_model_eligible=False), uncertainty


def validate_imu21(path, mapping=None):
    samples, total = il.matched_samples(path, limit=4000, imu_types=(21,))
    status = 'full_navigation'
    if len(samples) < 60:
        samples, total = il.matched_samples(path, limit=4000, imu_types=(21,), alignment_statuses=(1,))
        status = 'fine_alignment_decoder_diagnostic_only'
    result = dict(version=VERSION, matched_total=total, samples=len(samples), reference_status=status,
                  accepted=False, earth_model_eligible=False, manufacturer_scale_table_found=False,
                  interpretation='six little-endian signed int32 native-axis increments',
                  expected_angle_rad_per_count=ANGLE_SCALE, expected_velocity_mps_per_count=VELOCITY_SCALE,
                  velocity_scale_origin='2^-21 feet/second per count times exact 0.3048 metre/foot',
                  time_matching='nearest Group-4 time1 within 2.6 ms; actual adjacent dt; no interpolation',
                  reference='Group-1 fused angular rates and body acceleration with jointly fitted gravity',
                  processing=il.PROCESSING)
    if len(samples) < 60:
        return dict(result, reason='fewer than 60 matched usable samples', mapping=mapping)
    gyro = np.array([r['gyro'] for r in samples])
    target = np.array([r['gyro_reference'] for r in samples])
    discovery = il.validate_arrays(gyro, target, ANGLE_SCALE)
    alternatives = discovery['plausible_mapping_scores']
    if not alternatives:
        return dict(result, reason='no plausible gyro axis/sign mapping', mapping=mapping, gyro=discovery)
    discovered = {key:alternatives[0][key] for key in ('permutation', 'signs')}
    mapping = discovered if mapping is None else mapping
    perm, signs = mapping['permutation'], mapping['signs']
    result['mapping'] = mapping
    result['best_mapping_this_file'] = discovered
    result['mapping_matches_fixed'] = discovered == mapping
    result['gyro'] = il.validate_arrays(gyro[:, perm]*signs, target, ANGLE_SCALE)
    result['accelerometer'] = il.validate_arrays(
        np.array([r['force'] for r in samples])[:, perm]*signs,
        [r['acceleration_reference'] for r in samples], VELOCITY_SCALE, [r['gravity'] for r in samples])
    for kind in ('gyro', 'accelerometer'):
        for i, axis in enumerate(result[kind]['axes']):
            axis.update(source_axis='xyz'[perm[i]], sign=signs[i])
    result['time_matching_max_abs_s'] = max(abs(r['error']) for r in samples)
    result['accepted'] = bool(result['mapping_matches_fixed'] and result['gyro']['accepted']
                              and result['accelerometer']['accepted'])
    result['reason'] = None if result['accepted'] else 'axis, engineering-unit or chronological holdout check failed'
    return result


def physical_rows(path):
    """Explicit IMU21 units after caller validation; preserve native axes and raw counts."""
    previous = None
    for frame in il.groups(path, 4):
        row = ap.group4(frame)
        if row['imu_type'] != 21 or row['rate_code'] != 2:
            raise ValueError('unsupported IMU21 export configuration')
        out = ap.increments(row, previous, supported=True)
        for kind, scale, unit, rate_unit, rate_name in (
                ('dv', VELOCITY_SCALE, 'mps', 'mps2', 'specific_force'),
                ('dtheta', ANGLE_SCALE, 'rad', 'rads', 'angular_rate')):
            for axis in 'xyz':
                value = row[f'raw_{kind}_{axis}']*scale
                out[f'{kind}_{axis}_{unit}'] = value
                out[f'{rate_name}_{axis}_{rate_unit}'] = value/out['dt_s'] if not out['flags'] else None
        yield out
        previous = row


def write_csv_gz(path, rows):
    # Materialize only the small uncertainty context; physical output uses its own iterator.
    rows = list(rows)
    if not rows:
        return
    fields = sorted({key for r in rows for key in r})
    temporary = path.with_suffix(path.suffix+'.tmp')
    with temporary.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding='utf-8', newline='') as text:
                writer = csv.DictWriter(text, fieldnames=fields)
                writer.writeheader(); writer.writerows(rows)
        raw.flush(); os.fsync(raw.fileno())
    os.replace(temporary, path)


def export_windows(path, context, destination):
    """Streaming native-axis measurements; no offset correction, sorting or interpolation."""
    windows = context['screen']['windows']
    leap = context['timing']['gps_minus_utc_s']
    temporary = destination.with_suffix(destination.suffix+'.tmp')
    count, writer = 0, None
    with temporary.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding='utf-8', newline='') as text:
                for row in physical_rows(path):
                    time = follow.utc_tag(row, leap)
                    if not any(w['start_s'] <= time <= w['end_s'] for w in windows):
                        continue
                    row.update(source_file=context['filename'], utc_week_s=time,
                               physical_validation_version=VERSION, native_axes_preserved=True)
                    if writer is None:
                        writer = csv.DictWriter(text, fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow(row); count += 1
        raw.flush(); os.fsync(raw.fileno())
    os.replace(temporary, destination)
    return dict(rows=count, artifact=destination.name, artifact_sha256=il.sha256(destination),
                offsets_removed=False, earth_model_eligible=False)


def select_configurations(contexts):
    grouped = defaultdict(list)
    for row in contexts:
        inv = row['inspection']
        if set(inv['imu_types']) != {'21'} or set(inv['rate_codes']) != {'2'} or len(inv['versions']) != 1:
            continue
        key = json.dumps([sorted(inv['versions']), sorted(inv['imu_types']), sorted(inv['rate_codes'])])
        grouped[key].append(row)
    selected = []
    for key, members in sorted(grouped.items()):
        # Prefer independent fully aligned geometry, then actual receiver dates. No gyro selection.
        pool = [r for r in members if r['screen']['state'] == 'retain'] or members
        pool = sorted(pool, key=lambda r:(r['timing']['dates'][0], r['task_id']))
        first = pool[0]
        distinct = [r for r in pool[1:] if r['timing']['dates'][0] != first['timing']['dates'][0]
                    and r['inspection']['source_sha256'] != first['inspection']['source_sha256']]
        reps = [first] + ([distinct[-1]] if distinct else [])
        selected.append(dict(configuration=key, members=[r['task_id'] for r in members],
                             representatives=[r['task_id'] for r in reps]))
    return selected


def run(corpus, prior, output):
    corpus, prior, output = map(Path, (corpus, prior, output))
    old = json.loads((prior/'summary.json').read_text())
    contexts = [r for r in old['results'] if r['screen']['state'] != 'no_level_window']
    contexts_by_task = {r['task_id']:r for r in contexts}
    records = {r['task_id']:r for r in map(json.loads, (corpus/'records.jsonl').read_text().splitlines())}
    configurations = select_configurations(contexts)
    sources = [Path(__file__), Path(ap.__file__), Path(il.__file__), Path(follow.__file__), Path(models.__file__)]
    sources.append(Path(__file__).parents[1]/'tests'/'ilvis0_assessment_worker.py')
    inputs = [corpus/'records.jsonl', prior/'summary.json', prior/'cleanup.jsonl']
    manifest = dict(version=VERSION, sources={str(p):il.sha256(p) for p in sources},
                    inputs={str(p):il.sha256(p) for p in inputs}, task_ids=[r['task_id'] for r in contexts],
                    configurations=configurations, python=platform.python_version(), numpy=np.__version__,
                    gyro_scale=ANGLE_SCALE, velocity_scale=VELOCITY_SCALE, gps_policy=GPS_POLICY,
                    threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
    if output.exists() and not (output/'manifest.json').is_file():
        raise ValueError('refusing unmarked assessment directory')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'manifest.json').exists():
            if json.loads((output/'manifest.json').read_text()) != manifest:
                raise ValueError('assessment source/environment/input mismatch; use a new output')
        else:
            follow.atomic_json(output/'manifest.json', manifest)
        def frozen():
            for p in sources+inputs:
                expected = manifest['sources'].get(str(p), manifest['inputs'].get(str(p)))
                if il.sha256(p) != expected:
                    raise ValueError('frozen source/input changed')
        def status(phase, completed, total, task=None):
            frozen()
            follow.atomic_json(output/'status.json', dict(state='running', pid=os.getpid(), phase=phase,
                                                         completed=completed, total=total, task_id=task))
        diagnostics = []
        for i, context in enumerate(contexts):
            task = context['task_id']; destination = output/(task+'.context.json')
            status('uncertainty_and_GPS_geometry', i, len(contexts), task)
            if destination.exists():
                result = json.loads(destination.read_text())
            else:
                try:
                    result, uncertainties = read_diagnostics(follow.source_path(corpus, records[task]),
                                                            context['inspection']['source_sha256'])
                    write_csv_gz(output/(task+'.navigation-uncertainty.csv.gz'), uncertainties)
                except ValueError as error:
                    result = dict(error=str(error), earth_model_eligible=False)
                result.update(task_id=task, filename=context['filename'], prior_state=context['screen']['state'])
                follow.atomic_json(destination, result)
            diagnostics.append(result)
        physical, checks = {}, []
        for i, config in enumerate(configurations):
            mapping, tests = None, []
            for task in config['representatives']:
                status('configuration_units_validation', i, len(configurations), task)
                context = contexts_by_task[task]; dest = output/(task+'.physical.json')
                if dest.exists():
                    test = json.loads(dest.read_text())
                else:
                    test = validate_imu21(follow.source_path(corpus, records[task]), mapping)
                    test.update(task_id=task, source_sha256=context['inspection']['source_sha256'],
                                dates=context['timing']['dates'])
                    follow.atomic_json(dest, test)
                mapping = test.get('mapping') if mapping is None else mapping
                physical[task] = test
                tests.append(dict(task_id=task, dates=test['dates'], accepted=test['accepted']))
            checks.append(dict(config, mapping=mapping, tests=tests,
                               reproduced_on_two_dates=len(tests)==2 and all(t['accepted'] for t in tests)))
        exports = []
        members = [(config, task) for config in checks for task in config['members']]
        for i, (config, task) in enumerate(members):
            status('per_file_units_validation', i, len(members), task)
            context = contexts_by_task[task]; path = follow.source_path(corpus, records[task])
            dest = output/(task+'.physical.json')
            if task not in physical:
                if dest.exists():
                    test = json.loads(dest.read_text())
                else:
                    test = validate_imu21(path, config['mapping'])
                    test.update(task_id=task, source_sha256=context['inspection']['source_sha256'],
                                dates=context['timing']['dates'])
                    follow.atomic_json(dest, test)
                physical[task] = test
            if (config['reproduced_on_two_dates'] and physical[task]['accepted']
                    and context['screen']['state']=='retain'):
                dest = output/(task+'.export.json')
                if dest.exists():
                    exported = json.loads(dest.read_text())
                    if il.sha256(output/exported['artifact']) != exported['artifact_sha256']:
                        raise ValueError('physical export SHA-256 mismatch')
                else:
                    exported = export_windows(path, context, output/(task+'.imu-physical.csv.gz'))
                    exported.update(task_id=task, window_seconds=sum(w['duration_s'] for w in context['screen']['windows']))
                    follow.atomic_json(dest, exported)
                exports.append(exported)
        unresolved = [r for r in diagnostics if r['prior_state']=='unresolved']
        summary = dict(version=VERSION, state='complete', kept_sources=len(contexts),
                       configurations=checks, physical_results=list(physical.values()), exports=exports,
                       diagnostics=diagnostics, imu21_files=len(physical),
                       imu21_physical_passes=sum(r['accepted'] for r in physical.values()),
                       exported_candidate_files=len(exports), exported_window_seconds=sum(r['window_seconds'] for r in exports),
                       unresolved_files=len(unresolved),
                       unresolved_with_potential_GPS_windows=sum(bool(r.get('gps',{}).get('potential_windows')) for r in unresolved),
                       scientific_eligibility_changes=0, earth_model_fit_attempts=0, deleted_sources=0)
        frozen()
        follow.atomic_json(output/'summary.json', summary)
        compact = {k:v for k,v in summary.items() if k not in ('configurations','physical_results','exports','diagnostics')}
        follow.atomic_json(output/'status.json', dict(compact, pid=os.getpid()))
        print(json.dumps(compact), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, default=Path('data/ilvis0-ready'))
    parser.add_argument('--prior', type=Path, default=Path('data/ilvis0-followup-20261007'))
    parser.add_argument('--output', type=Path, default=Path('data/ilvis0-imu21-assessment-20261007'))
    args = parser.parse_args()
    run(args.corpus, args.prior, args.output)


if __name__ == '__main__':
    main()
