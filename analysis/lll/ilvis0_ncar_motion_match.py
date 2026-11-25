# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare separate NCAR aircraft records with the original recordings on selected NASA stretches.

One stretch is one task. Each repeats the fixed RF04 comparison of the two GPS
tracks and of whole-second rotation. No Earth model is evaluated and nothing
here enters a fit.
"""
import argparse
from datetime import datetime, timedelta
import gzip
import json
import math
from pathlib import Path

from . import ilvis0_stretch_checks as checks
from .ilvis0_ncar_rf04 import ATTITUDE, utc_string
from .ilvis0_rf04_motion_match import SHIFTS, WIDTHS, _stats, packet_windows, prefix_rotations
from .ilvis0_paired_gyro_clock import CLOCKS

ID = 'ilvis0-ncar-motion-match-v1'
FOLDER = 'docs/ncar-aircraft-records/'
ADAPTER = 'analysis/lll/ilvis0_ncar_motion_match.py'
TEST = 'analysis/tests/test_ilvis0_ncar_motion_match.py'
PLAN = FOLDER+'MOTION_MATCH_PLAN.md'
INTAKE = FOLDER+'intake.json'
EXTRACTS = 'data/ncar-aircraft-records/extracts/'
REQUEST = FOLDER+'qualification.json'
TEST_REPORT = FOLDER+'tests.xml'
SCOPE = 'separate aircraft records against original GPS and IMU rotation on selected NASA stretches; no Earth-model fits'
POSITION = ('GGLAT', 'GGLON', 'GGALT')
COMPARISONS = len(CLOCKS)*len(SHIFTS)*len(WIDTHS)
RADIUS_M = 6_371_000.
WALL_S = 3600
TESTS = ('test_receiver_offsets_recover_a_known_lag_and_side_offset',
         'test_week_second_follows_the_sunday_start_of_the_recorder_week',
         'test_tasks_are_the_stretches_with_complete_aircraft_seconds',
         'test_one_stretch_reproduces_the_published_rf04_comparison')


def week_second(utc):
    """Seconds since the Sunday 00:00 UTC that starts the recorder's week."""
    time = datetime.fromisoformat(utc.replace('Z', '+00:00'))
    return ((time.weekday()+1) % 7)*86400+time.hour*3600+time.minute*60+time.second


def _wrap(angle):
    return (angle+math.pi) % (2*math.pi)-math.pi


def receiver_offsets(rows, start, times, gps):
    """Original receiver position relative to the aircraft record at shared whole seconds.

    `along_m` is positive ahead of the aircraft record along its own track and
    `right_m` is positive to the right of that track.
    """
    paired, last = [], len(rows)-1
    for time, (lat, lon, height) in zip(times, gps, strict=True):
        dt = time-start
        index = round(dt)
        if not 0 <= index <= last or abs(dt-index) > 1e-7:
            continue
        low, high = max(index-1, 0), min(index+1, last)
        here, before, after = rows[index], rows[low], rows[high]
        if high == low or any(row.get(key) is None for row in (here, before, after) for key in POSITION):
            continue
        ref_lat, ref_lon = math.radians(here['GGLAT']), math.radians(here['GGLON'])
        north = RADIUS_M*math.radians(after['GGLAT']-before['GGLAT'])/(high-low)
        east = RADIUS_M*math.cos(ref_lat)*_wrap(math.radians(after['GGLON']-before['GGLON']))/(high-low)
        speed = math.hypot(north, east)
        hav = math.sin((lat-ref_lat)/2)**2+math.cos(lat)*math.cos(ref_lat)*math.sin((lon-ref_lon)/2)**2
        row = dict(index_s=index, horizontal_m=2*RADIUS_M*math.asin(math.sqrt(min(1., hav))),
                   height_offset_m=float(height-here['GGALT']), speed_mps=speed)
        if speed >= 1.:
            dn, de = RADIUS_M*(lat-ref_lat), RADIUS_M*math.cos(ref_lat)*_wrap(lon-ref_lon)
            row.update(along_m=(dn*north+de*east)/speed, right_m=(de*north-dn*east)/speed)
            row['lag_s'] = -row['along_m']/speed
        paired.append(row)
    if len(paired) < 2 or len({row['index_s'] for row in paired}) != len(paired):
        raise ValueError('unique matching GPS report times are required')
    first = paired[0]['height_offset_m']
    return [dict(row, height_change_difference_m=row['height_offset_m']-first) for row in paired]


def tasks(root):
    """Selected stretches whose aircraft record has every second of attitude and GPS."""
    root = Path(root)
    intake = json.loads((root/INTAKE).read_bytes())
    rows = {row['segment_id']: row for row in checks.stretches(root)}
    out = []
    for record in intake['stretches']:
        seconds = record['expected_seconds']
        if {record[key] for key in ('matching_seconds', 'attitude_seconds', 'reference_gps_seconds')} != {seconds}:
            continue
        row = rows[record['segment_id']]
        steps = 2*row['native_packets']+seconds+len(CLOCKS)*len(SHIFTS)*sum((seconds-1)//w for w in WIDTHS)
        out.append(dict(row, identity=row['segment_id'], input_key='extract-'+row['segment_id'],
            aircraft_file=record['filename'], extract_sha256=record['extract_sha256'], seconds=seconds,
            limits=dict(native_calls=0, packet_visits=0, bound_calls=3+COMPARISONS, bound_steps=steps)))
    if not out:
        raise ValueError('no complete aircraft record covers a selected stretch')
    return sorted(out, key=lambda task: task['identity'])


def code_sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (ADAPTER, TEST, 'analysis/lll/ncar_aircraft_records.py'))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=code_sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, digest, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS as RECOVERY_TESTS, qualification_sources

    root = Path(root).resolve()
    if (root/'data'/ID).exists():
        raise ValueError('the existing comparison must be retained')
    environment = runtime_environment()
    code = code_sources(root)
    qualification, tests = checked(root, REQUEST, sources=code, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, checks.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=RECOVERY_TESTS, minimum_tests=len(RECOVERY_TESTS))
    rows = tasks(root)
    inputs = dict(plan=PLAN, intake=INTAKE, selection=checks.SELECTION, contexts=checks.CONTEXTS,
                  analytics=checks.ANALYTICS, packets=checks.PACKETS)
    for row in rows:
        path = EXTRACTS+row['identity']+'.json'
        if digest((root/path).read_bytes()) != row['extract_sha256']:
            raise ValueError('saved aircraft extract differs from the intake')
        inputs[row['input_key']] = path
    folder = root/'data'/(ID+'-inputs')
    folder.mkdir(parents=True, exist_ok=True)
    staged = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(checks.RECOVERY_POLICY, maximum_wall_s=WALL_S)))
    for key, value in staged.items():
        path = folder/key
        if path.is_file() and path.read_bytes() != value:
            raise ValueError('prepared study materials changed')
        if not path.is_file():
            atomic(path, value)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, sources=sorted(set(code+[PLAN])),
        inputs=inputs, tasks=rows, workers=1, threads=1, maximum_wall_s=WALL_S)
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study=ID, stretches=len(rows), limits=manifest['limits'], allocation=manifest['allocation'])


def compare(rows, first, values, times, gps, *, reserve):
    """Receiver offsets and whole-window rotation differences for one stretch."""
    import numpy as np
    from scipy.spatial.transform import Rotation

    reserve(bound_calls=1, bound_steps=len(rows))
    positions = receiver_offsets(rows, first, times, gps)
    reserve(bound_calls=1, bound_steps=len(values))
    reference = Rotation.from_euler('ZYX', [[row[key] for key in reversed(ATTITUDE)] for row in rows], degrees=True)
    prefix = prefix_rotations(values[:, 9:12])
    stamps, periods = values[:, 1]-first, values[:, 2]
    clocks = dict(header_elapsed=(stamps, periods),
                  nominal_200Hz=(stamps[0]-periods[0]+.005*np.arange(1, len(values)+1), np.full(len(values), .005)))
    comparisons = []
    for clock in CLOCKS:
        for shift in SHIFTS:
            for width in WIDTHS:
                starts = np.arange(0, len(rows)-width, width)
                reserve(bound_calls=1, bound_steps=len(starts))
                entry = dict(clock=clock, shift_s=shift, window_s=width, error=None)
                try:
                    actual, coverage = packet_windows(prefix, *clocks[clock], starts+shift, width)
                    good = coverage >= width-.015-1e-8
                    expected = reference[starts].inv()*reference[starts+width]
                    entry.update(windows=int(good.sum()), omitted=int((~good).sum()),
                        uncovered_max_s=float(np.max(width-coverage)),
                        rotation_difference_deg=_stats(np.rad2deg((expected[good].inv()*actual[good]).magnitude())),
                        aircraft_rotation_deg=_stats(np.rad2deg(expected[good].magnitude())),
                        group4_rotation_deg=_stats(np.rad2deg(actual[good].magnitude())))
                except (ValueError, IndexError) as error:
                    entry['error'] = str(error) or type(error).__name__
                comparisons.append(entry)
    tracked = [row for row in positions if 'lag_s' in row]
    summary = dict(matched_receiver_seconds=len(positions),
        horizontal_separation_m=_stats([row['horizontal_m'] for row in positions]),
        relative_height_difference_m=_stats([abs(row['height_change_difference_m']) for row in positions]))
    if tracked:
        summary.update({name: float(np.median([row[key] for row in tracked])) for name, key in (
            ('along_track_median_m', 'along_m'), ('right_of_track_median_m', 'right_m'),
            ('lag_median_s', 'lag_s'), ('ground_speed_median_mps', 'speed_mps'))})
        summary['lag_s'] = _stats([row['lag_s'] for row in tracked])
    return positions, summary, comparisons


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
    first = week_second(rows[0]['utc']) if rows else None
    origin = datetime.fromisoformat(rows[0]['utc'].replace('Z', '+00:00')) if rows else None
    if (digest(raw) != task['extract_sha256'] or extract['segment_id'] != task['identity']
            or len(rows) != task['seconds'] or first != math.ceil(segment['start_s'])
            or first+len(rows)-1 != math.floor(segment['end_s'])
            or [row['utc'] for row in rows] != [utc_string(origin+timedelta(seconds=i)) for i in range(len(rows))]
            or any(row[key] is None for row in rows for key in ATTITUDE)):
        raise ValueError('complete consecutive aircraft seconds on the stretch clock are required')
    context.charge(bound_calls=1, bound_steps=task['native_packets'])
    values, times, gps, provenance = checks.load_stretch(task, context)
    if provenance['group1_observations_used']:
        raise ValueError('the original recorded stream is required')
    result = dict(identity=task['identity'], aircraft_file=task['aircraft_file'], date=task['date'],
        seconds=len(rows), packets=len(values), source_sha256=provenance['source_sha256'],
        extract_sha256=task['extract_sha256'], scientific_decision='abstain', new_fits=0, reserved_reads=0,
        independent_peak_rate_upper_bound_established=False)
    try:
        positions, summary, comparisons = compare(rows, first, values,
            times+provenance['first_interval_start_utc_s'], gps, reserve=context.charge)
        context.save('matched-receiver.json', positions)
        result.update(summary, comparisons=comparisons, reason=None,
                      passed=all(entry['error'] is None for entry in comparisons))
    except ValueError as error:
        result.update(passed=False, reason=str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
