# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare force predictions on the saved matched GPS position streams."""

import argparse
from contextlib import closing
import csv
import gzip
import io
import json
from pathlib import Path
import platform

import numpy as np

from .ilvis0_gps_reconstruction_pilot import FOLDER, IDENTITY, METHODS, SELECTION
from .ilvis0_receiver_force import MATCHED_MODELS, evaluate
from .ilvis0_shared_gps_error import FIELDS, GRAVITY, RADIUS, quadratic_weights, rate
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


WINDOWS = (5., 10., 15.)
ONBOARD = 'onboard'
HEIGHT_CONTROLS = ('l1_height_only', 'dual_height_only')
TRACKS = (ONBOARD, *METHODS, *HEIGHT_CONTROLS)
SOURCE = 'analysis/lll/ilvis0_gps_force_comparison.py'
TEST = 'analysis/tests/test_ilvis0_gps_force_comparison.py'
PLAN = FOLDER+'GPS_FORCE_COMPARISON_PLAN.md'
FREEZE = FOLDER+'gps-force-comparison-freeze.json'
POSITION_RECEIPT = FOLDER+'gps-reconstruction-pilot-receipt.json'
MAX_EPOCHS = 1112
MAX_WINDOWS = MAX_EPOCHS*len(WINDOWS)
MAX_PREDICTIONS = MAX_WINDOWS*len(TRACKS)*len(MATCHED_MODELS)


def support(tags, target, half):
    """Use one support for all tracks and leave windows with gaps empty."""
    lower, upper = target-round(1000*half), target+round(1000*half)
    first = int(np.searchsorted(tags, lower))
    stop = int(np.searchsorted(tags, upper, side='right'))
    local = tags[first:stop]
    if (len(local) < 5 or tags[0] > lower or tags[-1] < upper
            or local[0]-lower > 1500 or upper-local[-1] > 1500
            or np.max(np.diff(local)) > 1500):
        return 'unsupported', first, stop
    return 'evaluated', first, stop


def window_forces(offsets, coordinates):
    """Use a single polynomial operator on all GPS variants."""
    weights = quadratic_weights(offsets)
    raw, l1, dual = (np.asarray(coordinates[name], float).copy() for name in (ONBOARD, *METHODS))
    if any(a.shape != (len(offsets), 3) or not np.isfinite(a).all() for a in (raw, l1, dual)):
        raise ValueError('matching finite coordinates on the same GPS support required')
    for array in (raw, l1, dual):
        array[:, 1] = np.unwrap(array[:, 1])
    swaps = [np.column_stack((raw[:, :2], array[:, 2])) for array in (l1, dual)]
    rows = {}
    for name, array in zip(TRACKS, (raw, l1, dual, *swaps), strict=True):
        jet = weights @ array
        rows[name] = {model: evaluate(*jet, model=model, background_rate_rads=rate(model),
                                     gravity_mps2=GRAVITY, disc_radius_m=RADIUS)['specific_force_ned_mps2']
                      for model in MATCHED_MODELS}
    return rows


def position_tracks(study, selection):
    """Read absolute coordinates only from the verified receiver solution artifacts."""
    tracks = {}
    picked = {row['identity']: row for row in selection['selected']}
    for identity, task in study.tasks.items():
        outcome = study.envelope(identity)['result']
        inputs = json.loads(gzip.decompress(study.input(task['input_key'], raw=True)))
        solutions = json.loads(gzip.decompress(study.artifact(identity, 'positions.json.gz', raw=True)))
        source = task['source_identity']
        if (outcome['source_identity'] != source or outcome['observed_fit_starts']
                or inputs['source_identity'] != source
                or inputs['source_sha256'] != picked[source]['source_sha256']
                or [row['tag'] for row in inputs['records']] != task['selected_tags']
                or [(row['gps_millisecond_tag'], row['method']) for row in solutions] !=
                [(tag, method) for tag in task['selected_tags'] for method in METHODS]):
            raise ValueError('position pilot comparison material differs from its frozen task')
        by_tag = tracks.setdefault(source, {})
        for record in inputs['records']:
            tag = record['tag']
            if tag in by_tag:
                raise ValueError('duplicate recorded GPS epoch')
            ref = record['reference']
            by_tag[tag] = {ONBOARD: [float(np.deg2rad(float(ref['latitude_deg']))),
                                     float(np.deg2rad(float(ref['longitude_deg']))),
                                     float(ref['ellipsoid_height_m'])]}
        for solution in solutions:
            tag = solution['gps_millisecond_tag']
            if solution['status'] == 'converged':
                by_tag[tag][solution['method']] = [solution[name] for name in
                    ('latitude_rad', 'longitude_rad', 'ellipsoid_height_m')]
            elif solution['status'] != 'abstain':
                raise ValueError('unknown original GPS status')
    if set(tracks) != set(picked) or any(sorted(by_tag) != picked[source]['gps_millisecond_tags']
            for source, by_tag in tracks.items()):
        raise ValueError('position stream changed epoch inventory')
    return tracks


def _matching_positions(root):
    verified = json.loads((root/POSITION_RECEIPT).read_bytes())
    with closing(ClosedStudy(root, 'data/'+IDENTITY)) as study:
        if (study.completion['state'] != 'complete'
                or any(verified[key] != value for key, value in study.completion.items())
                or verified['selection_sha256'] != study.manifest['inputs']['selection']['sha256']
                or verified['position_starts'] != 2*MAX_EPOCHS or verified['imu_fit_starts'] != 0):
            raise ValueError('original completed two-flight position study required')
        selection = study.input('selection')
        return selection['selected'], position_tracks(study, selection), study.completion


def _row(segment, target, half, available, tags, coordinates):
    state, first, stop = support(tags, target, half)
    row = dict(segment_id=segment['segment_id'], imu_type=segment['imu_type'],
               gps_millisecond_tag=target, half_window_s=half,
               state=state if available else 'position_unavailable', sample_count=stop-first,
               first_used_tag=None, last_used_tag=None)
    if row['state'] != 'evaluated':
        return row
    row.update(first_used_tag=int(tags[first]), last_used_tag=int(tags[stop-1]))
    local = (tags[first:stop]-target)/1000.
    forces = window_forces(local, {name: values[first:stop] for name, values in coordinates.items()})
    for name, candidates in forces.items():
        magnitude = {model: float(np.linalg.norm(vector)) for model, vector in candidates.items()}
        row.update({f'{name}_{model}_magnitude_mps2': value for model, value in magnitude.items()})
        for label, globe, disc in FIELDS:
            row[f'{name}_{label}_globe_minus_disc_mps2'] = magnitude[globe]-magnitude[disc]
        if name != ONBOARD:
            for model, vector in candidates.items():
                row[f'{name}_{model}_vector_shift_mps2'] = float(np.linalg.norm(vector-forces[ONBOARD][model]))
    return row


def _percentile(values, quantile):
    return float(np.percentile(values, quantile)) if len(values) else None


def _summary(rows):
    by_window = []
    for imu in ('8', '21'):
        for half in WINDOWS:
            group = [row for row in rows if row['imu_type'] == imu and row['half_window_s'] == half]
            selected = [row for row in group if row['state'] == 'evaluated']
            result = dict(imu_type=imu, half_window_s=half, target_count=len(group),
                          evaluated=len(selected), position_unavailable=sum(
                              row['state'] == 'position_unavailable' for row in group),
                          contrasts=[])
            for label, _, _ in FIELDS:
                key = f'{label}_globe_minus_disc_mps2'
                prior = np.array([row[f'{ONBOARD}_{key}'] for row in selected])
                for track in TRACKS[1:]:
                    changed = np.array([row[f'{track}_{key}'] for row in selected])
                    error = abs(changed-prior)
                    forces = [abs(row[f'{track}_{model}_magnitude_mps2']-
                                  row[f'{ONBOARD}_{model}_magnitude_mps2'])
                              for row in selected for model in MATCHED_MODELS]
                    result['contrasts'].append(dict(field=label, track=track,
                        sign_reversals=int(np.count_nonzero(prior*changed < 0)),
                        ties_in_either=int(np.count_nonzero((prior == 0.) | (changed == 0.))),
                        median_abs_onboard_contrast_mps2=_percentile(abs(prior), 50.),
                        p95_abs_contrast_change_mps2=_percentile(error, 95.),
                        max_abs_contrast_change_mps2=float(error.max()) if len(error) else None,
                        p95_individual_force_change_mps2=_percentile(forces, 95.)))
            by_window.append(result)
    return by_window


def build(root):
    picks, saved, completion = _matching_positions(root)
    if sum(len(pick['gps_millisecond_tags']) for pick in picks) != MAX_EPOCHS:
        raise ValueError('changed GPS force window allowance')
    rows = []
    for pick in picks:
        by_time = saved[pick['identity']]
        tags = np.array(sorted(t for t, variants in by_time.items() if len(variants) == 3), dtype=np.int64)
        coordinates = {name: np.array([by_time[t][name] for t in tags], dtype=float)
                       for name in (ONBOARD, *METHODS)}
        for target in pick['gps_millisecond_tags']:
            for half in WINDOWS:
                rows.append(_row(pick, target, half, len(by_time[target]) == 3, tags, coordinates))
    evaluated = sum(row['state'] == 'evaluated' for row in rows)
    if len(rows) != MAX_WINDOWS or evaluated*len(TRACKS)*len(MATCHED_MODELS) > MAX_PREDICTIONS:
        raise ValueError('position-only prediction ceiling exceeded')
    result = dict(position_parent=completion, windows=len(rows), evaluated=evaluated,
                  force_predictions=evaluated*len(TRACKS)*len(MATCHED_MODELS),
                  position_solves=0, imu_fit_starts=0, scientific_decision='abstain',
                  comparisons=_summary(rows))
    return result, rows


def _configuration(root):
    from .studies.dependencies import source_closure

    return dict(sources_sha256={name: digest((root/name).read_bytes())
                                for name in source_closure(root, (SOURCE, TEST, PLAN))},
                receipt_sha256=digest((root/POSITION_RECEIPT).read_bytes()),
                selection_sha256=digest((root/SELECTION).read_bytes()),
                python=platform.python_version(), numpy=np.__version__, machine=platform.machine(),
                numerical_threads=1, position_solves=0, imu_fit_starts=0,
                maximum_windows=MAX_WINDOWS, maximum_force_predictions=MAX_PREDICTIONS)


def _write_equal(path, content):
    if path.is_file():
        if path.read_bytes() != content:
            raise ValueError('sealed force comparison differs: '+str(path))
    else:
        atomic(path, content)


def publish(root):
    freeze = (root/FREEZE).read_bytes()
    if freeze != encoded(_configuration(root)):
        raise ValueError('GPS force comparison differs from its frozen allowances')
    receipt, rows = build(root)
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(key for row in rows for key in row)),
                            lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    payload = gzip.compress(stream.getvalue().encode(), mtime=0)
    receipt.update(output_sha256=digest(payload), freeze_sha256=digest(freeze))
    _write_equal(root/FOLDER/'gps-force-comparison-windows.csv.gz', payload)
    _write_equal(root/FOLDER/'gps-force-comparison-receipt.json', encoded(receipt))
    return {name: value for name, value in receipt.items() if name != 'comparisons'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'freeze':
        configuration = encoded(_configuration(root))
        _write_equal(root/FREEZE, configuration)
        print(digest(configuration))
    else:
        print(json.dumps(publish(root), sort_keys=True))
