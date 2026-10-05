# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent, small checks for the experimental sensor-bias trajectory."""
import numpy as np
import pytest

from lll import fit, models
from lll.calib import RAD2DPH
from lll.inference import CandidateProblem, sensor_bias_basis
from test_release060 import crab_fixture
from test_research_candidates import settings


def problem(*, vertical=False, **overrides):
    bins, fwd = crab_fixture()
    options = settings(bias_model="dynamic", bias_knot_seconds=900., bias_rw_sigma_dph_sqrth=3., **overrides)
    return CandidateProblem(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), options,
                            vertical_only=vertical, crab_sigma_deg=0.)


def test_sensor_frame_curve_continues_across_mount_turns_and_gaps():
    bins = {"t": np.array([0., 300., 900., 1500., 2100.]),
            "seg": np.arange(5), "grav": np.array([0, 0, 1, 1, 0]),
            "up": np.array([[0, 0, 1], [0, 0, 1], [0, 0, -1], [0, 0, -1], [0, 0, 1.]])}
    H, B, knots, _ = sensor_bias_basis(bins)
    slope = np.array([1., -2., 3.])/RAD2DPH/3600
    values = knots[1:, None]*slope
    expected = bins["t"][:, None]*slope
    np.testing.assert_allclose((H @ values.ravel()).reshape(-1, 3), expected, atol=1e-15)
    np.testing.assert_array_equal(H[:3], 0)
    # Body-frame bias is unchanged by mount turns; only vertical projection changes sign.
    Hv, _, _, _ = sensor_bias_basis(bins, vertical_only=True)
    np.testing.assert_allclose(Hv @ values.ravel(), np.sum(-bins["up"]*expected, axis=1), atol=1e-15)


def test_random_walk_prior_units_and_time_scaling():
    p = problem()
    P = p.penalty()
    z = np.zeros(p.npar)
    hours = np.diff(p.bias_knots)/3600
    increments = np.tile((3/RAD2DPH*np.sqrt(hours))[:, None], (1, 3))
    z[p.bias_drift_slice] = np.cumsum(increments, axis=0).ravel()
    # Each independent knot/axis innovation equals exactly one prior standard deviation.
    assert np.sum((P @ z)**2) == pytest.approx(increments.size)
    assert np.sum((p.penalty(bias_drift=3) @ z)**2) == pytest.approx(increments.size/9)
    H, B, knots, penalty = sensor_bias_basis({**p.bins, "t": p.bins["t"]*4}, knot_seconds=3600.)
    np.testing.assert_allclose(penalty, p.bias_penalty/2)


@pytest.mark.parametrize("vertical", [False, True])
def test_dynamic_bias_map_and_covariance_match_linear_gaussian_reference(vertical):
    p = problem(vertical=vertical)
    # With crab and forward-angle estimation off, use a direct augmented linear reference.
    P = p.penalty()
    for fixed in (None, models.EXPECTED_K["sphere_still"]):
        keep = np.arange(p.p) if fixed is None else np.arange(3, p.p)
        offset = np.zeros(p.npar)
        if fixed is not None: offset[:3] = fixed
        A = np.vstack([p.X[:, keep]*np.sqrt(p.w)[:, None], P[:, keep]])
        y = np.r_[(p.y-p.X @ offset[:p.p])*np.sqrt(p.w), -P @ offset]
        expected = np.linalg.lstsq(A, y, rcond=None)[0]
        inverse = np.linalg.pinv(A)
        actual = p.solve(fixed=fixed)
        assert actual["success"]
        np.testing.assert_allclose(actual["z"][keep], expected, atol=1e-8)
        assert actual["objective"] == pytest.approx(np.sum((A @ expected-y)**2), rel=1e-9)
        np.testing.assert_allclose(actual["cov"], inverse @ inverse.T, rtol=2e-4, atol=1e-8)


def test_joint_crab_forward_bias_jacobian():
    bins, fwd = crab_fixture()
    p = CandidateProblem(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH),
                         settings(bias_model="dynamic", forward_uncertainty=True), forward_sigma_rad=.02)
    z = np.zeros(p.npar); z[:3] = [1.1, .9, .1]
    z[p.bias_drift_slice] = np.linspace(-1, 1, p.p-p.base_p)/RAD2DPH
    z[p.p:p.p+p.nc] = np.linspace(.01, .02, p.nc); z[-1] = .01
    _, J = p.prediction(z, True)
    for i in range(p.npar):
        h = 1e-7
        a, b = z.copy(), z.copy(); a[i] += h; b[i] -= h
        np.testing.assert_allclose(J[:, i], (p.prediction(a)-p.prediction(b))/(2*h), rtol=2e-5, atol=1e-9)


@pytest.mark.parametrize("refit", ["linearized", "nonlinear"])
def test_dynamic_bias_bootstrap_refits_and_sensitivity(refit, monkeypatch):
    bins, fwd = crab_fixture()
    captured = []
    solve = CandidateProblem.solve
    def record(self, *args, **kwargs):
        captured.append((self.bias_columns.copy(), self.w.copy(), kwargs.get("fixed")))
        return solve(self, *args, **kwargs)
    monkeypatch.setattr(CandidateProblem, "solve", record)
    r = fit.fit(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), n_boot=2, block_length=3,
                crab_model="dynamic", bias_model="dynamic", bootstrap_refit=refit, bootstrap_sampling="segment")
    assert r["convergence"]["converged"]
    assert r["bootstrap"]["replicates"] == 2 and not r["bootstrap"]["failures"]
    assert all(v == 2 for v in r["bootstrap"]["null_replicates"].values())
    assert all(v >= r["chi2_free"]-1e-6 for v in r["chi2"].values())
    assert "bias_drift" in r["prior_sensitivity"]["k_shift_sigma_by_prior"]
    assert r["sensor_bias"]["frame"] == "sensor"
    assert np.asarray(r["sensor_bias"]["per_bin_drift_dph"]).shape == (len(bins["t"]), 3)
    np.testing.assert_array_equal(r["sensor_bias"]["knot_drift_dph"][0], 0)
    for H, w, _ in captured[2:]:
        np.testing.assert_array_equal(H, captured[1][0])
        np.testing.assert_array_equal(w, captured[1][1])
    assert r["inference_policy"]["settings"]["bias_model"] == "dynamic"


@pytest.mark.parametrize("option,value", [("bias_rw_sigma_dph_sqrth", 0), ("bias_rw_sigma_dph_sqrth", float("nan")), ("bias_knot_seconds", -1)])
def test_invalid_dynamic_bias_settings(option, value):
    bins, fwd = crab_fixture()
    with pytest.raises(ValueError):
        fit.fit(bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH), n_boot=0,
                bias_model="dynamic", **{option: value})


def test_bias_prior_limit_and_uncertainty_propagation():
    bins, fwd = crab_fixture()
    args = (bins, fwd, lambda t: 0., np.full(3, 2/RAD2DPH))
    constant = CandidateProblem(*args, settings(), crab_sigma_deg=0.).solve()
    tight = CandidateProblem(*args, settings(bias_model="dynamic", bias_rw_sigma_dph_sqrth=.001), crab_sigma_deg=0.).solve()
    flexible = CandidateProblem(*args, settings(bias_model="dynamic"), crab_sigma_deg=0.).solve()
    np.testing.assert_allclose(tight["z"][:3], constant["z"][:3], atol=1e-5)
    # At the same weights and linear design, marginalizing added nuisance coefficients must
    # not spuriously reduce uncertainty in the model coefficients.
    difference = flexible["cov"][:3, :3]-constant["cov"][:3, :3]
    assert np.linalg.eigvalsh(difference).min() >= -1e-10


def test_bias_cli_options_reach_harness(monkeypatch, tmp_path):
    import sys
    import research
    captured = []
    def run(truth, scenario, *args, **kwargs):
        captured.append(kwargs["fit_options"])
        return {"truth": truth, "scenario": scenario, "failure": "mock analysis"}
    monkeypatch.setattr(research, "flight_run", run)
    monkeypatch.setattr(sys, "argv", ["research.py", "--bias-model", "constant", "dynamic",
                                    "--bias-knot-seconds", "1200", "--bias-rw-sigma-dph-sqrth", "2",
                                    "--bootstrap", "0", "-o", str(tmp_path/"pilot.json")])
    research.main()
    assert [c["bias_model"] for c in captured] == ["constant", "dynamic"]
    assert all(c["bias_knot_seconds"] == 1200 and c["bias_rw_sigma_dph_sqrth"] == 2 for c in captured)
