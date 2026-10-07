# SPDX-License-Identifier: AGPL-3.0-or-later
"""Coarse two-hour observed-window controls, without synthetic IMU or flight attempts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'analysis'), str(ROOT / 'analysis/tests')]

import numpy as np
import preflight_route_turns as screen
from lll import models
from lll.calib import RAD2DPH
from lll.design_geometry import geometry_problem
from lll.inference import science_information
from lll.pairwise import GLOBE_DISC_PAIRS
from lll.policy import CANDIDATE_POLICY
from lll.research_design import implementation_hash, realize
from lll.trajectory import TrackReplay, smooth_track_spec, track_spec

ARCHIVES = ('docs/flight-geometry-20261006/normalized-tracks.json.gz',
            'docs/scraped-flight-geometry-20261006/normalized-tracks.json.gz')
PATTERNS = {'no-turn': [], 'three-fixed': [25., 50., 85.],
            'six-distributed': [10., 30., 50., 70., 90., 110.]}


def nominal_scores(spec, kin, duration, schedule):
    design = realize(600902, 'wind+bias_mixed', geometry='observed',
                     trajectory_input=spec, turn_schedule=schedule)
    candidates = []
    for crab in ('wind', 'wind_tas'):
        p = geometry_problem(design, schedule, crab, kin=(kin, duration))
        fractions = {pair: 1. for pair in CANDIDATE_POLICY['contrasts']}
        for coefficients in models.EXPECTED_K.values():
            z = np.zeros(p.npar)
            z[:3] = coefficients
            _, jacobian = p.prediction(z, True)
            jacobian, weights = p.observation_information(
                z, jacobian, np.full(len(p.y), (RAD2DPH / 6.) ** 2))
            contrasts = science_information(jacobian, weights)['report']['model_contrast_information']
            for pair in fractions:
                fractions[pair] = min(fractions[pair], contrasts[pair]['pre_cutoff_retained_fraction'])
        passing = {pair: value >= CANDIDATE_POLICY['retention_threshold']
                   for pair, value in fractions.items()}
        candidates.append(dict(crab_model=crab, worst_nominal_pair_retention=fractions,
            nominal_pair_retention_pass=passing,
            both_shape_retention_pass=all(passing[pair] for pair in GLOBE_DISC_PAIRS),
            all_three_retention_pass=all(passing.values())))
    return candidates


def review():
    began = time.monotonic()
    cases, inputs = [], {}
    for relative in ARCHIVES:
        inputs[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        with gzip.open(ROOT / relative, 'rt') as source:
            bundle = json.load(source)
        if bundle.get('track_format') != 'position-track-2' or bundle.get('partition') != 'development':
            raise ValueError('requires the documented development track format')
        for track in bundle['tracks']:
            rows = track['rows']
            # Fixed grid chosen independently of previous 75-minute screen outcomes.
            for start in range(0, max(0, int(rows[-1]['t_s'] - 7200)) + 1, 900):
                end = start + 7200
                if end > rows[-1]['t_s']:
                    continue
                coverage = sum(max(0., min(b['t_s'], end) - max(a['t_s'], start))
                    for a, b in zip(rows, rows[1:])
                    if 0 < b['t_s'] - a['t_s'] <= 90
                    and not (a.get('is_provider_estimate') or b.get('is_provider_estimate'))) / 7200
                case = dict(track_id=track['id'], start_s=start, end_s=end,
                            observed_coverage_fraction=coverage)
                if coverage < .95:
                    cases.append({**case, 'failure': 'insufficient observed coverage'})
                    continue
                try:
                    selected = [row for row in rows if start <= row['t_s'] <= end]
                    spec = smooth_track_spec(track_spec(dict(id=track['id'],
                        source_sha256=track['source_sha256'], status='prepared_geometry_only',
                        rows=selected, candidate_window=dict(start_s=start, end_s=end))))
                    replay = TrackReplay(spec)
                    t = np.arange(0., replay.duration, 1.)
                    kin = dict(t=t, **replay.sample(t), bearing_ok=replay.support(t))
                    support = kin['bearing_ok'] & np.isfinite(kin['psi'])
                    edges = np.flatnonzero(np.diff(np.r_[False, support, False]))
                    for a, b in zip(edges[::2], edges[1::2]):
                        kin['psi'][a:b] = np.unwrap(kin['psi'][a:b])
                    bins, base, _ = screen.qualified_bins(kin, replay.duration)
                    mask = screen.maneuver_mask(kin, buffer_s=120.)
                    patterns = []
                    for name, schedule in PATTERNS.items():
                        result = screen.screen_schedule(bins, base, mask, schedule, replay.duration)
                        candidates = []
                        if result['passes_screen']:
                            candidates = nominal_scores(spec, kin, replay.duration, schedule)
                        patterns.append(dict(pattern=name, screen=result, candidates=candidates))
                    cases.append({**case, 'trajectory_hash': spec['trajectory_hash'],
                        'mean_supported_east_velocity_mps': float(np.mean(kin['v_e'][support])),
                        'patterns': patterns})
                except (ValueError, np.linalg.LinAlgError) as exc:
                    cases.append({**case, 'failure': str(exc)})
    return dict(state='coarse_observed_two_hour_controls_complete', cases=cases,
        window_seconds=7200, start_stride_seconds=900, input_sha256=inputs,
        implementation_hash=implementation_hash(),
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        preflight_helper_sha256=hashlib.sha256(Path(screen.__file__).read_bytes()).hexdigest(),
        elapsed_s=time.monotonic() - began, additional_flight_attempts=0, error_rate_validated=False,
        limitations=['Overlapping windows on seven recorded tracks are exploratory, not independent evidence.',
            'Fixed 15-minute start grid and three fixed turn patterns; not exhaustive schedule optimization.',
            'C2 motion interpolated from coarse positions is assumed, not measured high-rate aircraft motion.',
            'Nominal SVD only for observable-screen passes: three model anchors, zero wind/forward angle, TAS250 and6dph.',
            'Dynamic bias and forward uncertainty retained; full nuisance envelope and recovered axes untested.',
            'No IMU synthesis, nonlinear fit, bootstrap, power, calibration or validated protocol.'])


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
        nominal_shape_passes=[dict(track_id=c['track_id'], start_s=c['start_s'],
            pattern=p['pattern'], crab_model=v['crab_model'])
            for c in result['cases'] for p in c.get('patterns', [])
            for v in p['candidates'] if v['both_shape_retention_pass']])))
