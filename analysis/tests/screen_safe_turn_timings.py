# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded nominal timing search on already screened observed development windows."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import random
import time

import numpy as np
import screen_long_route_windows as baseline
from lll.policy import contrast_eligibility

ROOT = baseline.ROOT
screen = baseline.screen
PRIOR = ('docs/research-next-stage-20261006/long-route-window-screen.json',
         'docs/research-next-stage-20261006/extended-route-controls.json')
MAX_SCORED, PER_WINDOW, MAX_DRAWS, SECONDS_CAP = 96, 8, 512, 20.


def nominal_score(spec, kin, duration, schedule):
    design = baseline.realize(600902, 'wind+bias_mixed', geometry='observed',
                              trajectory_input=spec, turn_schedule=schedule)
    candidates = []
    for crab in ('wind', 'wind_tas'):
        problem = baseline.geometry_problem(design, schedule, crab, kin=(kin, duration))
        untruncated, truncated, ranks = {}, {}, {}
        for anchor, coefficients in baseline.models.EXPECTED_K.items():
            z = np.zeros(problem.npar)
            z[:3] = coefficients
            _, jac = problem.prediction(z, True)
            jac, weights = problem.observation_information(z, jac,
                np.full(len(problem.y), (baseline.RAD2DPH / 6.) ** 2))
            report = baseline.science_information(jac, weights)['report']
            ranks[anchor] = report['estimable_rank']
            for name, value in report['model_contrast_information'].items():
                for destination, prefix in ((untruncated, 'pre_cutoff_'), (truncated, '')):
                    old = destination.setdefault(name, dict(retained_fraction=1., information=float('inf')))
                    old['retained_fraction'] = min(old['retained_fraction'], value[prefix + 'retained_fraction'])
                    old['information'] = min(old['information'], value[prefix + 'information'])
        threshold = baseline.CANDIDATE_POLICY['retention_threshold']
        for mapping in (untruncated, truncated):
            for value in mapping.values():
                value['estimable'] = bool(value['retained_fraction'] >= threshold)
        # Reuse the contrast threshold/margin rule without claiming the full design envelope.
        pair_report = dict(rank_threshold=threshold, model_contrast_information=untruncated)
        pairs = {pair: contrast_eligibility(pair_report, pair) for pair in untruncated}
        candidates.append(dict(crab_model=crab, anchor_ranks=ranks,
            untruncated_contrasts=untruncated, truncated_contrasts=truncated,
            nominal_pair_criteria=pairs))
    shapes = [c['nominal_pair_criteria'][pair] for c in candidates for pair in baseline.GLOBE_DISC_PAIRS]
    return dict(candidates=candidates,
        both_shape_nominal_pass=all(s['all_estimable'] for s in shapes),
        worst_shape_margin=min(s['worst_margin'] for s in shapes),
        worst_shape_information=min(s['worst_information'] for s in shapes),
        all_three_nominal_pass=all(s['all_estimable'] for c in candidates for s in c['nominal_pair_criteria'].values()))


def ranking(row):
    return (-int(row['both_shape_nominal_pass']), -row['worst_shape_margin'],
            -row['worst_shape_information'], len(row['schedule_minutes']), row['schedule_minutes'])


def review():
    began = time.monotonic()
    inputs, tracks, selected = {}, {}, {}
    for relative in baseline.ARCHIVES:
        inputs[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        with gzip.open(ROOT / relative, 'rt') as source:
            bundle = json.load(source)
        if bundle.get('track_format') != 'position-track-2' or bundle.get('partition') != 'development':
            raise ValueError('requires documented development tracks')
        tracks.update({t['id']: t for t in bundle['tracks']})
    for relative in PRIOR:
        inputs[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        for case in json.loads((ROOT / relative).read_text())['cases']:
            passing = [p for p in case.get('patterns', []) if p['screen']['passes_screen']]
            if passing:
                selected[(case['track_id'], case['start_s'], case['end_s'])] = passing
    total, cases, capped = 0, [], False
    for (track_id, start, end), prior in sorted(selected.items()):
        if total >= MAX_SCORED or time.monotonic() - began >= SECONDS_CAP:
            capped = True
            break
        track = tracks[track_id]
        spec = baseline.smooth_track_spec(baseline.track_spec(dict(id=track_id,
            source_sha256=track['source_sha256'], status='prepared_geometry_only',
            rows=[r for r in track['rows'] if start <= r['t_s'] <= end],
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
        grid = [float(m) for m in np.arange(5., replay.duration / 60. - 5. + 1e-9, 5.)
                if screen.turn_motion_check(mask, m * 60 - 1., m * 60 + 25.)['safe']]
        seed = int(hashlib.sha256(f'{track_id}/{start}/{end}/timing-1'.encode()).hexdigest()[:16], 16)
        rng = random.Random(seed)
        seen, evaluated, rejected = set(), [], []
        initial = [p['screen']['schedule_minutes'] for p in prior]
        for draw in range(MAX_DRAWS):
            if len(evaluated) >= PER_WINDOW or total >= MAX_SCORED or time.monotonic() - began >= SECONDS_CAP:
                capped |= total >= MAX_SCORED or time.monotonic() - began >= SECONDS_CAP
                break
            if draw < len(initial):
                schedule = initial[draw]
            else:
                count = (3, 4, 5, 6)[(draw - len(initial)) % 4]
                if len(grid) < count:
                    continue
                schedule = sorted(rng.sample(grid, count))
            key = tuple(schedule)
            if key in seen:
                continue
            seen.add(key)
            try:
                screen.validate_turn_schedule(schedule, replay.duration / 60.)
            except ValueError as exc:
                rejected.append(dict(schedule_minutes=schedule, exclusions=[str(exc)]))
                continue
            preflight = screen.screen_schedule(bins, base, mask, schedule, replay.duration)
            if not preflight['passes_screen']:
                rejected.append(dict(schedule_minutes=schedule, exclusions=preflight['exclusions']))
                continue
            score = nominal_score(spec, kin, replay.duration, schedule)
            evaluated.append(dict(schedule_minutes=schedule, screen=preflight, **score))
            total += 1
        cases.append(dict(track_id=track_id, start_s=start, end_s=end,
            trajectory_hash=spec['trajectory_hash'], schedule_sampling_seed=seed,
            safe_grid_minutes=grid, scored=evaluated, rejected=rejected,
            rejection_counts=dict(Counter(reason for r in rejected for reason in r['exclusions'])),
            best_nominal_diagnostic=min(evaluated, key=ranking) if evaluated else None))
    return dict(state='bounded_nominal_timing_screen_complete', selected_windows=len(selected), cases=cases,
        scored_schedules=total, evaluation_or_time_cap_reached=capped,
        limits=dict(max_scored=MAX_SCORED, per_window=PER_WINDOW, draws_per_window=MAX_DRAWS, seconds=SECONDS_CAP),
        input_sha256=inputs, implementation_hash=baseline.implementation_hash(),
        helper_sha256={str(Path(p).resolve().relative_to(ROOT)): hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in (__file__, baseline.__file__, screen.__file__)},
        elapsed_s=time.monotonic() - began, additional_flight_attempts=0, error_rate_validated=False,
        score_order=['both_shape_nominal_pass', 'worst_shape_margin', 'worst_shape_information'],
        limitations=['Adaptive development search on overlapping windows, not independent evidence.',
            'Only previously preliminary-passing windows; bounded sampled schedules are not exhaustive.',
            'Same C2 motion assumptions, maneuver buffer, six-turn/spacing/edge and heading rules.',
            'Three science anchors, zero wind/forward angle, nominal TAS250, fixed6dph, dynamic bias and forward uncertainty.',
            'Scores use pair-specific untruncated contrasts; cut-rank contrasts and anchor ranks also recorded.',
            'Shared contrast criterion applied to nominal states only, not full-envelope candidate acceptance.',
            'No simulated IMU, recovered-axis check, nonlinear fit, bootstrap, power, calibration or protocol recommendation.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(windows=len(result['cases']), scored_schedules=result['scored_schedules'],
        elapsed_s=result['elapsed_s'], cap_reached=result['evaluation_or_time_cap_reached'],
        shape_passes=sum(s['both_shape_nominal_pass'] for c in result['cases'] for s in c['scored']),
        all_three_passes=sum(s['all_three_nominal_pass'] for c in result['cases'] for s in c['scored']))))
