# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline preparation must preserve holdouts, gaps, source identity and protocol feasibility."""
import copy

import pytest

from prepare_next_stage import budget_plan, geometry_plan, review_campaigns
from lll.research_design import freeze_manifest, validate_turn_schedule
from test_candidate_eligibility import candidate_fit


def campaign(seed=1, margin=0.):
    config = dict(partition='development', protocol={'lat0': 35.}, variant='spp',
        scenarios=['wind'], truths=['sphere_rotating'], geometry='fixed',
        fit_options={'n_boot': 20, 'rank_min_relative_margin': margin})
    manifest = freeze_manifest(config)
    row = candidate_fit()
    row.update(partition='development', truth='sphere_rotating', scenario='wind', seed=seed,
        variant='spp', candidate_id='candidate', model_test_rank=2, elapsed_s=1., rejected=False,
        exclusions=[], flags=[], design={'simulator': {'mount_slip_deg_per_h': [0., 0.]}})
    row['identifiability']['rank_boundary_margin'] = row['identifiability']['rank_threshold']*.2
    return dict(partition='development', config=config, manifest=manifest,
        manifest_hash=manifest['manifest_hash'], implementation_hash=manifest['implementation_hash'],
        numerical_environment_hash=manifest['numerical_environment_hash'],
        eligibility_policies=manifest['eligibility_policies'], records=[row], elapsed_s=1.)


def test_review_keeps_sources_separate_and_inputs_unchanged():
    data = [campaign(), campaign(2, .1)]
    original = copy.deepcopy(data)
    result = review_campaigns(data)
    assert data == original and result['source_versions_pooled_for_inference'] is False
    assert [r['cells']['sphere_rotating/wind']['eligible_rank2'] for r in result['reports']] == [1, 1]


def test_review_rejects_overlapping_seeds_holdouts_and_changed_policy():
    with pytest.raises(ValueError, match='duplicate'):
        review_campaigns([campaign(), campaign()])
    data = [campaign()]
    data[0]['partition'] = 'validation'
    with pytest.raises(ValueError, match='development'):
        review_campaigns(data)
    data = [campaign()]
    data[0]['eligibility_policies'] = {}
    with pytest.raises(ValueError, match='eligibility policy'):
        review_campaigns(data)


def bundle(estimated=False):
    rows = [dict(t_s=i*60, latitude_deg=5.+i*.01, longitude_deg=1., ground_course_deg=0.,
        ground_speed_mps=250., reported_altitude_m=10000., is_provider_estimate=estimated) for i in range(76)]
    return dict(partition='development', track_format='position-track-2', displayed_timezone='unspecified',
        tracks=[dict(id='track', origin='ORD', destination='AUH', source_filename='track.csv',
                     source_sha256='hash', rows=rows)])


def test_geometry_preserves_estimates_and_enforces_feasible_turns():
    data = [bundle(True)]
    original = copy.deepcopy(data)
    result = geometry_plan(data)
    assert data == original and result['state'] == 'prepared_not_run'
    track = result['observed_track_cases'][0]
    assert track['status'] == 'blocked_by_observed_coverage' and not track['observed_intervals']
    assert all(row['is_provider_estimate'] for row in track['rows'])
    assert geometry_plan([bundle()])['observed_track_cases'][0]['status'] == 'prepared_geometry_only'
    cells = result['selected_synthetic_cells']
    assert len(cells) == 24 and len({cell['id'] for cell in cells}) == 24
    for cell in cells:
        validate_turn_schedule([t for t, _ in cell['simulator']['index_turns']], cell['duration_min'])
    six = next(c for c in cells if c['duration_min'] == 60 and c['turn_count'] == 6)
    assert [t for t, _ in six['simulator']['index_turns']] == [5., 15., 25., 35., 45., 55.]


def test_attempt_reserve_is_conservative_and_not_launch_authorization():
    result = budget_plan(review_campaigns([campaign()]), 20, 30)
    point, reserve = result['profiles'].values()
    assert result['state'] == 'proposal_not_authorized'
    assert reserve['combined_attempts'] > point['combined_attempts']
    assert reserve['acceptance_probability'] < point['acceptance_probability']
    with pytest.raises(ValueError, match='positive'):
        budget_plan(review_campaigns([campaign()]), 0, 30)
