# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze the authorized six-task full-pipeline development replay; never launches it."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'analysis'), str(ROOT / 'analysis/tests')]

from lll.campaign_shards import build_plan, task_at
from lll.design_geometry import geometry_kinematics
from lll.maneuvers import maneuver_mask, turn_motion_check
from lll.research_design import freeze_manifest, realize
from lll.trajectory import TrackReplay

ENVELOPE = ROOT / 'docs/research-next-stage-20261006/observed-pair-envelope-plan.json'
RESULT = ROOT / 'docs/research-next-stage-20261006/observed-pair-envelope-result.json'
PREVIOUS = ROOT / 'docs/extended-airline-pilot-20261006/plan.json'


def prepare(output):
    envelope = json.loads(ENVELOPE.read_text())
    result = json.loads(RESULT.read_text())
    expected = hashlib.sha256(json.dumps(envelope, sort_keys=True).encode()).hexdigest()
    if (result['plan_sha256'] != expected or result['state'] != 'registered_pair_envelope_complete'
            or not result['criterion']['all_estimable']):
        raise ValueError('requires the completed passing envelope bound to its frozen plan')
    old = json.loads(PREVIOUS.read_text())
    route = envelope['trajectory_input']
    TrackReplay(route)
    jobs = old['jobs'][:2]
    if [j['crab_model'] for j in jobs] != ['wind', 'wind_tas']:
        raise ValueError('expected exactly the two declared wind candidates')
    config = {**old['manifest']['config'], 'seed': 600910, 'seeds': 1, 'truth': 'all',
        'scenario': 'wind+bias_mixed', 'scenarios': ['wind+bias_mixed'],
        'preregistered_scenarios': ['wind+bias_mixed'], 'trajectory_input': route,
        'turn_schedule': envelope['schedule_minutes'], 'candidate_jobs': jobs,
        'preregistered_geometry_cells': ['trajectory-' + route['trajectory_hash']],
        'evidence_use': 'matched full-pipeline development replay of one partial design control; no calibration or validation',
        'source_inputs': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (ENVELOPE, RESULT, PREVIOUS, Path(__file__))},
        'authorized_additional_attempts': 6, 'execution_authorized': True,
        'authorization': 'User go on2026-10-07 after proposal for three truths, both wind candidates, combined wind and IMU drift.'}
    design = realize(config['seed'], config['scenario'], geometry='observed',
                     trajectory_input=route, turn_schedule=config['turn_schedule'])
    kin, duration = geometry_kinematics(design)
    mask = maneuver_mask(kin, buffer_s=120.)
    checks = [dict(minute=m, **turn_motion_check(mask, m * 60 - 1., m * 60 + 25.))
              for m in config['turn_schedule']]
    if not all(c['safe'] for c in checks):
        raise ValueError('frozen schedule fails the buffered motion checks')
    plan = build_plan(freeze_manifest(config), jobs, shards=2)
    if plan['task_count'] != 6:
        raise ValueError('authorization covers exactly six task attempts')
    review = dict(state='frozen_authorized_not_launched', plan_hash=plan['plan_hash'],
        implementation_hash=plan['manifest']['implementation_hash'],
        numerical_environment_hash=plan['manifest']['numerical_environment_hash'],
        authorized_evaluations=6, completed_evaluations=0, seed=config['seed'],
        track_id=route['track_id'], trajectory_hash=route['trajectory_hash'],
        window_seconds=[envelope['start_s'], envelope['end_s']],
        turn_schedule=config['turn_schedule'], turn_checks=checks,
        tasks=[{k: task_at(plan, i)[k] for k in ('index', 'task_id', 'truth', 'scenario', 'seed', 'fit_options')}
               for i in range(6)],
        limitations=['One shared development seed across three truths and two candidates; not independent trials.',
            'Observed positions with assumed C2 between-fix motion and simulated high-rate GNSS/IMU.',
            'Matched forward reference recovers axes from generated measurements; does not substitute known design axes.',
            'Complete nonlinear analysis and pairwise profiles, zero bootstrap for geometry/preprocessing diagnosis.',
            'No empirical thresholds, validated decisions, calibration, production promotion or additional flights.',
            'Each started task, including failures or interruption, spends one attempt and must never be retried.'])
    output.mkdir(parents=True, exist_ok=False)
    for name, content in (('plan.json', plan), ('preparation-review.json', review)):
        (output / name).write_text(json.dumps(content, indent=2, allow_nan=False) + '\n')
    return review


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.output)
    print(json.dumps({k: result[k] for k in ('state', 'plan_hash', 'implementation_hash',
                                            'authorized_evaluations', 'seed', 'track_id')}))
