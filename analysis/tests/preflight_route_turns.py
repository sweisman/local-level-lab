# SPDX-License-Identifier: AGPL-3.0-or-later
"""Screen assumed route bins and turn timing, without simulation, fits or SVDs."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis'))

import numpy as np
from lll.collate import MIN_CRUISE_MIN
from lll.maneuvers import maneuver_mask, turn_motion_check
from lll.policy import heading_diversity
from lll.research_design import validate_turn_schedule
from lll.segments import Thresholds
from lll.trajectory import TrackReplay, smooth_track_spec


def qualified_bins(kin, duration):
    """Mirror analytic geometry's ten-minute qualification and full-minute masks.

    This assumes supported latent kinematics, not noisy GNSS or an IMU. The bank-rate
    maneuver mask is stricter than cruise selection; results are screening estimates,
    not bounds on real preprocessing or complete eligibility.
    """
    th = Thresholds()
    motion = maneuver_mask(kin)
    t = kin['t']
    ok = np.array([turn_motion_check(motion, s, s)['safe'] for s in t])
    qualified = np.zeros(len(t), bool)
    edges = np.flatnonzero(np.diff(np.r_[False, ok, False]))
    runs = []
    for a, b in zip(edges[::2], edges[1::2]):
        if t[b - 1] - t[a] >= th.min_segment_s:
            qualified[a:b] = True
            runs.append([float(t[a]), float(t[b - 1])])
    centers = np.arange(th.bin_s / 2, duration, th.bin_s)
    safe = np.array([turn_motion_check(motion, c - th.bin_s / 2,
                                     c + th.bin_s / 2)['safe'] for c in centers])
    safe &= np.interp(centers, t, qualified.astype(float)) == 1.
    psi = np.array([np.interp(c, t, kin['psi']) for c in centers])
    return dict(t=centers, dt=np.full(len(centers), th.bin_s), psi=psi), safe, runs


def screen_schedule(bins, base, mask, schedule, duration, turn_seconds=5.):
    validate_turn_schedule(schedule, duration / 60)
    checks = [dict(minute=m, **turn_motion_check(mask, m * 60 - 1.,
                                               m * 60 + turn_seconds + 20.))
              for m in schedule]
    keep = base.copy()
    for m in schedule:
        keep &= ((bins['t'] + bins['dt'] / 2 < m * 60 - 1.) |
                 (bins['t'] - bins['dt'] / 2 > m * 60 + turn_seconds + 20.))
    retained = {k: v[keep] for k, v in bins.items()}
    heading = heading_diversity(retained)
    minutes = float(retained['dt'].sum() / 60)
    reasons = []
    if not all(c['safe'] for c in checks): reasons.append('unsafe or unverified turn')
    if minutes < MIN_CRUISE_MIN: reasons.append('insufficient screened cruise duration')
    if not heading['adequate']: reasons.append('insufficient screened heading diversity')
    refs = [g for g in heading['groups'] if g['seconds'] >= heading['min_seconds_per_heading']]
    margin = max((min(a['seconds'], b['seconds']) - heading['min_seconds_per_heading']
                  for a, b in itertools.combinations(refs, 2)
                  if abs((a['heading_deg'] - b['heading_deg'] + 180) % 360 - 180)
                  >= heading['min_separation_deg']), default=None)
    epoch = np.searchsorted(np.asarray(schedule) * 60 + turn_seconds, retained['t'])
    return dict(schedule_minutes=list(schedule), turn_checks=checks,
                screened_minutes=minutes, heading_diversity=heading,
                heading_duration_margin_seconds=margin,
                retained_minutes_by_epoch=[float(retained['dt'][epoch == i].sum() / 60)
                                           for i in range(len(schedule) + 1)],
                passes_screen=not reasons, exclusions=reasons)


def review():
    core = ROOT / 'docs/core-pipeline-20261006'
    proposal = json.loads((core / 'proposal.json').read_text())
    cases = []
    inputs = {}
    for item in proposal['config']['replay_inputs']:
        if item['mode'] != 'simulated_high_rate': continue
        path = Path(item['path'])
        if path.parent != Path('trajectories') or path.suffix != '.json':
            raise ValueError('only explicit documented trajectory inputs are allowed')
        data = (core / path).read_bytes()
        inputs[str((core / path).relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
        spec = smooth_track_spec(json.loads(data))
        replay = TrackReplay(spec)
        t = np.arange(0., replay.duration, 1.)
        kin = dict(t=t, **replay.sample(t), bearing_ok=replay.support(t))
        # Unwrap within supported blocks so north crossings do not average to south.
        supported = kin['bearing_ok'] & np.isfinite(kin['psi'])
        edges = np.flatnonzero(np.diff(np.r_[False, supported, False]))
        for a, b in zip(edges[::2], edges[1::2]): kin['psi'][a:b] = np.unwrap(kin['psi'][a:b])
        bins, base, runs = qualified_bins(kin, replay.duration)
        mask = maneuver_mask(kin, buffer_s=120.)
        grid = [float(m) for m in np.arange(5., replay.duration / 60 - 5. + 1e-9, 5.)
                if turn_motion_check(mask, m * 60 - 1., m * 60 + 25.)['safe']]
        schedules = []
        for schedule in itertools.combinations(grid, 3):
            if any(b - a < 10. for a, b in zip(schedule, schedule[1:])): continue
            schedules.append(screen_schedule(bins, base, mask, schedule, replay.duration))
        schedules.sort(key=lambda s: (s['passes_screen'], s['heading_duration_margin_seconds']
                       if s['heading_duration_margin_seconds'] is not None else -1.,
                       s['screened_minutes'], min(s['retained_minutes_by_epoch'])), reverse=True)
        cases.append(dict(track_id=spec['track_id'], trajectory_hash=spec['trajectory_hash'],
            qualified_run_seconds=runs, buffered_motion_intervals=mask['intervals'],
            feasible_turn_grid_minutes=grid, feasible_three_turn_schedules=len(schedules),
            passing_three_turn_schedules=sum(s['passes_screen'] for s in schedules),
            no_turn=screen_schedule(bins, base, mask, [], replay.duration),
            original_schedule=screen_schedule(bins, base, mask, [20., 40., 60.], replay.duration),
            best_screened_schedule=schedules[0] if schedules else None))
    return dict(state='preflight_complete_no_flights', input_sha256=inputs,
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        thresholds=dict(min_cruise_minutes=MIN_CRUISE_MIN, maneuver_buffer_seconds=120.,
                        grid_minutes=5., min_turn_spacing_minutes=10., turn_count=3),
        cases=cases, authorized_additional_attempts=0,
        limitations=['Assumed C2 trajectory and one-second kinematics; no noisy GNSS or IMU.',
            'Analytic geometry qualification is a screen, not full preprocessing or a certified upper bound.',
            'No forward-reference check, nuisance projection, identifiability, power or decision calibration.',
            'Schedule ranking uses only observable screened geometry, not the scientific optimizer objective.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps([dict(track_id=c['track_id'], no_turn_minutes=c['no_turn']['screened_minutes'],
                          no_turn_heading=c['no_turn']['heading_diversity']['adequate'],
                          original_exclusions=c['original_schedule']['exclusions'],
                          safe_grid=c['feasible_turn_grid_minutes'],
                          feasible=c['feasible_three_turn_schedules'],
                          passing=c['passing_three_turn_schedules'],
                          best=c['best_screened_schedule']) for c in result['cases']]))
