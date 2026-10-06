# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze the screened extended-route pilot without executing any flight."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import preflight_route_turns as screen
from lll.campaign_shards import build_plan, task_at
from lll.research_design import freeze_manifest
from lll.trajectory import TrackReplay, smooth_track_spec, track_spec

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'docs/flight-geometry-20261006/normalized-tracks.json.gz'
REVIEW = ROOT / 'docs/matched-airline-pilot-20261006/extended-window-preflight.json'
OLD = ROOT / 'docs/matched-airline-pilot-20261006/plan.json'


def prepare(output):
    review = json.loads(REVIEW.read_text())
    candidates = [c for c in review['cases'] if c['minutes'] == 120. and c.get('best_schedule')]
    chosen = max(candidates, key=lambda c: (c['best_schedule']['heading_duration_margin_seconds'],
                 c['best_schedule']['screened_minutes'], -c['start_s']))
    with gzip.open(ARCHIVE, 'rt') as source: bundle = json.load(source)
    track = next(t for t in bundle['tracks'] if t['id'] == chosen['track_id'])
    rows = [r for r in track['rows'] if chosen['start_s'] <= r['t_s'] <= chosen['end_s']]
    route = smooth_track_spec(track_spec(dict(id=track['id'], source_sha256=track['source_sha256'],
        status='prepared_geometry_only', rows=rows,
        candidate_window=dict(start_s=chosen['start_s'], end_s=chosen['end_s']))))
    TrackReplay(route)
    if route['trajectory_hash'] != chosen['trajectory_hash']:
        raise ValueError('prepared route differs from reviewed trajectory')
    old = json.loads(OLD.read_text())
    config = {**old['manifest']['config'], 'seed':600902, 'trajectory_input':route,
        'turn_schedule':chosen['best_schedule']['schedule_minutes'],
        'preregistered_geometry_cells':['trajectory-' + route['trajectory_hash']],
        'evidence_use':'fresh extended airline-route development pilot; no independent validation or coverage claim',
        'source_inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (ARCHIVE, REVIEW, OLD, Path(screen.__file__), Path(__file__))},
        'authorized_additional_attempts':0, 'execution_authorized':False}
    plan = build_plan(freeze_manifest(config), old['jobs'], shards=2)
    report = dict(state='prepared_not_run', plan_hash=plan['plan_hash'],
        implementation_hash=plan['manifest']['implementation_hash'],
        numerical_environment_hash=plan['manifest']['numerical_environment_hash'],
        seed=600902, selected_window=chosen, proposed_evaluations=plan['task_count'],
        initial_proposed_evaluations=3, authorized_evaluations=0, completed_evaluations=0,
        first_tasks=[{k:task_at(plan, i)[k] for k in ('index','task_id','truth','scenario','seed')}
                     for i in range(3)],
        runtime_basis='Previous 75-minute prefix: 202.842514 attempt-seconds, 131.358896 wall-seconds; extended route runtime unknown.',
        limitations=['Chosen using observable development screens, not a nuisance-envelope optimizer.',
            'C2 between-fix motion and reported altitude remain assumptions.',
            'Forward reference, complete preprocessing and model contrast retention untested here.',
            'Zero bootstrap; one generating condition shared across initial three candidates.',
            'No new flights, remaining 15 evaluations, calibration, validation or git operations authorized.'])
    output.mkdir(parents=True, exist_ok=False)
    for name, data in (('plan.json',plan),('preparation-review.json',report)):
        (output / name).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    r = prepare(args.output)
    print(json.dumps({k:r[k] for k in ('state','plan_hash','implementation_hash','seed',
                                     'proposed_evaluations','authorized_evaluations')}))
