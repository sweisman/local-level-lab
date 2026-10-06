# SPDX-License-Identifier: AGPL-3.0-or-later
"""Preparation diagnostics only; no synthesis, inference fit, SVD or schedule search."""
import json

import numpy as np
import pytest

import prepare_airline_pilot as prepare
from lll.campaign_shards import check_plan,task_at
from lll.trajectory import track_spec


@pytest.fixture(autouse=True)
def no_expensive_work(monkeypatch):
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'): monkeypatch.setenv(key,'1')
    monkeypatch.setattr(np.linalg,'svd',lambda *a,**k:pytest.fail('preparation ran an SVD'))
    monkeypatch.setattr('research.flight_run',lambda *a,**k:pytest.fail('preparation ran a flight'))


def constant_route():
    return track_spec(dict(id=prepare.SELECTED,status='prepared_geometry_only',source_sha256='fixture',
        candidate_window={'start_s':0.,'end_s':4500.},rows=[dict(t_s=t,latitude_deg=30.+t*.0022,
            longitude_deg=5.,reported_altitude_m=11000.,ground_speed_mps=240.,ground_course_deg=0.,
            is_provider_estimate=False) for t in range(0,4501,60)]))


def ground_vectors(variation=False):
    t=np.arange(0.,4500.,1.)
    speed=250.+(10.*np.sin(2*np.pi*t/120.) if variation else np.zeros(len(t)))
    return dict(t=t,v_n=speed,v_e=np.zeros(len(t)),speed=speed,psi_dot=np.zeros(len(t)))


def test_geometry_review_preserves_assumptions_and_reports_mask_and_source_mismatch():
    result=prepare.route_review(constant_route())
    assert result['all_proposed_turns_pass_assumed_mask']
    assert result['duration_minutes']==75.
    assert result['public_observation_interval_seconds']['median']==60.
    assert abs(result['reported_minus_assumed_speed_mps']['median'])>1.
    assert result['physical_speed_review']['state_count']==65
    assert 'assumed' in result['status'] and 'simulated' in result['assumptions']['accuracy']


def test_fixed_grid_feasibility_review_does_not_remove_off_manifold_states():
    result=prepare.speed_state_review(ground_vectors())
    assert result['state_count']==len(result['states'])==65
    nominal=next(s for s in result['states'] if s['state']=='wind-0-0/tas-250.0')
    assert nominal['absolute_speed_residual_mps']['max']==0.
    assert nominal['fraction_within_3_constraint_sigma']==1.
    assert any(s['fraction_within_3_constraint_sigma']==0. for s in result['states'])
    assert result['states_with_every_sample_within_3_sigma']<65


def test_geometry_jitter_can_exceed_the_fixed_speed_constraint_without_fitting():
    result=prepare.speed_state_review(ground_vectors(True))
    assert result['knot_interpolation_speed_residual_mps']['max']>6.
    assert result['knot_interpolation_fraction_within_3_constraint_sigma']<.9


def test_unavailable_speed_review_stays_unavailable():
    kin=ground_vectors(); kin['v_n'][:]=np.nan
    assert not prepare.speed_state_review(kin)['available']


def test_new_proposal_is_frozen_and_unrun_and_initial_prefix_is_matched(tmp_path):
    core=tmp_path/'input'; core.mkdir(); (core/'trajectories').mkdir()
    spec=constant_route(); relative='trajectories/fixture.json'
    (core/relative).write_text(json.dumps(spec))
    (core/'proposal.json').write_text(json.dumps({'config':{'replay_inputs':[{'mode':'simulated_high_rate','path':relative}]}}))
    output=tmp_path/'output'
    plan,report=prepare.prepare(output,core)
    check_plan(plan)
    assert plan['task_count']==18 and report['distinct_recording_conditions']==6
    assert report['authorized_additional_attempts']==0 and not report['execution_authorized']
    assert not (output/'campaign.json').exists()
    assert json.loads((output/'plan.json').read_text())==plan
    first=[task_at(plan,i) for i in range(3)]
    assert len({(t['truth'],t['scenario'],t['seed'],t['geometry_cell']) for t in first})==1
    assert first[0]['fit_options']['crab_model']=='wind'
    assert first[1]['fit_options']['crab_model']=='wind_tas'
    assert first[2]['fit_options']['magnetic_ambiguity']=='model_and_compare'
    assert all(t['fit_options']['n_boot']==0 for t in first)
    assert all(t['partition']=='development' for t in first)


def test_selected_timing_failure_blocks_preparation_without_widening_mask(tmp_path):
    spec=constant_route()
    # A step in reported height during the first planned turn makes that assumed
    # path unsafe. The preparation must not shift times to manufacture a pass.
    for row in spec['rows']:
        if row['t_s']>=1200.: row['reported_altitude_m']+=1000.
    from lll.inference_policy import digest
    spec['trajectory_hash']=digest({k:v for k,v in spec.items() if k!='trajectory_hash'})
    result=prepare.route_review(spec)
    assert not result['all_proposed_turns_pass_assumed_mask']
    assert result['proposed_turns'][0]['minute']==20.
    core=tmp_path/'input'; core.mkdir(); (core/'trajectories').mkdir()
    (core/'trajectories'/'fixture.json').write_text(json.dumps(spec))
    (core/'proposal.json').write_text(json.dumps({'config':{'replay_inputs':[{'mode':'simulated_high_rate','path':'trajectories/fixture.json'}]}}))
    with pytest.raises(ValueError,match='fails current'): prepare.prepare(tmp_path/'output',core)
    assert not (tmp_path/'output').exists()
