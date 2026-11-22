# SPDX-License-Identifier: AGPL-3.0-or-later
"""Time-scale summary of frozen paired gyroscope differences."""

import csv
import gzip
import hashlib
import json
from pathlib import Path


WINDOW_SECONDS = (1, 10, 30, 60)


def summarize_windows(left, right, *, begin_s, end_s,
                      window_seconds=WINDOW_SECONDS):
    import numpy as np
    from .ilvis0_stretch_analytics import DPH

    if (not begin_s < end_s or not isinstance(window_seconds, tuple) or
            not window_seconds or any(type(n) is not int or n < 1
                                      for n in window_seconds)):
        raise ValueError('ordered overlap and positive fixed window lengths required')
    keys = sorted(k for k in set(left) & set(right)
                  if k >= begin_s and k + 1 <= end_s and
                  'raw_aircraft' in left[k] and 'raw_aircraft' in right[k])
    if not keys:
        raise ValueError('common complete UTC-second gyro bins required')
    differences = {}
    weights = {}
    for key in keys:
        a = np.asarray(left[key]['raw_aircraft'], float)
        b = np.asarray(right[key]['raw_aircraft'], float)
        weight = min(float(left[key]['duration_s']),
                     float(right[key]['duration_s']))
        if (a.shape != (3,) or b.shape != (3,) or
                not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or
                not np.isfinite(weight) or weight <= 0 or weight > 1):
            raise ValueError('finite paired three-axis full-second bins required')
        differences[key] = (a - b) * DPH
        weights[key] = weight
    rows = []
    anchor, last = keys[0], keys[-1]
    for width in window_seconds:
        means, totals = [], []
        for start in range(anchor, last + 2 - width, width):
            group = range(start, start + width)
            if not all(k in differences for k in group):
                continue
            current = [weights[k] for k in group]
            means.append(np.average([differences[k] for k in group],
                                    axis=0, weights=current))
            totals.append(sum(current))
        if not means:
            rows.append(dict(window_seconds=width, complete_windows=0,
                             mean_difference_dph=None,
                             rms_difference_dph=None))
            continue
        matrix = np.asarray(means)
        rows.append(dict(window_seconds=width,
                         complete_windows=len(means),
                         mean_difference_dph=np.average(
                             matrix, axis=0, weights=totals).tolist(),
                         rms_difference_dph=np.sqrt(np.average(
                             matrix**2, axis=0, weights=totals)).tolist()))
    return rows


def build(root):
    import numpy as np

    root = Path(root).resolve()
    pair_path = root / 'docs/ilvis0-current-findings-20261015/shared-leg-pairs.csv'
    pair_receipt = root / 'docs/ilvis0-current-findings-20261015/findings-receipt.json'
    cache_receipt = root / 'docs/ilvis0-position-stability-trial-20261013/analytics-receipt.json'
    pair_sha = hashlib.sha256(pair_path.read_bytes()).hexdigest()
    published = json.loads(pair_receipt.read_text())
    cached = json.loads(cache_receipt.read_text())
    if (published['artifacts'].get('shared-leg-pairs.csv') != pair_sha or
            cached.get('shared_pairs') != 12 or
            cached.get('priority_pairs') != 3):
        raise ValueError('verified frozen paired snapshot required')
    rows = list(csv.DictReader(pair_path.open(newline='')))
    if len(rows) != 12 or sum(r['priority_pair'] == 'True' for r in rows) != 3:
        raise ValueError('twelve frozen pairs and three priorities required')
    cache_hashes = {Path(name).name: sha
                    for name, sha in cached['cache_artifacts'].items()}
    used = {}
    def load(segment):
        name = segment + '.json.gz'
        path = root / 'data/ilvis0-stretch-analytics-20261013' / name
        blob = path.read_bytes()
        sha = hashlib.sha256(blob).hexdigest()
        if cache_hashes.get(name) != sha:
            raise ValueError('frozen per-second cache hash differs')
        result = json.loads(gzip.decompress(blob))
        if result['cache_manifest_sha256'] != cached['cache_manifest_sha256']:
            raise ValueError('cache manifest identity differs')
        used[name] = sha
        return {int(key): value for key, value in result['seconds'].items()}
    reports = []
    for pair in rows:
        left = load(pair['left_segment_id'])
        right = load(pair['right_segment_id'])
        scales = summarize_windows(left, right,
            begin_s=float(pair['overlap_start_utc_week_s']),
            end_s=float(pair['overlap_end_utc_week_s']))
        one = scales[0]
        if one['complete_windows'] != int(pair['raw_aircraft_matched_seconds']):
            raise ValueError('published one-second pair count differs')
        for index, axis in enumerate('xyz'):
            for metric, key in (('mean_difference_dph', 'raw_aircraft_difference_'),
                                ('rms_difference_dph', 'raw_aircraft_difference_rms_')):
                if not np.isclose(one[metric][index],
                                  float(pair[key + axis + '_dph']),
                                  rtol=1e-10, atol=1e-10):
                    raise ValueError('published one-second gyro difference differs')
        reports.append(dict(shared_leg_id=pair['shared_leg_id'],
                            left_segment_id=pair['left_segment_id'],
                            right_segment_id=pair['right_segment_id'],
                            left_filename=pair['left_filename'],
                            right_filename=pair['right_filename'],
                            priority_pair=pair['priority_pair'] == 'True',
                            overlap_duration_s=float(pair['overlap_duration_s']),
                            scales=scales))
    return dict(version='ilvis0-paired-gyro-time-scale-v1',
                pair_csv_sha256=pair_sha,
                pair_receipt_sha256=hashlib.sha256(pair_receipt.read_bytes()).hexdigest(),
                cache_receipt_sha256=hashlib.sha256(cache_receipt.read_bytes()).hexdigest(),
                cache_artifacts=used,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                pair_count=len(reports), priority_pair_count=3,
                window_seconds=list(WINDOW_SECONDS), axes=['x', 'y', 'z'],
                pairs=reports, original_reads=0, native_calls=0, model_fits=0,
                intrinsic_sensor_noise_estimated=False,
                physical_instrument_identity_verified=False,
                scientific_decision='abstain')


def publish(root):
    import statistics
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/ilvis0-pair-rate-scale'
    atomic(base / 'RESULT.json', encoded(result))
    lines = []
    for pair in result['pairs']:
        x = pair['scales']
        first = x[0]['rms_difference_dph']
        minute = x[-1]['rms_difference_dph']
        lines.append('| {} | {} | {} | {} |'.format(
            pair['shared_leg_id'], 'yes' if pair['priority_pair'] else 'no',
            '/'.join(f'{v:.2f}' for v in first),
            '—' if minute is None else '/'.join(f'{v:.2f}' for v in minute)))
    medians = []
    for scale in (0, -1):
        medians.append([statistics.median(p['scales'][scale][
            'rms_difference_dph'][axis] for p in result['pairs'])
            for axis in range(3)])
    page = ('# Paired gyro differences across time scales\n\n'
        'The twelve previously selected same-track recorder pairs were '
        'compared using their verified per-second cache. Every one-second '
        'difference reproduces the earlier public pair table. Each longer '
        'row averages fixed nonoverlapping complete UTC seconds; gaps are '
        'not interpolated and no Earth-model fit was run. Values are '
        'between-recorder X/Y/Z RMS differences in degrees/hour.\n\n'
        'Across the twelve pairs, median X/Y/Z differences fall from '
        f'{medians[0][0]:.2f}/{medians[0][1]:.2f}/{medians[0][2]:.2f}°/h '
        'at one second to '
        f'{medians[1][0]:.2f}/{medians[1][1]:.2f}/{medians[1][2]:.2f}°/h '
        'at one minute. Pairs are related recordings, not twelve independent '
        'flight replications.\n\n'
        '| Shared leg | Priority pair | One second X/Y/Z | One minute X/Y/Z |\n'
        '| --- | --- | --- | --- |\n' + '\n'.join(lines) + '\n\n'
        'Averaging can reduce rapid differential motion, but the remaining '
        'difference cannot be assigned to sensor noise alone. Mounting, '
        'timing, calibration and aircraft motion may differ, and matching '
        'receiver tracks do not prove a shared physical installation. '
        'These pairs cannot set the ESA IMU error law or establish an '
        'Earth-model decision.\n\n'
        '[Fixed method](PLAN.md) · [All axes and windows](RESULT.json).\n')
    atomic(base / 'RESULT.md', page.encode())
    return result


if __name__ == '__main__':
    result = publish('.')
    print(json.dumps({'pairs': result['pair_count'],
                      'priority_pairs': result['priority_pair_count']},
                     sort_keys=True))
