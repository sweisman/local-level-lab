# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the two-flight GPS position results and compare their derivatives."""

from collections import defaultdict
from contextlib import closing
import csv
import gzip
import io
import json
from pathlib import Path

import numpy as np

from .ilvis0_gps_reconstruction_pilot import (
    FOLDER, IDENTITY, MAX_ITERATIONS, METHODS, SELECTION, receiver_difference,
)
from .ilvis0_shared_gps_error import quadratic_weights
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


AXES = ('north', 'east', 'up')
WINDOWS = (5., 10., 15.)
LAGS_S = (1, 5, 15)


def _rms(values):
    return np.sqrt(np.mean(values**2, axis=0)).tolist() if len(values) else None


def comparisons(rows):
    """Report the same-coordinate position, velocity and acceleration disagreement."""
    valid = [row for row in rows if row['difference_neu_m'] is not None
             and not row['used_as_initialization']]
    values = np.asarray([row['difference_neu_m'] for row in valid], dtype=float).reshape((-1, 3))
    tags = np.asarray([row['gps_millisecond_tag'] for row in valid], dtype=np.int64)
    by_tag = dict(zip(tags.tolist(), values, strict=True))
    lags = {}
    for lag in LAGS_S:
        pairs = [(row, by_tag[t+lag*1000]) for t, row in by_tag.items() if t+lag*1000 in by_tag]
        correlation = [None]*3
        if len(pairs) > 2:
            left, right = np.array(pairs).transpose((1, 0, 2))
            correlation = [float(np.corrcoef(a, b)[0, 1])
                           if min(np.std(a), np.std(b)) > 0. else None
                           for a, b in zip(left.T, right.T, strict=True)]
        lags[str(lag)] = dict(pairs=len(pairs), correlation_neu=correlation)
    derivative_rows = []
    summary = {}
    for half in WINDOWS:
        estimates = []
        for target in tags:
            first = int(np.searchsorted(tags, target-half*1000))
            stop = int(np.searchsorted(tags, target+half*1000, side='right'))
            local = (tags[first:stop]-target)/1000.
            if (not len(tags) or tags[0] > target-half*1000 or tags[-1] < target+half*1000
                    or len(local) < 5 or local[0]+half > 1.5 or half-local[-1] > 1.5
                    or max(np.diff(local)) > 1.5):
                continue
            _, velocity, acceleration = quadratic_weights(local)@values[first:stop]
            estimates.append((velocity, acceleration))
            derivative_rows.append(dict(gps_millisecond_tag=int(target), half_window_s=half,
                                        count=len(local), velocity_neu_mps=velocity.tolist(),
                                        acceleration_neu_mps2=acceleration.tolist()))
        summary[str(half)] = dict(windows=len(estimates),
            velocity_rms_neu_mps=_rms(np.array(estimates)[:, 0]) if estimates else None,
            acceleration_rms_neu_mps2=_rms(np.array(estimates)[:, 1]) if estimates else None)
    result = dict(solves=len(rows), converged=sum(row['status'] == 'converged' for row in rows),
        comparison_epochs=len(valid), position_rms_neu_m=_rms(values),
        position_mean_neu_m=values.mean(axis=0).tolist() if len(values) else None,
        position_standard_deviation_neu_m=values.std(axis=0).tolist() if len(values) else None,
        exact_lag_s=lags, derivative_half_windows_s=summary)
    return result, derivative_rows


def build(root):
    by_recording = defaultdict(list)
    charges = 0
    seeds = {}
    with closing(ClosedStudy(root, 'data/'+IDENTITY)) as study:
        if (study.completion['state'] != 'complete' or study.summary['completed'] != len(study.tasks)
                or any(study.summary['charged'].values())):
            raise ValueError('closed GPS-only reconstruction pilot required')
        for path, sha in study.manifest['sources'].items():
            study.read('source-freeze/'+path, sha, raw=True)
        if study.manifest['inputs']['selection']['source'] != SELECTION:
            raise ValueError('unexpected pilot selection path')
        selection = study.input('selection')
        picks = {row['identity']: row for row in selection['selected']}
        for identity, task in study.tasks.items():
            envelope = study.envelope(identity)
            result = envelope['result']
            data = json.loads(gzip.decompress(study.input(task['input_key'], raw=True)))
            charge = study.artifact(identity, 'position-charge.json')
            solved = json.loads(gzip.decompress(study.artifact(identity, 'positions.json.gz', raw=True)))
            expected = [(record['tag'], method) for record in data['records'] for method in METHODS]
            seed = dict(tag=data['seed_tag'], ecef_m=data['seed_ecef_m'])
            source_identity = task['source_identity']
            if (result['observed_fit_starts'] != 0 or result['source_identity'] != source_identity
                    or charge['methods'] != list(METHODS)
                    or charge['seed_tag'] != seed['tag'] or charge['seed_ecef_m'] != seed['ecef_m']
                    or seeds.setdefault(source_identity, seed) != seed
                    or charge['gps_millisecond_tags'] != task['selected_tags']
                    or charge['maximum_iterations_per_start'] != MAX_ITERATIONS
                    or result['position_starts'] != len(solved)
                    or charge['charged_starts'] != len(solved) or len(solved) != task['position_starts']
                    or result['converged'] != sum(row['status'] == 'converged' for row in solved)
                    or [(row['gps_millisecond_tag'], row['method']) for row in solved] != expected):
                raise ValueError('position solve count, seed or epoch receipt changed')
            original = {record['tag']: record for record in data['records']}
            charges += charge['charged_starts']
            for row in solved:
                tag = row['gps_millisecond_tag']
                reference = original[tag]['reference']
                valid = row['status'] == 'converged'
                if (row['measurement_sha256'] != original[tag]['measurement']['payload_sha256']
                        or row.get('iterations', 0) > MAX_ITERATIONS
                        or row['used_as_initialization'] != (tag == seed['tag'])
                        or row['status'] not in ('converged', 'abstain')):
                    raise ValueError('position output measurement binding or limits changed')
                difference = row.get('difference_neu_m')
                if valid and not np.allclose(difference, receiver_difference(row['ecef_m'], reference),
                                             rtol=0., atol=1e-12):
                    raise ValueError('position difference does not replay')
                if not valid and difference is not None:
                    raise ValueError('an abstention acquired a position difference')
                slim = dict(segment_id=task['segment_id'], imu_type=picks[source_identity]['imu_type'],
                    method=row['method'], gps_millisecond_tag=tag, status=row['status'],
                    reason=row.get('reason'), iterations=row.get('iterations'),
                    observations=row.get('observations'), range_rms_m=row.get('range_rms_m'),
                    used_as_initialization=row['used_as_initialization'], difference_neu_m=difference)
                by_recording[source_identity, row['method']].append(slim)
        receipt = dict(study.completion, selection_sha256=study.manifest['inputs']['selection']['sha256'],
                       position_starts=charges, imu_fit_starts=0, scientific_decision='abstain')
    if charges != selection['position_solve_starts']:
        raise ValueError('frozen position allowance was not accounted for')
    detailed, derivatives, summary = [], [], []
    for (identity, method), rows in by_recording.items():
        rows.sort(key=lambda row: row['gps_millisecond_tag'])
        pick = picks[identity]
        if [row['gps_millisecond_tag'] for row in rows] != pick['gps_millisecond_tags']:
            raise ValueError('the scored method output omits frozen epochs')
        result, derivative = comparisons(rows)
        key = dict(segment_id=pick['segment_id'], imu_type=pick['imu_type'], method=method)
        summary.append(dict(key, **result, seed_gps_millisecond_tag=seeds[identity]['tag']))
        derivatives.extend(dict(key, **row) for row in derivative)
        detailed.extend(rows)
    return dict(receipt, comparisons=summary), detailed, derivatives


def _csv(rows, vector_fields):
    if not rows:
        return b''
    flat = []
    for row in rows:
        data = dict(row)
        for field, suffix in vector_fields:
            values = data.pop(field) or [None]*3
            data.update({f'{axis}_{suffix}': value for axis, value in zip(AXES, values, strict=True)})
        flat.append(data)
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=tuple(flat[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(flat)
    return stream.getvalue().encode()


def publish(root):
    receipt, rows, derivatives = build(root)
    output = {
        'gps-reconstruction-pilot-positions.csv': _csv(rows, (('difference_neu_m', 'difference_m'),)),
        'gps-reconstruction-pilot-derivatives.csv': _csv(derivatives, (
            ('velocity_neu_mps', 'velocity_difference_mps'),
            ('acceleration_neu_mps2', 'acceleration_difference_mps2'))),
    }
    receipt.update(output_sha256={name: digest(data) for name, data in output.items()},
                   reporter_sha256=digest(Path(__file__).read_bytes()))
    output['gps-reconstruction-pilot-receipt.json'] = encoded(receipt)
    for name, data in output.items():
        target = Path(root)/FOLDER/name
        if target.is_file() and target.read_bytes() != data:
            raise ValueError('sealed GPS reconstruction diagnostic changed')
        if not target.is_file():
            atomic(target, data)
    return receipt


if __name__ == '__main__':
    print(json.dumps(publish(Path.cwd()), sort_keys=True))
