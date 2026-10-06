# SPDX-License-Identifier: AGPL-3.0-or-later
"""Summarize completed saved pilot records; no numerical analysis or new attempts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


def review(directory):
    source=directory/'campaign.json'
    campaign=json.loads(source.read_text())
    status=json.loads((directory/'status.json').read_text())
    if status['state']!='budget_complete' or status['completed']!=3:
        raise ValueError('review expects the completed approved three-attempt prefix')
    if [r['task_index'] for r in campaign['records']]!=[0,1,2]:
        raise ValueError('missing or duplicate pilot tasks')
    launch=json.loads((directory/'launch.json').read_text())
    finished=datetime.fromtimestamp((directory/'status.json').stat().st_mtime,timezone.utc)
    started=datetime.fromisoformat(launch['started_utc'])
    cases=[]
    for r in campaign['records']:
        design=r.get('design_identifiability') or {}
        forward=r.get('forward_axis') or {}
        tas=r.get('wind_tas') or {}
        comparison=r.get('magnetic_ambiguity_comparison') or {}
        cases.append(dict(task_index=r['task_index'],task_id=r['task_id'],
            crab_model=r['fit_options']['crab_model'],
            magnetic_ambiguity=r['fit_options'].get('magnetic_ambiguity','exclude'),
            failure=r.get('failure'),elapsed_s=r['elapsed_s'],
            converged=(r.get('convergence') or {}).get('converged'),
            model_test_rank=r.get('model_test_rank'),
            design_rank=design.get('estimable_rank'),svd_evaluations=design.get('svd_evaluations'),
            design_contrasts=design.get('model_contrast_information'),
            untruncated_contrasts=design.get('untruncated_contrasts'),
            retention_threshold=design.get('rank_threshold'),
            forward_sigma_deg=math.degrees(forward['angle_sigma_rad']) if forward.get('angle_sigma_rad') else None,
            forward_gain=forward.get('gain'),forward_r2=forward.get('r2'),
            domain_observables=r.get('domain_observables'),
            exclusions=r.get('exclusions'),
            pairwise={name:{k:v.get(k) for k in ('eligible','decision','exclusions')}
                      for name,v in (r.get('pairwise') or {}).items()},
            watchdog_excluded_segments=(r.get('slip') or {}).get('exclude_segments'),
            wind_tas_speed_constraint_chi2=tas.get('speed_constraint_chi2'),
            wind_tas_relative_margin=tas.get('relative_margin'),
            wind_tas_near_boundary=tas.get('near_boundary'),
            magnetic_comparison=comparison))
    return dict(state='approved_prefix_complete_no_eligible_contrasts',
        campaign_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        implementation_hash=campaign['implementation_hash'],plan_hash=campaign['sharded_plan_hash'],
        execution=campaign['execution'],known_attempt_seconds=campaign['elapsed_s'],
        observed_wall_seconds=(finished-started).total_seconds(),
        wall_time_basis='launch UTC to final status filesystem mtime on original host',
        captured_finish_mtime_utc=finished.isoformat(),
        run_storage_snapshot_bytes=sum(p.stat().st_size for p in directory.rglob('*') if p.is_file()),
        remaining_authorized_evaluations=0,cases=cases,
        interpretation='One generating condition under three matched candidates, bootstrap zero; no error-rate, coverage or model winner claim. Do not spend remaining proposed cases without a new budget and reviewed geometry.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=review(args.directory)
    with args.output.open('x') as out:
        out.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},allow_nan=False))
