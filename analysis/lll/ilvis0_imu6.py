# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded, cross-date IMU6 decoder diagnostics; fused references are not science truth.

Never promotes a window or silently applies an empirically fitted acceleration scale.
"""
import argparse
from collections import defaultdict
import fcntl
import gzip
import json
import os
from pathlib import Path
import platform

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import ilvis0_motion_diagnosis as motion

VERSION = 'ilvis0-imu6-cross-date-v1'
# Empirical hypothesis from the earlier sample, not an authoritative sensor table.
ANGLE_SCALE = np.pi / (180 * 9000)  # 0.4 arcsecond per integer increment
MINIMUM_SAMPLES = 60


def select_representatives(retained, contexts):
    """Freeze earliest/latest distinct embedded dates/hashes; never select on gyro results."""
    grouped = defaultdict(list)
    for row in retained:
        if row['storage_decision'] != 'keep' or set(row['imu_types']) != {'6'}:
            continue
        context = contexts[row['task_id']]
        if len(row['actual_dates']) != 1:
            continue
        inspection = context['inspection']
        key = json.dumps({k: sorted(inspection[k]) for k in
                          ('versions', 'imu_types', 'rate_codes')}, sort_keys=True)
        grouped[key].append(row)
    result = []
    for key, rows in sorted(grouped.items()):
        rows.sort(key=lambda r: (r['actual_dates'][0], r['task_id']))
        first = rows[0]
        others = [r for r in rows if r['actual_dates'] != first['actual_dates']
                  and r['source_sha256'] != first['source_sha256']]
        result.append(dict(configuration=json.loads(key), members=[r['task_id'] for r in rows],
                           representatives=[first['task_id']] + ([others[-1]['task_id']] if others else [])))
    return result


def fit_force(raw, target, gravity):
    """Free empirical scale investigation with shared gravity and chronological holdouts."""
    scales, offsets, g, predicted = il._fit(raw, target, gravity)
    residual = predicted - target
    axes = []
    for j, axis in enumerate('xyz'):
        corrected = target[:, j] - offsets[j] - g * gravity[:, j]
        axes.append(dict(axis=axis, fitted_scale_mps_per_count=float(scales[j]),
                         intercept_mps2=float(offsets[j]),
                         correlation=float(np.corrcoef(raw[:, j], corrected)[0, 1])
                         if np.std(raw[:, j]) and np.std(corrected) else None,
                         rms_residual_mps2=float(np.sqrt(np.mean(residual[:, j] ** 2))),
                         p99_abs_residual_mps2=float(np.quantile(np.abs(residual[:, j]), .99)),
                         max_abs_residual_mps2=float(np.max(np.abs(residual[:, j]))),
                         raw_rate_standard_deviation=float(np.std(raw[:, j]))))
    split = len(raw) // 2
    holdouts = []
    for train, test in ((slice(0, split), slice(split, None)), (slice(split, None), slice(0, split))):
        s, b, gg, _ = il._fit(raw[train], target[train], gravity[train])
        error = raw[test] * s + b + gg * gravity[test] - target[test]
        holdouts.append(dict(fitted_scales_mps_per_count=s.tolist(), gravity_mps2=gg,
                             rms_residual_mps2=np.sqrt(np.mean(error**2, axis=0)).tolist()))
    return dict(axes=axes, shared_gravity_mps2=g, chronological_holdouts=holdouts,
                exact_velocity_scale_known=False,
                interpretation='Reference-fitted estimates only; no physical acceleration export authorized.')


def validate_samples(samples, mapping=None, frozen_velocity_scale=None):
    result = dict(version=VERSION, samples=len(samples), expected_angle_rad_per_count=float(ANGLE_SCALE),
                  angle_scale_origin='empirical 0.4 arcsecond/count hypothesis; manufacturer table not found',
                  scientific_eligible=False, complete_physical_decoder_validated=False,
                  reference='Group-1 fused angular rates and body acceleration with joint gravity',
                  time_matching='nearest Group-4 within 2.6 ms, actual adjacent dt; no interpolation')
    if len(samples) < MINIMUM_SAMPLES:
        return dict(result, gyro_scale_validated=False, reason='fewer than 60 matched samples', mapping=mapping)
    raw = np.asarray([s['gyro'] for s in samples], float)
    target = np.asarray([s['gyro_reference'] for s in samples], float)
    discovery = il.validate_arrays(raw, target, ANGLE_SCALE)
    if not discovery['plausible_mapping_scores']:
        return dict(result, gyro_scale_validated=False, reason='no plausible gyro mapping', mapping=mapping,
                    gyro_discovery=discovery)
    best = {k: discovery['plausible_mapping_scores'][0][k] for k in ('permutation', 'signs')}
    mapping = best if mapping is None else mapping
    perm, signs = mapping['permutation'], np.asarray(mapping['signs'])
    gyro = il.validate_arrays(raw[:, perm] * signs, target, ANGLE_SCALE)
    force = np.asarray([s['force'] for s in samples])[:, perm] * signs
    acceleration = np.asarray([s['acceleration_reference'] for s in samples])
    gravity = np.asarray([s['gravity'] for s in samples])
    empirical = fit_force(force, acceleration, gravity)
    velocity = (float(np.median([a['fitted_scale_mps_per_count'] for a in empirical['axes'][:2]]))
                if frozen_velocity_scale is None else float(frozen_velocity_scale))
    empirical_check = il.validate_arrays(force, acceleration, velocity, gravity)
    # Test accelerometer alternatives independently, even though gyro mapping is frozen.
    alternative = il.validate_arrays(np.asarray([s['force'] for s in samples]), acceleration, velocity, gravity)
    for kind in (gyro, empirical, empirical_check):
        for j, axis in enumerate(kind['axes']):
            axis.update(source_axis='xyz'[perm[j]], sign=int(signs[j]))
    matrix = np.eye(3)[perm] * signs[:, None]
    return dict(result, mapping=mapping, best_mapping_this_file=best, mapping_matches_fixed=best == mapping,
                mapping_rotation_determinant=float(np.linalg.det(matrix)),
                gyro=gyro, gyro_scale_validated=bool(best == mapping and gyro['accepted']),
                accelerometer_empirical=empirical,
                frozen_empirical_velocity_scale_mps_per_count=velocity,
                accelerometer_frozen_scale_check=empirical_check,
                accelerometer_alternative_mapping_scores=alternative['plausible_mapping_scores'],
                accelerometer_empirical_scale_reproduces=bool(best == mapping and empirical_check['accepted']),
                time_matching_max_abs_s=max(abs(s['error']) for s in samples),
                processing=il.PROCESSING,
                interpretation='Relative mapping to fused body channels is not independent aircraft mounting/orientation. Neither offset fitting nor scale agreement proves Earth-rate retention.')


def write_samples(path, samples, total):
    with path.open('wb') as out:
        with gzip.GzipFile(filename='', fileobj=out, mode='wb', mtime=0) as compressed:
            compressed.write(json.dumps(dict(matched_total=total, samples=samples), sort_keys=True).encode())


def run(corpus, retention, prior, output):
    corpus, retention, prior, output = map(Path, (corpus, retention, prior, output))
    retained = json.loads((retention / 'summary.json').read_text())['results']
    selected_rows = {r['task_id']: r for r in retained}
    contexts = {r['task_id']: r for r in json.loads((prior / 'summary.json').read_text())['results']}
    records = {r['task_id']: r for r in map(json.loads, (corpus / 'records.jsonl').read_text().splitlines())}
    configurations = select_representatives(retained, contexts)
    sources = [Path(__file__), Path(ap.__file__), Path(il.__file__), Path(follow.__file__), Path(motion.__file__),
               Path(__file__).parents[1] / 'tests' / 'ilvis0_imu6_worker.py']
    inputs = [corpus / 'records.jsonl', retention / 'summary.json', retention / 'cleanup.jsonl', prior / 'summary.json']
    manifest = dict(version=VERSION, configurations=configurations, angle_scale=float(ANGLE_SCALE),
                    sample_limit=4000, alignment_statuses=[0, 1], python=platform.python_version(), numpy=np.__version__,
                    sources={str(p): il.sha256(p) for p in sources}, inputs={str(p): il.sha256(p) for p in inputs},
                    threads={k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')})
    if output.exists() and not (output / 'manifest.json').exists():
        raise ValueError('unmarked IMU6 audit directory')
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (output / 'manifest.json').exists():
            if json.loads((output / 'manifest.json').read_text()) != manifest:
                raise ValueError('IMU6 audit source/input/environment mismatch')
        else:
            follow.atomic_json(output / 'manifest.json', manifest)
        def frozen():
            for p in sources + inputs:
                if il.sha256(p) != manifest['sources'].get(str(p), manifest['inputs'].get(str(p))):
                    raise ValueError('frozen IMU6 audit source/input changed')
        reports, checks = [], []
        for configuration in configurations:
            mapping, velocity, tests = None, None, []
            for task in configuration['representatives']:
                frozen()
                follow.atomic_json(output / 'status.json', dict(state='running', pid=os.getpid(),
                                  completed=len(reports), total=sum(len(c['representatives']) for c in configurations), task_id=task))
                dest = output / (task + '.json')
                if dest.exists():
                    report = json.loads(dest.read_text())
                    if 'matched_artifact' in report:
                        if il.sha256(output / report['matched_artifact']) != report['matched_artifact_sha256']:
                            raise ValueError('saved IMU6 matched samples changed')
                else:
                    path = follow.source_path(corpus, records[task])
                    row = selected_rows[task]
                    try:
                        # Full strict framing/hash/timing scan before the two bounded matcher passes.
                        _, _, provenance = motion.read_motion(path, row['source_sha256'])
                        samples, total = il.matched_samples(path, limit=4000, imu_types=(6,), alignment_statuses=(0, 1))
                        report = validate_samples(samples, mapping, velocity)
                        artifact = output / (task + '.matched-samples.json.gz')
                        write_samples(artifact, samples, total)
                        report.update(provenance=provenance, matched_total=total,
                                      matched_artifact=artifact.name, matched_artifact_sha256=il.sha256(artifact))
                    except ValueError as error:
                        report = dict(error=str(error), gyro_scale_validated=False, scientific_eligible=False)
                    report.update(task_id=task, filename=row['filename'], dates=row['actual_dates'])
                    follow.atomic_json(dest, report)
                if mapping is None:
                    mapping = report.get('mapping')
                    velocity = report.get('frozen_empirical_velocity_scale_mps_per_count')
                reports.append(report)
                tests.append(dict(task_id=task, gyro_pass=report['gyro_scale_validated'],
                                  accelerometer_empirical_pass=report.get('accelerometer_empirical_scale_reproduces', False)))
            checks.append(dict(configuration, mapping=mapping, frozen_empirical_velocity_scale_mps_per_count=velocity,
                               tests=tests, gyro_reproduced_on_two_dates=len(tests) == 2 and all(t['gyro_pass'] for t in tests),
                               accelerometer_empirical_reproduced_on_two_dates=len(tests) == 2 and all(t['accelerometer_empirical_pass'] for t in tests)))
        frozen()
        summary = dict(version=VERSION, state='complete', configurations=checks, results=reports,
                       files=len(reports), errors=sum('error' in r for r in reports),
                       gyro_passes=sum(r['gyro_scale_validated'] for r in reports),
                       complete_physical_decoder_validated=False, scientific_eligibility_changes=0,
                       originals_deleted=0, earth_model_fit_attempts=0)
        follow.atomic_json(output / 'summary.json', summary)
        compact = {k: v for k, v in summary.items() if k not in ('results', 'configurations')}
        follow.atomic_json(output / 'status.json', dict(compact, pid=os.getpid()))
        print(json.dumps(compact), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, default=Path('data/ilvis0-ready'))
    parser.add_argument('--retention', type=Path, default=Path('data/ilvis0-retention-84-20261007'))
    parser.add_argument('--prior', type=Path, default=Path('data/ilvis0-followup-20261007'))
    parser.add_argument('--output', type=Path, default=Path('data/ilvis0-imu6-cross-date-20261007'))
    a = parser.parse_args()
    run(a.corpus, a.retention, a.prior, a.output)


if __name__ == '__main__':
    main()
