# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tables for the review checks, written only from closed studies. Nothing is refitted."""
import argparse
from contextlib import closing
import csv
import gzip
import io
import json
from pathlib import Path

from . import ilvis0_highspeed_alignment_ablation as ablation, ilvis0_ncar_motion_match as motion
from . import ilvis0_stretch_checks as checks
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy

DATES = 'docs/ilvis0-exploratory-20261008/corpus-inventory.csv'


def _table(rows, columns):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator='\n', extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def _complete(study):
    if study.completion['state'] != 'complete' or len(study.rows) != len(study.tasks):
        raise ValueError('a complete closed study is required')


def classify(recovered, published):
    """Place one recovered interval against the published stretches of the same file."""
    start, end = recovered['start_s'], recovered['end_s']
    if any((start, end) == (row['start_s'], row['end_s']) for row in published):
        return 'published'
    if any(start < row['end_s'] and row['start_s'] < end for row in published):
        return 'overlaps_published'
    return 'additional'


def selection(root):
    """Compare the selection repeated without the alignment flag with the published 53."""
    with gzip.open(root/checks.SELECTION, 'rt') as stream:
        chosen = json.load(stream)['selected']
    published = {}
    for row in chosen:
        published.setdefault(row['task'], []).append(row['segment'])
    with (root/DATES).open(newline='') as stream:
        dates = {row['task']: row['embedded_dates'] for row in csv.DictReader(stream)}
    rows, unsupported, rejections = [], [], {}
    with closing(ClosedStudy(root, 'data/'+ablation.ID)) as study:
        _complete(study)
        for identity in sorted(study.tasks):
            result = study.envelope(identity)['result']
            saved = study.artifact(identity, 'inventory.json')
            if not result['passed']:
                unsupported.append(dict(task=identity, filename=saved['filename'], reason=saved.get('reason')))
                continue
            for key, count in saved['rejections'].items():
                rejections[key] = rejections.get(key, 0)+count
            for segment in saved['segments']:
                rows.append(dict(task=identity, filename=saved['filename'], file_dates=dates[identity],
                    start_week_s=segment['start_s'], end_week_s=segment['end_s'],
                    duration_s=segment['duration_s'], imu_type=segment['imu_type'],
                    time_types=segment['time_types'],
                    minimum_ground_speed_kmh=segment['minimum_receiver_ground_speed_kmh'],
                    median_ground_speed_kmh=segment['median_receiver_ground_speed_kmh'],
                    relation=classify(segment, published.get(identity, []))))
        completion, total = study.completion, len(study.tasks)
    found = {(row['task'], row['start_week_s'], row['end_week_s']) for row in rows}
    missing = [dict(task=task, segment_id=segment['segment_id']) for task, segments in sorted(published.items())
               for segment in segments if (task, segment['start_s'], segment['end_s']) not in found]
    counts = {name: sum(row['relation'] == name for row in rows)
              for name in ('published', 'overlaps_published', 'additional')}
    extra = [row for row in rows if row['relation'] != 'published']
    value = dict(study=ablation.ID, files=total, files_scanned=total-len(unsupported),
        files_not_readable=unsupported, intervals=len(rows), relation_counts=counts,
        published_stretches=len(chosen), published_not_reproduced=missing,
        additional_minutes=sum(row['duration_s'] for row in rows if row['relation'] == 'additional')/60,
        additional_file_dates=sorted({row['file_dates'] for row in rows if row['relation'] == 'additional'}),
        rejections=dict(sorted(rejections.items())), completion=completion,
        earth_model_fits=0, gyro_residuals_inspected=False, scientific_decision='abstain')
    _write_equal(root/(ablation.FOLDER+'result.json'), encoded(value))
    _write_equal(root/(ablation.FOLDER+'other-intervals.csv'), _table(extra, [
        'task', 'filename', 'file_dates', 'start_week_s', 'end_week_s', 'duration_s', 'imu_type', 'time_types',
        'minimum_ground_speed_kmh', 'median_ground_speed_kmh', 'relation']))
    return {key: value[key] for key in ('intervals', 'relation_counts', 'published_not_reproduced',
                                        'additional_minutes', 'additional_file_dates')} | dict(
        not_readable=len(unsupported))


def motion_match(root):
    """One row per stretch from the closed aircraft-record comparison."""
    rows = []
    with closing(ClosedStudy(root, 'data/'+motion.ID)) as study:
        _complete(study)
        for identity in sorted(study.tasks):
            envelope = study.envelope(identity)
            result = envelope['result']
            if envelope['charged'] != study.tasks[identity]['limits'] and result['passed']:
                raise ValueError('a passing stretch must use exactly its declared steps')
            row = dict(segment_id=identity, date=result['date'], aircraft_file=result['aircraft_file'],
                       seconds=result['seconds'], compared=result['passed'], reason=result.get('reason'))
            if 'horizontal_separation_m' in result:
                row.update(matched_receiver_seconds=result['matched_receiver_seconds'],
                    horizontal_median_m=result['horizontal_separation_m']['median'],
                    horizontal_maximum_m=result['horizontal_separation_m']['maximum'],
                    along_track_median_m=result.get('along_track_median_m'),
                    right_of_track_median_m=result.get('right_of_track_median_m'),
                    lag_median_s=result.get('lag_median_s'),
                    ground_speed_median_mps=result.get('ground_speed_median_mps'),
                    relative_height_rms_m=result['relative_height_difference_m']['rms'])
                for entry in result['comparisons']:
                    if entry['clock'] == 'header_elapsed' and entry['error'] is None:
                        shift = {0.: '', -.08: '_80ms_earlier', .08: '_80ms_later'}[entry['shift_s']]
                        name = f"rotation_difference_rms_{entry['window_s']}s{shift}_deg"
                        row[name] = entry['rotation_difference_deg']['rms']
                        if not shift:
                            row[f"aircraft_rotation_rms_{entry['window_s']}s_deg"] = entry['aircraft_rotation_deg']['rms']
                            row[f"imu_rotation_rms_{entry['window_s']}s_deg"] = entry['group4_rotation_deg']['rms']
                row['comparison_errors'] = sum(entry['error'] is not None for entry in result['comparisons'])
            rows.append(row)
        completion = study.completion
    columns = sorted({key for row in rows for key in row}, key=lambda key: (
        key not in ('segment_id', 'date', 'aircraft_file', 'seconds', 'compared', 'reason'), key))
    value = dict(study=motion.ID, stretches=len(rows), compared=sum(row['compared'] for row in rows),
        rows=rows, completion=completion, new_fits=0, scientific_decision='abstain')
    _write_equal(root/(motion.FOLDER+'motion-match-result.json'), encoded(value))
    _write_equal(root/(motion.FOLDER+'motion-match.csv'), _table(rows, columns))
    return dict(stretches=len(rows), compared=value['compared'])


def motion_lag(root):
    """Rotation differences at the three fixed shifts, one row per stretch."""
    from . import ilvis0_ncar_motion_lag as lag
    from statistics import median

    rows = []
    with closing(ClosedStudy(root, 'data/'+lag.ID)) as study:
        _complete(study)
        for identity in sorted(study.tasks):
            result = study.envelope(identity)['result']
            row = dict(segment_id=identity, date=result['date'], gps_lag_s=result['gps_lag_s'],
                       compared=result['passed'])
            for entry in result['comparisons']:
                if entry['clock'] == 'header_elapsed' and entry['error'] is None:
                    row[f"difference_rms_{entry['window_s']}s_{entry['shift']}_deg"] = (
                        entry['rotation_difference_deg']['rms'])
                    if entry['shift'] == 'none':
                        row[f"aircraft_rotation_rms_{entry['window_s']}s_deg"] = entry['aircraft_rotation_deg']['rms']
            rows.append(row)
        completion = study.completion
    summary = {}
    for width in (1, 5, 10):
        base = [row[f'difference_rms_{width}s_none_deg'] for row in rows]
        turning = [row[f'aircraft_rotation_rms_{width}s_deg'] for row in rows]
        entry = dict(aircraft_rotation_median_deg=median(turning))
        for name in lag.SHIFTS:
            values = [row[f'difference_rms_{width}s_{name}_deg'] for row in rows]
            entry[name] = dict(minimum_deg=min(values), median_deg=median(values), maximum_deg=max(values),
                stretches_lower_than_unshifted=sum(a < b for a, b in zip(values, base)),
                median_share_of_turning=median(a/b for a, b in zip(values, turning)))
        summary[f'{width}s'] = entry
    value = dict(study=lag.ID, stretches=len(rows), compared=sum(row['compared'] for row in rows),
        summary=summary, rows=rows, completion=completion, new_fits=0, scientific_decision='abstain')
    _write_equal(root/(lag.FOLDER+'motion-lag-result.json'), encoded(value))
    columns = ['segment_id', 'date', 'gps_lag_s', 'compared']+sorted(
        {key for row in rows for key in row}-{'segment_id', 'date', 'gps_lag_s', 'compared'})
    _write_equal(root/(lag.FOLDER+'motion-lag.csv'), _table(rows, columns))
    return dict(stretches=len(rows), compared=value['compared'], summary=summary)


def receiver_motion(root):
    """GPS-only motion of the recovered intervals against the published stretches."""
    from . import ilvis0_interval_receiver_motion as interval
    from statistics import median

    with closing(ClosedStudy(root, 'data/'+interval.ID)) as study:
        _complete(study)
        results = [study.envelope(task['identity'])['result'] for task in study.manifest['tasks']]
        completion = study.completion
    published = [row['profile'] for row in results if row['kind'] == 'published' and row['passed']]
    keys = (*interval.RATES, 'minimum_speed_kmh', 'median_speed_kmh', 'duration_s', 'course_span_deg',
            'height_span_m', 'supported_course_rate_epochs')
    limits = {key: max(row[key] for row in published) for key in interval.RATES}
    limits['minimum_speed_kmh'] = min(row['minimum_speed_kmh'] for row in published)
    rows = []
    for result in results:
        row = dict(identity=result['identity'], kind=result['kind'], filename=result['filename'],
                   imu_type=result['imu_type'], profiled=result['passed'], reason=result['reason'])
        if result['passed']:
            profile = result['profile']
            row.update({key: profile[key] for key in keys})
            if result['kind'] == 'recovered':
                outside = [key for key in interval.RATES if profile[key] > limits[key]]
                if profile['minimum_speed_kmh'] < limits['minimum_speed_kmh']:
                    outside.append('minimum_speed_kmh')
                row.update(inside_published_range=interval.inside_published_range(profile, published),
                           outside_on=';'.join(outside))
        rows.append(row)
    ranges = {kind: {key: dict(minimum=min(values), median=median(values), maximum=max(values))
                     for key in (*interval.RATES, 'minimum_speed_kmh')
                     for values in [[row[key] for row in rows if row['kind'] == kind and row['profiled']]] if values}
              for kind in ('published', 'recovered')}
    recovered = [row for row in rows if row['kind'] == 'recovered']
    value = dict(study=interval.ID, intervals=len(rows),
        published_profiled=sum(row['profiled'] for row in rows if row['kind'] == 'published'),
        recovered_profiled=sum(row['profiled'] for row in recovered),
        recovered_inside_published_range=sum(bool(row.get('inside_published_range')) for row in recovered),
        published_limits=limits, ranges=ranges, rows=rows, completion=completion,
        earth_model_fits=0, gyro_used=False, scientific_decision='abstain')
    _write_equal(root/(interval.FOLDER+'receiver-motion-result.json'), encoded(value))
    _write_equal(root/(interval.FOLDER+'receiver-motion.csv'), _table(rows, [
        'identity', 'kind', 'filename', 'imu_type', 'profiled', 'reason', *keys, 'inside_published_range',
        'outside_on']))
    return {key: value[key] for key in ('intervals', 'published_profiled', 'recovered_profiled',
                                        'recovered_inside_published_range', 'published_limits', 'ranges')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = {'selection': selection, 'motion-match': motion_match, 'motion-lag': motion_lag,
               'receiver-motion': receiver_motion}
    parser.add_argument('action', choices=tuple(actions))
    action = actions[parser.parse_args().action]
    print(json.dumps(action(Path.cwd().resolve()), sort_keys=True))


if __name__ == '__main__':
    main()
