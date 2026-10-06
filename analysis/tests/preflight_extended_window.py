# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check longer observed windows around a recorded development-screen anchor."""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import preflight_route_turns as screen
from lll.trajectory import TrackReplay, smooth_track_spec, track_spec

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = 'docs/flight-geometry-20261006/normalized-tracks.json.gz'
ANCHOR = 'docs/matched-airline-pilot-20261006/window-preflight.json'


def review():
    prior = json.loads((ROOT / ANCHOR).read_text())
    anchors = [(t['track_id'], w) for t in prior['tracks'] for w in t['windows']
               if w.get('no_turn_minutes', 0) >= 60 and w.get('no_turn_heading_adequate')]
    with gzip.open(ROOT / ARCHIVE, 'rt') as source: bundle = json.load(source)
    tracks = {t['id']: t for t in bundle['tracks']}
    cases = []
    for track_id, anchor in anchors:
        track = tracks[track_id]
        for minutes in (90., 105., 120.):
            extra = minutes * 60 - (anchor['end_s'] - anchor['start_s'])
            for left in np.arange(0., extra + 1., 300.):
                start, end = anchor['start_s'] - left, anchor['end_s'] + extra - left
                if start < track['rows'][0]['t_s'] or end > track['rows'][-1]['t_s']: continue
                rows = [r for r in track['rows'] if start <= r['t_s'] <= end]
                coverage = sum(max(0., min(b['t_s'], end) - max(a['t_s'], start))
                    for a, b in zip(rows, rows[1:]) if 0 < b['t_s'] - a['t_s'] <= 90
                    and not (a.get('is_provider_estimate') or b.get('is_provider_estimate'))) / (end - start)
                result = dict(track_id=track_id, start_s=start, end_s=end, minutes=minutes,
                              observed_coverage_fraction=coverage)
                if coverage < .95:
                    cases.append({**result, 'failure':'insufficient observed coverage'}); continue
                try:
                    spec = smooth_track_spec(track_spec(dict(id=track_id, source_sha256=track['source_sha256'],
                        status='prepared_geometry_only', rows=rows,
                        candidate_window=dict(start_s=start, end_s=end))))
                    replay = TrackReplay(spec)
                    t = np.arange(0., replay.duration, 1.)
                    kin = dict(t=t, **replay.sample(t), bearing_ok=replay.support(t))
                    support = kin['bearing_ok'] & np.isfinite(kin['psi'])
                    edges = np.flatnonzero(np.diff(np.r_[False, support, False]))
                    for a, b in zip(edges[::2], edges[1::2]): kin['psi'][a:b] = np.unwrap(kin['psi'][a:b])
                    bins, base, _ = screen.qualified_bins(kin, replay.duration)
                    mask = screen.maneuver_mask(kin, buffer_s=120.)
                    no_turn = screen.screen_schedule(bins, base, mask, [], replay.duration)
                    grid = [float(m) for m in np.arange(5., minutes - 5. + 1., 5.)
                            if screen.turn_motion_check(mask, m * 60 - 1., m * 60 + 25.)['safe']]
                    schedules = []
                    evaluated = 0
                    for turns in itertools.combinations(grid, 3):
                        if any(b - a < 10. for a, b in zip(turns, turns[1:])): continue
                        evaluated += 1
                        s = screen.screen_schedule(bins, base, mask, turns, replay.duration)
                        if s['passes_screen']: schedules.append(s)
                    schedules.sort(key=lambda s: (s['heading_duration_margin_seconds'],
                                   s['screened_minutes'], min(s['retained_minutes_by_epoch'])), reverse=True)
                    cases.append({**result, 'trajectory_hash':spec['trajectory_hash'],
                        'no_turn':no_turn, 'evaluated_schedules':evaluated,
                        'passing_schedules':len(schedules),
                        'best_schedule':schedules[0] if schedules else None})
                except ValueError as exc:
                    cases.append({**result, 'failure':str(exc)})
    return dict(state='extended_window_preflight_complete_no_flights', cases=cases,
        input_sha256={p:hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (ARCHIVE, ANCHOR)},
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        preflight_helper_sha256=hashlib.sha256(Path(screen.__file__).read_bytes()).hexdigest(),
        authorized_additional_attempts=0,
        scope='Exploratory overlapping extensions chosen after development screening; not independent evidence.',
        limitations=['Only duration changed; coverage, heading, motion and turn rules unchanged.',
            'Assumed C2 motion; full preprocessing, forward reference and nuisance separation untested.',
            'No fit, SVD, power, empirical threshold or validation; no new protocol adopted.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open('x') as out: out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(windows=len(result['cases']), failures=sum('failure' in c for c in result['cases']),
        passing_windows=sum(bool(c.get('passing_schedules')) for c in result['cases']),
        best_by_duration={str(m):max((c for c in result['cases'] if c['minutes'] == m and c.get('best_schedule')),
            key=lambda c:(c['best_schedule']['heading_duration_margin_seconds'],c['best_schedule']['screened_minutes']),
            default=None) for m in (90.,105.,120.)})))
