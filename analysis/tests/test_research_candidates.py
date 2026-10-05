# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small independent checks for research machinery; no tail campaigns in CI."""
import json

import numpy as np
import pytest
from scipy.optimize import least_squares

from lll import fit, models
from lll.calib import RAD2DPH
from lll.inference import CandidateProblem, crab_basis, residual_weights, science_information
from lll.inference_policy import INFERENCE_POLICY, digest
from lll.research_design import seed_range, streams, realize, simulator_options, freeze_manifest, validate_manifest
from test_release060 import crab_fixture


def settings(**overrides):
    return {"crab_model": "dynamic", "noise_model": "axis_segment", "forward_uncertainty": False,
            "crab_knot_seconds": 300., "crab_rate_sigma_dph": 1., "variance_shrinkage_bins": 20.,
            "max_nfev": 200, "bootstrap_refit": "nonlinear", **overrides}


def test_partitions_and_frozen_manifest():
    assert seed_range("calibration").start == 1_000_000
    for partition, start, count in [("development", 999999, 2), ("calibration", 999999, 1), ("validation", 3000000, 1)]:
        with pytest.raises(ValueError): seed_range(partition, start, count)
    assert len(set(streams(123).values())) == 7
    assert streams(123) != streams(2_000_123, "validation")
    config = {"seed": 1_000_001, "partition": "calibration"}
    manifest = freeze_manifest(config)
    assert validate_manifest(manifest, config) == manifest["manifest_hash"]
    with pytest.raises(ValueError): validate_manifest(manifest, {**config, "seed": 1_000_002})


@pytest.mark.parametrize("scenario", ["drift+1", "crab_long_drift", "correlated_thermal", "forward_crab", "turn_dropout_drift", "fuzz"])
def test_design_replay_and_paired_geometry(scenario):
    d = realize(49, scenario)
    assert d == json.loads(json.dumps(d)) == realize(49, scenario)
    opts = simulator_options(d)
    assert opts["seed"] == d["streams"]["sensor"]
    assert np.isfinite(opts["crab_trajectory"](np.arange(100))).all()
    assert d["simulator"]["legs"] == realize(49, "drift+0")["simulator"]["legs"]
    assert realize(50, scenario)["simulator"]["legs"] != d["simulator"]["legs"]
    if scenario == "turn_dropout_drift":
        t = d["simulator"]["index_turns"][0][0]
        assert d["simulator"]["link_dropouts"][0][0] == pytest.approx(t+.02)


def test_dynamic_basis_reproduces_linear_rate_across_breaks():
    bins, _ = crab_fixture()
    B, D, knots = crab_basis(bins, "dynamic")
    angles = .03+np.radians(2)*(knots-knots[0])/3600
    np.testing.assert_allclose(B @ angles, .03+np.radians(2)*(bins["t"]-knots[0])/3600)
    np.testing.assert_allclose(D @ angles, np.radians(2)/3600, atol=1e-16)
    np.testing.assert_allclose(B.sum(axis=1), 1.)


def test_weighted_subspace_and_contrasts():
    # Curvature and disc coefficients are individually aliased, but their difference is measured.
    J = np.array([[1., 0., 0., 0.], [0., 1., -1., 0.], [0., 0., 0., 1.],
                  [0., 0., 0., 1.]])
    result = science_information(J, np.array([1., 4., 1., 1.]))
    assert result["report"]["estimable_rank"] == 2
    assert result["report"]["model_contrast_information"]["sphere_still_vs_flat_still"]["estimable"]
    assert result["report"]["model_contrast_information"]["sphere_still_vs_flat_still"]["information"] > 0
    J[:, 1] = J[:, 2] = 0
    assert not science_information(J, np.ones(4))["report"]["model_contrast_information"]["sphere_still_vs_flat_still"]["estimable"]


def test_independent_protocol_and_missingness_streams():
    from lll.research_design import validate_turn_schedule
    d = realize(49, "drift+0")
    changed = realize(49, "drift+0", turn_schedule=[15., 35.])
    assert changed["simulator"]["legs"] == d["simulator"]["legs"]
    assert changed["simulator"]["gnss_dropouts"] == d["simulator"]["gnss_dropouts"]
    assert changed["simulator"]["index_turns"] == [[15., "z"], [35., "z"]]
    with pytest.raises(ValueError): validate_turn_schedule([5., 10.], 90.)


def test_exact_campaign_size():
    from lll.research_calibration import required_accepted_n
    from scipy.stats import beta
    n = required_accepted_n(.0027, 9)
    assert beta.ppf(1-.05/9, 1, n) <= .0027
    assert beta.ppf(1-.05/9, 1, n-1) > .0027


def test_candidate_prediction_jacobian_and_independent_map():
    bins, fwd = crab_fixture()
    problem = CandidateProblem(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH),
                               settings(forward_uncertainty=True), forward_sigma_rad=.02)
    z = np.r_[1.1, .9, .1, [1e-6, -1e-6, 1e-6], np.linspace(.01, .03, problem.nc), .02]
    pred, J = problem.prediction(z, True)
    for i in range(len(z)):
        h = 1e-7 if i < 6 else 1e-5
        a, b = z.copy(), z.copy(); a[i] += h; b[i] -= h
        np.testing.assert_allclose(J[:, i], (problem.prediction(a)-problem.prediction(b))/(2*h), rtol=3e-5, atol=1e-9)
    # Vertical rotation is independently -d(crab)/dt for this +z-up fixture.
    no_rate = problem.B @ z[problem.p:problem.p+problem.nc]
    _, X, *_ = fit.build_rows(bins, fwd*np.cos(z[-1])+problem.tangent*np.sin(z[-1]), lambda t: 0., dpsi=no_rate)
    expected = (X @ z[:problem.p]).reshape(-1, 3)
    expected[:, 2] -= problem.D @ z[problem.p:problem.p+problem.nc]
    np.testing.assert_allclose(pred.reshape(-1, 3), expected)
    P = problem.penalty()
    for fixed in [None, models.EXPECTED_K["flat_still"]]:
        actual = problem.solve(fixed=fixed)
        keep = np.arange(problem.npar) if fixed is None else np.arange(3, problem.npar)
        def fun(x):
            v = actual["z"].copy(); v[keep] = x
            return np.r_[(problem.prediction(v)-problem.y)*np.sqrt(problem.w), P @ v]
        ref = least_squares(fun, actual["z"][keep], jac="3-point", x_scale="jac", ftol=1e-11, xtol=1e-11, gtol=1e-9)
        assert actual["objective"] == pytest.approx(ref.fun @ ref.fun, abs=1e-7, rel=1e-7)


def test_variance_shrinkage_and_short_segments():
    bins = {"t": np.arange(101), "seg": np.r_[np.zeros(100), 1]}
    r = np.tile([1., 3., 9.], (101, 1)); r[-1] = 0
    w, info = residual_weights(r.ravel(), bins, "axis_segment")
    assert np.isfinite(w).all()
    assert w.reshape(-1, 3)[0, 0] > w.reshape(-1, 3)[0, 2]
    assert info["group_counts"] == [100, 1]
    np.testing.assert_allclose(1/w.reshape(-1, 3)[-1], np.mean(r*r)*20/21)


def test_nonlinear_bootstrap_and_frozen_weights(monkeypatch):
    bins, fwd = crab_fixture()
    from lll import inference
    captured = []
    original = inference.CandidateProblem.solve
    def solve(self, *args, **kwargs):
        captured.append(self.w.copy())
        return original(self, *args, **kwargs)
    monkeypatch.setattr(inference.CandidateProblem, "solve", solve)
    result = fit.fit(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), n_boot=2, block_length=3,
                     crab_model="dynamic", noise_model="axis_segment", bootstrap_refit="nonlinear", bootstrap_sampling="segment")
    assert result["bootstrap"]["replicates"] == 2
    assert result["bootstrap"]["failures"] == []
    assert all(v == 2 for v in result["bootstrap"]["null_replicates"].values())
    assert all(c >= result["chi2_free"]-1e-6 for c in result["chi2"].values())
    for w in captured[2:]: np.testing.assert_array_equal(w, captured[1])
    assert np.linalg.eigvalsh(result["k_cov"]).min() >= -1e-12


def test_segment_sampling_respects_time_breaks():
    bins = {"t": np.r_[np.arange(5), 100+np.arange(5)], "dt": np.ones(10), "seg": np.zeros(10)}
    for seed in range(10):
        order = fit.bootstrap_order(np.random.default_rng(seed), bins, 3, "segment")
        assert np.all(order[:5] < 5) and np.all(order[5:] >= 5)


def test_forward_regression_covariance():
    from lll.attitude import estimate_forward_axis, course_rate
    t = np.arange(600.)
    bearing = 40*np.sin(t/60)
    speed = np.full(len(t), 230.)
    bank_rate = np.gradient(np.arctan(speed*course_rate(t, bearing)/9.80665), t)
    rng = np.random.default_rng(3)
    g = bank_rate[:, None]*np.array([1., 0., 0.])+rng.normal(0, .0001, (len(t), 3))
    axis, info = estimate_forward_axis(t, g, t, speed, bearing, np.array([0., 0., 1.]))
    assert axis is not None and info["angle_sigma_rad"] > 0
    C = np.array(info["axis_cov"])
    assert np.linalg.eigvalsh(C).min() > -1e-14
    np.testing.assert_allclose(C @ axis, 0, atol=1e-12)
    np.testing.assert_allclose(C[2], 0, atol=1e-12)


def test_pool_bootstrap_keeps_clusters(monkeypatch):
    from lll import collate
    items = []
    for u in range(4):
        for f in range(u+1):
            items.append((str(u), dict(zip(fit.TERM_NAMES, [1+u*.01, 1+f*.01, .01])), dict.fromkeys(fit.TERM_NAMES, .1), {}, np.eye(3)*.01))
    original = collate.pool_hierarchical
    samples = []
    def pool(sample):
        samples.append(sample)
        return original(sample)
    monkeypatch.setattr(collate, "pool_hierarchical", pool)
    result = collate.bootstrap_joint_tests(items, n_boot=8, seed=4)
    assert result["status"] == "experimental"
    for sample in samples[1:]:
        ids = {x[0] for x in sample}
        assert len(ids) == 4
        for identity in ids:
            cluster = [x for x in sample if x[0] == identity]
            assert 1 <= len(cluster) <= 4
            # Flight curvature increments survive centering and resampling intact.
            assert np.ptp([x[1]["k_curv"] for x in cluster]) == pytest.approx((len(cluster)-1)*.01)
    assert all(v["p"] >= 1/9 for v in result["tests"].values())


def test_calibration_requires_independent_evidence():
    from lll.research_calibration import calibrate, assess
    from lll import __version__
    rows = [{"scenario": "baseline", "candidate_id": "x", "truth": m, "partition": "calibration", "exclusions": [],
             "seed": 1_000_000+i, "delta_chi2_raw": {m: float(i)}, "rejected": False} for m in models.MODELS for i in range(5)]
    campaign = {"partition": "calibration", "manifest_hash": "frozen", "analysis_version": __version__, "records": rows}
    policy = calibrate(campaign, min_accepted=5)
    with pytest.raises(ValueError): calibrate({**campaign, "partition": "development"}, min_accepted=5)
    with pytest.raises(ValueError): calibrate(campaign, min_accepted=6)
    with pytest.raises(ValueError, match="duplicate"):
        calibrate({**campaign, "records": rows+[rows[0]]}, min_accepted=5)
    validation = {**campaign, "partition": "validation", "config": {"tail_min_accepted": 2000, "decision_policy_hash": policy["policy_hash"]},
                  "records": [{**r, "seed": r["seed"]+1_000_000, "partition": "validation", "decision_policy_hash": policy["policy_hash"]} for r in rows]}
    report = assess(validation, policy)
    assert not report["validated"] and all(r["status"] == "inconclusive" for r in report["results"])
    assert report["family_size"] == 3


def test_summary_separates_candidates():
    from research import summarize
    rows = [{"truth": "flat_still", "scenario": "smooth", "candidate_id": candidate, "failure": "no fit"} for candidate in ("a", "b")]
    assert len(summarize(rows)) == 2


def test_bootstrap_null_distribution_is_centered():
    from lll.collate import bootstrap_joint_tests
    items = [(str(i), dict(zip(fit.TERM_NAMES, [1+i*.01, .9-i*.01, .03*i])),
              dict.fromkeys(fit.TERM_NAMES, .1), {}, np.eye(3)*.01) for i in range(5)]
    r = bootstrap_joint_tests(items, n_boot=10, seed=42)
    # Centering at any tested null must produce the same studentized null distribution.
    distributions = [v["null_statistics"] for v in r["tests"].values()]
    for d in distributions[1:]: np.testing.assert_allclose(d, distributions[0], atol=1e-10)


def test_local_and_nonlinear_agree_for_linear_problem():
    bins, fwd = crab_fixture()
    problem = CandidateProblem(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), settings(), crab_sigma_deg=0.)
    reference = problem.solve()
    y = problem.y+np.random.default_rng(4).normal(0, .1/RAD2DPH, len(problem.y))
    for fixed in (None, models.EXPECTED_K["flat_still"]):
        a, b = problem.local(y, reference, fixed), problem.solve(y, fixed=fixed)
        assert a["objective"] == pytest.approx(b["objective"], abs=1e-8)
        np.testing.assert_allclose(a["z"], b["z"], atol=1e-7)


def test_collation_rejects_mixed_inference_policies():
    from lll.collate import collate
    rows = [{"fit": {"inference_policy": {"configuration_hash": h}}} for h in ("a", "b")]
    with pytest.raises(ValueError, match="incompatible inference"):
        collate(rows)


def test_failed_flight_retains_replay_inputs(monkeypatch):
    import research
    calls = []
    monkeypatch.setattr(research, "synthesize", lambda *a, **kw: calls.append(kw))
    def fail(*args, **kwargs):
        assert kwargs["fit_options"]["research_forward_offset_deg"] == 3.
        raise ValueError("deliberate analysis failure")
    monkeypatch.setattr(research, "analyze", fail)
    row = research.flight_run("flat_still", "forward_crab", 7, "segment", 3, 0, "ble", geometry="seeded")
    assert "deliberate analysis failure" in row["failure"]
    replay = research.flight_run("flat_still", "forward_crab", 7, "segment", 3, 0, "ble", design=row["design"], fit_options=row["fit_options"])
    assert row["design"] == replay["design"] and row["candidate_id"] == replay["candidate_id"]
    assert calls[0]["seed"] == calls[1]["seed"]


def test_empirical_rule_keeps_analytic_diagnostics():
    bins, fwd = crab_fixture()
    result = fit.fit(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), n_boot=0,
                     decision_thresholds=dict.fromkeys(models.MODELS, 1e20), decision_policy_hash="research-only")
    assert not any(result["rejected"].values())
    assert result["decision_policy_hash"] == "research-only"
    assert "rejected_analytic" in result and "p_asymptotic" in result


def test_environment_does_not_invoke_git(monkeypatch):
    import subprocess
    from lll.analyze import environment
    def unexpected(*args, **kwargs): raise AssertionError("environment must not launch commands")
    monkeypatch.setattr(subprocess, "run", unexpected)
    monkeypatch.setenv("LLL_GIT_COMMIT", "provided-by-build")
    assert environment()["git_commit"] == "provided-by-build"
