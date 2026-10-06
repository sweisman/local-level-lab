# SPDX-License-Identifier: AGPL-3.0-or-later
"""Screen observed 75-minute windows; no simulated flights or science optimization."""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import preflight_route_turns as screen
from import_flight_tracks import summary
from lll.trajectory import TrackReplay, smooth_track_spec, track_spec

ROOT = Path(__file__).resolve().parents[2]
ARCHIVES = ('docs/flight-geometry-20261006/normalized-tracks.json.gz',
            'docs/scraped-flight-geometry-20261006/normalized-tracks.json.gz')


def review():
    reports = []
    for relative in ARCHIVES:
        with gzip.open(ROOT / relative, 'rt') as source: bundle = json.load(source)
        if bundle.get('track_format') != 'position-track-2' or bundle.get('partition') != 'development':
            raise ValueError('requires provenance-bearing development position tracks')
        for track in bundle['tracks']:
            windows = [w for w in summary(track)['windows_75min']
                       if w['observed_coverage_fraction'] >= .95]
            results = []
            for w in windows:
                rows = [r for r in track['rows'] if w['start_s'] <= r['t_s'] <= w['end_s']]
                case = dict(id=track['id'], source_sha256=track['source_sha256'], rows=rows,
                            candidate_window=w, status='prepared_geometry_only')
                try:
                    spec = smooth_track_spec(track_spec(case))
                    replay = TrackReplay(spec)
                    t = np.arange(0., replay.duration, 1.)
                    kin = dict(t=t, **replay.sample(t), bearing_ok=replay.support(t))
                    supported = kin['bearing_ok'] & np.isfinite(kin['psi'])
                    edges = np.flatnonzero(np.diff(np.r_[False, supported, False]))
                    for a, b in zip(edges[::2], edges[1::2]): kin['psi'][a:b] = np.unwrap(kin['psi'][a:b])
                    bins, base, _ = screen.qualified_bins(kin, replay.duration)
                    mask = screen.maneuver_mask(kin, buffer_s=120.)
                    no_turn = screen.screen_schedule(bins, base, mask, [], replay.duration)
                    # Removing turn intervals cannot increase retained duration. Do not
                    # prune on heading groups: regrouping after exclusion can change them.
                    schedules = []
                    count = 0
                    if no_turn['screened_minutes'] >= screen.MIN_CRUISE_MIN:
                        grid = [float(m) for m in np.arange(5., 71., 5.)
                                if screen.turn_motion_check(mask, m * 60 - 1., m * 60 + 25.)['safe']]
                        for turns in itertools.combinations(grid, 3):
                            if any(b - a < 10. for a, b in zip(turns, turns[1:])): continue
                            count += 1
                            s = screen.screen_schedule(bins, base, mask, turns, replay.duration)
                            if s['passes_screen']: schedules.append(s)
                    schedules.sort(key=lambda s: (s['heading_duration_margin_seconds'],
                                   s['screened_minutes'], min(s['retained_minutes_by_epoch'])), reverse=True)
                    results.append(dict(start_s=w['start_s'], end_s=w['end_s'],
                        observed_coverage_fraction=w['observed_coverage_fraction'],
                        trajectory_hash=spec['trajectory_hash'], no_turn_minutes=no_turn['screened_minutes'],
                        no_turn_heading_adequate=no_turn['heading_diversity']['adequate'],
                        evaluated_three_turn_schedules=count, passing_three_turn_schedules=len(schedules),
                        best_schedule=schedules[0] if schedules else None))
                except ValueError as exc:
                    results.append(dict(start_s=w['start_s'], end_s=w['end_s'], failure=str(exc)))
            passing = [r for r in results if r.get('best_schedule') is not None]
            passing.sort(key=lambda r: (r['best_schedule']['heading_duration_margin_seconds'],
                         r['best_schedule']['screened_minutes'], -r['start_s']), reverse=True)
            reports.append(dict(track_id=track['id'], coverage_qualified_windows=len(windows),
                failed_windows=sum('failure' in r for r in results),
                passing_windows=len(passing), best_window=passing[0] if passing else None,
                windows=results))
    return dict(state='window_screen_complete_no_flights', tracks=reports,
        input_sha256={p:hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ARCHIVES},
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        preflight_helper_sha256=hashlib.sha256(Path(screen.__file__).read_bytes()).hexdigest(),
        authorized_additional_attempts=0,
        limits=dict(window_minutes=75., minimum_observed_coverage=.95, maximum_interval_seconds=90.,
                    grid_minutes=5., min_turn_spacing_minutes=10., maneuver_buffer_seconds=120., turn_count=3),
        scope='Overlapping development windows on assumed C2 paths; observable screen only, no independent trials.',
        limitations=['Latitude-based window selection replaced only for this diagnostic; original proposals unchanged.',
            'Curve derivatives and altitude reference are assumptions; no actual IMU or high-rate GNSS.',
            'Analytic motion bins differ from full preprocessing; pass is not eligibility or identifiability.',
            'No fit, SVD, coverage validation, wind/bias injection, power or calibration.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open('x') as out: out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps([dict(track_id=t['track_id'], windows=t['coverage_qualified_windows'],
                          failures=t['failed_windows'], passing=t['passing_windows'],
                          best=t['best_window']) for t in result['tracks']]))
