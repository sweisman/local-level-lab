# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small independent checks of the experimental design and decision interfaces."""
import json

import numpy as np
import pytest

from lll import fit, models
from lll.calib import RAD2DPH
from lll.inference import CandidateProblem, crab_basis, science_information
from lll.research_calibration import calibrate, decision_stratum, diagnostic_stratum
from lll.synth import wind_velocity
from lll.policy import CANDIDATE_POLICY, MODEL_CONTRASTS, eligibility_policies, eligibility_provenance
from lll.runtime import numerical_environment
from test_release060 import crab_fixture
from test_research_candidates import settings


def test_weighting_and_discarded_science_information():
    J = np.zeros((5, 4))
    J[:3, :3] = np.eye(3)
    J[3, 0] = 1
    J[0, 3] = 1
    first = science_information(J, np.ones(5))
    weighted = science_information(J, np.array([1e-6, 1, 1, 1, 1.]))
    assert min(weighted["report"]["normalized_singular_values"]) > min(first["report"]["normalized_singular_values"])
    J[3, 0] = 0
    J[4, 3] = 1e-3
    dropped = science_information(J, np.ones(5))
    assert dropped["report"]["estimable_rank"] == 2
    np.testing.assert_allclose(dropped["fisher"][:, 0], 0, atol=1e-12)
    assert json.loads(json.dumps(dropped["report"])) == dropped["report"]


def test_profile_leaves_unobservable_combination_free():
    bins, fwd = crab_fixture()
    p = CandidateProblem(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), settings(), crab_sigma_deg=0.)
    free = p.solve()
    C = np.array([[1., 0., 0.], [0., 1/np.sqrt(2), -1/np.sqrt(2)]])
    target = np.array([0., 1., 0.])
    a = p.profile(target, C, reference=free)
    b = p.profile(target+np.array([0., 100., 100.]), C, reference=free)
    assert a["success"] and b["success"]
    assert a["objective"] == pytest.approx(b["objective"], abs=1e-8)
    np.testing.assert_allclose(C @ a["z"][:3], C @ target, atol=1e-12)
    # Independent linear Gaussian profile in explicit null/nuisance coordinates.
    T = np.zeros((p.npar, p.npar-2))
    T[:3, 0] = [0., 1/np.sqrt(2), 1/np.sqrt(2)]
    T[3:, 1:] = np.eye(p.npar-3)
    offset = np.r_[target, np.zeros(p.npar-3)]
    A = np.vstack([p.X*np.sqrt(p.w)[:, None], p.penalty()])
    y = np.r_[p.y*np.sqrt(p.w), np.zeros(len(p.penalty()))]-A @ offset
    x = np.linalg.lstsq(A @ T, y, rcond=None)[0]
    assert a["objective"] == pytest.approx(np.sum((y-A @ T @ x)**2), rel=1e-10)


def test_bootstrap_failure_invalidates_empirical_decision(monkeypatch):
    bins, fwd = crab_fixture()
    original = CandidateProblem.solve
    attempts = []
    def fail_bootstrap(self, y=None, *args, **kwargs):
        result = original(self, y, *args, **kwargs)
        if y is not None and kwargs.get("record") is False:
            attempts.append(kwargs.get("start"))
            result["success"] = False
        return result
    monkeypatch.setattr(CandidateProblem, "solve", fail_bootstrap)
    result = fit.fit(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), n_boot=20, block_length=3,
                     research_candidate=True, crab_sigma_deg=0., bootstrap_refit="nonlinear",
                     decision_thresholds=dict.fromkeys(models.MODELS, 0.), decision_policy_hash="test")
    assert len(attempts) >= 20*3
    assert not result["bootstrap"]["bootstrap_valid"]
    assert result["bootstrap"]["free_success_fraction"] == 0
    assert result["p_bootstrap_calibrated"] is None
    assert not result["decision_valid"]
    assert all(v is None for v in result["rejected"].values())


def test_wind_triangle_and_course_dependent_crab_derivative():
    t = np.linspace(0., 3600., 100)
    psi = np.linspace(0., np.pi, len(t))
    wind0, wind_rate = np.array([12., -8.]), np.array([3., -2.])
    speed, ground, heading = wind_velocity(psi, t, 230., wind0, wind_rate)
    wind = wind0+t[:, None]/3600*wind_rate
    np.testing.assert_allclose(np.linalg.norm(ground-wind, axis=1), 230., atol=1e-12)
    np.testing.assert_allclose(ground/speed[:, None], np.column_stack([np.cos(psi), np.sin(psi)]))
    np.testing.assert_allclose(heading, np.arctan2((ground-wind)[:, 1], (ground-wind)[:, 0]))
    rate = np.full(len(t), np.pi/3600)
    B, D, knots = crab_basis({"t": t, "psi": psi, "psi_dot": rate}, "wind", 900.)
    coefficients = np.tile([.05, -.02], len(knots))
    np.testing.assert_allclose(B @ coefficients, .05*np.sin(psi)-.02*np.cos(psi), atol=1e-15)
    np.testing.assert_allclose(D @ coefficients, (.05*np.cos(psi)+.02*np.sin(psi))*rate, atol=1e-15)
    with pytest.raises(ValueError): wind_velocity(psi, t, 5., wind0)


def test_wind_candidate_joint_jacobian():
    bins, fwd = crab_fixture()
    p = CandidateProblem(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH),
                         settings(crab_model="wind", bias_model="dynamic", crab_knot_seconds=900.))
    z = np.zeros(p.npar)
    z[:3] = [1.1, .9, .1]
    z[p.p:] = np.tile([.04, -.02], p.nc//2)
    _, J = p.prediction(z, True)
    for i in range(p.npar):
        a, b = z.copy(), z.copy()
        a[i] += 1e-7
        b[i] -= 1e-7
        np.testing.assert_allclose(J[:, i], (p.prediction(a)-p.prediction(b))/2e-7, rtol=2e-5, atol=1e-9)
    assert np.isfinite(p.penalty()).all()


@pytest.mark.parametrize("n_boot", [0, 2])
def test_rank_zero_abstains_despite_raw_model_difference(monkeypatch, n_boot):
    import lll.inference as inference
    original = inference.science_information
    monkeypatch.setattr(inference, "science_information", lambda J, w: original(J, w, threshold=10.))
    bins, fwd = crab_fixture()
    result = fit.fit(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), n_boot=n_boot, block_length=3,
                     research_candidate=True, crab_sigma_deg=0.)
    assert result["model_test_rank"] == 0
    assert max(result["delta_chi2_raw"].values()) > 0
    assert all(p is None for p in result["p_vs_free"].values())
    assert all(rejected is None for rejected in result["rejected"].values())
    assert all(attempts == 0 for attempts in result["bootstrap"]["null_attempted_by_model"].values())


def test_design_evaluation_uses_two_free_fits(monkeypatch):
    bins, fwd = crab_fixture()
    calls = []
    original = CandidateProblem.solve
    def solve(self, *args, **kwargs):
        calls.append(kwargs.get("fixed"))
        return original(self, *args, **kwargs)
    monkeypatch.setattr(CandidateProblem, "solve", solve)
    result = fit.fit(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), n_boot=0, design_only=True,
                     crab_model="dynamic", noise_model="axis_segment", bias_model="dynamic")
    assert calls == [None, None]
    assert result["design_only"] and result["delta_chi2_raw"] is None
    assert "expected_k_sd_without_priors" in result["identifiability"]
    assert all(v is None for v in result["rejected"].values())


def test_operational_threshold_covers_each_adversary():
    rows = [{"scenario": scenario, "candidate_id": "x", "variant": "spp", "geometry": geometry,
             "truth": truth, "partition": "calibration", "exclusions": [], "seed": 1_000_000+i,
             "delta_chi2_identifiable": {truth: float(i+shift)}, "model_test_rank": 2,
             "eligibility_policy": eligibility_provenance(True), "convergence": {"converged": True},
             "inference_policy": {"settings": {"engine": "candidate-1", "n_boot": 20}},
             "numerical_environment": numerical_environment(),
             "design_identifiability": {"rank_threshold": CANDIDATE_POLICY["retention_threshold"],
                 "assumptions": CANDIDATE_POLICY["design_assumptions"],
                 "model_contrast_information": {name: {"estimable": True, "retained_fraction": .8, "information": 10.}
                                                for name in MODEL_CONTRASTS}},
             "bootstrap": {"bootstrap_valid": True}}
            for scenario, geometry, shift in [("bias_step", "fixed", 0), ("bias_mixed", "seeded", 10)]
            for truth in models.MODELS for i in range(5)]
    policy = calibrate({"partition": "calibration", "manifest_hash": "test", "analysis_version": "0.6.0",
                        "numerical_environment": numerical_environment(),
                        "config": {"calibration_tail_observations": 1, "calibration_tail_confidence": .01, "calibration_min_accepted": 5},
                        "eligibility_policies": eligibility_policies(), "records": rows}, min_accepted=5)
    assert len(policy["thresholds"]) == 1 and len(policy["diagnostic_thresholds"]) == 2
    assert set(next(iter(policy["thresholds"].values())).values()) == {14.}
    assert decision_stratum(rows[0]) == decision_stratum(rows[-1])
    assert diagnostic_stratum(rows[0]) != diagnostic_stratum(rows[-1])


def test_optimizer_pairs_inputs_and_searches_turn_counts(monkeypatch):
    import optimize_turns
    captured = []
    def flight(truth, scenario, seed, *args, design, **kwargs):
        captured.append((truth, design, kwargs["fit_options"]["crab_model"]))
        n = len(design["simulator"]["index_turns"])
        return {"convergence": {"converged": True}, "design_identifiability": {
            "assumptions": CANDIDATE_POLICY["design_assumptions"],
            "estimable_rank": 3, "normalized_singular_values": [1., 1., 1.],
            "rank_threshold": CANDIDATE_POLICY["retention_threshold"],
            "model_contrast_information": {name: {"information": float(n), "retained_fraction": .5+.1*n, "estimable": True}
                                           for name in MODEL_CONTRASTS}}}
    monkeypatch.setattr(optimize_turns, "flight_run", flight)
    result = optimize_turns.search(seeds=[49], scenarios=["bias_mixed"], max_turns=2, grid_min=20.)
    assert len(result["best"]["turn_schedule_min"]) == 2
    assert len(result["frontier_by_turn_count"]) == 3
    inputs = [{k: v for k, v in d["simulator"].items() if k != "index_turns"} for _, d, _ in captured]
    assert all(v == inputs[0] for v in inputs)
    assert {truth for truth, _, _ in captured} == set(models.MODELS)
    assert {crab for _, _, crab in captured} == {"dynamic", "wind"}
    assert result == json.loads(json.dumps(result))


def test_summary_keeps_abstentions_and_requires_retaining_truth():
    from research import summarize
    base = {"truth": "sphere_still", "scenario": "bias_step", "k": dict(zip(fit.TERM_NAMES, [0., 1., 0.]))}
    rows = [{**base, "rejected": None, "exclusions": ["model contrast not identified"]},
            {**base, "rejected": True, "exclusions": [], "rejected_by_model": dict.fromkeys(models.MODELS, True)}]
    summary = summarize(rows)[0]
    assert summary["analysis_failures"] == 0 and summary["no_decision"] == 1
    assert summary["coefficient_rmse"] == [0., 0., 0.]
    assert summary["model_separation_power"] == 0


def test_manifest_cost_includes_failed_attempts(monkeypatch, tmp_path):
    import research
    import sys
    pilot = tmp_path/"pilot.json"
    pilot.write_text(json.dumps({"partition": "development", "records": [
        {"failure": "no fit", "elapsed_s": 2.}, {"rejected": False, "exclusions": [], "elapsed_s": 4.}]}))
    manifest = tmp_path/"manifest.json"
    monkeypatch.setattr(sys, "argv", ["research.py", "--truth", "all", "--scenario", "bias_mixed",
                                    "--bias-model", "dynamic", "--model-test-ranks", "3", "--development-campaign", str(pilot),
                                    "--write-manifest", str(manifest), "-o", str(tmp_path/"unused.json")])
    research.main()
    plan = json.loads(manifest.read_text())["config"]["campaign_plan"]
    assert plan["decision_cells"] == 3
    assert plan["development_acceptance_probability"] == .5
    assert plan["estimated_attempts_total"] == 6*plan["required_accepted_per_cell"]
    assert plan["estimated_compute_seconds"] == 3*plan["estimated_attempts_total"]
