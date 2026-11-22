# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propagate saved carrier-phase motion through the matched force comparison."""

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path

import numpy as np

from . import gnss_position as gps, ilvis0_gps_carrier_report as phase
from . import ilvis0_matched_force_average as average, ilvis0_matched_force_gain as gain
from .ilvis0_control_shards import runtime_environment
from .ilvis0_gps_force_comparison import POSITION_RECEIPT, _matching_positions
from .ilvis0_receiver_force import evaluate
from .studies.artifacts import digest, encoded

FOLDER = phase.FOLDER
SUPPORT = average.support
PLAN = FOLDER+'GPS_CARRIER_FORCE_PLAN.md'
FREEZE = FOLDER+'gps-carrier-force-freeze.json'
RECEIPT = FOLDER+'gps-carrier-force-receipt.json'
OUTPUT = FOLDER+'gps-carrier-force-windows.json.gz'
INPUTS = (phase.RECEIPT, phase.PAIRS, average.FREEZE, average.RESULT, average.OUTPUT,
          SUPPORT.RESULT, SUPPORT.OUTPUT, SUPPORT.WINDOWS, SUPPORT.WINDOW_RECEIPT,
          gain.FREEZE, gain.RESULT, POSITION_RECEIPT)


def centered_path(tags, target, center, pairs):
    """Integrate already solved ECEF increments around the common centre fix."""
    if len(tags) < 2 or target not in tags:
        raise ValueError('phase window requires an observed centre and at least two endpoints')
    increments = []
    for a, b in zip(tags, tags[1:]):
        row = pairs.get(a)
        if row is None or row['last_tag'] != b or row['status'] != 'converged':
            raise ValueError('complete adjacent phase displacements required')
        increments.append(row['displacement_ecef_m'])
    cumulative = np.vstack((np.zeros(3), np.cumsum(increments, axis=0)))
    index = tags.index(target)
    positions = gps.ecef(*center)+(cumulative-cumulative[index])
    coordinates = np.array([gps.geodetic(position) for position in positions])
    coordinates[index] = center
    coordinates[:, 1] = np.unwrap(coordinates[:, 1])
    return coordinates


def _checked_inputs(root):
    raw = {name: (root/name).read_bytes() for name in INPUTS}
    source = json.loads(raw[phase.RECEIPT])
    saved_gain = json.loads(raw[gain.RESULT])
    position = json.loads(raw[POSITION_RECEIPT])
    if (source['output_sha256'][phase.PAIRS] != digest(raw[phase.PAIRS])
            or source['imu_fit_starts'] or source['phase_supported_windows'] != phase.WINDOWS
            or saved_gain['freeze_sha256'] != digest(raw[gain.FREEZE])
            or saved_gain['model_cases'] != gain.MAX_CASES
            or source['provenance']['code_completion'] !=
            {k: position[k] for k in ('state', 'manifest_sha256', 'summary_sha256')}):
        raise ValueError('frozen carrier-phase, position and gain receipts required')
    for output, receipt in ((average.OUTPUT, average.RESULT),
                            (SUPPORT.OUTPUT, SUPPORT.RESULT), (SUPPORT.WINDOWS, SUPPORT.WINDOW_RECEIPT)):
        if json.loads(raw[receipt])['output_sha256'] != digest(raw[output]):
            raise ValueError('changed prior receiver support or force result')
    if json.loads(raw[average.RESULT])['freeze_sha256'] != digest(raw[average.FREEZE]):
        raise ValueError('changed prior packet interval freeze')
    pairs = json.loads(gzip.decompress(raw[phase.PAIRS]))
    if len(pairs) != source['pair_attempts']:
        raise ValueError('changed phase pair inventory')
    tracks = defaultdict(dict)
    for row in pairs:
        key, tag = row['segment_id'], row['first_tag']
        if tag in tracks[key]:
            raise ValueError('duplicate phase pair')
        tracks[key][tag] = row
    return raw, source, saved_gain, tracks


def _centers(jet):
    return {m: float(np.linalg.norm(evaluate(*jet, model=m, background_rate_rads=average.rate(m),
        gravity_mps2=average.GRAVITY, disc_radius_m=average.RADIUS)['specific_force_ned_mps2']))
        for m in average.MATCHED_MODELS}


def build(root, raw, source, saved_gain, pairs):
    models, fields = average.MATCHED_MODELS, average.FIELDS
    picks, tracks, completion = _matching_positions(root)
    if completion != source['provenance']['code_completion']:
        raise ValueError('carrier phase was evaluated against a different GPS position study')
    positions = {rec['segment_id']: tracks[rec['identity']] for rec in picks}
    tags = {key: sorted(by_tag) for key, by_tag in positions.items()}
    windows = [r for r in average._table(raw[SUPPORT.OUTPUT]) if r['state']=='supported']
    gps_windows = {(r['segment_id'], r['gps_millisecond_tag']): r for r in
        average._table(raw[SUPPORT.WINDOWS]) if float(r['half_window_s'])==SUPPORT.HALF_WINDOW_S}
    baseline = {(r['segment_id'], r['gps_millisecond_tag'], r['clock']): r for r in
                average._table(raw[average.OUTPUT]) if r['gps_stream']=='onboard'}
    gains = {(str(r['imu_type']), r['model']): r['training_gain'] for r in saved_gain['by_recorder_model']}
    if (len(windows) != average.WINDOW_COUNT or len(baseline) != len(windows)*len(SUPPORT.CLOCKS)
            or len(gains) != 2*len(models) or set(positions) != set(pairs)):
        raise ValueError('changed force comparison allowance')
    rows = []
    for window in windows:
        key = window['segment_id'], window['gps_millisecond_tag']
        segment, timestamp = key
        info, target = gps_windows[key], int(timestamp)
        lo, hi = int(info['first_used_tag']), int(info['last_used_tag'])
        cuts = tags[segment]
        selected = cuts[cuts.index(lo):cuts.index(hi)+1]
        if len(selected) != int(info['sample_count']) or info['state'] != 'evaluated':
            raise ValueError('different receiver support')
        coordinates = centered_path(selected, target, positions[segment][target]['onboard'], pairs[segment])
        jet = average.quadratic_weights((np.asarray(selected)-target)/1000.)@coordinates
        centers = _centers(jet)
        for clock in SUPPORT.CLOCKS:
            prior = baseline[(*key, clock)]
            if prior['side'] != window['side']:
                raise ValueError('changed training split')
            interval = (float(prior['interval_start_s']), float(prior['interval_end_s']))
            offset = SUPPORT.TIME_OFFSET_S
            means = {m: average.bound_average(jet, interval, offset_bounds_s=(-offset, offset),
                subdivisions=average.SUBDIVISIONS, model=m, background_rate_rads=average.rate(m),
                gravity_mps2=average.GRAVITY, disc_radius_m=average.RADIUS) for m in models}
            low = float(window[clock+'_lower_mps2'])
            original = {m: float(info[f'onboard_{m}_magnitude_mps2']) for m in models}
            shifts = {m: centers[m]-original[m] for m in models}
            held_gain = {m: gains[window['imu_type'], m] for m in models}
            rows.append(dict(segment_id=segment, gps_millisecond_tag=target, imu_type=window['imu_type'],
                side=window['side'], clock=clock, interval_s=interval, bounds_mps2=means,
                center_shift_mps2=shifts,
                sign_preserved={name: (means[g][0] > means[d][1] and original[g] > original[d])
                              or (means[g][1] < means[d][0] and original[g] < original[d])
                              for name, g, d in fields},
                shift_exceeds_onboard_shape_gap={name: max(abs(shifts[g]), abs(shifts[d])) > abs(original[g]-original[d])
                                                 for name, g, d in fields},
                fixed_gain_phase_violations={m: gain._violation([(low, means[m][1])], held_gain[m])[0] for m in models},
                fixed_gain_onboard_violations={m: gain._violation([(low, float(prior[m+'_upper_mps2']))], held_gain[m])[0]
                                               for m in models}))
    return rows


def main():
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    raw, source, saved_gain, pairs = _checked_inputs(root)
    sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_ilvis0_carrier_force.py')
    config = encoded(dict(sources={p: digest((root/p).read_bytes()) for p in source_closure(root, sources)},
        inputs={p: digest(value) for p, value in raw.items()}, environment=runtime_environment(),
        windows=average.WINDOW_COUNT, max_envelopes=average.WINDOW_COUNT*len(SUPPORT.CLOCKS)*len(average.MATCHED_MODELS),
        subdivisions=average.SUBDIVISIONS, models=list(average.MATCHED_MODELS), offsets_s=SUPPORT.TIME_OFFSET_S,
        numerical_threads=1, position_solves=0, imu_fit_starts=0))
    if args.action == 'freeze':
        SUPPORT._write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('changed carrier-force calculation freeze')
    rows = build(root, raw, source, saved_gain, pairs)
    groups = []
    for imu in ('8', '21'):
        for side in ('training', 'later'):
            group = [r for r in rows if (r['imu_type'], r['side']) == (imu, side)]
            counts = {}
            for key in ('sign_preserved', 'shift_exceeds_onboard_shape_gap', 'fixed_gain_phase_violations',
                        'fixed_gain_onboard_violations'):
                counts[key] = {m: sum(row[key][m] for row in group) for m in group[0][key]}
            shifts = [abs(v) for row in group for v in row['center_shift_mps2'].values()]
            groups.append(dict(imu_type=imu, side=side, window_clock_count=len(group),
                               center_shift_p95_mps2=float(np.percentile(shifts, 95)), **counts))
    payload = gzip.compress(encoded(rows), mtime=0)
    receipt = dict(freeze_sha256=digest(config), output_sha256=digest(payload), groups=groups,
        model_envelopes=len(rows)*len(average.MATCHED_MODELS), imu_fit_starts=0,
        gyro_observations_used=False, receiver_error_calibrated=False, scientific_decision='abstain')
    SUPPORT._write_equal(root/OUTPUT, payload)
    SUPPORT._write_equal(root/RECEIPT, encoded(receipt))
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
