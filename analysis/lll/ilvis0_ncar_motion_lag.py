# SPDX-License-Identifier: AGPL-3.0-or-later
"""Whole-second rotation compared again with the gyro windows moved by fixed time labels.

The first aircraft-record comparison found the two GPS tracks a nearly
constant fraction of a second apart. This repeats only its rotation part,
with the gyro windows moved by that GPS lag and by the middle of a
one-second average. No Earth model is evaluated.
"""
import argparse
from datetime import datetime, timedelta
import gzip
import json
import math
from pathlib import Path

from . import ilvis0_ncar_motion_match as match, ilvis0_review_study as review, ilvis0_stretch_checks as checks
from .ilvis0_ncar_rf04 import ATTITUDE, utc_string
from .ilvis0_paired_gyro_clock import CLOCKS
from .ilvis0_rf04_motion_match import WIDTHS, _stats, packet_windows, prefix_rotations

ID = 'ilvis0-ncar-motion-lag-v1'
FOLDER = match.FOLDER
ADAPTER = 'analysis/lll/ilvis0_ncar_motion_lag.py'
TEST = 'analysis/tests/test_ilvis0_ncar_motion_lag.py'
PLAN = FOLDER+'MOTION_LAG_PLAN.md'
PARENT = FOLDER+'motion-match-result.json'
REQUEST = FOLDER+'lag-qualification.json'
TEST_REPORT = FOLDER+'lag-tests.xml'
SCOPE = 'whole-second rotation at fixed time-label shifts on selected NASA stretches; no Earth-model fits'
# Fifty samples a second starting on the labelled second have their middle 0.49 s later.
AVERAGE_S = .49
SHIFTS = ('none', 'gps_lag', 'one_second_average')
COMPARISONS = len(CLOCKS)*len(SHIFTS)*len(WIDTHS)
WALL_S = 3600
TESTS = ('test_a_known_label_delay_is_matched_only_at_its_own_shift',
         'test_tasks_carry_the_saved_gps_lag_and_declared_steps',
         'test_unshifted_windows_reproduce_the_closed_comparison')


def shifts(gps_lag_s):
    if not .2 < gps_lag_s < .7:
        raise ValueError('a saved GPS lag of a fraction of a second is required')
    return dict(none=0., gps_lag=float(gps_lag_s), one_second_average=AVERAGE_S)


def tasks(root):
    """The 32 compared stretches, each with its own GPS lag from the closed comparison."""
    root = Path(root)
    parent = json.loads((root/PARENT).read_bytes())
    lags = {row['segment_id']: row['lag_median_s'] for row in parent['rows'] if row['compared']}
    out = []
    for task in match.tasks(root):
        seconds = task['seconds']
        steps = 2*task['native_packets']+len(CLOCKS)*len(SHIFTS)*sum((seconds-1)//w for w in WIDTHS)
        out.append(dict(task, gps_lag_s=lags[task['identity']],
            limits=dict(native_calls=0, packet_visits=0, bound_calls=2+COMPARISONS, bound_steps=steps)))
    return out


def code_sources(root):
    return review.code_sources(root, ADAPTER, TEST, 'analysis/lll/ncar_aircraft_records.py')


def request(root):
    return review.request(root, sources=code_sources(root), output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .studies.artifacts import digest

    root = Path(root).resolve()
    rows = tasks(root)
    inputs = dict(parent=PARENT, intake=match.INTAKE, selection=checks.SELECTION, contexts=checks.CONTEXTS,
                  analytics=checks.ANALYTICS, packets=checks.PACKETS)
    for row in rows:
        path = match.EXTRACTS+row['identity']+'.json'
        if digest((root/path).read_bytes()) != row['extract_sha256']:
            raise ValueError('saved aircraft extract differs from the intake')
        inputs[row['input_key']] = path
    return review.prepare(root, identity=ID, scope=SCOPE, adapter=ADAPTER, plan=PLAN, sources=code_sources(root),
        qualification=REQUEST, tests=TESTS, inputs=inputs, tasks=rows, wall_s=WALL_S)


def compare(rows, first, values, moved, *, reserve):
    """Whole-window rotation differences with the gyro windows moved by each named shift."""
    import numpy as np
    from scipy.spatial.transform import Rotation

    reserve(bound_calls=1, bound_steps=len(values))
    reference = Rotation.from_euler('ZYX', [[row[key] for key in reversed(ATTITUDE)] for row in rows], degrees=True)
    prefix = prefix_rotations(values[:, 9:12])
    stamps, periods = values[:, 1]-first, values[:, 2]
    clocks = dict(header_elapsed=(stamps, periods),
                  nominal_200Hz=(stamps[0]-periods[0]+.005*np.arange(1, len(values)+1), np.full(len(values), .005)))
    comparisons = []
    for clock in CLOCKS:
        for name in SHIFTS:
            for width in WIDTHS:
                starts = np.arange(0, len(rows)-width, width)
                reserve(bound_calls=1, bound_steps=len(starts))
                entry = dict(clock=clock, shift=name, shift_s=moved[name], window_s=width, error=None)
                try:
                    actual, coverage = packet_windows(prefix, *clocks[clock], starts+moved[name], width)
                    good = coverage >= width-.015-1e-8
                    expected = reference[starts].inv()*reference[starts+width]
                    entry.update(windows=int(good.sum()), omitted=int((~good).sum()),
                        rotation_difference_deg=_stats(np.rad2deg((expected[good].inv()*actual[good]).magnitude())),
                        aircraft_rotation_deg=_stats(np.rad2deg(expected[good].magnitude())),
                        group4_rotation_deg=_stats(np.rad2deg(actual[good].magnitude())))
                except (ValueError, IndexError) as error:
                    entry['error'] = str(error) or type(error).__name__
                comparisons.append(entry)
    return comparisons


def evaluate(task, context):
    from .studies.artifacts import digest

    if context.manifest['scope'] != SCOPE:
        raise ValueError('unchanged comparison-only scope required')
    raw = context.input_path(task['input_key']).read_bytes()
    extract = json.loads(raw)
    rows = extract['rows']
    with gzip.open(context.input_path('selection'), 'rt') as stream:
        segment, = (row['segment'] for row in json.load(stream)['selected']
                    if row['segment']['segment_id'] == task['identity'])
    parent = json.loads(context.input_path('parent').read_bytes())
    saved, = (row for row in parent['rows'] if row['segment_id'] == task['identity'])
    first = match.week_second(rows[0]['utc']) if rows else None
    origin = datetime.fromisoformat(rows[0]['utc'].replace('Z', '+00:00')) if rows else None
    if (digest(raw) != task['extract_sha256'] or extract['segment_id'] != task['identity']
            or len(rows) != task['seconds'] or first != math.ceil(segment['start_s'])
            or saved['lag_median_s'] != task['gps_lag_s'] or not saved['compared']
            or [row['utc'] for row in rows] != [utc_string(origin+timedelta(seconds=i)) for i in range(len(rows))]
            or any(row[key] is None for row in rows for key in ATTITUDE)):
        raise ValueError('complete consecutive aircraft seconds and the saved GPS lag are required')
    context.charge(bound_calls=1, bound_steps=task['native_packets'])
    values, _, _, provenance = checks.load_stretch(task, context)
    if provenance['group1_observations_used']:
        raise ValueError('the original recorded stream is required')
    comparisons = compare(rows, first, values, shifts(task['gps_lag_s']), reserve=context.charge)
    return dict(identity=task['identity'], aircraft_file=task['aircraft_file'], date=task['date'],
        seconds=len(rows), gps_lag_s=task['gps_lag_s'], comparisons=comparisons,
        passed=all(entry['error'] is None for entry in comparisons),
        scientific_decision='abstain', new_fits=0, reserved_reads=0,
        independent_peak_rate_upper_bound_established=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
