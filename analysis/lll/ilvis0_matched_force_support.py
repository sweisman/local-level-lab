# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check saved accelerometer support and count bounds on matched GPS windows."""

import argparse
import csv
import gzip
import io
import json
from pathlib import Path
import platform

import numpy as np

from .ilvis0_increment_bounds import magnitude_bounds
from .ilvis0_matched_observed_inputs import CLOCKS, FOLDER, MAX_INTERVAL, RECEIPT, _write_equal
from .studies.artifacts import digest, encoded, safe_path


SOURCE = 'analysis/lll/ilvis0_matched_force_support.py'
TEST = 'analysis/tests/test_ilvis0_matched_force_support.py'
PLAN = FOLDER+'MATCHED_FORCE_SUPPORT_PLAN.md'
FREEZE = FOLDER+'matched-force-support-freeze.json'
WINDOWS = FOLDER+'gps-force-comparison-windows.csv.gz'
WINDOW_RECEIPT = FOLDER+'gps-force-comparison-receipt.json'
OUTPUT = FOLDER+'matched-force-support-windows.csv.gz'
RESULT = FOLDER+'matched-force-support-receipt.json'
MAX_WINDOWS = 1112
MAX_PACKETS = 225_000
MAX_WINDOW_PACKETS = 6200
HALF_WINDOW_S = 15.
TIME_OFFSET_S = .15
COUNT_ERROR = .5


def clock_envelopes(ends_by_clock, offset):
    """Return earliest starts and latest ends on each of the two clocks."""
    return tuple((np.r_[0., ends[:-1]]-offset, ends+offset) for ends in ends_by_clock)


def common_slice(envelopes, window):
    first = max(int(np.searchsorted(start, window[0], side='left')) for start, _ in envelopes)
    stop = min(int(np.searchsorted(end, window[1], side='right')) for _, end in envelopes)
    return slice(first, max(first, stop))


def force_summary(counts, periods, *, scale, clock):
    bounds = magnitude_bounds(counts, np.column_stack((periods, periods)),
        scale_mps_per_count=scale, count_uncertainty=COUNT_ERROR, period_hypothesis=clock)
    duration = float(np.sum(periods))
    return dict(support_s=duration,
        observed_packet_mean_mps2=float(np.sum(np.linalg.norm(counts, axis=1))*scale/duration),
        lower_mps2=bounds['time_weighted_magnitude_lower_mps2'],
        upper_mps2=bounds['time_weighted_magnitude_upper_mps2'])


def _inputs(root):
    raw = {name: safe_path(root, name).read_bytes() for name in (RECEIPT, WINDOWS, WINDOW_RECEIPT)}
    earlier = json.loads(raw[RECEIPT])
    windows = json.loads(raw[WINDOW_RECEIPT])
    if (earlier['position_parent'] != windows['position_parent'] or earlier['imu_fit_starts']
            or len(earlier['recordings']) != 2 or digest(raw[WINDOWS]) != windows['output_sha256']):
        raise ValueError('unchanged matched recording and GPS window receipts required')
    for case in earlier['recordings']:
        for key in ('packets.npy.gz', 'training.json', 'scoring.json', 'packet-provenance.json'):
            item = case['artifacts'][key]
            path = item['path']
            values = safe_path(root, path).read_bytes()
            if digest(values) != item['sha256']:
                raise ValueError('changed prepared material: '+path)
            raw[path] = values
    return earlier, raw


def configuration(root, raw):
    from .studies.dependencies import source_closure

    return dict(sources={name: digest((root/name).read_bytes()) for name in source_closure(root, (SOURCE, PLAN, TEST))},
        input_sha256={name: digest(values) for name, values in raw.items()},
        python=platform.python_version(), numpy=np.__version__, machine=platform.machine(),
        windows=MAX_WINDOWS, maximum_source_packets=MAX_PACKETS, maximum_window_packets=MAX_WINDOW_PACKETS,
        half_window_s=HALF_WINDOW_S, common_offset_s=TIME_OFFSET_S, count_error=COUNT_ERROR,
        clocks=list(CLOCKS), threads=1, fit_starts=0, continuous_force_upper_bound=False)


def _record(case, raw):
    def material(key):
        return raw[case['artifacts'][key]['path']]

    packets = np.load(io.BytesIO(gzip.decompress(material('packets.npy.gz'))), allow_pickle=False)
    provenance = json.loads(material('packet-provenance.json'))
    training, later = (json.loads(material(name)) for name in ('training.json', 'scoring.json'))
    times = np.asarray(training['query_times_s']+later['query_times_s'], float)
    tags = np.asarray(training['gps_tags_ms']+later['gps_tags_ms'], np.int64)
    cut = case['training_epochs']
    if (packets.shape != (case['source_packets'], 15) or len(times) != len(tags)
            or len(tags) != cut+case['scoring_epochs'] or len(training['gps_tags_ms']) != cut
            or np.any(np.diff(tags) <= 0) or not np.isfinite(times).all() or np.any(np.diff(times) <= 0.)
            or provenance['group1_observations_used'] or not provenance['all_original_integers_preserved']
            or provenance['source_sha256'] != case['source_sha256']):
        raise ValueError('original integer increment provenance and split required')
    integer_values = packets[:, 3:6]
    elapsed = packets[:, 2]
    if (not np.isfinite(integer_values).all() or np.any(integer_values != np.rint(integer_values))
            or np.any(integer_values < -2**31) or np.any(integer_values >= 2**31)
            or not np.isfinite(elapsed).all() or np.any(elapsed < .0025) or np.any(elapsed > MAX_INTERVAL)):
        raise ValueError('signed accelerometer counts and complete recorded intervals required')
    periods = (np.full(len(packets), .005), elapsed)
    ends = tuple(np.cumsum(durations) for durations in periods)
    return dict(tags=tags, times=times, cut=cut, imu_type=str(case['imu_type']),
        counts=integer_values.astype(np.int64), periods=periods,
        envelopes=clock_envelopes(ends, TIME_OFFSET_S), scale=provenance['velocity_scale_mps_per_count'])


def _window(row, record):
    tags, cut = record['tags'], record['cut']
    target = int(row['gps_millisecond_tag'])
    output = dict(segment_id=row['segment_id'], imu_type=row['imu_type'], gps_millisecond_tag=target,
                  state=row['state'], side=None, packet_first=None, packet_stop=None, packets=None)
    if row['state'] != 'evaluated':
        return output
    lo, hi = int(row['first_used_tag']), int(row['last_used_tag'])
    first = int(np.searchsorted(tags, lo))
    stop = int(np.searchsorted(tags, hi, side='right'))
    index = int(np.searchsorted(tags, target))
    if (not first <= index < stop or tags[first] != lo or tags[stop-1] != hi or tags[index] != target
            or stop-first != int(row['sample_count']) or np.any(np.diff(tags[first:stop]) > 1500)):
        raise ValueError('saved window differs from original receiver support')
    if first < cut < stop:
        return dict(output, state='crosses_cut')
    side = 'training' if stop <= cut else 'later'
    selection = common_slice(record['envelopes'], (record['times'][first], record['times'][stop-1]))
    count = selection.stop-selection.start
    if count == 0:
        return dict(output, state='no_common_packets', side=side)
    if count > MAX_WINDOW_PACKETS:
        raise ValueError('retained packet allowance exceeded')
    output.update(state='supported', side=side, packet_first=selection.start,
                  packet_stop=selection.stop, packets=count)
    counts = record['counts'][selection]
    for clock, periods in zip(CLOCKS, record['periods'], strict=True):
        for key, value in force_summary(counts, periods[selection], scale=record['scale'], clock=clock).items():
            output[clock+'_'+key] = value
    for field in ('zero', 'specified'):
        output['gps_'+field+'_abs_shape_gap_mps2'] = abs(float(row[f'onboard_{field}_globe_minus_disc_mps2']))
    return output


def _summary(rows, imu):
    selected = [row for row in rows if row['imu_type'] == imu and row['state'] == 'supported']
    widths = [row[CLOCKS[0]+'_upper_mps2']-row[CLOCKS[0]+'_lower_mps2'] for row in selected]
    shifts = [abs(row[CLOCKS[0]+'_observed_packet_mean_mps2']-row[CLOCKS[1]+'_observed_packet_mean_mps2'])
              for row in selected]
    return dict(imu_type=imu, training=sum(row['side']=='training' for row in selected),
        later=sum(row['side']=='later' for row in selected),
        minimum_packets=min(row['packets'] for row in selected),
        maximum_packets=max(row['packets'] for row in selected),
        median_nominal_count_width_mps2=float(np.median(widths)),
        median_abs_clock_change_mps2=float(np.median(shifts)),
        maximum_abs_clock_change_mps2=max(shifts),
        median_abs_zero_shape_gap_mps2=float(np.median([r['gps_zero_abs_shape_gap_mps2'] for r in selected])),
        median_abs_specified_shape_gap_mps2=float(np.median([r['gps_specified_abs_shape_gap_mps2'] for r in selected])))


def publish(root, earlier, raw, config):
    recorded = (root/FREEZE).read_bytes()
    if recorded != encoded(config):
        raise ValueError('packet and window calculation differs from its freeze')
    if sum(case['source_packets'] for case in earlier['recordings']) > MAX_PACKETS:
        raise ValueError('source packet allowance exceeded')
    records = {case['segment_id']: _record(case, raw) for case in earlier['recordings']}
    force_rows = csv.DictReader(io.StringIO(gzip.decompress(raw[WINDOWS]).decode()))
    rows = []
    for row in force_rows:
        if float(row['half_window_s']) != HALF_WINDOW_S:
            continue
        if len(rows) >= MAX_WINDOWS:
            raise ValueError('30-second window allowance exceeded')
        record = records[row['segment_id']]
        if record['imu_type'] != row['imu_type']:
            raise ValueError('window has a different recorder')
        rows.append(_window(row, record))
    if len(rows) != MAX_WINDOWS or len({(r['segment_id'], r['gps_millisecond_tag']) for r in rows}) != MAX_WINDOWS:
        raise ValueError('changed GPS window inventory')
    stream = io.StringIO(newline='')
    fields = list(dict.fromkeys(key for row in rows for key in row))
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    payload = gzip.compress(stream.getvalue().encode(), mtime=0)
    receipt = dict(freeze_sha256=digest(recorded), output_sha256=digest(payload), windows=len(rows),
        supported=sum(row['state']=='supported' for row in rows),
        crosses_cut=sum(row['state']=='crosses_cut' for row in rows),
        clocks=list(CLOCKS), imu=[_summary(rows, imu) for imu in ('8', '21')],
        averaged_gyro_values=False, gyro_observations_used=False, fused_navigation_used=False,
        continuous_force_upper_bound=False, fit_starts=0, scientific_decision='abstain')
    _write_equal(root/OUTPUT, payload)
    _write_equal(root/RESULT, encoded(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    earlier, raw = _inputs(root)
    config = configuration(root, raw)
    if args.action == 'freeze':
        content = encoded(config)
        _write_equal(root/FREEZE, content)
        print(digest(content))
    else:
        print(json.dumps(publish(root, earlier, raw, config), sort_keys=True))


if __name__ == '__main__':
    main()
