"""The finite matched geometry rule must be identical for every candidate."""

import pytest


def test_two_routes_each_fit_all_three_candidates_with_one_rule():
    from lll.matched_one_sided_geometry_study import recipe,tasks
    from lll.matched_candidate_case import MODELS
    r=recipe();rows=tasks(r)
    assert [row['identity'] for row in rows]==['straight-level','turning-level']
    assert r['workers']*r['threads']==2
    assert r['maximum_evaluations']==200
    assert r['verification_evaluations']==9
    assert {row['payload']['truth_model'] for row in rows}=={'sphere_rotating'}
    assert {row['payload']['route'] for row in rows}=={'straight','turning'}
    assert len(MODELS)==3
    assert rows[0]['payload']['seed']==rows[1]['payload']['seed']
    assert all(row['limits']['native_calls']>3*r['maximum_evaluations'] for row in rows)


def test_short_preflight_is_separate_and_finite():
    from lll.matched_one_sided_geometry_study import preflight_recipe,tasks
    r=preflight_recipe();rows=tasks(r)
    assert r['maximum_evaluations']==18
    assert len(rows)==1 and rows[0]['identity']=='preflight-straight-level'
    assert rows[0]['payload']['route']=='straight'


def test_route_changes_generation_recipe_but_not_identity_spec():
    from lll.matched_candidate_generated_study import generated_case
    from lll.matched_one_sided_geometry_study import recipe,tasks
    rows=tasks();r=recipe()
    straight,sr=generated_case(rows[0]['payload'],r)
    turning,tr=generated_case(rows[1]['payload'],r)
    assert straight==turning
    assert set(straight)=={'model','latitude_deg','profile','start','policy_id'}
    assert sr['route']=='straight' and tr['route']=='turning'


def test_changed_task_fails_before_input_or_native_work():
    from lll.matched_one_sided_geometry_study import validate_task,tasks
    row=tasks()[0]
    with pytest.raises(ValueError,match='unchanged matched geometry task'):
        validate_task(dict(row,payload=dict(row['payload'],route='other')),preflight=False)


def test_provider_uses_same_research_rule_for_every_candidate(monkeypatch):
    from lll import matched_one_sided_geometry_study as study
    called=[]
    def fake(problem,model,*,start,maximum_evaluations,physical_step,
             stability_verifier,verification_evaluations):
        called.append((model,stability_verifier,verification_evaluations))
        return {'model':model}
    monkeypatch.setattr('lll.ilvis0_solver_trust_v2.fit_candidate',fake)
    provider=study.solver_provider()
    for model in ('sphere_rotating','sphere_still','flat_still'):
        assert provider(object(),model,start=[],maximum_evaluations=200)=={'model':model}
    from lll.one_sided_stopping import verify
    assert called==[(model,verify,9) for model in
                    ('sphere_rotating','sphere_still','flat_still')]
