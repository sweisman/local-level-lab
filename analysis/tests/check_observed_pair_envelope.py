# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare, or explicitly execute, one time-bounded observed-route pair envelope."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import signal
import time

import screen_safe_turn_timings as timings
from lll.design_envelope import envelope_information, envelope_size, envelope_assumptions
from lll.policy import contrast_eligibility
from lll.runtime import numerical_environment, numerical_environment_hash

ROOT = timings.ROOT
baseline = timings.baseline
PARTIAL = 'docs/research-next-stage-20261006/partial-timing-counterexamples.json'
PAIR = 'sphere_still_vs_flat_still'


def prepare():
    inputs = {PARTIAL: hashlib.sha256((ROOT / PARTIAL).read_bytes()).hexdigest()}
    prior = json.loads((ROOT / PARTIAL).read_text())
    candidates = [c for c in prior['cases'] if PAIR in c['unresolved_pairs']]
    case = max(candidates, key=lambda c: min(s['pair_retention'][PAIR] for s in c['tested_states']))
    tracks = {}
    for relative in baseline.ARCHIVES:
        inputs[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        with gzip.open(ROOT / relative, 'rt') as source:
            tracks.update({t['id']: t for t in json.load(source)['tracks']})
    track = tracks[case['track_id']]
    spec = baseline.smooth_track_spec(baseline.track_spec(dict(id=case['track_id'],
        source_sha256=track['source_sha256'], status='prepared_geometry_only',
        rows=[r for r in track['rows'] if case['start_s'] <= r['t_s'] <= case['end_s']],
        candidate_window=dict(start_s=case['start_s'], end_s=case['end_s']))))
    design = baseline.realize(600902, 'wind+bias_mixed', geometry='observed',
        trajectory_input=spec, turn_schedule=case['schedule_minutes'])
    problem = baseline.geometry_problem(design, case['schedule_minutes'], case['crab_model'])
    count = envelope_size(problem)
    return dict(state='prepared_only_requires_compute_approval', track_id=case['track_id'],
        start_s=case['start_s'], end_s=case['end_s'], trajectory_input=spec,
        schedule_minutes=case['schedule_minutes'], crab_model=case['crab_model'], comparison=PAIR,
        envelope_assumptions=envelope_assumptions(problem.settings), svd_evaluations=count,
        seconds_estimate=count * prior['elapsed_s'] / prior['svd_evaluations'], wall_seconds_cap=120,
        implementation_hash=baseline.implementation_hash(),
        numerical_environment=numerical_environment(), numerical_environment_hash=numerical_environment_hash(),
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), input_sha256=inputs,
        additional_flight_attempts=0,
        limitations=['Selected adaptively after development timing screening; not independent evidence.',
            'Only the registered finite physical-wind envelope and one partial comparison.',
            'Broader wind fails nominal retention; physical wind/TAS assumptions still need justification.',
            'Assumed interpolated geometry and supplied axes; no recovered-axis or full-pipeline certification.',
            'No simulated flight, nonlinear fit, power, calibrated threshold or Earth-model decision.'])


def execute(plan):
    if not isinstance(plan['wall_seconds_cap'], (int, float)) or not 0 < plan['wall_seconds_cap'] <= 120:
        raise ValueError('envelope time cap must be positive and at most120seconds')
    if plan['implementation_hash'] != baseline.implementation_hash():
        raise ValueError('scientific implementation changed')
    if plan['numerical_environment_hash'] != numerical_environment_hash():
        raise ValueError('numerical environment changed')
    if plan['helper_sha256'] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError('envelope helper changed')
    for relative, expected in plan['input_sha256'].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
            raise ValueError('recorded input changed')
    began = time.monotonic()
    def deadline(signum, frame):
        raise TimeoutError('authorized envelope wall-time cap reached')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, plan['wall_seconds_cap'])
    try:
        design = baseline.realize(600902, 'wind+bias_mixed', geometry='observed',
            trajectory_input=plan['trajectory_input'], turn_schedule=plan['schedule_minutes'])
        problem = baseline.geometry_problem(design, plan['schedule_minutes'], plan['crab_model'])
        report = envelope_information(problem)
        criterion = contrast_eligibility(dict(rank_threshold=report['rank_threshold'],
            model_contrast_information=report['untruncated_contrasts']), plan['comparison'])
        result = dict(state='registered_pair_envelope_complete', report=report, criterion=criterion)
    except TimeoutError as exc:
        result = dict(state='wall_time_cap_reached_no_envelope_claim', failure=str(exc))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.)
        signal.signal(signal.SIGALRM, previous)
    return dict(**result, elapsed_s=time.monotonic() - began,
        plan_sha256=hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest(),
        implementation_hash=plan['implementation_hash'],
        numerical_environment_hash=plan['numerical_environment_hash'],
        comparison=plan['comparison'], additional_flight_attempts=0, error_rate_validated=False,
        limitations=plan['limitations'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--run', action='store_true', help='requires separately approved compute budget')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.run:
        if args.output is None:
            parser.error('--run requires --output')
        if args.output.exists():
            parser.error('output already exists; completed checks must not be silently replaced')
        result = execute(json.loads(args.plan.read_text()))
        with args.output.open('x') as out:
            out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
        print(json.dumps({k: result[k] for k in ('state', 'elapsed_s', 'comparison')}))
    else:
        plan = prepare()
        with args.plan.open('x') as out:
            out.write(json.dumps(plan, indent=2, allow_nan=False) + '\n')
        print(json.dumps({k: plan[k] for k in ('track_id', 'schedule_minutes', 'svd_evaluations', 'seconds_estimate', 'wall_seconds_cap')}))
