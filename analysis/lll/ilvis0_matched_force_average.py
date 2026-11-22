# SPDX-License-Identifier: AGPL-3.0-or-later
"""Enclose GPS-derived force means over the archived common packet support."""

import argparse
import csv
import gzip
import io
import json
from pathlib import Path
import platform

import numpy as np

from . import ilvis0_matched_force_support as support
from .ilvis0_force_support_average import bound_average
from .ilvis0_matched_observed_inputs import TRACKS
from .ilvis0_receiver_force import MATCHED_MODELS
from .ilvis0_shared_gps_error import FIELDS, GRAVITY, RADIUS, quadratic_weights, rate
from .studies.artifacts import digest, encoded


SOURCE = 'analysis/lll/ilvis0_matched_force_average.py'
TEST = 'analysis/tests/test_ilvis0_matched_force_average.py'
PLAN = support.FOLDER+'MATCHED_FORCE_AVERAGE_PLAN.md'
FREEZE = support.FOLDER+'matched-force-average-freeze.json'
OUTPUT = support.FOLDER+'matched-force-average-windows.csv.gz'
RESULT = support.FOLDER+'matched-force-average-receipt.json'
SUBDIVISIONS = 8
WINDOW_COUNT = 991


def checked_interval(ends, selected, receiver, offset, target):
    if not 0 <= selected.start < selected.stop <= len(ends):
        raise ValueError('nonempty retained whole-packet range required')
    start = 0. if selected.start == 0 else ends[selected.start-1]
    end = ends[selected.stop-1]
    if start-offset < receiver[0] or end+offset > receiver[1]:
        raise ValueError('retained interval exceeds receiver offset support')
    return start-target, end-target


def shape_interval(globe, disc):
    return float(np.nextafter(globe[0]-disc[1], -np.inf)), float(np.nextafter(globe[1]-disc[0], np.inf))


def _table(raw):
    return csv.DictReader(io.StringIO(gzip.decompress(raw).decode()))


def _configuration(root, inputs):
    from .studies.dependencies import source_closure

    return dict(sources={name: digest((root/name).read_bytes()) for name in source_closure(root, (SOURCE, PLAN, TEST))},
        inputs={name: digest(raw) for name, raw in inputs.items()},
        environment=dict(python=platform.python_version(), numpy=np.__version__, machine=platform.machine()),
        windows=WINDOW_COUNT, subdivisions=SUBDIVISIONS, models=list(MATCHED_MODELS),
        clock_hypotheses=list(support.CLOCKS), gps_streams=list(TRACKS),
        maximum_force_envelopes=WINDOW_COUNT*len(support.CLOCKS)*len(TRACKS)*len(MATCHED_MODELS),
        gravity_mps2=GRAVITY, disc_radius_m=RADIUS, time_offset_s=support.TIME_OFFSET_S,
        numerical_threads=1, fit_starts=0)


def _record(case, raw):
    record = support._record(case, raw)
    def read(alias):
        return json.loads(raw[case['artifacts'][alias]['path']])

    earlier, later = read('training.json'), read('scoring.json')
    coords = {track: np.asarray(earlier['coordinates'][track]+later['coordinates'][track], float)
              for track in TRACKS}
    if any(values.shape != (len(record['times']), 3) or not np.isfinite(values).all()
           for values in coords.values()):
        raise ValueError('finite matched three-coordinate receiver streams required')
    return dict(record, coordinates=coords, ends=tuple(np.cumsum(periods) for periods in record['periods']))


def _window(window, gps_window, record):
    tags, times = record['tags'], record['times']
    lo = int(np.searchsorted(tags, int(gps_window['first_used_tag'])))
    hi = int(np.searchsorted(tags, int(gps_window['last_used_tag']), side='right'))
    target = int(np.searchsorted(tags, int(window['gps_millisecond_tag'])))
    if (not lo <= target < hi or hi-lo != int(gps_window['sample_count'])
            or lo < record['cut'] < hi
            or window['side'] != ('training' if hi <= record['cut'] else 'later')):
        raise ValueError('the receiver support changes or crosses the saved cut')
    receiver = (times[lo], times[hi-1])
    selected = slice(int(window['packet_first']), int(window['packet_stop']))
    if selected != support.common_slice(record['envelopes'], receiver):
        raise ValueError('the packet support changed')
    weights = quadratic_weights((tags[lo:hi]-tags[target])/1000.)
    offset = support.TIME_OFFSET_S
    for clock, ends in zip(support.CLOCKS, record['ends'], strict=True):
        interval = checked_interval(ends, selected, receiver, offset, times[target])
        for track, source in record['coordinates'].items():
            local = source[lo:hi].copy()
            local[:, 1] = np.unwrap(local[:, 1])
            jet = weights @ local
            row = {key: window[key] for key in ('segment_id', 'imu_type', 'gps_millisecond_tag', 'side')}
            row.update(clock=clock, gps_stream=track, interval_start_s=interval[0], interval_end_s=interval[1])
            means = {}
            for model in MATCHED_MODELS:
                bounds = bound_average(jet, interval, offset_bounds_s=(-offset, offset),
                    subdivisions=SUBDIVISIONS, model=model, background_rate_rads=rate(model),
                    gravity_mps2=GRAVITY, disc_radius_m=RADIUS)
                center = float(gps_window[f'{track}_{model}_magnitude_mps2'])
                row[model+'_lower_mps2'], row[model+'_upper_mps2'] = bounds
                row[model+'_maximum_center_difference_mps2'] = max(abs(value-center) for value in bounds)
                means[model] = bounds
            for label, globe, disc in FIELDS:
                low, high = shape_interval(means[globe], means[disc])
                center = float(gps_window[f'{track}_{label}_globe_minus_disc_mps2'])
                row[label+'_shape_lower_mps2'], row[label+'_shape_upper_mps2'] = low, high
                row[label+'_same_sign'] = (low > 0. and center > 0.) or (high < 0. and center < 0.)
            yield row


def build(earlier, raw):
    previous = json.loads(raw[support.RESULT])
    if (digest(raw[support.OUTPUT]) != previous['output_sha256']
            or digest(raw[support.FREEZE]) != previous['freeze_sha256']
            or previous['supported'] != WINDOW_COUNT or previous['fit_starts']):
        raise ValueError('exact sealed packet support required')
    records = {case['segment_id']: _record(case, raw) for case in earlier['recordings']}
    gps = {(entry['segment_id'], entry['gps_millisecond_tag']): entry
           for entry in _table(raw[support.WINDOWS]) if float(entry['half_window_s']) == support.HALF_WINDOW_S}
    seen = set()
    rows = []
    for window in _table(raw[support.OUTPUT]):
        if window['state'] != 'supported':
            continue
        key = (window['segment_id'], window['gps_millisecond_tag'])
        if key in seen or len(seen) >= WINDOW_COUNT or gps[key]['state'] != 'evaluated':
            raise ValueError('changed supported window inventory')
        seen.add(key)
        rows.extend(_window(window, gps[key], records[key[0]]))
    if len(seen) != WINDOW_COUNT or len(rows) != WINDOW_COUNT*len(TRACKS)*len(support.CLOCKS):
        raise ValueError('incomplete recorded average calculation')
    return rows


def publish(root, earlier, raw, config):
    freeze = (root/FREEZE).read_bytes()
    if freeze != encoded(config):
        raise ValueError('average calculation differs from the source and input freeze')
    rows = build(earlier, raw)
    groups = []
    for imu in ('8', '21'):
        group = [row for row in rows if row['imu_type'] == imu]
        differences = [row[model+'_maximum_center_difference_mps2']
                       for row in group for model in MATCHED_MODELS]
        groups.append(dict(imu_type=imu, window_clock_stream_cases=len(group),
            zero_sign_preserved=sum(row['zero_same_sign'] for row in group),
            specified_sign_preserved=sum(row['specified_same_sign'] for row in group),
            median_maximum_center_difference_mps2=float(np.median(differences)),
            maximum_center_difference_mps2=max(differences)))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    payload = gzip.compress(stream.getvalue().encode(), mtime=0)
    receipt = dict(freeze_sha256=digest(freeze), output_sha256=digest(payload), windows=WINDOW_COUNT,
        model_envelopes=len(rows)*len(MATCHED_MODELS), interval_evaluations=len(rows)*len(MATCHED_MODELS)*SUBDIVISIONS,
        by_recorder=groups, receiver_error_calibrated=False, gyro_observations_used=False,
        fused_navigation_used=False, fit_starts=0, scientific_decision='abstain')
    support._write_equal(root/OUTPUT, payload)
    support._write_equal(root/RESULT, encoded(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    earlier, raw = support._inputs(root)
    raw.update({path: (root/path).read_bytes() for path in (support.FREEZE, support.OUTPUT, support.RESULT)})
    config = _configuration(root, raw)
    if args.action == 'freeze':
        content = encoded(config)
        support._write_equal(root/FREEZE, content)
        print(digest(content))
    else:
        print(json.dumps(publish(root, earlier, raw, config), sort_keys=True))


if __name__ == '__main__':
    main()
