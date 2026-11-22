# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only relative alignment of frozen paired gyroscope caches."""

import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from .ilvis0_pair_rate_scale import build as verified_pair_snapshot
from .ilvis0_stretch_analytics import DPH


MIN_HALF_SECONDS = 60
MIN_SINGULAR_RATIO = 0.05


def _metrics(residual, weights):
    mean = np.average(residual, axis=0, weights=weights)
    rms = np.sqrt(np.average(residual**2, axis=0, weights=weights))
    vector = np.sqrt(np.average(np.sum(residual**2, axis=1), weights=weights))
    return dict(mean_dph=mean.tolist(), axis_rms_dph=rms.tolist(),
                vector_rms_dph=float(vector))


def _window_vector_rms(keys, residual, weights, width):
    lookup = {key: index for index, key in enumerate(keys)}
    anchor, last = keys[0], keys[-1]
    means, totals = [], []
    for start in range(anchor, last + 2 - width, width):
        indices = [lookup.get(key) for key in range(start, start + width)]
        if any(index is None for index in indices):
            continue
        window_weights = weights[indices]
        means.append(np.average(residual[indices], axis=0,
                                weights=window_weights))
        totals.append(float(window_weights.sum()))
    if not means:
        return dict(complete_windows=0, vector_rms_dph=None)
    return dict(complete_windows=len(means),
                vector_rms_dph=float(np.sqrt(np.average(
                    np.sum(np.asarray(means)**2, axis=1), weights=totals))))


def compare_halves(left, right, *, begin_s, end_s):
    """Fit the earlier half, then score the later half with parameters fixed."""
    if not np.isfinite([begin_s, end_s]).all() or begin_s >= end_s:
        raise ValueError('finite ordered published overlap required')
    midpoint = (begin_s + end_s) / 2
    keys = sorted(k for k in set(left) & set(right)
                  if k >= begin_s and k + 1 <= end_s and
                  'raw_aircraft' in left[k] and 'raw_aircraft' in right[k])
    early = [k for k in keys if k + 1 <= midpoint]
    later = [k for k in keys if k >= midpoint]
    if min(len(early), len(later)) < MIN_HALF_SECONDS:
        raise ValueError('at least 60 matched complete seconds in each half required')

    def arrays(group):
        a, b, weights = [], [], []
        for key in group:
            la, rb = left[key], right[key]
            x = np.asarray(la['raw_aircraft'], dtype=float)
            y = np.asarray(rb['raw_aircraft'], dtype=float)
            w = min(float(la['duration_s']), float(rb['duration_s']))
            if (x.shape != (3,) or y.shape != (3,) or
                    not np.isfinite(x).all() or not np.isfinite(y).all() or
                    not np.isfinite(w) or not 0 < w <= 1):
                raise ValueError('finite three-axis complete-second bins required')
            a.append(x * DPH)
            b.append(y * DPH)
            weights.append(w)
        return np.asarray(a), np.asarray(b), np.asarray(weights)

    train_a, train_b, train_w = arrays(early)
    test_a, test_b, test_w = arrays(later)
    mean_a = np.average(train_a, axis=0, weights=train_w)
    mean_b = np.average(train_b, axis=0, weights=train_w)
    centered_a, centered_b = train_a - mean_a, train_b - mean_b
    singular = np.linalg.svd(centered_b * np.sqrt(train_w[:, None]),
                             compute_uv=False)
    ratio = float(singular[-1] / singular[0]) if singular[0] > 0 else 0.0
    baseline_offset = mean_a - mean_b
    baseline_train = _metrics(train_a - train_b - baseline_offset, train_w)
    baseline_error = test_a - test_b - baseline_offset
    baseline_test = _metrics(baseline_error, test_w)
    windows = {}
    for width in (10, 60):
        summary = _window_vector_rms(later, baseline_error, test_w, width)
        windows[width] = dict(complete_windows=summary['complete_windows'],
                              offset_only_vector_rms_dph=summary['vector_rms_dph'],
                              rotated_vector_rms_dph=None)
    result = dict(split_utc_week_s=float(midpoint),
                  training_seconds=len(early), heldout_seconds=len(later),
                  excluded_midpoint_seconds=len(keys)-len(early)-len(later),
                  singular_ratio=ratio,
                  rotation_identifiable=bool(ratio >= MIN_SINGULAR_RATIO),
                  offset_only_dph=baseline_offset.tolist(),
                  training_offset_only=baseline_train,
                  heldout_offset_only=baseline_test,
                  heldout_offset_only_vector_rms_dph=baseline_test['vector_rms_dph'],
                  heldout_windows=windows,
                  fitted_rotation_angle_deg=None,
                  fitted_rotation_matrix=None,
                  fitted_rotated_offset_dph=None,
                  training_rotated=None, heldout_rotated=None,
                  heldout_rotated_vector_rms_dph=None)
    if result['rotation_identifiable']:
        cross = centered_a.T @ (centered_b * train_w[:, None])
        u, _, vt = np.linalg.svd(cross)
        correction = np.diag([1., 1., np.linalg.det(u @ vt)])
        rotation = u @ correction @ vt
        rotated_offset = mean_a - rotation @ mean_b
        train_error = train_a - train_b @ rotation.T - rotated_offset
        test_error = test_a - test_b @ rotation.T - rotated_offset
        rotated_train = _metrics(train_error, train_w)
        rotated_test = _metrics(test_error, test_w)
        angle_cos = np.clip((np.trace(rotation)-1) / 2, -1., 1.)
        result.update(fitted_rotation_angle_deg=float(np.rad2deg(np.arccos(angle_cos))),
                      fitted_rotation_matrix=rotation.tolist(),
                      fitted_rotated_offset_dph=rotated_offset.tolist(),
                      training_rotated=rotated_train,
                      heldout_rotated=rotated_test,
                      heldout_rotated_vector_rms_dph=rotated_test['vector_rms_dph'])
        for width in windows:
            windows[width]['rotated_vector_rms_dph'] = _window_vector_rms(
                later, test_error, test_w, width)['vector_rms_dph']
    return result


def build(root):
    """Verify frozen pair and cache identities, then score all twelve pairs."""
    root = Path(root).resolve()
    snapshot = verified_pair_snapshot(root)
    pair_path = root / 'docs/ilvis0-current-findings-20261015/shared-leg-pairs.csv'
    overlap = {row['shared_leg_id']: (
        float(row['overlap_start_utc_week_s']),
        float(row['overlap_end_utc_week_s']))
        for row in csv.DictReader(pair_path.open(newline=''))}
    if len(overlap) != snapshot['pair_count']:
        raise ValueError('unique published pair overlaps required')
    expected = snapshot['cache_artifacts']
    cache_root = root / 'data/ilvis0-stretch-analytics-20261013'
    loaded = {}

    def load(segment):
        name = segment + '.json.gz'
        if name not in loaded:
            blob = (cache_root / name).read_bytes()
            if hashlib.sha256(blob).hexdigest() != expected.get(name):
                raise ValueError('frozen per-second cache hash differs')
            parsed = json.loads(gzip.decompress(blob))
            loaded[name] = {int(k): v for k, v in parsed['seconds'].items()}
        return loaded[name]

    pairs = []
    for item in snapshot['pairs']:
        begin, end = overlap[item['shared_leg_id']]
        metrics = compare_halves(load(item['left_segment_id']),
                                 load(item['right_segment_id']),
                                 begin_s=begin, end_s=end)
        pairs.append(dict(shared_leg_id=item['shared_leg_id'],
                          priority_pair=item['priority_pair'],
                          left_segment_id=item['left_segment_id'],
                          right_segment_id=item['right_segment_id'],
                          **metrics))
    return dict(version='ilvis0-paired-gyro-earlier-alignment-v1',
                pair_csv_sha256=snapshot['pair_csv_sha256'],
                pair_receipt_sha256=snapshot['pair_receipt_sha256'],
                cache_receipt_sha256=snapshot['cache_receipt_sha256'],
                cache_artifacts=expected,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                split='published overlap arithmetic midpoint',
                minimum_matched_seconds_per_half=MIN_HALF_SECONDS,
                minimum_centered_singular_ratio=MIN_SINGULAR_RATIO,
                pair_count=len(pairs),
                identifiable_pairs=sum(x['rotation_identifiable'] for x in pairs),
                heldout_improved_pairs=sum(
                    x['rotation_identifiable'] and
                    x['heldout_rotated_vector_rms_dph'] <
                    x['heldout_offset_only_vector_rms_dph'] for x in pairs),
                priority_pair_count=sum(x['priority_pair'] for x in pairs),
                pairs=pairs, original_reads=0, native_calls=0,
                earth_model_fits=0, later_data_used_for_fit=False,
                intrinsic_sensor_noise_estimated=False,
                physical_instrument_identity_verified=False,
                scientific_decision='abstain')


def publish(root):
    import statistics
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/ilvis0-pair-alignment'
    atomic(base / 'RESULT.json', encoded(result))
    rows = []
    for pair in result['pairs']:
        rotated = pair['heldout_rotated_vector_rms_dph']
        rows.append('| {} | {} | {} | {:.2f} | {} |'.format(
            pair['shared_leg_id'], 'yes' if pair['priority_pair'] else 'no',
            'yes' if pair['rotation_identifiable'] else 'no',
            pair['heldout_offset_only_vector_rms_dph'],
            '—' if rotated is None else f'{rotated:.2f}'))
    medians = []
    for key in ('heldout_offset_only_vector_rms_dph',
                'heldout_rotated_vector_rms_dph'):
        values = [p[key] for p in result['pairs'] if p[key] is not None]
        medians.append(statistics.median(values) if values else None)
    window_medians = {}
    for width in (10, 60):
        window_medians[width] = [statistics.median(
            p['heldout_windows'][width][key] for p in result['pairs']
            if p['heldout_windows'][width]['complete_windows'])
            for key in ('offset_only_vector_rms_dph', 'rotated_vector_rms_dph')]
    page = ('# Paired recorder alignment on unseen seconds\n\n'
        'A fixed relative rotation and rate offset were estimated from the earlier '
        'half of each published same-track pair, then applied unchanged to the '
        'later half. The comparison uses recorded gyro bins only.\n\n'
        f"{result['identifiable_pairs']}/{result['pair_count']} pairs passed "
        'the fixed numerical rank check for a rotation; noise can also create '
        'apparent rank. Median later-half vector RMS was '
        f'{medians[0]:.2f}°/h with an earlier-only offset and '
        f'{medians[1]:.2f}°/h with an earlier-only offset plus rotation '
        'among identifiable pairs. For fixed complete 10-second windows, the '
        f'medians are {window_medians[10][0]:.2f} and '
        f'{window_medians[10][1]:.2f}°/h; for one-minute windows, '
        f'{window_medians[60][0]:.2f} and '
        f'{window_medians[60][1]:.2f}°/h. Adjacent windows and pairs are '
        'dependent. This is a relative recorder check, not an intrinsic '
        'sensor-noise measurement.\n\n'
        '| Shared leg | Priority | Rotation identified | Offset-only RMS (°/h) | Rotation + offset RMS (°/h) |\n'
        '| --- | --- | --- | ---: | ---: |\n' + '\n'.join(rows) + '\n\n'
        f"The rotated fit improves later-half RMS in {result['heldout_improved_pairs']} "
        f"of {result['pair_count']} pairs, but the "
        'remaining differences are substantial. The comparison cannot '
        'distinguish sensor calibration from mounting, '
        'timing, processing or real aircraft motion. The pairs share flight '
        'conditions and are not independent confirmations. No Earth-model '
        'decision or ESA error law follows.\n\n'
        '[Fixed method](PLAN.md) · [All fitted and held-out values](RESULT.json).\n')
    atomic(base / 'RESULT.md', page.encode())
    return result


if __name__ == '__main__':
    outcome = publish('.')
    print(json.dumps({'pairs': outcome['pair_count'],
                      'identifiable_pairs': outcome['identifiable_pairs']},
                     sort_keys=True))
