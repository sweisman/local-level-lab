# SPDX-License-Identifier: AGPL-3.0-or-later
"""Summarize the six completed matched replay tasks; no simulations, fits or thresholds."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


def review(directory):
    campaign_path = directory / 'campaign.json'
    campaign = json.loads(campaign_path.read_text())
    status = json.loads((directory / 'status.json').read_text())
    plan = json.loads((directory / 'plan.json').read_text())
    if status['state'] != 'complete' or status['completed'] != 6 or not campaign['execution']['complete']:
        raise ValueError('requires the completed six-attempt replay')
    records = campaign['records']
    if [r['task_index'] for r in records] != list(range(6)) or len({r['task_id'] for r in records}) != 6:
        raise ValueError('replay task IDs are missing or duplicated')
    if plan['plan_hash'] != campaign['sharded_plan_hash'] or plan['task_count'] != 6:
        raise ValueError('merged campaign does not match the frozen six-task plan')
    paired = []
    for truth in plan['truths']:
        rows = [r for r in records if r['truth'] == truth]
        if len(rows) != 2 or {r['fit_options']['crab_model'] for r in rows} != {'wind', 'wind_tas'}:
            raise ValueError('each truth requires exactly the two declared wind candidates')
        available = all(r.get('design') is not None for r in rows)
        if len({r['seed'] for r in rows}) != 1 or (available and rows[0]['design'] != rows[1]['design']):
            raise ValueError('candidate comparison does not share generating conditions')
        paired.append(dict(truth=truth, seed=rows[0]['seed'],
                           generating_design_matches=True if available else None))
    cases = []
    for r in records:
        forward = r.get('forward_axis') or {}
        design = r.get('design_identifiability') or {}
        pairwise = r.get('pairwise') or {}
        cases.append(dict(task_index=r['task_index'], task_id=r['task_id'], truth=r['truth'],
            crab_model=r['fit_options']['crab_model'], failure=r.get('failure'), elapsed_s=r['elapsed_s'],
            converged=(r.get('convergence') or {}).get('converged'),
            model_test_rank=r.get('model_test_rank'), design_rank=design.get('estimable_rank'),
            forward_sigma_deg=math.degrees(forward['angle_sigma_rad']) if forward.get('angle_sigma_rad') is not None else None,
            forward_method=forward.get('reference_method'), forward_gain=forward.get('gain'), forward_r2=forward.get('r2'),
            domain_observables=r.get('domain_observables'), heading_diversity=r.get('heading_diversity'),
            exclusions=r.get('exclusions'), bootstrap_requested=r['fit_options']['n_boot'],
            design_untruncated_contrasts=design.get('untruncated_contrasts'),
            pairwise={name: {key: value.get(key) for key in
                ('eligible', 'status', 'preferred_model', 'calibrated', 'exclusions', 'estimate', 'sd',
                 'statistics', 'converged', 'design_information', 'bootstrap')}
                for name, value in pairwise.items()},
            watchdog_excluded_segments=(r.get('slip') or {}).get('exclude_segments'),
            wind_tas=r.get('wind_tas'), wind_tas_test_near_boundary=r.get('wind_tas_test_near_boundary')))
    launch = json.loads((directory / 'launch.json').read_text())
    finish = datetime.fromtimestamp((directory / 'status.json').stat().st_mtime, timezone.utc)
    start = datetime.fromisoformat(launch['started_utc'])
    names = sorted({name for c in cases for name in c['pairwise']})
    return dict(state='six_task_replay_review_complete', cases=cases, paired_generating_conditions=paired,
        execution=campaign['execution'], plan_hash=plan['plan_hash'],
        implementation_hash=campaign['implementation_hash'],
        campaign_sha256=hashlib.sha256(campaign_path.read_bytes()).hexdigest(),
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        processing_failures=sum(c['failure'] is not None for c in cases),
        converged=sum(c['converged'] is True for c in cases),
        pairwise_eligible_counts={name: sum(c['pairwise'].get(name, {}).get('eligible') is True for c in cases) for name in names},
        pairwise_abstention_counts={name: sum(c['pairwise'].get(name, {}).get('status') == 'abstain' for c in cases) for name in names},
        known_attempt_seconds=campaign['elapsed_s'], observed_wall_seconds=(finish - start).total_seconds(),
        wall_time_basis='original-host launch UTC to captured final status file mtime',
        captured_finish_mtime_utc=finish.isoformat(), remaining_authorized_attempts=0,
        limitations=['One development generating seed per truth; matched candidates are not independent null draws.',
            'Coarse real positions, assumed interpolated motion, simulated high-rate GPS/IMU; no hardware evidence.',
            'Eligible pairwise geometry is not a calibrated decision or a power estimate.',
            'Zero bootstrap and no empirical thresholds; profile endpoint diagnostics are uncalibrated.',
            'Do not interpret a pair coordinate as a three-model winner, especially when truth is outside that pair.',
            'All six attempts are spent; no retry, calibration, validation, promotion or extra attempt follows.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review(args.directory)
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('state', 'processing_failures', 'converged',
        'pairwise_eligible_counts', 'pairwise_abstention_counts', 'observed_wall_seconds')}))
