# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze a fresh smoother-route/matched-reference pilot; preparation never runs flights."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'analysis'),str(ROOT/'analysis'/'tests')]

from lll.campaign_shards import build_plan,task_at
from lll.design_geometry import geometry_kinematics
from lll.forward_reference import FORWARD_REFERENCE_POLICY
from lll.inference_policy import digest
from lll.maneuvers import maneuver_mask,turn_motion_check
from lll.research_design import freeze_manifest,realize
from lll.trajectory import TrackReplay


def prepare(output):
    old_path=ROOT/'docs/airline-pilot-preparation-20261006/plan.json'
    route_path=ROOT/'docs/airline-pilot-preparation-20261006/smooth-trajectory.json'
    old=json.loads(old_path.read_text())
    route=json.loads(route_path.read_text()); TrackReplay(route)
    jobs=[{**job,'forward_reference':'matched'} for job in old['jobs']]
    config={**old['manifest']['config'],'seed':600901,'trajectory_input':route,
            'candidate_jobs':jobs,
            'preregistered_geometry_cells':['trajectory-'+route['trajectory_hash']],
            'evidence_use':'fresh matched-reference and C2 latent-route development pilot only; no coverage or decision claim',
            'forward_reference_policy':dict(FORWARD_REFERENCE_POLICY),
            'source_inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (old_path,route_path,Path(__file__))},
            'authorized_additional_attempts':0,'execution_authorized':False}
    design=realize(config['seed'],config['scenarios'][0],geometry='observed',
                   trajectory_input=route,turn_schedule=config['turn_schedule'])
    kin,_=geometry_kinematics(design)
    mask=maneuver_mask(kin,buffer_s=120.)
    checks=[dict(minute=m,**turn_motion_check(mask,m*60.-1.,m*60.+design['simulator']['turn_seconds']+20.))
            for m in config['turn_schedule']]
    if not all(c['safe'] for c in checks):
        raise ValueError('smooth-route schedule fails declared buffered maneuver mask')
    plan=build_plan(freeze_manifest(config),jobs,shards=2)
    first=[task_at(plan,i) for i in range(3)]
    review=dict(state='prepared_not_run',plan_hash=plan['plan_hash'],
                implementation_hash=plan['manifest']['implementation_hash'],
                numerical_environment_hash=plan['manifest']['numerical_environment_hash'],
                proposed_evaluations=plan['task_count'],initial_proposed_evaluations=3,
                authorized_evaluations=0,completed_evaluations=0,
                first_tasks=[{**{k:t[k] for k in ('index','task_id','truth','scenario','seed')},
                              'candidate_id':digest(t['fit_options'])} for t in first],
                turn_checks=checks,
                limitations=['Matched-angle covariance remains uncalibrated; independent predictor-error assumption.',
                    'C2 between-fix motion and natural endpoint curvature are assumptions, not observed aircraft behavior.',
                    'Small real aircraft corrections are physical motion; controlled tests do not measure their actual population.',
                    'No IMU hardware qualification, full-pipeline successful runtime or rare-error validation.',
                    'Three planned candidates share generating conditions; failures are spent attempts, not retries.'])
    output.mkdir(parents=True,exist_ok=False)
    for name,data in (('plan.json',plan),('preparation-review.json',review)):
        (output/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    return review


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.output),allow_nan=False))
