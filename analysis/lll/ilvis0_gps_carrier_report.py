# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare closed carrier-phase motion with the original matched receiver windows."""

from collections import Counter, defaultdict
from contextlib import closing
import gzip
import json
from pathlib import Path

import numpy as np

from . import gnss_position as gps, ilvis0_gps_carrier_pilot as pilot
from .ilvis0_matched_force_average import _table, support
from .ilvis0_matched_observed_layout import OUTPUT as LAYOUT
from .ilvis0_shared_gps_error import quadratic_weights
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy

FOLDER = pilot.pilot.FOLDER
TRACKS = ('onboard', *pilot.pilot.METHODS)
WINDOWS = 991
RECEIPT = FOLDER+'gps-carrier-pilot-receipt.json'
PAIRS = FOLDER+'gps-carrier-pair-results.json.gz'
DETAILS = FOLDER+'gps-carrier-matched-windows.json.gz'


def _local(anchor):
    latitude, longitude, _ = gps.geodetic(anchor)
    return gps.local_rotation(latitude, longitude)


def _summary(array):
    if not len(array):
        return dict(samples=0)
    values = np.asarray(array)
    return dict(samples=len(values), rms_neu=np.sqrt(np.mean(values**2, axis=0)).tolist(),
                mean_neu=np.mean(values, axis=0).tolist(),
                p95_abs_neu=np.percentile(abs(values), 95, axis=0).tolist())


def _lags(samples):
    results = {}
    for lag in (1, 5, 15):
        pairs = [(value, samples[tag+lag*1000]) for tag, value in samples.items()
                 if tag+lag*1000 in samples]
        correlation = None
        if len(pairs) >= 3:
            a, b = np.array(pairs).transpose(1, 0, 2)
            correlation = [float(np.corrcoef(x, y)[0, 1]) if min(np.std(x), np.std(y)) > 0. else None
                           for x, y in zip(a.T, b.T, strict=True)]
        results[str(lag)] = dict(pairs=len(pairs), correlation_neu=correlation)
    return results


def window_differences(tags, rows, target, rotation):
    """Accumulate adjacent increments locally and use the fixed position weights."""
    if any(row['status'] != 'converged' for row in rows):
        return None
    weights = quadratic_weights((np.asarray(tags)-target)/1000.)
    differences = {}
    for name in TRACKS:
        increments = np.array([row['difference_ecef_m'][name] for row in rows])
        displacement = np.vstack((np.zeros(3), np.cumsum(increments, axis=0)))
        _, velocity, acceleration = weights@displacement@rotation.T
        differences[name] = dict(velocity_neu_mps=velocity.tolist(), acceleration_neu_mps2=acceleration.tolist())
    return differences


def _load_results(study):
    pairs = defaultdict(dict)
    positions = defaultdict(dict)
    attempts = 0
    if study.completion['state'] != 'complete' or not study.summary['passed']:
        raise ValueError('all frozen phase blocks must be readable and closed')
    for identity, task in study.tasks.items():
        envelope = study.envelope(identity)
        charge = study.artifact(identity, 'phase-charge.json')
        expected = list(zip(task['tags'], task['tags'][1:]))
        data = pilot._decode(study.input(task['input_key'], raw=True))
        output = study.artifact(identity, 'phase.json')
        key = task['segment_id']
        if (expected != [(row['first_tag'], row['last_tag']) for row in output]
                or task['tags'] != charge['tags']
                or [r['tag'] for r in data['records']] != task['tags']
                or any(row['status'] not in ('converged', 'abstain')
                       or row.get('iterations', 0) > pilot.phase.MAX_ITERATIONS for row in output)
                or charge['maximum_iterations'] != pilot.phase.MAX_ITERATIONS
                or charge['maximum_attempts'] != len(expected)
                or charge['imu_fit_starts'] or envelope['result']['imu_fit_starts']
                or not envelope['result']['passed'] or any(envelope['charged'].values())):
            raise ValueError('phase result or charge inventory changed')
        for row in output:
            first = row['first_tag']
            if first in pairs[key]:
                raise ValueError('phase pair appears in two blocks')
            pairs[key][first] = row
        for row in data['records']:
            tag = row['tag']
            if positions[key].setdefault(tag, row['onboard']) != row['onboard']:
                raise ValueError('phase block boundary changed its reported position')
        attempts += charge['maximum_attempts']
    if attempts != pilot.MAX_PAIRS:
        raise ValueError('recorded pair allowance changed')
    for key, records in positions.items():
        tags = sorted(records)
        if sorted(pairs[key]) != tags[:-1] or [pairs[key][tag]['last_tag'] for tag in tags[:-1]] != tags[1:]:
            raise ValueError('phase pair coverage is incomplete')
    return pairs, positions


def build(root, study):
    pairs, positions = _load_results(study)
    window_source = {k: (root/k).read_bytes() for k in (
        support.OUTPUT, support.RESULT, support.WINDOWS, support.WINDOW_RECEIPT, LAYOUT)}
    support_receipt = json.loads(window_source[support.RESULT])
    gps_receipt = json.loads(window_source[support.WINDOW_RECEIPT])
    if (support_receipt['output_sha256'] != digest(window_source[support.OUTPUT])
            or gps_receipt['output_sha256'] != digest(window_source[support.WINDOWS])
            or gps_receipt['position_parent'] != study.input('provenance')['code_completion']):
        raise ValueError('matched accelerometer support changed')
    windows = [row for row in _table(window_source[support.OUTPUT]) if row['state']=='supported']
    source = {(r['segment_id'], int(r['gps_millisecond_tag'])): r
              for r in _table(window_source[support.WINDOWS]) if float(r['half_window_s'])==support.HALF_WINDOW_S}
    layout = {item['segment_id']: item for item in json.loads(window_source[LAYOUT])['layouts']}
    if set(layout) != set(pairs) or len(windows) != WINDOWS:
        raise ValueError('changed recorded windows or flight selection')
    detailed = []
    pair_rows = []
    summary = {}
    for key, records in pairs.items():
        coordinates = positions[key]
        tags = sorted(coordinates)
        cut_ms = round(1000*(layout[key]['first_prediction_utc_week_s']+layout[key]['gps_minus_utc_s']))
        velocity = defaultdict(dict)
        for tag, row in sorted(records.items()):
            first_side = (tag % pilot.pilot.parent.WEEK_MS) < cut_ms
            last_side = (row['last_tag'] % pilot.pilot.parent.WEEK_MS) < cut_ms
            side = ('training' if first_side else 'later') if first_side == last_side else 'crossing'
            pair_rows.append(dict(segment_id=key, side=side, **row))
            if row['status'] == 'converged' and side != 'crossing':
                rotation = _local(coordinates[tag])
                for name in TRACKS:
                    velocity[(side, name)][tag] = rotation@row['difference_ecef_m'][name]/row['duration_s']
        for window in (row for row in windows if row['segment_id']==key):
            target = int(window['gps_millisecond_tag'])
            info = source[key, target]
            lo, hi = int(info['first_used_tag']), int(info['last_used_tag'])
            first, stop = tags.index(lo), tags.index(hi)+1
            selected = tags[first:stop]
            if len(selected) != int(info['sample_count']) or target not in selected:
                raise ValueError('receiver window differs from the original support')
            values = window_differences(selected, [records[tag] for tag in selected[:-1]],
                                        target, _local(coordinates[target]))
            detailed.append(dict(segment_id=key, imu_type=int(window['imu_type']),
                gps_millisecond_tag=target, side=window['side'], phase_supported=values is not None,
                differences=values))
        summary[key] = dict(pairs=len(records),
            converged=sum(r['status']=='converged' for r in records.values()),
            phase_range_residual_median_m=float(np.median([r['range_difference_rms_m']
                for r in records.values() if r['status']=='converged'])) if velocity else None,
            abstentions=dict(Counter(r['reason'] for r in records.values() if r['status']=='abstain')),
            velocity_by_side={side: {name: dict(_summary(list(velocity[side, name].values())),
                lag_seconds=_lags(velocity[side, name])) for name in TRACKS} for side in ('training', 'later')},
            matched_windows={side: {name: _summary([r['differences'][name]['acceleration_neu_mps2']
                for r in detailed if r['segment_id']==key and r['side']==side and r['phase_supported']])
                for name in TRACKS} for side in ('training', 'later')})
    return dict(completion=study.completion, pair_attempts=pilot.MAX_PAIRS, matched_windows=WINDOWS,
        phase_supported_windows=sum(r['phase_supported'] for r in detailed), by_segment=summary,
        input_sha256={name: digest(value) for name, value in window_source.items()},
        provenance=study.input('provenance'), imu_fit_starts=0, scientific_decision='abstain'), pair_rows, detailed


def publish(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+pilot.IDENTITY)) as study:
        result, pairs, windows = build(root, study)
    output = {PAIRS: gzip.compress(encoded(pairs), mtime=0),
              DETAILS: gzip.compress(encoded(windows), mtime=0)}
    result.update(reporter_sha256=digest(Path(__file__).read_bytes()),
                  output_sha256={name: digest(raw) for name, raw in output.items()})
    output[RECEIPT] = encoded(result)
    for name, raw in output.items():
        _write_equal(root/name, raw)
    return result


if __name__ == '__main__':
    result = publish(Path.cwd())
    print(json.dumps({k: v for k, v in result.items() if k != 'by_segment'}, sort_keys=True))
