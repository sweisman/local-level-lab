# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fast policy and optimizer checks; no numerical search or tail campaign."""
import copy
import json

import pytest

from lll import __version__, models
from lll.collate import gate, collate
from lll.inference_policy import digest
from lll.policy import (CANDIDATE_POLICY, MODEL_CONTRASTS, contrast_eligibility,
                        eligibility_policies, eligibility_provenance, scientific_exclusions)
from lll.research_calibration import eligible, calibrate, assess, check_policy
from lll.research_design import freeze_manifest, validate_manifest
from lll.runtime import numerical_environment
from test_analysis import _fake, _approvals


def candidate_fit(retention=.8, information=10.):
    threshold = CANDIDATE_POLICY["retention_threshold"]
    result = {"convergence": {"converged": True}, "model_test_rank": 3,
            "eligibility_policy": eligibility_provenance(True),
            "inference_policy": {"settings": {"engine": "candidate-1", "n_boot": 20}},
            "bootstrap": {"requested": 20, "bootstrap_valid": True, "empirical_k_cov": None},
            "identifiability": {"estimable_rank": 3, "rank_threshold": threshold,
                "model_contrast_information": {name: {"estimable": retention >= threshold,
                    "retained_fraction": retention, "information": information} for name in MODEL_CONTRASTS}}}
    result["design_identifiability"] = copy.deepcopy(result["identifiability"])
    result["design_identifiability"]["assumptions"] = copy.deepcopy(CANDIDATE_POLICY["design_assumptions"])
    result["identifiability"]["estimable_combinations"] = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
    return result


@pytest.mark.parametrize("change,reason", [
    (lambda f: f["design_identifiability"]["model_contrast_information"].pop(MODEL_CONTRASTS[0]), "model contrast not identified"),
    (lambda f: f["design_identifiability"]["model_contrast_information"].clear(), "model contrast not identified"),
    (lambda f: f.update(model_test_rank=0), "no identifiable model-test subspace"),
    (lambda f: f["convergence"].update(converged=False), "inference did not converge"),
    (lambda f: f["bootstrap"].update(bootstrap_valid=False), "inadequate bootstrap convergence"),
    (lambda f: f.pop("bootstrap"), "inadequate bootstrap convergence"),
    (lambda f: f.pop("eligibility_policy"), "candidate eligibility policy mismatch; reprocess"),
])
def test_candidate_policy_shared_by_gate_and_calibration(change, reason):
    result = _fake("u", (1, 1, 0), (.1, .1, .1), flags=["k_not_identified"])
    result["fit"].update(candidate_fit())
    approval = _approvals([result])[result["input_sha256"]]
    assert scientific_exclusions(result) == []
    assert gate(result, {}, approval=approval) == []
    change(result["fit"])
    assert reason in scientific_exclusions(result)
    assert reason in gate(result, {}, approval=approval)
    row = {**result["fit"], "flags": result["flags"], "exclusions": []}
    assert not eligible(row)  # Recomputes science even if serialized exclusions are empty.
    assert "curvature not identified" not in scientific_exclusions(result)


def test_zero_bootstrap_is_allowed_for_development_and_legacy_stays_unchanged():
    fit = candidate_fit()
    fit["inference_policy"]["settings"]["n_boot"] = 0
    fit["bootstrap"].update(requested=0, bootstrap_valid=False)
    assert not scientific_exclusions({"fit": fit})
    result = _fake("u", (1, 1, 0), (.1, .1, .1), flags=["k_not_identified", "prior_dominated"])
    assert scientific_exclusions(result) == ["curvature not identified", "prior-dominated"]
    result["fit"].update(fit)
    assert scientific_exclusions(result) == ["prior-dominated"]


def test_retention_boundary_and_nonfinite_diagnostics():
    threshold = CANDIDATE_POLICY["retention_threshold"]
    assert contrast_eligibility(candidate_fit(threshold)["identifiability"])["all_estimable"]
    assert not contrast_eligibility(candidate_fit(threshold-1e-10)["identifiability"])["all_estimable"]
    assert not contrast_eligibility(candidate_fit(information=float("nan"))["identifiability"])["valid"]
    report = candidate_fit()["identifiability"]
    report["rank_threshold"] += .01
    assert not contrast_eligibility(report)["valid"]


def campaign():
    rows = [{**candidate_fit(), "scenario": "baseline", "candidate_id": "x", "variant": "spp",
             "geometry": "fixed", "truth": truth, "partition": "calibration", "exclusions": [],
             "seed": 1_000_000+i, "delta_chi2_identifiable": {m: float(i) for m in models.MODELS},
             "numerical_environment": numerical_environment(),
             "rejected": False} for truth in models.MODELS for i in range(5)]
    return {"partition": "calibration", "manifest_hash": "test", "analysis_version": __version__,
            "numerical_environment": numerical_environment(),
            "config": {"calibration_tail_observations": 1, "calibration_tail_confidence": .01, "calibration_min_accepted": 5},
            "eligibility_policies": eligibility_policies(), "records": rows}


def test_frozen_policy_mismatches_and_independent_assessment():
    data = campaign()
    policy = calibrate(data, min_accepted=5)
    check_policy(policy)
    validation = {**data, "partition": "validation", "config": {
        "tail_min_accepted": 2000, "decision_policy_hash": policy["policy_hash"]},
        "records": [{**row, "partition": "validation", "seed": row["seed"]+1_000_000,
                     "decision_policy_hash": policy["policy_hash"]} for row in data["records"]]}
    assert not assess(validation, policy)["validated"]
    bad = copy.deepcopy(data)
    bad["records"][0]["eligibility_policy"]["policy_hash"] = "old"
    with pytest.raises(ValueError, match="record eligibility policy mismatch"):
        calibrate(bad, min_accepted=5)
    with pytest.raises(ValueError, match="campaign eligibility policy mismatch"):
        calibrate({**data, "eligibility_policies": {}}, min_accepted=5)
    bad_policy = copy.deepcopy(policy)
    bad_policy["eligibility_policies"] = {}
    bad_policy["policy_hash"] = digest({k: v for k, v in bad_policy.items() if k != "policy_hash"})
    with pytest.raises(ValueError, match="eligibility policy mismatch"):
        check_policy(bad_policy)
    with pytest.raises(ValueError, match="recalibration"):
        check_policy({**policy, "version": "empirical-decision-2"})
    manifest = freeze_manifest({})
    manifest["eligibility_policies"] = {}
    with pytest.raises(ValueError, match="frozen manifest"):
        validate_manifest(manifest, {})


def test_collation_rejects_mixed_eligibility_policies():
    a = _fake("u", (1, 1, 0), (.1, .1, .1))
    b = copy.deepcopy(a)
    b["input_sha256"] = "different"
    a["fit"].update(candidate_fit())
    b["fit"].update(candidate_fit())
    b["fit"]["eligibility_policy"]["policy_hash"] = "old"
    with pytest.raises(ValueError, match="incompatible inference configurations"):
        collate([a, b])


def test_research_uses_shared_gate_without_rewriting(monkeypatch):
    import research
    result = _fake("u", (1, 1, 0), (.1, .1, .1), flags=["synthetic", "k_not_identified"])
    f = result["fit"]
    f.update(candidate_fit())
    f.update(k_cov=None, delta_chi2_raw={}, delta_chi2_identifiable={}, p_vs_free={}, prior_sensitivity={})
    f["bootstrap"]["bootstrap_valid"] = False
    monkeypatch.setattr(research, "synthesize", lambda *args, **kwargs: None)
    monkeypatch.setattr(research, "analyze", lambda *args, **kwargs: result)
    row = research.flight_run("sphere_rotating", "drift+0", 49, "moving", 15, 20, "spp")
    expected = scientific_exclusions(result)
    assert row["exclusions"] == expected == ["inadequate bootstrap convergence"]
    assert row["eligibility_policy"] == eligibility_provenance(True)
    assert not eligible(row)


def optimizer(monkeypatch, values, route_minutes=60., transform=None, **options):
    import optimize_turns
    # A tiny deterministic route gives grid points at 20 and 40 minutes.
    monkeypatch.setattr(optimize_turns, "realize", lambda seed, scenario, **kwargs:
        {"simulator": {"legs": [[0., route_minutes]], "index_turns": []}})
    def flight(truth, scenario, seed, *args, design, fit_options):
        schedule = tuple(t for t, _ in design["simulator"]["index_turns"])
        retention, information = values(schedule, fit_options["crab_model"])
        row = candidate_fit(retention, information)
        return transform(row, schedule) if transform else row
    monkeypatch.setattr(optimize_turns, "flight_run", flight)
    return optimize_turns.search(seeds=[49], scenarios=["wind"], grid_min=20., **options)


def test_optimizer_estimability_then_margin_then_information(monkeypatch):
    scores = {(): (.1, 1e9), (20.,): (.4, 1e6), (40.,): (.6, 2.)}
    result = optimizer(monkeypatch, lambda schedule, crab: scores[schedule], max_turns=1)
    assert result["best"]["turn_schedule_min"] == [40.]
    scores[(20.,)] = (.6, 3.)
    result = optimizer(monkeypatch, lambda schedule, crab: scores[schedule], max_turns=1)
    assert result["best"]["turn_schedule_min"] == [20.]
    scores[(20.,)] = (.2, 1e9)
    result = optimizer(monkeypatch, lambda schedule, crab: scores[schedule], max_turns=1)
    assert result["best"]["turn_schedule_min"] == [40.]


def test_optimizer_worst_crab_and_no_feasible_winner(monkeypatch):
    def values(schedule, crab):
        if schedule == (20.,): return (.9 if crab == "dynamic" else .2), 100.
        return (.5, 5.) if schedule else (.1, 1.)
    result = optimizer(monkeypatch, values, max_turns=1)
    assert result["best"]["turn_schedule_min"] == [40.]
    row = next(r for r in result["schedule_scores"] if r["turn_schedule_min"] == [20.])
    assert row["limiting_evaluation"]["crab_model"] == "wind"
    result = optimizer(monkeypatch, lambda schedule, crab: (.1, 1.), max_turns=1)
    assert result["best"] is None and not result["feasible_winner"]
    assert result["best_diagnostic"]["turn_schedule_min"] == []


def test_optimizer_nonfinite_cannot_win_and_output_is_json(monkeypatch):
    result = optimizer(monkeypatch, lambda schedule, crab: (.9, float("nan")) if schedule == (20.,) else (.4, 1.), max_turns=1)
    assert result["best"]["turn_schedule_min"] == []
    assert result == json.loads(json.dumps(result, allow_nan=False))


@pytest.mark.parametrize("change", [
    lambda row: row["convergence"].update(converged=False),
    lambda row: row["design_identifiability"]["model_contrast_information"].pop(MODEL_CONTRASTS[0]),
    lambda row: row["design_identifiability"].pop("estimable_rank"),
    lambda row: row.update(failure="fit failed"),
])
def test_optimizer_failed_or_incomplete_evaluation_cannot_win(monkeypatch, change):
    def transform(row, schedule):
        if schedule == (20.,): change(row)
        return row
    result = optimizer(monkeypatch, lambda schedule, crab: (.9, 1e9) if schedule == (20.,) else (.4, 1.),
                       transform=transform, max_turns=1)
    assert result["best"]["turn_schedule_min"] == []
    assert not next(row for row in result["schedule_scores"] if row["turn_schedule_min"] == [20.])["valid_evaluations"]


def test_collation_reports_the_candidate_policy_and_blocks_promotion():
    result = _fake("u", (1, 1, 0), (.1, .1, .1))
    result["fit"].update(candidate_fit())
    output = collate([result], provenance=_approvals([result]))
    assert output["eligibility_policy"] == eligibility_provenance(True)
    assert output["policy_version"] == CANDIDATE_POLICY["version"]
    assert output["n_primary"] == 0
    assert "experimental inference candidate" in output["rows"][0]["excluded_because"]


def test_optimizer_beam_preserves_lower_scoring_prefix_and_cost(monkeypatch):
    scores = {(): (.1, 1.), (20.,): (.4, 1.), (40.,): (.3, 1.), (60.,): (.3, 1.),
              (20., 40.): (.4, 2.), (20., 60.): (.4, 2.), (40., 60.): (.8, 10.)}
    result = optimizer(monkeypatch, lambda schedule, crab: scores[schedule], route_minutes=80., max_turns=2)
    assert result["best"]["turn_schedule_min"] == [40., 60.]
    assert result["settings"]["beam_width"] == 16
    greedy = optimizer(monkeypatch, lambda schedule, crab: scores[schedule], route_minutes=80., max_turns=2, beam_width=1)
    assert greedy["best"]["turn_schedule_min"] == [20., 40.]
    cost = optimizer(monkeypatch, lambda schedule, crab: pytest.fail("estimate ran a fit"),
                     max_turns=2, estimate_only=True, pilot_seconds=2.)
    assert cost["upper_bound_evaluations"] == (1+2*16*2)*3*2
    assert cost["upper_bound_fits"] == 2*cost["upper_bound_evaluations"]
    assert cost["estimated_seconds_upper"] == 2.*cost["upper_bound_fits"]
