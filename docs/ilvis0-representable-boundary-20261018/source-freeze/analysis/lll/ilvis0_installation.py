# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate six-file installation/timing investigation, preserving previous failures.

Legacy Message 1 offsets are empirical; Message 20 is the public V6 layout.
Rate-period comparisons are diagnostics, not a replacement for timestamp-derived rates.
"""
import argparse
from collections import Counter
import fcntl
import gzip
import json
import os
from pathlib import Path
import platform
import struct

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import ilvis0_motion_diagnosis as motion

VERSION = 'ilvis0-installation-clock-v1'
PERIOD_S = .005
ANGLE_SCALE = np.pi / (180 * 9000)
VELOCITY_SCALE = 3.38e-5


def rotation(angles_deg):
    """Active sensor-to-parent rotation Rz(yaw) Ry(pitch) Rx(roll)."""
    x, y, z = np.deg2rad(angles_deg)
    cx, cy, cz, sx, sy, sz = np.cos(x), np.cos(y), np.cos(z), np.sin(x), np.sin(y), np.sin(z)
    return np.array([[cz*cy, cz*sy*sx-sz*cx, cz*sy*cx+sz*sx],
                     [sz*cy, sz*sy*sx+cz*cx, sz*sy*cx-cz*sx],
                     [-sy, cy*sx, cy*cx]])


def installation_message(frame):
    if frame.tag != '$MSG' or frame.group not in (1, 20):
        raise ValueError('not an installation candidate')
    out = dict(message_id=frame.group, packet_offset=frame.offset, packet_size=len(frame.packet),
               packet_hex=frame.packet.hex(), public_reference=ap.ICD_URL, usable=False)
    expected = 80 if frame.group == 1 else 92
    if len(frame.packet) != expected:
        return dict(out, layout_status='unsupported_size_preserved')
    angle_offset = 37 if frame.group == 1 else 61
    lever = np.array(struct.unpack_from('<3f', frame.packet, 13))
    angles = np.array(struct.unpack_from('<6f', frame.packet, angle_offset))
    status = 'empirically_inferred_legacy_MSG1_prefix' if frame.group == 1 else 'documented_V6_MSG20'
    out.update(layout_status=status, candidate_reference_to_imu_m=lever.tolist(),
               imu_wrt_reference_angles_deg=angles[:3].tolist(),
               reference_wrt_aircraft_angles_deg=angles[3:].tolist(),
               uninterpreted_tail_hex=frame.packet[angle_offset+24:-4].hex())
    if not np.all(np.isfinite(np.r_[lever, angles])) or np.any(np.abs(angles) > 180):
        return dict(out, reason='nonfinite or out-of-range candidate fields')
    matrix = rotation(angles[3:]) @ rotation(angles[:3])
    return dict(out, usable=True, imu_to_aircraft_rotation=matrix.tolist(),
                candidate_imu_offset_aircraft_m=(rotation(angles[3:]) @ lever).tolist(),
                semantics='Legacy field roles remain inferred, even when the rotation agrees with gyro checks. Recorded setup is not an independent physical mount survey.')


def read_context(path, expected_hash):
    nav, times, offsets, types, rates, settings = [], [], [], Counter(), Counter(), []
    current = None
    with il.open_source(path) as original:
        stream = follow.HashedReader(original)
        for frame in ap.frames(stream):
            if frame.tag == '$MSG' and frame.group in (1, 20):
                signature = frame.packet[10:-4].hex()
                if current is not None and signature == current['signature']:
                    current['count'] += 1
                    current['last_packet_offset'] = frame.offset
                else:
                    current = dict(installation_message(frame), signature=signature, count=1,
                                   last_packet_offset=frame.offset)
                    settings.append(current)
                    if len(settings) > 100:
                        raise ValueError('too many setting epochs for bounded audit')
            elif frame.tag == '$GRP' and frame.group == 1:
                nav.append(ap.group1(frame))
            elif frame.tag == '$GRP' and frame.group == 4:
                row = ap.group4(frame)
                times.append(row['time1_s']); offsets.append(frame.offset)
                types[row['imu_type']] += 1; rates[row['rate_code']] += 1
            if len(nav) > 250000 or len(times) > 1000000:
                raise ValueError('bounded context capacity exceeded')
    if stream.digest.hexdigest() != expected_hash:
        raise ValueError('original SHA-256 mismatch')
    if set(types) != {6} or set(rates) != {2}:
        raise ValueError('unexpected IMU type or rate code')
    t = np.asarray(times); dt = np.diff(t)
    if len(dt) < 2 or np.any(dt <= 0):
        raise ValueError('insufficient or non-increasing IMU times')
    if any(b['time1_s'] <= a['time1_s'] for a, b in zip(nav, nav[1:])):
        raise ValueError('non-increasing navigation times')
    statistics = dict(count=len(times), mean_dt_s=float(np.mean(dt)), median_dt_s=float(np.median(dt)),
        minimum_dt_s=float(np.min(dt)), maximum_dt_s=float(np.max(dt)),
        dt_standard_deviation_us=float(np.std(dt)*1e6),
        adjacent_interval_correlation=float(np.corrcoef(dt[:-1], dt[1:])[0, 1]) if np.std(dt) else None,
        gaps_over_7_5ms=int(np.sum(dt > .0075)),
        nominal_period_cumulative_error_s=float((t[-1]-t[0]) - (len(t)-1)*PERIOD_S),
        nominal_period_mean_relative_error=float(np.mean(dt)/PERIOD_S-1),
        interpretation='Header interval distribution, not direct measurement of the sensor integration clock.')
    return nav, settings, statistics, dict(source_sha256=expected_hash, source_bytes=stream.size)


def compare_rates(samples, settings):
    selected, before_settings, unusable = [], 0, 0
    for sample in samples:
        candidates = [s for s in settings if s['packet_offset'] <= sample['source_packet_offset']]
        if not candidates:
            before_settings += 1
            continue
        setting = candidates[-1]
        if not setting['usable']:
            unusable += 1
            continue
        matrix = np.array(setting['imu_to_aircraft_rotation'])
        raw = np.array(sample['raw_increments'])
        selected.append((sample, matrix @ raw[:3], matrix @ raw[3:], setting))
    result = dict(samples=len(selected), before_first_recorded_setting=before_settings,
                  unusable_setting_samples=unusable, scientific_eligible=False,
                  header_intervals_preserved=True, automatic_decoder_enabled=False)
    if len(selected) < 60:
        return dict(result, reason='insufficient samples after a usable recorded setup')
    target = np.asarray([s['acceleration_reference'] for s, _, _, _ in selected])
    gyro_target = np.asarray([s['gyro_reference'] for s, _, _, _ in selected])
    gravity = np.asarray([s['gravity'] for s, _, _, _ in selected])
    dv = np.asarray([dv for _, dv, _, _ in selected])
    theta = np.asarray([th for _, _, th, _ in selected])
    dt = np.array([s['dt'] for s, _, _, _ in selected])
    cases = {}
    for name, periods in (('measured_header_interval', dt), ('fixed_200Hz_period_hypothesis', np.full(len(dt), PERIOD_S))):
        force = dv / periods[:, None]
        gyro = il.validate_arrays(theta / periods[:, None], gyro_target, ANGLE_SCALE)
        acceleration = il.validate_arrays(force, target, VELOCITY_SCALE, gravity)
        scales, biases, g, prediction = il._fit(force, target, gravity)
        residual = prediction-target
        cases[name] = dict(gyro=gyro, accelerometer=acceleration,
                          vertical_residual_header_dt_correlation=float(np.corrcoef(residual[:, 2], dt)[0, 1])
                          if np.std(dt) and np.std(residual[:,2]) else None)
    first, fixed = (cases[k] for k in ('measured_header_interval', 'fixed_200Hz_period_hypothesis'))
    ratios = [a['rms_residual']/b['rms_residual'] for a, b in zip(first['accelerometer']['axes'], fixed['accelerometer']['axes'])]
    return dict(result, cases=cases, residual_improvement_factors=ratios,
                increments_unit_hypotheses=dict(angle_rad_per_count=float(ANGLE_SCALE), velocity_mps_per_count=VELOCITY_SCALE),
                hypothesis_origin='empirical decimal velocity scale and fixed period; no manufacturer scale/clock specification found',
                interpretation='Fused-reference agreement favors fixed-period normalization. It does not independently prove the physical integration interval, onboard processing or Earth-rate retention.')


def lever_comparison(nav, samples, settings):
    """Fixed recorded offset, both signs; derivative timescales are diagnostic, not fitted lags."""
    t = np.array([r['time1_s'] for r in nav])
    omega = np.deg2rad([[r[f'angular_rate_{a}_deg_s'] for a in 'xyz'] for r in nav])
    indices = np.searchsorted(t, [s['time'] for s in samples])
    if np.any(indices >= len(t)) or not np.all(t[indices] == [s['time'] for s in samples]):
        raise ValueError('cached navigation epochs do not reproduce exactly')
    eligible = [(j, s, next((v for v in reversed(settings) if v['packet_offset'] <= s['source_packet_offset']), None))
                for j, s in enumerate(samples)]
    eligible = [(j, s, setting) for j, s, setting in eligible if setting and setting['usable']]
    results = []
    for span in (.2, 1., 2.):
        alpha = np.column_stack([motion.local_slope(t, omega[:, j], span, maximum_gap_s=.05) for j in range(3)])
        chosen = [(j, s, setting) for j, s, setting in eligible if np.all(np.isfinite(alpha[indices[j]]))]
        if len(chosen) < 60:
            results.append(dict(derivative_span_s=span, samples=len(chosen), supported=False))
            continue
        idx = np.array([indices[j] for j, _, _ in chosen])
        r = np.array([setting['candidate_imu_offset_aircraft_m'] for _, _, setting in chosen])
        effect = np.cross(alpha[idx], r) + np.cross(omega[idx], np.cross(omega[idx], r))
        raw = np.array([np.array(setting['imu_to_aircraft_rotation']) @ np.array(s['raw_increments'][:3])
                        for _, s, setting in chosen]) / PERIOD_S
        target = np.array([s['acceleration_reference'] for _, s, _ in chosen])
        gravity = np.array([s['gravity'] for _, s, _ in chosen])
        comparisons = {}
        for sign in (0, 1, -1):
            _, _, _, prediction = il._fit(raw, target+sign*effect, gravity)
            residual = prediction-sign*effect-target
            comparisons[str(sign)] = np.sqrt(np.mean(residual**2, axis=0)).tolist()
        results.append(dict(derivative_span_s=span, samples=len(chosen), supported=True,
                            lever_acceleration_rms_mps2=np.sqrt(np.mean(effect**2, axis=0)).tolist(),
                            residual_rms_mps2_by_sign=comparisons))
    return dict(comparisons=results, interpretation='Fixed-offset diagnostics using fused rates. Sparse/gapped context is unsupported; no lever correction is applied to science measurements.')


def run(corpus, prior, output):
    corpus, prior, output = map(Path, (corpus, prior, output))
    previous = json.loads((prior/'summary.json').read_text())
    earlier_mappings={r['task_id']:r['chronological_first_half_mapping']
                      for r in json.loads((prior/'axis-change-supplement.json').read_text())['results']}
    if previous['state'] != 'complete':
        raise ValueError('previous units audit must complete first')
    records = {r['task_id']: r for r in map(json.loads, (corpus/'records.jsonl').read_text().splitlines())}
    sources = [Path(__file__), Path(ap.__file__), Path(il.__file__), Path(follow.__file__), Path(motion.__file__),
               Path(__file__).parents[1]/'tests/ilvis0_installation_worker.py']
    inputs = [prior/'manifest.json', prior/'summary.json', prior/'axis-change-supplement.json', corpus/'records.jsonl']
    inputs += [prior/r['matched_artifact'] for r in previous['results']]
    manifest = dict(version=VERSION, sources={str(p):il.sha256(p) for p in sources}, inputs={str(p):il.sha256(p) for p in inputs},
                    tasks=[r['task_id'] for r in previous['results']], nominal_period_s=PERIOD_S,
                    angle_scale=float(ANGLE_SCALE), empirical_velocity_scale=VELOCITY_SCALE,
                    python=platform.python_version(), numpy=np.__version__,
                    threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked installation audit directory')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'manifest.json').exists():
            if json.loads((output/'manifest.json').read_text()) != manifest:
                raise ValueError('installation audit source/input/environment mismatch')
        else:
            follow.atomic_json(output/'manifest.json', manifest)
        def frozen():
            for p in sources+inputs:
                if il.sha256(p) != manifest['sources'].get(str(p),manifest['inputs'].get(str(p))):
                    raise ValueError('frozen installation input/source changed')
        reports=[]
        for old in previous['results']:
            frozen(); task=old['task_id']; dest=output/(task+'.json')
            follow.atomic_json(output/'status.json', dict(state='running', pid=os.getpid(), completed=len(reports),total=len(previous['results']),task_id=task))
            if dest.exists():
                report=json.loads(dest.read_text())
            else:
                try:
                    artifact=prior/old['matched_artifact']
                    if il.sha256(artifact)!=old['matched_artifact_sha256']:
                        raise ValueError('matched artifact SHA-256 mismatch')
                    with gzip.open(artifact,'rt') as stream:
                        samples=json.load(stream)['samples']
                    nav,settings,timing,provenance=read_context(follow.source_path(corpus,records[task]),old['provenance']['source_sha256'])
                    comparison=compare_rates(samples,settings)
                    mapped=earlier_mappings[task]
                    matrix=np.eye(3)[mapped['permutation']]*np.asarray(mapped['signs'])[:,None]
                    errors=[float(np.max(np.abs(np.asarray(s['imu_to_aircraft_rotation'])-matrix)))
                            for s in settings if s['usable']]
                    report=dict(settings=settings,timing=timing,provenance=provenance,rate_comparison=comparison,
                                recorded_rotation_max_abs_difference_from_prior_mapping=max(errors) if errors else None,
                                lever_diagnostic=lever_comparison(nav,samples,settings))
                except ValueError as error:
                    report=dict(error=str(error))
                report.update(task_id=task,filename=old['filename'],scientific_eligible=False)
                follow.atomic_json(dest,report)
            reports.append(report)
        summary=dict(version=VERSION,state='complete',files=len(reports),errors=sum('error' in r for r in reports),results=reports,
                     scientific_eligibility_changes=0,earth_model_fit_attempts=0,originals_deleted=0,automatic_decoder_enabled=False)
        frozen(); follow.atomic_json(output/'summary.json',summary)
        compact={k:v for k,v in summary.items() if k!='results'}
        follow.atomic_json(output/'status.json',dict(compact,pid=os.getpid()));print(json.dumps(compact),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',type=Path,default=Path('data/ilvis0-ready'))
    parser.add_argument('--prior',type=Path,default=Path('data/ilvis0-imu6-cross-date-20261007'))
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-installation-clock-20261007'))
    args=parser.parse_args(); run(args.corpus,args.prior,args.output)


if __name__=='__main__':main()
