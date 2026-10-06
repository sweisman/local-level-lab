# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review assumed route geometry and freeze an unrun matched pilot; no fits or SVDs."""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from lll.campaign_shards import build_plan, task_at
from lll.design_envelope import ENVELOPE_ASSUMPTIONS, PHYSICAL_ENVELOPE_ASSUMPTIONS, nuisance_states
from lll.design_geometry import geometry_kinematics
from lll.inference_policy import INFERENCE_POLICY, digest
from lll.maneuvers import maneuver_mask, turn_motion_check
from lll.mount_yaw import MOUNT_YAW_POLICY
from lll.research_design import freeze_manifest, plain, realize, validate_turn_schedule
from lll.trajectory import TrackReplay
from lll.wind_tas import WIND_TAS_POLICY, WindTAS

ROOT=Path(__file__).resolve().parents[2]
CORE=ROOT/'docs/core-pipeline-20261006'
SELECTED='2026-10-02-lufthansa-572-fra-jnb'
SCHEDULE=[20.,40.,60.]
SCENARIOS=['wind+bias_mixed','wind+bias_mixed+correlated+thermal']


def summary(values):
    values=np.asarray(values,float)
    values=values[np.isfinite(values)]
    if not len(values): return None
    return dict(min=float(values.min()),median=float(np.median(values)),p95=float(np.quantile(values,.95)),max=float(values.max()))


def speed_state_review(kin):
    """Compare all frozen physical envelope states with their speed constraint.

    This is a feasibility diagnostic, not an identifiability score or a reason
    to prune an inconvenient envelope state. No science Jacobian is evaluated.
    """
    keep=np.isfinite(kin['v_n']) & np.isfinite(kin['v_e']) & np.isfinite(kin['psi_dot'])
    keep &= kin['speed']>=WIND_TAS_POLICY['minimum_ground_speed_mps']
    # Ten-second sampling measures the assumed path's behavior, not public-fix accuracy.
    indices=np.flatnonzero(keep & (np.arange(len(keep))%10==0))
    if len(indices)<2: return dict(available=False,reason='insufficient supported cruise ground vectors')
    bins={k:np.asarray(kin[k])[indices] for k in ('t','v_n','v_e','psi_dot')}
    wind=WindTAS(bins,WIND_TAS_POLICY)
    problem=SimpleNamespace(nc=wind.npar,wind_tas=wind,knots=wind.knots)
    states=[]
    for name,q in nuisance_states(problem):
        residual=wind.speed_constraint(q)
        states.append(dict(state=name,absolute_speed_residual_mps=summary(abs(residual)*WIND_TAS_POLICY['ground_constraint_sigma_mps']),
                           fraction_within_3_constraint_sigma=float(np.mean(abs(residual)<=3.))))
    # Use the independently prescribed wind for a separate diagnostic of the latent TAS
    # implied by the observed ground path. Do not fit wind or TAS to make the path agree.
    t=bins['t']; truth_wind=np.array([12.,-8.])+t[:,None]/3600*np.array([3.,-2.])
    tas=np.linalg.norm(np.column_stack([bins['v_n'],bins['v_e']])-truth_wind,axis=1)
    knots=wind.knots
    # Exact sampled knot values with linear log interpolation: fixed geometry diagnostic,
    # neither optimal projection onto the spline nor a fitted airspeed observation.
    q=np.zeros(wind.npar).reshape(-1,3)
    q[:,:2]=np.array([12.,-8.])+knots[:,None]/3600*np.array([3.,-2.])
    q[:,2]=np.interp(knots,t,np.log(tas/WIND_TAS_POLICY['tas_reference_mps']))
    residual=wind.speed_constraint(q.ravel())
    return dict(available=True,sample_seconds=10,states=states,
        state_count=len(states),states_with_every_sample_within_3_sigma=sum(s['fraction_within_3_constraint_sigma']==1. for s in states),
        independently_prescribed_wind_ne_mps=[12.,-8.],independently_prescribed_wind_rate_ne_mps_per_h=[3.,-2.],
        implied_true_airspeed_mps=summary(tas),
        knot_interpolation_speed_residual_mps=summary(abs(residual)*WIND_TAS_POLICY['ground_constraint_sigma_mps']),
        knot_interpolation_fraction_within_3_constraint_sigma=float(np.mean(abs(residual)<=3.)),
        interpretation='Off-manifold states and knot mismatch are diagnostics only. No state removed, constraint changed, SVD scored or model fitted.')


def route_review(spec,seed=600900):
    replay=TrackReplay(spec)
    design=realize(seed,'wind+bias_mixed',geometry='observed',trajectory_input=spec,turn_schedule=SCHEDULE)
    kin,duration=geometry_kinematics(design)
    supported=replay.support(kin['t'])
    valid=supported & np.isfinite(kin['speed']) & np.isfinite(kin['psi_dot']) & np.isfinite(kin['vz'])
    validate_turn_schedule(SCHEDULE,duration/60.,10.,5.)
    mask=maneuver_mask(kin,buffer_s=120.)
    turns=[dict(minute=m,**turn_motion_check(mask,m*60.-1.,m*60.+design['simulator']['turn_seconds']+20.)) for m in SCHEDULE]
    short_blocks=[dict(start_s=max(0.,a),end_s=min(duration,b)) for a,b,_ in replay.blocks if b>=0 and a<=duration]
    times=np.asarray([r['t_s']-spec['start_s'] for r in spec['rows'] if not r.get('is_provider_estimate')],float)
    within=(times>=0)&(times<=duration)
    public_intervals=np.diff(times[within])
    # Report source speed versus assumed path derivative only at actual supported rows.
    rows=[r for r in spec['rows'] if not r.get('is_provider_estimate') and spec['start_s']<=r['t_s']<=spec['end_s']]
    row_t=np.array([r['t_s']-spec['start_s'] for r in rows],float)
    path=replay.sample(row_t)
    reported=np.array([r.get('ground_speed_mps',np.nan) for r in rows],float)
    return dict(track_id=spec['track_id'],trajectory_hash=spec['trajectory_hash'],mode=spec['mode'],
        status='assumed-path review only; not reconstructed IMU, receiver accuracy or scientific eligibility',
        duration_minutes=duration/60.,supported_fraction_on_1s_grid=float(np.mean(supported)),
        supported_intervals=short_blocks,public_observation_interval_seconds=summary(public_intervals),
        assumed_ground_speed_mps=summary(kin['speed'][valid]),assumed_vertical_speed_mps=summary(abs(kin['vz'][valid])),
        assumed_latitude_deg=summary(np.degrees(kin['lat'][valid])),
        reported_minus_assumed_speed_mps=summary(reported-path['speed']),
        proposed_turns=turns,all_proposed_turns_pass_assumed_mask=all(v['safe'] for v in turns),
        physical_speed_review=speed_state_review(kin),
        assumptions=dict(interpolation=spec['interpolation'],altitude=spec['altitude_assumption'],clock=spec['clock_assumption'],
            accuracy='Dense GPS is simulated; latent motion between public fixes is assumed, not observed',
            maneuver_mask='Two-minute buffered assumed-path mask; actual reconstruction may differ'))


def candidate_jobs():
    common=dict(n_boot=0,bootstrap_sampling='moving',block_length=15,noise_model='axis_segment',bootstrap_refit='nonlinear',
        forward_uncertainty=True,crab_rate_sigma_dph=1.,crab_knot_seconds=None,research_candidate=True,
        bias_model='dynamic',bias_knot_seconds=INFERENCE_POLICY['bias_knot_seconds'],
        bias_rw_sigma_dph_sqrth=INFERENCE_POLICY['bias_rw_sigma_dph_sqrth'],rank_min_relative_margin=0.,
        design_mode='envelope',pairwise_method='profile')
    return [{**common,'crab_model':'wind'}, {**common,'crab_model':'wind_tas'},
            {**common,'crab_model':'wind_tas','magnetic_ambiguity':'model_and_compare'}]


def prepare(output,core=CORE):
    core=Path(core); output=Path(output)
    original=json.loads((core/'proposal.json').read_text())
    cases=[c for c in original['config']['replay_inputs'] if c['mode']=='simulated_high_rate']
    if any(Path(c['path']).parent!=Path('trajectories') or Path(c['path']).suffix!='.json' for c in cases):
        raise ValueError('prepared trajectory paths must be explicit files in the documented trajectories directory')
    files=[core/c['path'] for c in cases]
    specs=[json.loads(path.read_text()) for path in files]
    if len({s['track_id'] for s in specs})!=len(specs): raise ValueError('duplicate archived track IDs')
    review=[route_review(spec) for spec in specs]
    selected=next(s for s in specs if s['track_id']==SELECTED)
    selected_review=next(r for r in review if r['track_id']==SELECTED)
    if not selected_review['all_proposed_turns_pass_assumed_mask']:
        raise ValueError('selected timing control fails current assumed-path maneuver mask')
    jobs=candidate_jobs()
    cell='trajectory-'+selected['trajectory_hash']
    hashes={str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [core/'proposal.json',*files,Path(__file__)]}
    config=dict(partition='development',seed=600900,seeds=1,truth='all',scenario='drift+0',scenarios=SCENARIOS,
        geometry='observed',variant='spp',bootstrap=0,flight_domain=None,trajectory_input=selected,
        protocol=None,same_side_up_turns=False,turn_schedule=SCHEDULE,turn_min_spacing=10.,turn_edge_margin=5.,
        preregistered_scenarios=SCENARIOS,preregistered_geometry_cells=[cell],
        decision_policy_hash=None,pairwise_decision_policy_hash=None,
        pairwise_evidence=True,design_mode='envelope',pairwise_method='profile',
        evidence_use='matched development timing/storage and assumption diagnostic only; no threshold or tail evidence',
        source_inputs=hashes,authorized_additional_attempts=0,execution_authorized=False)
    plan=build_plan(freeze_manifest(config),jobs,shards=2)
    task_list=[{k:v for k,v in task_at(plan,i).items() if k!='fit_options'} for i in range(plan['task_count'])]
    report=dict(state='prepared_not_run',execution_authorized=False,authorized_additional_attempts=0,
        source_inputs=hashes,routes=review,selected_track=SELECTED,plan_hash=plan['plan_hash'],
        task_count=plan['task_count'],distinct_recording_conditions=6,
        initial_proposed_prefix=3,initial_conditions='rotating-globe truth, wind+mixed bias; same seed and path under all three fit candidates',
        full_proposed_prefix=plan['task_count'],tasks=task_list,
        numerical_threads_per_worker=1,maximum_local_workers=2,new_seconds_per_evaluation=None,new_storage_bytes_per_evaluation=None,
        runtime_quote='Unavailable until an approved pilot measures this implementation. Historical 7-12 s flights do not estimate the new envelope and dual-path cost.',
        acceptance_review=['Scientific exclusions and every failure are retained.','All-contrast and pair-specific availability are separate.',
            'Preserve forward-axis uncertainty, watchdog/control path, prior sensitivity, parameter-boundary diagnostics and actual domain observables.',
            'A fitted crab or airspeed curve is model-dependent, not independent truth.','Bootstrap zero cannot establish error rates or promotion.'],
        policies=dict(wind_tas=WIND_TAS_POLICY,mount_yaw=MOUNT_YAW_POLICY,
            ordinary_envelope=ENVELOPE_ASSUMPTIONS,physical_envelope=PHYSICAL_ENVELOPE_ASSUMPTIONS),
        pending_controls=['Matched true mount-slip controls and slowly varying/nonlinear wind/TAS departures remain necessary before protocol selection.',
            'Other routes, original sparse-fix mode, schedule search and nonzero complete bootstrap need separately bounded stages.',
            'Do not prune off-manifold envelope states or loosen the speed constraint based on favorable retained-model information.'])
    output.mkdir(parents=True,exist_ok=False)
    (output/'plan.json').write_text(json.dumps(plain(plan),indent=2,allow_nan=False)+'\n')
    (output/'assumption-review.json').write_text(json.dumps(plain(report),indent=2,allow_nan=False)+'\n')
    return plan,report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    plan,review=prepare(args.output)
    print(json.dumps(dict(state=review['state'],tasks=plan['task_count'],plan_hash=plan['plan_hash'],
        reviewed_routes=len(review['routes']),authorized_attempts=0),sort_keys=True))


if __name__=='__main__': main()
