"""Small correctness fixtures; expensive coverage belongs in research.py."""
import itertools

import numpy as np
import pytest

from lll import calib, fit, models
from lll.attitude import course_rate, mount_epochs
from lll.policy import heading_diversity
from lll.segments import InvalidGnssData, gnss_kinematics


def test_heading_permutations_and_north_wrap():
    for angles in ([359, 1, 9, 40], [0, 9, 18, 60], [0, 90, 180, 270]):
        times = np.array([300, 300, 600, 600])
        expected = heading_diversity({"psi": np.radians(angles), "dt": times})
        for order in itertools.permutations(range(4)):
            assert heading_diversity({"psi": np.radians(angles)[list(order)], "dt": times[list(order)]}) == expected


@pytest.mark.parametrize("rate", [20, 100])
def test_missing_turn_cannot_double_angle(rate):
    t = np.arange(0, 30, 1 / rate)
    g = np.zeros((len(t), 3))
    g[(t >= 10) & (t < 12), 2] = np.radians(45)
    # Lose the stop of a 90-degree turn; zero-order hold used to invent the missing rotation.
    keep = ~((t >= 12) & (t < 14))
    epochs, _ = mount_epochs(t[keep], g[keep], [(20, "index_turn")], expected_period=1 / rate)
    assert epochs[-1]["orientation_unresolved"]
    assert epochs[-1]["turn"]["unresolved_gap"]
    assert epochs[-1]["turn"]["angle_deg"] is None


def test_dense_short_gnss_and_duplicates():
    t = np.arange(100) / 100
    gn = {"t_ns": (t * 1e9).astype(np.int64), "lat": t * 0 + 40, "lon": t * 0,
          "bearing_deg": t * 0, "speed_mps": t * 0 + 200, "alt_m": t * 0 + 10000, "h_acc_m": t * 0 + 5}
    assert np.isfinite(gnss_kinematics(gn)["psi_dot"]).all()
    assert np.all(course_rate(t, t) == 0)
    duplicated = {k: np.repeat(v, 2) for k, v in gn.items()}
    assert len(gnss_kinematics(duplicated)["t"]) == len(t)
    duplicated["lat"][1] += 1
    with pytest.raises(InvalidGnssData, match="conflicting fixes"):
        gnss_kinematics(duplicated)


def crab_fixture():
    n = 48
    seg = np.repeat(np.arange(4), 12)
    psi = np.radians(np.array([10, 90, 180, 270])[seg])
    bins = {"t": np.arange(n) * 60., "dt": np.full(n, 60.), "seg": seg,
            "psi": psi, "lat": np.radians(np.linspace(30, 55, n)), "h": np.full(n, 11000.),
            "v_n": 230 * np.cos(psi), "v_e": 230 * np.sin(psi),
            "up": np.tile([0., 0., 1.], (n, 1)), "dup_dt": np.zeros((n, 3)),
            "psi_dot": np.zeros(n), "gyro": np.zeros((n, 3))}
    fwd = np.tile([1., 0., 0.], (n, 1)) * np.where(np.arange(n) % 2, -1, 1)[:, None]
    _, X, *_ = fit.build_rows(bins, fwd, lambda t: 0., dpsi=np.radians(np.array([8, -7, 4, 10])[seg]))
    theta = np.r_[1.1, .9, .1, np.array([.2, -.3, .1]) / calib.RAD2DPH]
    bins["gyro"] = (X @ theta).reshape(n, 3) + np.random.default_rng(9).normal(0, .2 / calib.RAD2DPH, (n, 3))
    return bins, fwd


@pytest.mark.parametrize("sd", [5., 15.])
def test_crab_matches_independent_numerical_map(sd):
    from scipy.optimize import least_squares
    bins, fwd = crab_fixture()
    result = fit.fit(bins, fwd, lambda t: 0., np.full(3, 2 / calib.RAD2DPH), n_boot=0, crab_sigma_deg=sd)
    assert result["convergence"]["converged"]
    terms = np.stack(models.terms(bins["lat"], bins["h"], bins["v_n"], bins["v_e"]), axis=-1)
    sigma = result["sigma_bin_dph"]
    for fixed in [None, *models.EXPECTED_K]:
        def residual(z):
            k, b, d = (z[:3], z[3:6], z[6:]) if fixed is None else (models.EXPECTED_K[fixed], z[:3], z[3:])
            v = terms @ k * calib.RAD2DPH
            angle = bins["psi"] + np.radians(d[bins["seg"]])
            co, si = np.cos(angle), np.sin(angle)
            # Explicit NED-to-sensor rotation, independent of build_rows and its Jacobian.
            pred = np.column_stack([co*v[:, 0] + si*v[:, 1], si*v[:, 0] - co*v[:, 1], -v[:, 2]])
            pred[:, :2] *= fwd[:, :1]
            return np.r_[((pred + b - bins["gyro"] * calib.RAD2DPH) / sigma).ravel(), b / 2, d / sd]
        z0 = np.r_[list(result["k"].values()), np.zeros(7)] if fixed is None else np.zeros(7)
        ref = least_squares(residual, z0, ftol=1e-12, xtol=1e-12, gtol=1e-10)
        objective = result["chi2_free"] if fixed is None else result["chi2"][fixed]
        assert objective == pytest.approx(ref.fun @ ref.fun, rel=2e-7, abs=1e-7)
        if fixed is None:
            np.testing.assert_allclose(list(result["k"].values()), ref.x[:3], atol=1e-5)


def test_nonconvergence_and_bootstrap_covariance():
    bins, fwd = crab_fixture()
    args = (bins, fwd, lambda t: 0., np.full(3, 2 / calib.RAD2DPH))
    assert not fit.fit(*args, n_boot=0, max_nfev=1)["convergence"]["converged"]
    r = fit.fit(*args, n_boot=8, bootstrap_sampling="segment", block_length=3)
    covariance = np.array(r["bootstrap"]["empirical_k_cov"])
    assert np.linalg.eigvalsh(covariance).min() >= -1e-12
    order = fit.bootstrap_order(np.random.default_rng(3), bins, 3, "segment")
    np.testing.assert_array_equal(bins["seg"][order], bins["seg"])


def test_calibration_covariance_direct_and_gaussian(monkeypatch):
    rng = np.random.default_rng(6)
    positions = [0, 1, 2, 3, 3, 2, 1, 0]
    vis = [{"pos": calib.POSITIONS[p], "t": float(i * 300), "g": rng.normal(size=3) / calib.RAD2DPH,
            "g_sem": np.array([.1, .2, .4]) / calib.RAD2DPH, "up": np.array([0, 0, 1 if p < 2 else -1]), "mag": None}
           for i, p in enumerate(positions)]
    monkeypatch.setattr(calib, "_visits", lambda *a: vis)
    r = calib.calibrate(None, "cal_pre")
    # Coefficient order b, drift, w0, w1, w2; w3 = -w0-w1-w2.
    L = np.array([[0, 0, .5, -.5, 0], [0, 0, .5, .5, 1]])
    C = np.kron(L, np.diag([1, 1, 0]))
    cov = np.array(r["regression_cov_dph2"])
    expected = C @ cov @ C.T
    np.testing.assert_allclose(r["earth_h_vector_cov_dph2"], expected, atol=1e-12)
    draws = rng.multivariate_normal(np.zeros(len(cov)), cov, size=20000) @ C.T
    np.testing.assert_allclose(np.cov(draws.T), expected, atol=.02 * np.max(np.diag(expected)), rtol=.06)


def test_old_results_require_reprocessing():
    from test_policy import eligible
    from lll.collate import gate
    r, approval = eligible()
    r["analysis_version"] = "0.5.0"
    assert "reprocess with analysis 0.6.0" in gate(r, {}, approval=approval)


def test_pooling_independent_closed_form_fixtures():
    import json
    from pathlib import Path
    from lll.collate import random_effects
    fixtures = json.loads(Path(__file__).with_name("pooling_reference.json").read_text())
    for ref in fixtures["fixtures"]:
        actual = random_effects(ref["y"], ref["sd"])
        for field in ("mu", "tau2", "se"):
            assert actual[field] == pytest.approx(ref[field], abs=1e-10)


def test_null_denominators_keep_failures_and_gates_separate():
    from research import summarize, scenario_options
    base = {"truth": "flat_still", "scenario": "smooth"}
    rows = [{**base, "failure": "no fit"}, {**base, "rejected": True, "exclusions": ["prior"]},
            {**base, "rejected": False, "exclusions": []}]
    r = summarize(rows)[0]
    assert (r["attempted"], r["analysis_failures"], r["eligibility_exclusions"], r["accepted"]) == (3, 1, 1, 1)
    assert r["unconditional"]["rate"] == .5
    assert r["complete_gated_rule"]["n"] == 3
    assert r["conditional_on_acceptance"]["n"] == 1
    for rate in (-5, -2, -1, -.5, 0, .5, 1, 2, 5):
        trajectory = scenario_options(f"drift{rate:+g}")["crab_trajectory"]
        assert trajectory(np.array([3600]))[0] == rate


def test_dynamic_crab_includes_sensor_rotation(tmp_path):
    from lll.synth import synthesize
    from lll.format import read_session
    means = []
    for rate in (0, 360):
        path = tmp_path / f"crab-{rate}.zip"
        synthesize(path, "flat_still", fs=10, legs=((90, 12),), cal=(), gap_s=0,
                   gyro_range_dps=250, pitch_trim_deg_per_h=0, mount_tilt_deg=0,
                   crab_trajectory=lambda t: rate * t / 3600)
        s = read_session(path)
        from lll.policy import verified_config
        assert all(verified_config(d, s.manifest["imu"]) for _, kind, d in s.events if kind == "imu_config")
        assert any(kind == "imu_config" for _, kind, _ in s.events)
        gs = s.streams["gyro"]
        means.append(np.mean(gs["z"]))
    # Tray mount +z points up; heading rotation is about down. 360 deg/hour remains small per sample.
    assert (means[1] - means[0]) * calib.RAD2DPH == pytest.approx(-360, abs=2)


@pytest.mark.parametrize("variant", ["spp", "ble"])
def test_decoded_turn_dropout_is_unresolved(tmp_path, variant):
    from lll.synth import synthesize
    from lll.format import read_session
    path = tmp_path / "gap.zip"
    synthesize(path, "flat_still", fs=20, legs=((90, 12),), cal=(), gap_s=0, variant=variant,
               index_turns=((4, "z"),), link_dropouts=((4 + 1/60, 2),))
    s = read_session(path)
    g = s.streams["gyro"]
    events = [(t / 1e9, kind) for t, kind, _ in s.events if kind == "index_turn"]
    epochs, _ = mount_epochs(g["t_ns"] / 1e9, np.column_stack([g[x] for x in "xyz"]),
                             events, expected_period=.05)
    assert epochs[-1]["orientation_unresolved"]
    assert epochs[-1]["turn"]["unresolved_gap"]
