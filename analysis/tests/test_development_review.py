# SPDX-License-Identifier: AGPL-3.0-or-later
"""A proposed gate cannot rerun fits, alter records, or absorb holdout evidence."""
import copy

import pytest

from review_development import review
from lll.policy import CANDIDATE_POLICY
from lll.research_design import implementation_hash
from test_candidate_eligibility import candidate_fit
from research import planning_eligible


def campaign():
    rows = []
    for scenario, margin, rejected in [('bias_mixed', .02, True), ('wind', .3, False)]:
        row = candidate_fit()
        row.update(partition='development', truth='sphere_rotating', scenario=scenario,
            model_test_rank=2, rejected=rejected, exclusions=[], flags=[],
            design={'simulator': {'mount_slip_deg_per_h': [0., 0.]}}, seed=1)
        row['identifiability'].update(rank_boundary_margin=CANDIDATE_POLICY['retention_threshold']*margin)
        rows.append(row)
    return dict(partition='development', implementation_hash=implementation_hash(),
                elapsed_s=2., records=rows)


def test_margin_review_preserves_inputs_and_does_not_promote_excluded_flights():
    data = campaign()
    original = copy.deepcopy(data)
    result = review(data, 10, 5)
    assert data == original
    baseline, _, proposed, _ = result['rank_margin_profiles']
    assert baseline['eligible'] == 2 and baseline['null_rejections'] == 1
    assert proposed['eligible'] == 1 and proposed['null_rejections'] == 0
    assert proposed['estimated_combined_attempts'] is None  # one cell has no accepted rank-2 samples
    data['records'][1]['exclusions'] = ['external gate exclusion']
    assert review(data, 10, 5)['rank_margin_profiles'][0]['eligible'] == 1


def test_review_rejects_holdouts_replays_and_changed_gate_source():
    data = campaign()
    data['partition'] = 'validation'
    with pytest.raises(ValueError, match='development evidence'):
        review(data)
    data = campaign()
    data['records'][0]['replay'] = True
    with pytest.raises(ValueError, match='original development'):
        review(data)
    data = campaign()
    data['implementation_hash'] = 'changed'
    with pytest.raises(ValueError, match='differs'):
        review(data)


def test_campaign_cost_uses_proposed_rank_margin_without_mutating_pilot():
    data = campaign()
    original = copy.deepcopy(data)
    assert all(planning_eligible(row, 0.) for row in data['records'])
    assert not planning_eligible(data['records'][0], .1)
    assert planning_eligible(data['records'][1], .1)
    assert data == original


def test_cost_planning_cannot_count_missing_or_failed_convergence_as_acceptance():
    row = {'rejected': False, 'exclusions': []}
    assert not planning_eligible(row, 0.)
    assert not planning_eligible({**row, 'convergence': {'converged': False}}, 0.)
    assert planning_eligible({**row, 'convergence': {'converged': True}}, 0.)
