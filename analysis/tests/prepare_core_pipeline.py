# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze prospective replay/timing inputs and cost bounds; never run a flight or search."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

from lll import models
from lll.inference_policy import digest
from lll.maneuvers import maneuver_mask,turn_motion_check
from lll.design_geometry import geometry_kinematics
from lll.research_design import realize,freeze_manifest,validate_turn_schedule,plain
from lll.trajectory import track_spec
from optimize_turns import search_geometry

ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=['bias_mixed','wind','wind+bias_mixed','wind+bias_mixed+correlated+thermal']
CANDIDATES=[dict(research_candidate=True,crab_model=crab,bias_model='dynamic',noise_model='axis_segment',
    forward_uncertainty=True,n_boot=0,**extra) for crab,extra in itertools.product(
        ['dynamic','wind'],[{},dict(design_mode='envelope',pairwise_method='profile')])]


def prepare(track_plan,protocol_manifest,audit,output):
    source=json.loads(track_plan.read_text())
    history=json.loads(protocol_manifest.read_text())
    timing=json.loads(audit.read_text())
    tracks=source['observed_track_cases']
    if len({v['id'] for v in tracks})!=len(tracks): raise ValueError('duplicate track IDs')
    output.mkdir(parents=True,exist_ok=False)
    inputs=output/'trajectories'; inputs.mkdir()
    replay_inputs=[]; grids=[]; blocked=[]
    for case in tracks:
        if case['status']!='prepared_geometry_only':
            blocked.append({k:case[k] for k in ('id','status','source_sha256','candidate_window')})
            continue
        for mode in ('observed_fixes','simulated_high_rate'):
            spec=track_spec(case,mode)
            name=f"{case['id']}-{mode}.json"
            (inputs/name).write_text(json.dumps(spec,indent=2,allow_nan=False)+'\n')
            replay_inputs.append(dict(track_id=case['id'],mode=mode,path='trajectories/'+name,
                trajectory_hash=spec['trajectory_hash'],source_sha256=case['source_sha256'],
                turn_schedule_min=[5.,25.,45.,65.],state='unrun control; not optimized or certified'))
            if mode=='simulated_high_rate':
                design=realize(600600,'wind+bias_mixed',geometry='observed',trajectory_input=spec)
                estimate=search_geometry([design],estimate_only=True)
                kin,_=geometry_kinematics(design)
                mask=maneuver_mask(kin,buffer_s=120.)
                checks=[dict(minute=m,**turn_motion_check(mask,m*60.-1.,m*60.+25.)) for m in [5.,25.,45.,65.]]
                grids.append(dict(track_id=case['id'],**estimate,control_turn_checks=checks,
                    prospective_objectives=['all contrasts',*models_pair_names()]))
    revised=history['config']['protocols']['repeated-opposing-directions-90min']
    arms=[dict(name=name,protocol=p) for name,p in history['config']['protocols'].items()]
    for shift in (-10.,-5.,5.,10.):
        schedule=list(revised['turn_schedule']); schedule[1]+=shift
        arms.append(dict(name=f'second-turn-shift-{shift:+g}',protocol={**revised,'turn_schedule':schedule}))
    arms.append(dict(name='timing-correction',protocol={**revised,
        'turn_schedule':timing['timing_only_proposal']['turn_schedule_min']}))
    for arm in arms:
        p=arm['protocol']; schedule=p['turn_schedule']
        try:
            validate_turn_schedule(schedule,sum(v[1] for v in p['legs']),10.,5.)
        except ValueError as exc:
            arm.update(state='blocked by unchanged spacing/edge rule',failure=str(exc),eligible_to_schedule=False)
            continue
        design=realize(600600,'wind+bias_mixed',geometry='fixed',protocol=p)
        kin,_=geometry_kinematics(design); mask=maneuver_mask(kin,buffer_s=120.)
        checks=[dict(minute=m,**turn_motion_check(mask,m*60.-1.,m*60.+25.)) for m in schedule]
        arm.update(state='unrun matched diagnostic',eligible_to_schedule=True,
            maneuver_checks=checks,optimizer_feasible=all(v['safe'] for v in checks),
            interpretation='unsafe controls must abstain; never deploy as a turn recommendation')
    valid_arms=sum(a['eligible_to_schedule'] for a in arms)
    factor=3*len(models.MODELS)*len(SCENARIOS)*len(CANDIDATES)
    baseline_seconds=None
    status_path=protocol_manifest.parent/'status.json'
    if status_path.exists():
        summary=json.loads(status_path.read_text())
        # Historical timing is a baseline only: the new envelope/profile costs are unmeasured.
        elapsed=summary.get('charged_s')
        count=summary.get('completed_evaluations')
        if elapsed and count: baseline_seconds=elapsed/count
    config=dict(partition='development',state='prepared_not_run',execution_authorized=False,
        authorized_additional_attempts=0,seeds=[600600,600601,600602],truths=list(models.MODELS),
        scenarios=SCENARIOS,candidates=CANDIDATES,bootstrap=0,diagnostics_required=True,
        replay_inputs=replay_inputs,blocked_tracks=blocked,matched_timing_arms=arms,
        seed_pairing='same sensor/nuisance/bootstrap streams across schedule, crab and candidate arms; not independent cells',
        comparison_protocol='matched original/shifted/corrected controls; safety failures retained as abstentions',
        source_inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (track_plan,protocol_manifest,audit,*([status_path] if status_path.exists() else []))},
        preparation_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        cost=dict(proposed_replay_attempts=len(replay_inputs)*factor,
            proposed_matched_timing_attempts=valid_arms*factor,
            proposed_total_attempts=(len(replay_inputs)+valid_arms)*factor,
            historical_seconds_per_attempt=baseline_seconds,
            new_seconds_per_attempt=None,estimated_new_runtime=None,
            optimizer_svd_upper_per_objective=sum(v['upper_bound_anchor_svd_evaluations'] for v in grids),
            optimizer_objective_count=4,optimizer_fits=0,
            pricing_status='New runtime and storage must be measured in an authorized bounded pilot; historical cost is not a quote'),
        evidence_scope='Prepared inputs and maneuver masks only; no new flight, optimizer search, SVD study, calibration or validation')
    manifest=freeze_manifest(plain(config))
    (output/'proposal.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    (output/'optimizer-estimates.json').write_text(json.dumps(grids,indent=2,allow_nan=False)+'\n')
    return manifest


def models_pair_names():
    from lll.policy import MODEL_PAIRS
    return list(MODEL_PAIRS)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    manifest=prepare(ROOT/'docs/research-next-stage-20261006/geometry-stress-plan.json',
        ROOT/'docs/protocol-development-20261006/manifest.json',
        ROOT/'docs/protocol-development-20261006/processing-audit.json',args.output)
    config=manifest['config']
    print(json.dumps(dict(state=config['state'],prepared_replays=len(config['replay_inputs']),
        blocked_tracks=len(config['blocked_tracks']),proposed_attempts=config['cost']['proposed_total_attempts'],
        authorized_attempts=0)))


if __name__=='__main__': main()
