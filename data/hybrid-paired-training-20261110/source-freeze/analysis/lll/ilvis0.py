# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproducible ILVIS0 decoding and bounded empirical validation.

Run with PYTHONPATH=analysis python -m lll.ilvis0 --help. Group 1 is always
fused navigation; it validates the decoder, never an independent Earth test.
"""
import argparse
from collections import Counter
import contextlib
import csv
import datetime
import gzip
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import platform
import shutil
import tempfile

import numpy as np

from . import applanix as ap

VALIDATION_VERSION = 'ilvis0-increments-v1'
SCREEN_POLICY = dict(version='ilvis0-level-v2', minimum_window_s=60, minimum_speed_mps=50,
                     maximum_vertical_speed_mps=1.5, maximum_course_rate_deg_s=0.05,
                     maximum_roll_deg=5, maneuver_buffer_s=10, maximum_context_gap_s=2,
                     minimum_context_coverage_for_discard=0.95)
PROCESSING = {
    'sensor_calibration': 'unknown', 'scale_factor_correction': 'unknown',
    'bias_correction': 'unknown; nonzero fused-reference offsets observed',
    'earth_rate_compensation': 'unknown; must resolve before independent Earth inference',
    'coning_correction': 'unknown', 'sculling_correction': 'unknown',
    'filtering': 'unknown', 'automatic_zeroing': 'unknown',
    'lever_arm_compensation': 'Group-1 reference lever arm documented; Group-4 unknown',
    'mounting_axes': 'empirical agreement with Group-1 aircraft axes, exact mounting unknown',
    'latency': 'time-tag matching measured; physical latency unknown',
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def provenance(path):
    return dict(source_file=Path(path).name, source_bytes=Path(path).stat().st_size,
                source_sha256=sha256(path), parser_sha256=sha256(Path(ap.__file__)),
                decoder_sha256=sha256(Path(__file__)), python=platform.python_version(),
                numpy=np.__version__, validation_version=VALIDATION_VERSION)


def open_source(path):
    """Read originals or their lossless gzip copies without materializing a file."""
    return gzip.open(path, 'rb') if Path(path).suffix == '.gz' else Path(path).open('rb')


def groups(path, group):
    with open_source(path) as stream:
        for frame in ap.frames(stream):
            if frame.tag == '$GRP' and frame.group == group:
                yield frame


def inventory(path):
    """Strict framing inventory, even when a physical layout is unsupported."""
    counts, versions, layouts, types, rates, time_types = (Counter() for _ in range(6))
    with Path(path).open('rb') as stream:
        for frame in ap.frames(stream):
            counts[f'{frame.tag}:{frame.group}'] += 1
            if frame.tag != '$GRP':
                continue
            if frame.group == 4:
                layouts[len(frame.packet)] += 1
                if len(frame.packet) == 68:
                    row = ap.group4(frame)
                    types[row['imu_type']] += 1
                    rates[row['rate_code']] += 1
                    time_types[row['time_types']] += 1
            elif frame.group == 99:
                versions[ap.group99(frame)] += 1
    return dict(frame_count=sum(counts.values()), frame_counts=dict(counts),
                versions=dict(versions), group4_sizes=dict(layouts),
                imu_types=dict(types), rate_codes=dict(rates), time_types=dict(time_types),
                checksum_failures=0, unframed_bytes=0)


def imu_rows(path, supported=False):
    previous = None
    for frame in groups(path, 4):
        row = ap.group4(frame)
        yield ap.increments(row, previous, supported=supported)
        previous = row


def _gravity(nav):
    roll, pitch = np.deg2rad([nav['roll_deg'], nav['pitch_deg']])
    return np.array([-np.sin(pitch), np.sin(roll) * np.cos(pitch), np.cos(roll) * np.cos(pitch)])


def matched_samples(path, limit=20000, imu_types=(8,), alignment_statuses=(0,)):
    """Two streaming passes, nearest IMU tag, no interpolation; bounded reservoir."""
    imu = iter(imu_rows(path, supported=True))
    current = next(imu, None)
    previous = None
    samples = []
    rng = np.random.default_rng(13013)
    total = 0
    last_nav = -math.inf
    interval_sum = np.zeros(6)
    interval_dt, interval_count, interval_valid = 0., 0, True
    for frame in groups(path, 1):
        nav = ap.group1(frame)
        time = nav['time1_s']
        if time <= last_nav:
            raise ValueError('nonmonotonic Group-1 time')
        last_nav = time
        while current is not None and current['time1_s'] <= time:
            if current['flags']:
                interval_valid = False
            else:
                interval_sum += [current[key] for key in ap.RAW_FIELDS]
                interval_dt += current['dt_s']
                interval_count += 1
            previous, current = current, next(imu, None)
        candidates = [row for row in (previous, current) if row is not None]
        if not candidates:
            continue
        row = min(candidates, key=lambda value: abs(value['time1_s'] - time))
        error = row['time1_s'] - time
        if (abs(error) > 0.0026 or row['flags']
                or nav['alignment_status'] not in alignment_statuses
                or row['imu_type'] not in imu_types or row['rate_code'] != 2
                or (row['time_types'] & 15) != (nav['time_types'] & 15)):
            interval_sum[:], interval_dt, interval_count, interval_valid = 0, 0., 0, True
            continue
        sample = dict(time=time, error=error, dt=row['dt_s'], gravity=_gravity(nav).tolist(),
                      source_packet_offset=row['packet_offset'], raw_increments=[row[key] for key in ap.RAW_FIELDS],
                      gyro=[row[f'raw_dtheta_{axis}'] / row['dt_s'] for axis in 'xyz'],
                      force=[row[f'raw_dv_{axis}'] / row['dt_s'] for axis in 'xyz'],
                      gyro_reference=np.deg2rad([nav[f'angular_rate_{axis}_deg_s'] for axis in 'xyz']).tolist(),
                      acceleration_reference=[nav[f'acceleration_{axis}_mps2'] for axis in 'xyz'])
        sample['interval_average'] = (dict(raw_rates=(interval_sum / interval_dt).tolist(),
                                           duration_s=interval_dt, count=interval_count)
                                      if interval_valid and interval_dt > 0 else None)
        interval_sum[:], interval_dt, interval_count, interval_valid = 0, 0., 0, True
        total += 1
        if len(samples) < limit:
            samples.append(sample)
        else:
            choice = int(rng.integers(total))
            if choice < limit:
                samples[choice] = sample
    # Exhaust the strict iterator even when navigation ends early.
    for _ in imu:
        pass
    return sorted(samples, key=lambda row: row['time']), total


def _fit(raw, target, gravity=None):
    n = len(raw)
    if gravity is None:
        coefficients = np.array([np.linalg.lstsq(np.column_stack((raw[:, j], np.ones(n))),
                                                target[:, j], rcond=None)[0] for j in range(3)])
        scale, intercept = coefficients[:, 0], coefficients[:, 1]
        return scale, intercept, None, raw * scale + intercept
    # A single gravity magnitude across axes; per-axis scales and offsets estimated.
    # Fitting gravity independently per axis would confound Z scale and gravity.
    design = np.zeros((n * 3, 7))
    for j in range(3):
        design[j::3, j] = raw[:, j]
        design[j::3, j + 3] = 1
    design[:, 6] = gravity.reshape(-1)
    coef = np.linalg.lstsq(design, target.reshape(-1), rcond=None)[0]
    return coef[:3], coef[3:6], float(coef[6]), (design @ coef).reshape(n, 3)


def validate_arrays(raw, target, expected, gravity=None):
    raw, target = np.asarray(raw, float), np.asarray(target, float)
    gravity = None if gravity is None else np.asarray(gravity, float)
    scales, intercepts, g, prediction = _fit(raw, target, gravity)
    residual = prediction - target
    alternatives = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1, 1), repeat=3):
            trial = raw[:, permutation] * signs
            trial_scales, _, _, fitted = _fit(trial, target, gravity)
            # Positive, physically plausible scale is essential for testing signs.
            if np.all((trial_scales > expected * 0.5) & (trial_scales < expected * 1.5)):
                alternatives.append(dict(permutation=list(permutation), signs=list(signs),
                                         rms=float(np.sqrt(np.mean((fitted - target) ** 2)))))
    alternatives.sort(key=lambda row: row['rms'])
    split = len(raw) // 2
    holdouts = []
    for train, test in ((slice(0, split), slice(split, None)), (slice(split, None), slice(0, split))):
        s, b, gg, _ = _fit(raw[train], target[train], None if gravity is None else gravity[train])
        pred = raw[test] * s + b
        if gg is not None:
            pred += gg * gravity[test]
        holdouts.append(dict(scale_ratios=(s / expected).tolist(), gravity_mps2=gg,
                             rms=np.sqrt(np.mean((pred - target[test]) ** 2, axis=0)).tolist()))
    rows = []
    for j, axis in enumerate('xyz'):
        corrected = target[:, j] - intercepts[j]
        if g is not None:
            corrected -= g * gravity[:, j]
        correlation = (float(np.corrcoef(raw[:, j], corrected)[0, 1])
                       if np.std(raw[:, j]) > 0 and np.std(corrected) > 0 else None)
        fixed_prediction = raw[:, j] * expected
        if g is not None:
            fixed_prediction += g * gravity[:, j]
        fixed_intercept = float(np.mean(target[:, j] - fixed_prediction))
        fixed_residual = fixed_prediction + fixed_intercept - target[:, j]
        rows.append(dict(axis=axis, source_axis=axis, sign=1, samples=len(raw),
                         expected_scale=expected, fitted_scale=float(scales[j]),
                         scale_ratio=float(scales[j] / expected), intercept=float(intercepts[j]),
                         correlation=correlation, rms_residual=float(np.sqrt(np.mean(residual[:, j] ** 2))),
                         max_abs_residual=float(np.max(np.abs(residual[:, j]))),
                         p99_abs_residual=float(np.quantile(np.abs(residual[:, j]), 0.99)),
                         fixed_expected_scale_intercept=fixed_intercept,
                         fixed_expected_scale_rms=float(np.sqrt(np.mean(fixed_residual ** 2)))))
    best_expected = bool(alternatives and alternatives[0]['permutation'] == [0, 1, 2]
                         and alternatives[0]['signs'] == [1, 1, 1])
    passed = best_expected and all(abs(row['scale_ratio'] - 1) <= 0.001 and row['correlation'] is not None
                                  and row['correlation'] >= 0.9999 for row in rows)
    stable = all(all(abs(ratio - 1) <= 0.001 for ratio in holdout['scale_ratios']) for holdout in holdouts)
    if g is not None:
        passed &= 9.7 <= g <= 9.9
    return dict(axes=rows, shared_gravity_mps2=g, mappings_tested=48,
                plausible_mapping_scores=alternatives, chronological_holdouts=holdouts,
                engineering_checks_pass=bool(passed), holdout_scale_checks_pass=bool(stable),
                accepted=bool(passed and stable))


def validate(path):
    framing = inventory(path)
    if framing['group4_sizes'] != {68: framing['frame_counts'].get('$GRP:4', 0)}:
        return dict(**provenance(path), inventory=framing, accepted=False,
                    reason='unsupported Group-4 layout; raw framing inventory only')
    samples, total = matched_samples(path)
    versions = framing['versions']
    result = dict(**provenance(path), inventory=framing, versions=dict(versions), matched_total=total,
                  retained_validation_samples=len(samples), processing=PROCESSING,
                  interpretation='six little-endian signed int32: dv XYZ, dtheta XYZ',
                  time_matching='nearest Group-4 time1 within 2.6 ms; no interpolation',
                  validation_reference='Group-1 fused navigation, not independent science',
                  engineering_limits=dict(min_correlation=0.9999, maximum_scale_relative_error=0.001),
                  manufacturer_scale_table_found=False)
    if len(samples) < 60:
        return dict(result, accepted=False, reason='fewer than 60 matched usable samples')
    errors = np.array([row['error'] for row in samples])
    result['time_matching_max_abs_s'] = float(np.max(np.abs(errors)))
    result['gyro'] = validate_arrays([row['gyro'] for row in samples], [row['gyro_reference'] for row in samples], ap.DELTA_ANGLE_SCALE)
    result['accelerometer'] = validate_arrays([row['force'] for row in samples],
                                              [row['acceleration_reference'] for row in samples],
                                              ap.DELTA_V_SCALE, [row['gravity'] for row in samples])
    averaged = [row for row in samples if row['interval_average'] is not None and row['interval_average']['count'] >= 100]
    if len(averaged) >= 60:
        result['timing_sensitivity'] = dict(
            interpretation='Preceding navigation-interval means compared with endpoint Group-1; diagnostic only, no interpolation',
            samples=len(averaged),
            gyro=validate_arrays([row['interval_average']['raw_rates'][3:] for row in averaged],
                                 [row['gyro_reference'] for row in averaged], ap.DELTA_ANGLE_SCALE),
            accelerometer=validate_arrays([row['interval_average']['raw_rates'][:3] for row in averaged],
                                          [row['acceleration_reference'] for row in averaged],
                                          ap.DELTA_V_SCALE, [row['gravity'] for row in averaged]))
    compatible_version = (len(versions) == 1 and all('AV-510' in v and '04.60' in v and '15.00' in v for v in versions)
                          and set(framing['imu_types']) == {8} and set(framing['rate_codes']) == {2}
                          and set(framing['time_types']) == {2})
    result['known_layout_version'] = compatible_version
    result['accepted'] = bool(compatible_version and result['gyro']['accepted'] and result['accelerometer']['accepted'])
    result['state'] = 'empirically_supported_increments' if result['accepted'] else 'candidate_interpretation_not_accepted'
    result['limitations'] = ['Shared-reference internal agreement does not establish sensor accuracy or independent Earth evidence.',
                            'Per-axis offsets are fitted for decoder validation only; never subtracted from exported increments.',
                            'Chronological holdouts test stability, not statistical coverage; gravity and Z offset can be confounded.',
                            'Only the independently tested configuration is eligible for physical conversion.']
    return result


@contextlib.contextmanager
def csv_output(path, fields, compressed=False):
    with contextlib.ExitStack() as stack:
        if compressed:
            raw = stack.enter_context(Path(path).open('xb'))
            binary = stack.enter_context(gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0))
            out = stack.enter_context(io.TextIOWrapper(binary, newline=''))
        else:
            out = stack.enter_context(Path(path).open('x', newline=''))
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        yield writer


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def decode(path, output):
    path, output = Path(path), Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    validation = validate(path)
    supported = validation['accepted']
    with tempfile.TemporaryDirectory(prefix='.ilvis0-', dir=output.parent) as temp:
        stage = Path(temp)
        # Read strictly to EOF and publish the directory only after all outputs close.
        counts, versions, types, rates, flags, status = (Counter() for _ in range(6))
        nmea = ap.NMEA()
        gps_counts, dates = Counter(), Counter()
        previous, first, last, total_imu = None, None, None, 0
        intervals = Counter()
        dt_min, dt_max, dt_sum, dt_count = math.inf, -math.inf, 0, 0
        template = ap.increments(dict(packet_offset=0, time1_s=0, time2_s=0, time_types=0, distance_type=0,
                                     distance_tag_m=0, imu_payload_hex='', data_status=0, imu_type=8, rate_code=2,
                                     imu_status=0, **dict.fromkeys(ap.RAW_FIELDS, 0)))
        imu_fields = ['source_file'] + list(template)
        nav_fields = ['packet_offset', 'time1_s', 'time2_s', 'distance_tag_m', 'time_types', 'distance_type'] + list(ap.NAV_FIELDS) + ['alignment_status', 'source_kind']
        gps_fields = ['stream_offset', 'packet_offset', 'packet_time1_s', 'sentence', 'valid']
        fix_fields = ['time1_s', 'utc_seconds_of_day', 'latitude_deg', 'longitude_deg', 'fix_quality',
                      'orthometric_height_m', 'geoid_separation_m', 'ellipsoidal_height_m', 'stream_offset']
        with contextlib.ExitStack() as stack:
            iw = stack.enter_context(csv_output(stage / 'imu-physical.csv.gz', imu_fields, True))
            nw = stack.enter_context(csv_output(stage / 'navigation.csv', nav_fields))
            gw = stack.enter_context(csv_output(stage / 'gps-sentences.csv', gps_fields))
            fw = stack.enter_context(csv_output(stage / 'gps-fixes.csv', fix_fields))
            raw_gps = stack.enter_context((stage / 'primary-gps-stream.bin.gz').open('xb'))
            gps_out = stack.enter_context(gzip.GzipFile(filename='', fileobj=raw_gps, mode='wb', mtime=0))
            stream = stack.enter_context(path.open('rb'))
            for frame in ap.frames(stream):
                counts[f'{frame.tag}:{frame.group}'] += 1
                if frame.tag != '$GRP':
                    continue
                if frame.group == 4:
                    row = ap.group4(frame)
                    # Per-record guards prevent converting a mixed file configuration.
                    eligible = supported and row['imu_type'] == 8 and row['rate_code'] == 2
                    physical = ap.increments(row, previous, eligible)
                    iw.writerow(dict(source_file=path.name, **physical))
                    types[row['imu_type']] += 1
                    rates[row['rate_code']] += 1
                    status[f"{row['data_status']}:{row['imu_status']}"] += 1
                    flags.update(filter(None, physical['flags'].split(';')))
                    if previous is not None:
                        dt = physical['dt_s']
                        dt_min, dt_max = min(dt_min, dt), max(dt_max, dt)
                        dt_sum += dt
                        dt_count += 1
                        intervals[round(dt, 7)] += 1
                    first = row['time1_s'] if first is None else first
                    last, previous = row['time1_s'], row
                    total_imu += 1
                elif frame.group == 1:
                    nw.writerow(ap.group1(frame))
                elif frame.group == 99:
                    versions[ap.group99(frame)] += 1
                elif frame.group == 10001:
                    _, payload = ap.group10001(frame)
                    gps_out.write(payload)
                    packet_time = ap.time_header(frame)['time1_s']
                    for sentence in nmea.feed(payload):
                        gw.writerow(dict(stream_offset=sentence['stream_offset'], packet_offset=frame.offset,
                                         packet_time1_s=packet_time, sentence=sentence['sentence'], valid=sentence['valid']))
                        if not sentence['valid']:
                            continue
                        f = sentence['fields']
                        gps_counts[f[0]] += 1
                        if f[0].endswith('ZDA'):
                            dates[datetime.date(int(f[4]), int(f[3]), int(f[2])).isoformat()] += 1
                        if f[0].endswith('GGA') and int(f[6]) > 0:
                            utc = int(f[1][:2]) * 3600 + int(f[1][2:4]) * 60 + float(f[1][4:])
                            if not 0 <= utc < 86401:
                                raise ValueError('invalid GGA UTC')
                            if ap.time_header(frame)['time_types'] & 15 != 2:
                                # Do not map POS/GPS time to UTC by an assumed offset.
                                continue
                            time = round((packet_time - utc) / 86400) * 86400 + utc
                            if f[10] != 'M' or (f[11] and f[12] != 'M'):
                                raise ValueError('unexpected GGA height units')
                            height = float(f[9]) if f[9] else None
                            geoid = float(f[11]) if f[11] else None
                            fw.writerow(dict(time1_s=time, utc_seconds_of_day=utc,
                                             latitude_deg=ap.coordinate(f[2], f[3]), longitude_deg=ap.coordinate(f[4], f[5]),
                                             fix_quality=int(f[6]), orthometric_height_m=height, geoid_separation_m=geoid,
                                             ellipsoidal_height_m=height + geoid if height is not None and geoid is not None else None,
                                             stream_offset=sentence['stream_offset']))
        ordered = sorted(intervals.items())
        midpoint, cumulative, median = dt_count // 2, 0, None
        for interval, count in ordered:
            cumulative += count
            if cumulative > midpoint:
                median = interval
                break
        report = dict(**provenance(path), validation=validation, frame_count=sum(counts.values()),
                      frame_counts=dict(counts), checksum_failures=0, unframed_bytes=0, versions=dict(versions),
                      imu=dict(count=total_imu, types=dict(types), rate_codes=dict(rates), status=dict(status),
                               first_time_s=first, last_time_s=last, duration_s=None if first is None else last - first,
                               dt_min_s=dt_min if dt_count else None, dt_max_s=dt_max if dt_count else None,
                               dt_median_s=median, effective_rate_hz=1 / median if median and median > 0 else None,
                               flags=dict(flags)), gps=dict(**nmea.finish(), sentence_counts=dict(gps_counts), dates=dict(dates)),
                      vtq_timing='VTG has no UTC; preserved with packet/receiver-order context only',
                      gps_kind='receiver navigation output, not pseudorange/carrier phase')
        write_json(stage / 'inspection.json', report)
        write_json(stage / 'validation.json', validation)
        # Deterministic original compression, with no change to original bytes.
        with path.open('rb') as src, (stage / (path.name + '.gz')).open('xb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
        stage.rename(output)
    return report


def screen(output):
    """Select geometry before model-dependent residuals; Group-1 only motion context."""
    output = Path(output)
    p = SCREEN_POLICY
    windows = []
    current = None
    qualified = 0
    valid_context = 0
    context_samples = 0
    last_nav = -math.inf
    with (output / 'gps-fixes.csv').open() as gs, (output / 'navigation.csv').open() as ns:
        fixes = iter(csv.DictReader(gs))
        fix, previous_fix = next(fixes, None), None
        rows = iter(csv.DictReader(ns))
        previous = next(rows, None)
        row = next(rows, None)
        for following in rows:
            context_samples += 1
            time = float(row['time1_s'])
            if time <= last_nav:
                report = dict(policy=p, state='unresolved', reason='navigation timestamp reversal', windows=[], earth_model_eligible=False)
                write_json(output / 'screen.json', report)
                return report
            last_nav = time
            while fix is not None and float(fix['time1_s']) < time:
                previous_fix, fix = fix, next(fixes, None)
            candidates = [f for f in (previous_fix, fix) if f is not None]
            gps_ok = bool(candidates and min(abs(float(f['time1_s']) - time) for f in candidates) <= p['maximum_context_gap_s'])
            dt1, dt2 = time - float(previous['time1_s']), float(following['time1_s']) - time
            support = (gps_ok and int(row['time_types']) & 15 == 2
                       and 0 < dt1 <= p['maximum_context_gap_s'] and 0 < dt2 <= p['maximum_context_gap_s']
                       and int(row['alignment_status']) == 0)
            valid_context += support
            def course(value):
                return math.degrees(math.atan2(float(value['velocity_east_mps']), float(value['velocity_north_mps'])))
            rate = abs((course(following) - course(previous) + 180) % 360 - 180) / (dt1 + dt2) if support else math.inf
            good = (support and float(row['speed_mps']) >= p['minimum_speed_mps']
                    and abs(float(row['velocity_down_mps'])) <= p['maximum_vertical_speed_mps']
                    and abs(float(row['roll_deg'])) <= p['maximum_roll_deg']
                    and rate <= p['maximum_course_rate_deg_s'])
            if good:
                qualified += 1
                if current is None:
                    current = [time, time]
                elif time - current[1] <= p['maximum_context_gap_s']:
                    current[1] = time
                else:
                    windows.append(current)
                    current = [time, time]
            elif current is not None:
                windows.append(current)
                current = None
            previous, row = row, following
    if current is not None:
        windows.append(current)
    buffer = p['maneuver_buffer_s']
    windows = [dict(start_s=a + buffer, end_s=b - buffer, duration_s=b - a - 2 * buffer)
               for a, b in windows if b - a - 2 * buffer >= p['minimum_window_s']]
    coverage = valid_context / context_samples if context_samples else 0
    reliable_absence = valid_context >= 60 and coverage >= p['minimum_context_coverage_for_discard']
    report = dict(policy=p, state='retain' if windows else ('no_level_window' if reliable_absence else 'unresolved'),
                  qualifying_context_samples=qualified, valid_context_samples=valid_context, windows=windows,
                  context_samples=context_samples, context_coverage_fraction=coverage,
                  selection_basis='GPS synchronization and fused navigation motion only; no gyro/model residual selection',
                  earth_model_eligible=False,
                  earth_model_blockers=['Group-4 onboard Earth-rate/bias corrections and mounting/latency unresolved',
                                        'Independent attitude/motion reconstruction and nuisance-projected shape information not established',
                                        'Permanent aircraft mount has no participant reversal controls'])
    write_json(output / 'screen.json', report)
    if windows:
        with gzip.open(output / 'imu-physical.csv.gz', 'rt', newline='') as src:
            reader = csv.DictReader(src)
            with csv_output(output / 'level-imu.csv.gz', reader.fieldnames, True) as dst:
                for row in reader:
                    if any(w['start_s'] <= float(row['time1_s']) <= w['end_s'] for w in windows):
                        dst.writerow(row)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('decode', 'validate'):
        p = sub.add_parser(command)
        p.add_argument('--input', required=True, type=Path)
        p.add_argument('--output', required=True, type=Path)
    p = sub.add_parser('screen')
    p.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.command == 'decode':
        report = decode(args.input, args.output)
        print(json.dumps(dict(output=str(args.output), accepted=report['validation']['accepted'], frames=report['frame_count'])))
    elif args.command == 'validate':
        report = validate(args.input)
        write_json(args.output, report)
        print(json.dumps(dict(accepted=report['accepted'], matches=report.get('matched_total', 0), output=str(args.output))))
    else:
        report = screen(args.output)
        print(json.dumps(report))


if __name__ == '__main__':
    main()
