# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded checks for design selection, calibration precision and partial evidence."""
import copy
import json
import sys

import numpy as np
import pytest
from scipy.stats import binom

from lll import fit, models
from lll.calib import RAD2DPH
from lll.inference import CandidateProblem, design_information
from lll.inference_policy import digest
from lll.pairwise import flight_evidence, pool_evidence, three_model_winner, check_pairwise_policy
from lll.pairwise_calibration import calibrate as calibrate_pairs, assess as assess_pairs
from lll.policy import CANDIDATE_POLICY, MODEL_CONTRASTS, MODEL_PAIRS, decision_stratum, scientific_exclusions, eligibility_policies
from lll.rank_sweep import sweep
from lll.research_calibration import calibrate, required_calibration_n, required_accepted_n, check_policy, validation_power_plan, tail_upper, calibration_precision
from lll.research_design import geometry_stress_matrix, realize, freeze_manifest, validate_manifest, implementation_hash, plain, protocol_geometry
from lll.runtime import numerical_environment
from test_candidate_eligibility import candidate_fit, campaign
from test_release060 import crab_fixture
from test_research_candidates import settings


@pytest.fixture
def domain_file(tmp_path):
    from test_flight_domain import envelope
    path=tmp_path/'flight-domain.json'
    path.write_text(json.dumps(envelope('synthetic_gnss')))
    return path


@pytest.mark.parametrize("crab,bias,forward_uncertainty", [("dynamic", "constant", False), ("wind", "dynamic", False), ("dynamic", "dynamic", True)])
def test_design_information_ignores_gyro_and_fitted_weights(crab, bias, forward_uncertainty):
    bins, forward = crab_fixture()
    problem = CandidateProblem(bins, forward, lambda t: 0., np.full(3, 2/RAD2DPH),
                               settings(crab_model=crab, bias_model=bias, forward_uncertainty=forward_uncertainty),
                               forward_sigma_rad=.02 if forward_uncertainty else None)
    expected = design_information(problem)
    problem.y[:] = 1e12
    problem.w[:] = 1e-20
    problem.bins["gyro"][:] = -1e9
    assert design_information(problem) == expected
    assert not expected["uses_gyro_realization"]
    assert set(expected["anchors"]) == set(models.MODELS)
    for name in MODEL_CONTRASTS:
        values = [anchor["model_contrast_information"][name] for anchor in expected["anchors"].values()]
        assert expected["model_contrast_information"][name]["retained_fraction"] == min(v["retained_fraction"] for v in values)
        assert expected["model_contrast_information"][name]["estimable"] == all(v["estimable"] for v in values)


def test_free_fit_identifiability_is_diagnostic_for_design_gate():
    result = candidate_fit()
    result["identifiability"]["model_contrast_information"].clear()
    assert scientific_exclusions({"fit": result}) == []
    result["design_identifiability"]["model_contrast_information"][MODEL_CONTRASTS[0]]["estimable"] = False
    assert "model contrast not identified" in scientific_exclusions({"fit": result})


def test_rank_sweep_counts_flips_and_optional_margin_gate():
    threshold = CANDIDATE_POLICY["retention_threshold"]
    rows = [{"seed": i, "truth": "sphere_still", "scenario": "baseline", "candidate_id": "x",
             "identifiability": {"normalized_singular_values": singular}}
            for i, singular in enumerate(([1., .99*threshold, .1*threshold], [1., .8, .7]))]
    report = sweep({"partition": "development", "records": rows}, [threshold*.9, threshold, threshold*1.1])
    assert report["flights"][0]["ranks"] == [2, 1, 1]
    assert report["flights"][0]["near_boundary"] and report["flights"][0]["rank_flips"]
    assert not report["flights"][1]["rank_flips"]
    with pytest.raises(ValueError, match="development"):
        sweep({"partition": "validation", "records": rows})
    result = candidate_fit()
    result["identifiability"].update(rank_threshold=threshold, rank_boundary_margin=threshold*.01)
    assert not scientific_exclusions({"fit": result})
    result["inference_policy"]["settings"]["rank_min_relative_margin"] = .1
    assert "unstable model-test rank" in scientific_exclusions({"fit": result})


def test_geometry_matrix_is_deterministic_and_observable():
    matrix = geometry_stress_matrix()
    assert len(matrix) == 288 and len({cell["id"] for cell in matrix}) == len(matrix)
    assert {abs(cell["latitude_deg"]) for cell in matrix} == {5., 35., 65.}
    assert {cell["heading_count"] for cell in matrix} == {2, 6}
    assert {cell["turn_count"] for cell in matrix} == {0, 3, 6}
    first = realize(49, "bias_mixed", geometry="stress", geometry_cell=matrix[0]["id"])
    second = realize(50, "bias_mixed", geometry="stress", geometry_cell=matrix[0]["id"])
    assert first["simulator"]["legs"] == second["simulator"]["legs"]
    assert first["simulator"]["index_turns"] == second["simulator"]["index_turns"]
    assert first["streams"] != second["streams"]
    with pytest.raises(ValueError, match="nuisance-only"):
        realize(49, "equator", geometry="stress", geometry_cell=matrix[0]["id"])


def test_exact_protocol_is_frozen_and_cannot_be_overridden(monkeypatch, tmp_path, domain_file):
    import research
    protocol = dict(lat0=35, lon0=-30, speed=270, legs=[[10, 15], [100, 15], [190, 15], [280, 15], [10, 15]],
                    turn_schedule=[5, 15, 25, 35, 45, 55])
    normalized = protocol_geometry(protocol)
    first = realize(49, "bias_mixed", geometry="fixed", protocol=protocol)
    second = realize(50, "wind", geometry="fixed", protocol=protocol)
    assert first["simulator"]["legs"] == second["simulator"]["legs"] == normalized["legs"]
    assert first["simulator"]["index_turns"] == [[t, "z"] for t in protocol["turn_schedule"]]
    assert first["geometry_cell"] == second["geometry_cell"] == "protocol-"+digest(normalized)
    for kwargs in (dict(geometry="seeded"), dict(geometry="fixed", turn_schedule=[])):
        with pytest.raises(ValueError, match="protocol requires"):
            realize(49, "bias_mixed", protocol=protocol, **kwargs)
    with pytest.raises(ValueError, match="nuisance-only"):
        realize(49, "equator", geometry="fixed", protocol=protocol)
    with pytest.raises(ValueError, match="exactly"):
        protocol_geometry({**protocol, "bias_model": "constant"})
    input_file = tmp_path/"protocol.json"
    output = tmp_path/"manifest.json"
    input_file.write_text(json.dumps(protocol))
    monkeypatch.setattr(sys, "argv", ["research.py", "--partition", "calibration", "--truth", "all",
        "--geometry", "fixed", "--protocol", str(input_file), '--flight-domain',str(domain_file), "--write-manifest", str(output), "-o", str(tmp_path/"unused.json")])
    research.main()
    manifest = json.loads(output.read_text())
    config = manifest["config"]
    assert config["protocol"] == normalized
    assert config["preregistered_geometry_cells"] == [first["geometry_cell"]]
    assert config["geometry_domain"] == [{"id": first["geometry_cell"], **normalized}]
    changed = copy.deepcopy(config)
    changed["protocol"]["speed"] = 260
    with pytest.raises(ValueError, match="frozen manifest"):
        validate_manifest(manifest, changed)


def test_exact_calibration_count_is_independent_of_validation_count():
    count = required_calibration_n(.0027)
    assert binom.sf(29, count, .0027) >= .95
    assert binom.sf(29, count-1, .0027) < .95
    assert count > 30/.0027
    data = campaign()
    data["config"] = {}
    with pytest.raises(ValueError, match="tail-precision"):
        calibrate(data, min_accepted=5)


def test_calibration_margin_preserves_claimed_rate_and_sizes_actual_tail(monkeypatch):
    data = campaign()
    data["config"].update(calibration_alpha=.00135, calibration_tail_confidence=.001)
    quantiles = []
    original = np.quantile
    def quantile(values, q, **kwargs):
        quantiles.append(q)
        return original(values, q, **kwargs)
    monkeypatch.setattr(np, "quantile", quantile)
    policy = calibrate(data, min_accepted=5)
    assert policy["alpha"] == .0027 and policy["calibration_alpha"] == .00135
    assert quantiles and all(q == 1-.00135 for q in quantiles)
    assert calibration_precision({"calibration_alpha": .00135}, .0027)["minimum_accepted"] == required_calibration_n(.00135)
    with pytest.raises(ValueError, match="tail target"):
        calibration_precision({"calibration_alpha": 0.}, .0027)


def test_validation_power_plan_has_exact_bound_and_declared_power():
    plan = validation_power_plan(.0027, 9, .00135)
    assert tail_upper(plan["required_accepted"], plan["allowed_failures"], 9) <= .0027
    assert binom.cdf(plan["allowed_failures"], plan["required_accepted"], .00135) >= .9
    assert plan["achieved_power"] >= plan["desired_power"] == .9
    assert plan["achieved_power"] == pytest.approx(1-9*(1-plan["per_cell_power"]))
    with pytest.raises(ValueError, match="below the claimed"):
        validation_power_plan(.0027, 9, .0027)


def test_environment_freezing_and_record_mismatch():
    manifest = freeze_manifest({})
    assert manifest["numerical_environment"] == numerical_environment()
    assert manifest["numerical_environment_hash"] == digest(numerical_environment())
    changed = copy.deepcopy(manifest)
    changed["numerical_environment"]["numpy"] = "different"
    with pytest.raises(ValueError, match="frozen manifest"): validate_manifest(changed, {})
    data = campaign()
    policy = calibrate(data, min_accepted=5)
    changed = copy.deepcopy(policy)
    changed["numerical_environment"]["scipy"] = "different"
    changed["policy_hash"] = digest({k: v for k, v in changed.items() if k != "policy_hash"})
    with pytest.raises(ValueError, match="numerical environment"): check_policy(changed)
    data["records"][0]["numerical_environment"] = {**numerical_environment(), "python": "different"}
    with pytest.raises(ValueError, match="numerical environment"): calibrate(data, min_accepted=5)


def test_numerical_thread_settings_are_frozen(monkeypatch):
    from lll.runtime import check_environment
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "1")
    expected = numerical_environment()
    assert expected["thread_settings"]["OPENBLAS_NUM_THREADS"] == "1"
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "2")
    with pytest.raises(ValueError, match="thread settings"):
        check_environment(expected)


def test_rank_strata_select_threshold_after_fitting_and_abstain_when_unseen(monkeypatch):
    from test_flight_domain import scoped_campaign, geometry
    data = scoped_campaign()
    extra = []
    for row in data["records"]:
        second = copy.deepcopy(row)
        second.update(model_test_rank=2, seed=row["seed"]+100,
                      delta_chi2_identifiable={model: 10+value for model, value in row["delta_chi2_identifiable"].items()})
        extra.append(second)
    data["records"].extend(extra)
    policy = calibrate(data, min_accepted=5)
    assert len(policy["thresholds"]) == 2
    assert decision_stratum(data["records"][0]) != decision_stratum(extra[0])
    result = candidate_fit()
    result.update(model_test_rank=2, chi2_free=0., chi2={m: 12. for m in models.MODELS},
                  delta_chi2_identifiable={m: 12. for m in models.MODELS}, rejected=dict.fromkeys(models.MODELS, False))
    monkeypatch.setattr("lll.inference.candidate_fit", lambda *args, **kwargs: copy.deepcopy(result))
    observed = fit.fit(geometry(), None, None, None, research_candidate=True, n_boot=0,
                       decision_policy=policy, decision_candidate_id="x", decision_variant="spp")
    assert all(value is False for value in observed["rejected"].values())  # rank-2 cutoff=14, rank-3 cutoff=4.
    result["model_test_rank"] = 1
    observed = fit.fit(geometry(), None, None, None, research_candidate=True, n_boot=0,
                       decision_policy=policy, decision_candidate_id="x", decision_variant="spp")
    assert not observed["decision_valid"] and all(value is None for value in observed["rejected"].values())


def test_duplicate_seed_cannot_migrate_between_rank_strata():
    data = campaign()
    row = copy.deepcopy(data["records"][0])
    row["model_test_rank"] = 2
    data["records"].append(row)
    with pytest.raises(ValueError, match="duplicate"): calibrate(data, min_accepted=5)


def test_manifest_preregisters_geometry_rank_and_both_sample_goals(monkeypatch, tmp_path, domain_file):
    import research
    cells = [cell["id"] for cell in geometry_stress_matrix()[:2]]
    output = tmp_path/"manifest.json"
    monkeypatch.setattr(sys, "argv", ["research.py", "--partition", "calibration", "--truth", "all",
        "--geometry", "stress", "--geometry-cells", *cells, "--research-candidate", "--model-test-ranks", "2",
        "--pairwise-evidence", '--flight-domain',str(domain_file), "--write-manifest", str(output), "-o", str(tmp_path/"unused.json")])
    research.main()
    config = json.loads(output.read_text())["config"]
    assert config["preregistered_geometry_cells"] == cells
    assert all(json.loads(cell)[2] == 2 for cell in config["operational_cells"])
    assert all(json.loads(cell)[3] == config['flight_domain']['domain_id'] for cell in config['operational_cells'])
    assert config["campaign_plan"]["validation_family_size"] == 18
    assert config["campaign_plan"]["attempt_cells"] == 6
    assert config["calibration_min_accepted"] == required_calibration_n(.0027)
    assert config["campaign_plan"]["required_accepted_per_cell"] == config["calibration_min_accepted"]


def test_optimizer_cost_can_include_full_design_evaluation(monkeypatch):
    from test_candidate_eligibility import optimizer
    output = optimizer(monkeypatch, lambda *args: pytest.fail("estimate fitted a flight"), max_turns=1,
                       estimate_only=True, pilot_seconds=1., pilot_evaluation_seconds=10.)
    assert output["estimated_seconds_upper"] == 10.*output["upper_bound_evaluations"]
    assert output["upper_bound_anchor_svd_evaluations"] == 3*output["upper_bound_evaluations"]
    assert output["cost_basis"] == "complete design evaluation"


def test_manifest_freezes_explicit_nuisance_subset_and_validation_power(monkeypatch, tmp_path, domain_file):
    import research
    output = tmp_path/"manifest.json"
    monkeypatch.setattr(sys, "argv", ["research.py", "--partition", "calibration", "--truth", "all",
        "--scenarios", "wind", "bias_mixed", "wind", "--geometry", "fixed", "--research-candidate",
        "--model-test-ranks", "2", "--pairwise-evidence", "--calibration-alpha", ".00135",
        "--validation-design-rate", ".00135", '--flight-domain',str(domain_file), "--write-manifest", str(output), "-o", str(tmp_path/"unused.json")])
    research.main()
    config = json.loads(output.read_text())["config"]
    assert config["preregistered_scenarios"] == ["bias_mixed", "wind"]
    assert config["campaign_plan"]["validation_family_size"] == 18
    assert config["campaign_plan"]["attempt_cells"] == 6
    assert config["calibration_min_accepted"] == required_calibration_n(.00135)
    assert config["tail_min_accepted"] == required_accepted_n(.0027, 18, allowed_failures=config["allowed_failures"])
    assert config["campaign_plan"]["validation_power_plan"]["achieved_power"] >= .90


def test_replay_applies_supplied_pairwise_policy(monkeypatch, tmp_path):
    import research
    from lll.research_calibration import diagnostic_stratum
    original = tmp_path/"original.json"
    policy_file = tmp_path/"pairwise.json"
    output = tmp_path/"replayed.json"
    row = dict(truth="sphere_rotating", scenario="baseline", seed=1, sampling="joint", block=1,
               fit_options={"n_boot": 0}, variant="spp", partition="development", design={})
    policy = {"policy_hash": "frozen", "mode": "flight", "family_size": 6,
              "thresholds": {json.dumps(["x", "spp", 3]): {}},
              "diagnostic_thresholds": {json.dumps([diagnostic_stratum({'scenario':'baseline','candidate_id':'x',
                  'variant':'spp','model_test_rank':3}), MODEL_CONTRASTS[0],None]): {}}}
    original.write_text(json.dumps({"records": [row]}))
    policy_file.write_text(json.dumps(policy))
    calls = []
    monkeypatch.setattr(research, "check_pairwise_policy", lambda *args: None)
    monkeypatch.setattr(research, "summarize", lambda rows: {})
    def replay(*args, **kwargs):
        calls.append(kwargs)
        return {"truth": args[0]}
    monkeypatch.setattr(research, "flight_run", replay)
    monkeypatch.setattr(sys, "argv", ["research.py", "--replay", str(original),
        "--pairwise-decision-policy", str(policy_file), "-o", str(output)])
    research.main()
    assert calls[0]["pairwise_decision_policy"] == policy
    assert json.loads(output.read_text())["records"][0]["replay"]


def test_missing_preregistered_geometry_cell_is_not_silently_omitted():
    data = campaign()
    data["config"].update(operational_cells=[decision_stratum(data["records"][0])], geometry="fixed",
                          preregistered_scenarios=["baseline"], preregistered_geometry_cells=[None, "missing"])
    with pytest.raises(ValueError, match="insufficient accepted"): calibrate(data, min_accepted=5)


def measured_fit(truth):
    result = candidate_fit()
    result["k"] = dict(zip(fit.TERM_NAMES, models.EXPECTED_K[truth]))
    result["k_cov"] = (np.eye(3)*1e-4).tolist()
    return result


def test_partial_pair_decision_does_not_manufacture_three_way_winner():
    result = measured_fit("sphere_rotating")
    for name in list(MODEL_PAIRS)[1:]: result["design_identifiability"]["model_contrast_information"][name]["estimable"] = False
    assert "model contrast not identified" in scientific_exclusions({"fit": result})
    evidence = flight_evidence(result)
    first = list(MODEL_PAIRS)[0]
    assert evidence[first]["status"] == "decision" and evidence[first]["preferred_model"] == "sphere_rotating"
    assert all(evidence[name]["status"] == "abstain" for name in list(MODEL_PAIRS)[1:])
    assert three_model_winner(evidence) is None
    evidence[list(MODEL_PAIRS)[1]] = {"status": "decision", "preferred_model": "sphere_rotating"}
    assert three_model_winner(evidence) == "sphere_rotating"


def test_pair_pool_keeps_units_and_excludes_uninformative_flights():
    name = list(MODEL_PAIRS)[0]
    informative = {name: {"eligible": True, "estimate": 1., "sd": .001}}
    excluded = {name: {"eligible": False, "estimate": -100., "sd": 1e-10}}
    single = pool_evidence([("one", informative)]*20, "x", "spp")
    assert single["pairwise"][name]["n_units"] == 1 and single["pairwise"][name]["status"] == "abstain"
    output = pool_evidence([("one", informative)]*20+[("two", informative), ("three", informative), ("four", excluded)], "x", "spp")
    entry = output["pairwise"][name]
    assert entry["n_units"] == 3 and entry["n_sessions"] == 22
    assert entry["estimate"] == pytest.approx(1.) and entry["status"] == "decision"
    assert output["three_model_winner"] is None


def test_flight_pairwise_calibration_is_separate_and_validation_applies_it():
    from test_flight_domain import scoped_campaign
    data = scoped_campaign()
    data["implementation_hash"] = implementation_hash()
    for row in data["records"]:
        row.update(measured_fit(row["truth"]))
        row["pairwise"] = flight_evidence(row)
    policy = calibrate_pairs(data, min_accepted=5)
    assert policy["family_size"] == 6
    check_pairwise_policy(policy, "flight")
    validation = copy.deepcopy(data)
    validation.update(partition="validation")
    validation["config"].update(tail_min_accepted=2000, pairwise_decision_policy_hash=policy["policy_hash"])
    for row in validation["records"]:
        row.update(partition="validation", seed=row["seed"]+1_000_000)
        row["pairwise"] = flight_evidence(row, policy=policy, candidate_id="x", variant="spp")
    report = assess_pairs(validation, policy)
    assert not report["validated"] and all(row["status"] == "inconclusive" for row in report["results"])
    bad = copy.deepcopy(validation)
    bad["records"][0]["pairwise"][MODEL_CONTRASTS[0]].pop("decision_policy_hash")
    with pytest.raises(ValueError, match="frozen rule"): assess_pairs(bad, policy)
    with pytest.raises(ValueError, match="decision mode"): check_pairwise_policy(policy, "pool")


def test_pooled_pairwise_calibration_pipeline_and_unseen_unit_count():
    from research import pooled_run
    data = campaign()
    data["implementation_hash"] = implementation_hash()
    data["records"] = plain([pooled_run(truth, 1_000_000+i, 3, partition="calibration", pairwise=True)
                             for truth in models.MODELS for i in range(5)])
    policy = calibrate_pairs(data, mode="pool", min_accepted=5)
    validation = copy.deepcopy(data)
    validation.update(partition="validation")
    validation["config"].update(tail_min_accepted=2000, pairwise_decision_policy_hash=policy["policy_hash"])
    validation["records"] = plain([pooled_run(truth, 2_000_000+i, 3, partition="validation", pairwise=True,
                                              pairwise_decision_policy=policy) for truth in models.MODELS for i in range(5)])
    report = assess_pairs(validation, policy)
    assert not report["validated"] and report["family_size"] == 6
    unseen = pooled_run("sphere_still", 49, 4, pairwise=True, pairwise_decision_policy=policy)
    assert all(entry["status"] == "abstain" for entry in unseen["pairwise"].values())
    assert all("uncalibrated pairwise pool stratum" in entry["exclusions"] for entry in unseen["pairwise"].values())
