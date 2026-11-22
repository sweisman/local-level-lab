# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay bounded sampled-direction motion checks on two sealed recordings."""

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import ilvis0_force_path_order as paths
from .ilvis0_control_shards import runtime_environment
from .ilvis0_force_motion_history import motion_history
from .ilvis0_force_motion_screen import nominal_witness, screen
from .ilvis0_force_motion_triplets import force_in_fixed_frame
from .studies.artifacts import digest, encoded
from .studies.dependencies import source_closure


FOLDER = paths.FOLDER
PLAN = FOLDER+'RECORDED_MOTION_RATE_PLAN.md'
FREEZE = FOLDER+'recorded-motion-rate-freeze.json'
RESULT = FOLDER+'recorded-motion-rate-receipt.json'
TWISTS = 4096
CELLS = 4_000_000
DEGREE = 4
HISTORIES = 64


def rate_bracket(counts, required, times, *, twists):
    intervals = np.diff(times)
    length = np.linalg.norm(counts, axis=1)
    radius_counts = np.sqrt(3.)*paths.SUPPORT.COUNT_ERROR
    if np.any(length <= radius_counts):
        raise ValueError('packet direction is undefined under its count uncertainty')
    count_error = np.arcsin(radius_counts/length)
    errors = dict(body_direction_error_rad=count_error, frame_direction_error_rad=np.zeros(len(times)))
    pair = screen(counts, required, times, maximum_rate_rad_s=0., **errors)
    witness = nominal_witness(counts, required, times,
                              maximum_rate_rad_s=np.nextafter(np.pi/intervals.min(), np.inf))
    if not witness['nominal_witness_within_bound']:
        raise ValueError('could not verify the initial nominal motion path')
    lower = float(np.max(np.asarray(pair['necessary_turn_rad'])/intervals))
    upper = float(np.max(np.asarray(witness['turn_rad'])/intervals))
    if lower-upper > 1e-12:
        raise ValueError('inconsistent direction-rate bracket')
    initial = dict(initial_lower_rads=lower, initial_upper_rads=upper)
    threshold = (lower+upper)/2
    probe = motion_history(counts, required, times, maximum_rate_rad_s=threshold,
                           twists=twists, maximum_cells=CELLS, **errors)
    if probe['status'] == 'excluded':
        lower = threshold
    elif probe['status'] == 'nominal_witness':
        upper = min(upper, float(np.max(np.asarray(probe['sampled_turn_rad'])/intervals)))
    return dict(**initial, lower_rads=lower, upper_rads=upper,
                probe_rate_rads=threshold, probe_status=probe['status'], samples=len(times),
                span_s=float(times[-1]-times[0]), smallest_interval_s=float(intervals.min()),
                maximum_count_direction_error_rad=float(count_error.max()))


def collect(root, raw, source, pairs, records):
    grouped = defaultdict(list)
    selected = []
    for window, offsets, coordinates, _ in paths._paths(root, raw, source, pairs):
        if len(selected) >= paths.average.WINDOW_COUNT:
            raise ValueError('force evaluation budget exceeded')
        segment, side = window['segment_id'], window['side']
        record = records[segment]
        tag = int(window['gps_millisecond_tag'])
        index = int(np.searchsorted(record['tags'], tag))
        if index >= len(record['tags']) or record['tags'][index] != tag:
            raise ValueError('unchanged receiver time target required')
        target = record['times'][index]
        start, stop = int(window['packet_first']), int(window['packet_stop'])
        nominal = record['midpoints'][0][start:stop]
        packet = start+int(np.argmin(abs(nominal-target)))
        counts = record['counts'][packet]
        selected.append((segment, tag, side, packet))
        for track, positions in zip(paths.TRACKS, coordinates, strict=True):
            polynomial = paths.fit_path(offsets, positions, degree=DEGREE)
            for clock, midpoint in zip(paths.SUPPORT.CLOCKS, record['midpoints'], strict=True):
                elapsed = midpoint[packet]
                offset = elapsed-target
                if not offsets[0] <= offset <= offsets[-1]:
                    raise ValueError('packet midpoint is outside the unchanged GPS window')
                jet = paths.point_jet(polynomial, offset)
                for model in paths.average.MATCHED_MODELS:
                    force = paths.evaluate(*jet, **paths._settings(model))['specific_force_ned_mps2']
                    grouped[segment, side, track, clock, model].append((elapsed, counts, force, jet[0]))
    if len(selected) != paths.average.WINDOW_COUNT or len(grouped) != HISTORIES:
        raise ValueError('unchanged two-recording history inventory required')
    if sum(map(len, grouped.values())) != len(selected)*16:
        raise ValueError('missing or duplicated force-point evaluation')
    return selected, grouped


def build(root, raw, source, pairs, earlier):
    records = {}
    for case in earlier['recordings']:
        record = paths.SUPPORT._record(case, raw)
        if not 0 < len(record['counts']) <= paths.SUPPORT.MAX_PACKETS:
            raise ValueError('source packet budget exceeded')
        record['midpoints'] = tuple(np.cumsum(periods)-periods/2 for periods in record['periods'])
        records[case['segment_id']] = record
    selected, grouped = collect(root, raw, source, pairs, records)
    rows = []
    for (segment, side, track, clock, model), history in sorted(grouped.items()):
        times, counts, force, position = zip(*history, strict=True)
        required = force_in_fixed_frame(force, position, model=model)
        profile = rate_bracket(counts, required, times, twists=TWISTS)
        rows.append(dict(segment_id=segment, imu_type=records[segment]['imu_type'], side=side,
                         track=track, clock=clock, model=model, **profile))
    return dict(windows=len(selected), packet_selection_sha256=digest(encoded(selected)),
                rows=rows, force_point_evaluations=sum(map(len, grouped.values())),
                fit_starts=0, original_reads=0, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    raw, source, _, pairs = paths.carrier._checked_inputs(root)
    earlier, prepared = paths.SUPPORT._inputs(root)
    raw.update(prepared)
    own = Path(__file__).relative_to(root).as_posix()
    test = 'analysis/tests/test_ilvis0_recorded_motion_rate.py'
    config = encoded(dict(sources={name: digest((root/name).read_bytes())
            for name in source_closure(root, (own, PLAN, test))}, environment=runtime_environment(),
        inputs={name: digest(values) for name, values in raw.items()}, polynomial_degree=DEGREE,
        windows=paths.average.WINDOW_COUNT, maximum_path_approximations=1982,
        maximum_force_point_evaluations=15856, histories=HISTORIES, probe_twists=TWISTS,
        maximum_cells_per_probe=CELLS, threads=1, fit_starts=0))
    if args.action == 'freeze':
        paths.SUPPORT._write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('changed recorded motion-rate freeze')
    result = build(root, raw, source, pairs, earlier)
    payload = encoded(dict(result, freeze_sha256=digest(config)))
    paths.SUPPORT._write_equal(root/RESULT, payload)
    print(dict(windows=result['windows'], histories=len(result['rows']), sha256=digest(payload)))


if __name__ == '__main__':
    main()
