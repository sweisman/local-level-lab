# SPDX-License-Identifier: AGPL-3.0-or-later
"""Three/four-hour fixed timing controls; no new IMU simulation or flight attempts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import screen_long_route_windows as baseline

ROOT = baseline.ROOT
screen = baseline.screen


def patterns(minutes):
    # These timing patterns are chosen before looking at any window's model score.
    result = {'no-turn': [],
        'three-distributed': [minutes * x for x in (25 / 120, 50 / 120, 85 / 120)],
        'six-distributed': np.linspace(10., minutes - 10., 6).tolist(),
        **{f'six-central-twenty-minute-spacing-shift-{shift:+d}':
           (minutes / 2. + np.arange(-50., 51., 20.) + shift).tolist()
           for shift in (-5, 0, 5)}}
    for schedule in result.values():
        screen.validate_turn_schedule(schedule, minutes)
    return result


def review():
    began = time.monotonic()
    schedules = {minutes: patterns(minutes) for minutes in (180, 240)}
    cases, inputs = [], {}
    for relative in baseline.ARCHIVES:
        inputs[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        with gzip.open(ROOT / relative, 'rt') as source:
            bundle = json.load(source)
        if bundle.get('track_format') != 'position-track-2' or bundle.get('partition') != 'development':
            raise ValueError('requires documented development position tracks')
        for track in bundle['tracks']:
            rows = track['rows']
            for minutes in (180, 240):
                length = minutes * 60
                for start in range(0, max(0, int(rows[-1]['t_s'] - length)) + 1, 900):
                    end = start + length
                    if end > rows[-1]['t_s']:
                        continue
                    coverage = sum(max(0., min(b['t_s'], end) - max(a['t_s'], start))
                        for a, b in zip(rows, rows[1:])
                        if 0 < b['t_s'] - a['t_s'] <= 90
                        and not (a.get('is_provider_estimate') or b.get('is_provider_estimate'))) / length
                    case = dict(track_id=track['id'], minutes=minutes, start_s=start, end_s=end,
                                observed_coverage_fraction=coverage)
                    if coverage < .95:
                        cases.append({**case, 'failure': 'insufficient observed coverage'})
                        continue
                    try:
                        spec = baseline.smooth_track_spec(baseline.track_spec(dict(id=track['id'],
                            source_sha256=track['source_sha256'], status='prepared_geometry_only',
                            rows=[row for row in rows if start <= row['t_s'] <= end],
                            candidate_window=dict(start_s=start, end_s=end))))
                        replay = baseline.TrackReplay(spec)
                        t = np.arange(0., replay.duration, 1.)
                        kin = dict(t=t, **replay.sample(t), bearing_ok=replay.support(t))
                        support = kin['bearing_ok'] & np.isfinite(kin['psi'])
                        edges = np.flatnonzero(np.diff(np.r_[False, support, False]))
                        for a, b in zip(edges[::2], edges[1::2]):
                            kin['psi'][a:b] = np.unwrap(kin['psi'][a:b])
                        bins, base, _ = screen.qualified_bins(kin, replay.duration)
                        mask = screen.maneuver_mask(kin, buffer_s=120.)
                        controls = []
                        for name, schedule in schedules[minutes].items():
                            result = screen.screen_schedule(bins, base, mask, schedule, replay.duration)
                            candidates = baseline.nominal_scores(spec, kin, replay.duration, schedule) \
                                if result['passes_screen'] else []
                            controls.append(dict(pattern=name, screen=result, candidates=candidates))
                        cases.append({**case, 'trajectory_hash': spec['trajectory_hash'],
                            'mean_supported_east_velocity_mps': float(np.mean(kin['v_e'][support])),
                            'patterns': controls})
                    except (ValueError, np.linalg.LinAlgError) as exc:
                        cases.append({**case, 'failure': str(exc)})
    return dict(state='extended_observed_route_controls_complete', cases=cases,
        window_minutes=[180, 240], start_stride_seconds=900,
        pattern_definitions={str(m): patterns(m) for m in (180, 240)},
        input_sha256=inputs, implementation_hash=baseline.implementation_hash(),
        helper_sha256={str(Path(p).resolve().relative_to(ROOT)):
            hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in (__file__, baseline.__file__, screen.__file__)},
        elapsed_s=time.monotonic() - began, additional_flight_attempts=0, error_rate_validated=False,
        limitations=['Overlapping windows and timing variants are exploratory, not independent trials.',
            'Only three/four-hour windows on a 15-minute start grid and six fixed timing patterns.',
            'Course/bank between coarse position fixes is assumed by C2 interpolation.',
            'Coverage, heading, duration, maneuver buffer and nuisance assumptions are unchanged.',
            'Nominal SVD at three anchors only for screening passes; no full nuisance envelope.',
            'No IMU synthesis, recovered-axis check, nonlinear fit, bootstrap, power or calibration.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(windows=len(result['cases']), elapsed_s=result['elapsed_s'],
        failures=sum('failure' in c for c in result['cases']),
        passing_controls=sum(p['screen']['passes_screen'] for c in result['cases'] for p in c.get('patterns', [])),
        nominal_shape_passes=[dict(track_id=c['track_id'], minutes=c['minutes'], start_s=c['start_s'],
            pattern=p['pattern'], crab_model=v['crab_model'])
            for c in result['cases'] for p in c.get('patterns', [])
            for v in p['candidates'] if v['both_shape_retention_pass']])))
