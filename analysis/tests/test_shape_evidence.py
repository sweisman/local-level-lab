# SPDX-License-Identifier: AGPL-3.0-or-later
"""Composite shape evidence must survive rotation abstention without bypassing pair gates."""
from itertools import product

import pytest

from lll.pairwise import GLOBE_DISC_PAIRS, shape_evidence, three_model_winner, decide, pool_evidence
from lll.policy import CANDIDATE_POLICY, MODEL_PAIRS
from optimize_turns import geometry_criterion
from research import summarize


def entry(name, outcome, calibrated=False):
    globe, disc = MODEL_PAIRS[name]
    flags = {'globe':(False,True), 'disc':(True,False), 'neither':(False,False), 'both':(True,True)}
    if outcome == 'missing': return {}
    g, d = flags[outcome]
    evidence = dict(eligible=True, exclusions=[], statistics={globe:100. if g else 0.,disc:100. if d else 0.},
                    p_diagnostic={globe:0. if g else 1.,disc:0. if d else 1.})
    return decide(evidence,name,{globe:10.,disc:10.} if calibrated else None)


@pytest.mark.parametrize('outcomes',list(product(('missing','globe','disc','neither','both'),repeat=2)))
def test_all_shape_endpoint_combinations(outcomes):
    evidence={name:entry(name,outcome) for name,outcome in zip(GLOBE_DISC_PAIRS,outcomes)}
    result=shape_evidence(evidence)
    expected=None if 'globe' in outcomes and 'disc' in outcomes else 'globe' if 'globe' in outcomes else 'disc' if outcomes==('disc','disc') else None
    assert result['preferred_family']==expected
    assert result['status']==('decision' if expected else 'abstain')
    assert not result['error_rate_validated'] and not result['validated_for_primary_claims']
    if expected=='globe': assert three_model_winner(evidence) is None


def test_shape_ignores_rotation_and_does_not_certify_calibrated_union():
    evidence={name:entry(name,'globe',True) for name in GLOBE_DISC_PAIRS}
    name='sphere_rotating_vs_sphere_still'
    evidence[name]=dict(eligible=False,exclusions=['rotation not identified'],status='abstain')
    result=shape_evidence(evidence)
    assert result['preferred_family']=='globe' and result['pairwise_thresholds_calibrated']
    assert not result['error_rate_validated']
    assert three_model_winner(evidence) is None


@pytest.mark.parametrize('change',[{'eligible':False},{'exclusions':['outside calibrated domain']},
    {'status':'abstain'},{'preferred_model':'flat_still'}, {'rejected_by_model':{}}])
def test_stale_or_excluded_pair_cannot_supply_shape_evidence(change):
    name=GLOBE_DISC_PAIRS[0]
    result=shape_evidence({name:{**entry(name,'globe'),**change}})
    assert result['preferred_family'] is None
    assert result['unavailable_comparisons'][name]


def test_pool_preserves_shape_evidence_without_rotation_comparison():
    name=GLOBE_DISC_PAIRS[1]
    evidence={name:dict(method='pair-line-profile-1',eligible=True,estimate=.98,sd=.02)}
    result=pool_evidence([(unit,evidence) for unit in ('a','b','c')],'candidate','spp')
    assert result['shape_evidence']['preferred_family']=='globe'
    assert result['three_model_winner'] is None
    assert result['pairwise'][name]['n_units']==3


def design_report():
    return dict(rank_threshold=CANDIDATE_POLICY['retention_threshold'],estimable_rank=0,
        assumptions=CANDIDATE_POLICY['design_assumptions'],
        model_contrast_information={},untruncated_contrasts={name:dict(estimable=True,
            retained_fraction=.6,information=20.) for name in GLOBE_DISC_PAIRS})


def test_shape_geometry_uses_both_untruncated_pairs_without_rotation_rank():
    report=design_report()
    assert not geometry_criterion(report)['all_estimable']
    assert geometry_criterion(report,objective='globe-disc')['all_estimable']
    report['untruncated_contrasts'][GLOBE_DISC_PAIRS[0]].update(estimable=False,retained_fraction=.1)
    assert not geometry_criterion(report,objective='globe-disc')['all_estimable']
    assert geometry_criterion(report,comparison=GLOBE_DISC_PAIRS[1])['all_estimable']


def test_shape_geometry_rejects_missing_comparison_and_ambiguous_objective():
    report=design_report(); report['untruncated_contrasts'].pop(GLOBE_DISC_PAIRS[0])
    assert not geometry_criterion(report,objective='globe-disc')['valid']
    with pytest.raises(ValueError,match='either'):
        geometry_criterion(report,comparison=GLOBE_DISC_PAIRS[1],objective='globe-disc')


def test_research_summary_counts_failures_and_abstentions_in_attempts():
    base=dict(truth='sphere_rotating',scenario='wind',exclusions=[])
    rows=[{**base,'pairwise':{GLOBE_DISC_PAIRS[0]:entry(GLOBE_DISC_PAIRS[0],'globe')}},
          {**base,'failure':'preserved analysis failure'},
          {**base,'pairwise':{name:entry(name,'disc') for name in GLOBE_DISC_PAIRS}}]
    result=summarize(rows)[0]['experimental_shape']
    assert result['attempted']==3
    assert result['correct_preferences']==result['incorrect_preferences']==result['abstentions']==1
    assert not result['error_rate_validated']


def test_readable_report_keeps_shape_and_rotation_separate():
    from lll.report import _shape_report
    evidence={name:entry(name,'globe') for name in GLOBE_DISC_PAIRS}
    rendered=_shape_report({'pairwise':evidence})
    assert 'Globe preference; rotation may remain unresolved' in rendered
    assert 'shape error rate has not been validated' in rendered
    assert 'every possible non-globe' in rendered


def test_shape_uses_final_profile_gate_even_when_global_fit_fails():
    from test_core_pipeline import profile_fit_fixture
    from lll.pairwise import flight_evidence
    fit=profile_fit_fixture()
    rotation='sphere_rotating_vs_sphere_still'
    fit['pairwise_profile'].pop(rotation)
    shape=shape_evidence(flight_evidence(fit))
    assert shape['preferred_family']=='globe'
    assert rotation not in shape['comparisons']
    assert not fit['convergence']['converged'] and fit['model_test_rank']==0
    assert shape_evidence(flight_evidence(fit,flags=['orientation_unresolved']))['status']=='abstain'


def test_optimizer_shape_objective_uses_envelope_and_both_nuisance_candidates(monkeypatch):
    import numpy as np
    import optimize_turns as optimizer
    import lll.design_geometry as geometry
    import lll.design_envelope as envelope
    kin=dict(t=np.arange(2400.),speed=np.full(2400,240.),psi_dot=np.zeros(2400))
    monkeypatch.setattr(geometry,'geometry_kinematics',lambda _: (kin,2400.))
    monkeypatch.setattr(geometry,'geometry_problem',lambda design,schedule,crab,kin=None: (tuple(schedule),crab))
    calls=[]
    def score(problem):
        calls.append(problem)
        report=design_report()
        if problem[1]=='wind':
            report['untruncated_contrasts'][GLOBE_DISC_PAIRS[0]].update(retained_fraction=.1,estimable=False)
        return report
    monkeypatch.setattr(envelope,'envelope_information',score)
    monkeypatch.setattr(optimizer,'flight_run',lambda *args,**kwargs:pytest.fail('full fitter called'))
    result=optimizer.search_geometry([{'geometry_cell':'fixture'}],max_turns=0,
        objective='globe-disc',crab_models=('wind','wind_tas'))
    assert set(calls)=={((),'wind'),((),'wind_tas')}
    assert result['objective']=='globe-disc' and result['best'] is None
    assert not result['feasible_winner']
