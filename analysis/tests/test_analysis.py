# SPDX-License-Identifier: AGPL-3.0-or-later
import json

import numpy as np
import pytest

from lll import models
from lll.analyze import analyze
from lll.calib import RAD2DPH
from lll.fit import TERM_NAMES
from lll.cli import analyze_to, collate_to
from lll.format import read_session
from lll.synth import synthesize
from conftest import geometric_truth

VECTORS = json.loads((__import__("pathlib").Path(__file__).parents[2] / "docs" / "test_vectors.json").read_text())


@pytest.mark.parametrize("v", VECTORS["transport"], ids=lambda v: v["name"])
def test_transport_vectors(v):
    got = models.transport_rate(np.radians(v["lat_deg"]), v["h_m"], v["v_n"], v["v_e"])
    np.testing.assert_allclose(got, v["omega_en"], rtol=1e-9, atol=1e-15)


@pytest.mark.parametrize("v", VECTORS["earth_rate"], ids=lambda v: v["name"])
def test_earth_rate_vectors(v):
    np.testing.assert_allclose(models.earth_rate_sphere(np.radians(v["lat_deg"])), v["sphere"], atol=1e-15)


def test_headline_numbers():
    # 224 m/s (~500 mph) due north at the equator → ~3.5e-5 rad/s ≈ 7.3 °/h
    w = models.transport_rate(0.0, 0.0, 224.0, 0.0)
    assert abs(w[1]) == pytest.approx(3.536e-5, rel=1e-3)
    assert abs(w[1]) * RAD2DPH == pytest.approx(7.29, rel=1e-2)
    assert models.OMEGA_E * RAD2DPH == pytest.approx(15.041, rel=1e-4)


def test_reads_kotlin_style_floats(tmp_path):
    # Kotlin's Float/Double.toString writes exponents like "1.0E-5"; multi-member gzip repeats the header
    import gzip
    import zipfile
    hdr = b"t_ns,utc_ms,lat,lon,alt_m,speed_mps,bearing_deg,h_acc_m,v_acc_m,speed_acc_mps,bearing_acc_deg,sats_used\n"
    with zipfile.ZipFile(tmp_path / "k.zip", "w") as zf:
        zf.writestr("manifest.json", json.dumps({"schema_version": 2, "phases": []}))
        zf.writestr("gnss.csv.gz", gzip.compress(hdr + b"1,2,40.5,-73.8,1.0E-5,230.0,90.0,5.0,8.0,0.3,0.5,12\n")
                    + gzip.compress(hdr + b"3,4,40.6,-73.7,-2.5E3,231.5,,5.0,8.0,0.3,0.5,11\n"))
    g = read_session(tmp_path / "k.zip").streams["gnss"]
    assert g["t_ns"].tolist() == [1, 3]
    assert g["alt_m"].tolist() == [1e-5, -2500.0]
    assert np.isnan(g["bearing_deg"][1])


NES_LEGS = ((10.0, 40.0), (100.0, 25.0), (190.0, 40.0))


@pytest.fixture(scope="module")
def synth_results(tmp_path_factory):
    d = tmp_path_factory.mktemp("synth")
    out = {}
    for truth in models.MODELS:
        p = d / f"{truth}.zip"
        # North, east, then south: horizontal transport (only the globe tilts local level) is
        # what separates a still globe from a still disc, whose vertical rates are similar.
        synthesize(p, truth, seed=11, fs=20.0, legs=NES_LEGS, omega_in_fn=geometric_truth(truth))
        out[truth] = analyze(p)
    return out


@pytest.mark.parametrize("truth", list(models.MODELS))
def test_recovers_true_model(synth_results, truth):
    r = synth_results[truth]
    f = r["fit"]
    assert f["mode"] == "3-axis"
    assert not f["rejected"][truth], f["p_vs_free"]          # the truth is never rejected
    for name, exp in zip(TERM_NAMES, models.EXPECTED_K[truth]):
        assert abs(f["k"][name] - exp) < 3.5 * f["k_sd"][name], (name, f["k"], f["k_sd"])
    # Earth rotation in globe form has a horizontal part, which heading changes separate from bias:
    # one flight settles "rotating globe or not".
    if truth == "sphere_rotating":
        assert all(f["rejected"][m] for m in models.MODELS if m != truth), f["p_vs_free"]
    # The corrected total-angle MAP objective changes fixed-model fits and bootstrap
    # calibration. Rejection power on still-world seeds is an empirical validation
    # question, not a correctness invariant. Require valid nested objectives instead;
    # test_release060 independently checks free/fixed MAP estimates and objectives.
    assert f["convergence"]["converged"]
    assert all(c >= f["chi2_free"] - 1e-6 for c in f["chi2"].values())


@pytest.mark.parametrize("truth", ["sphere_still", "flat_still"])
def test_turns_about_the_vertical_make_a_straight_flight_decisive(tmp_path, truth):
    """On a straight route, horizontal transport looks like bias. Turning the IMU 180° about the
    vertical (same side up) moves the signal to other axes while bias and g-sensitivity stay. A flip
    moves gravity to another axis, which brings its own g-sensitivity offset, so it doesn't help."""
    legs = ((50.0, 30.0), (90.0, 110.0))
    out = {}
    for name, turns in (("none", ()), ("vertical", ((50, "z"), (80, "z"), (110, "z"))), ("flip", ((50, "x"), (80, "x"), (110, "x")))):
        p = tmp_path / f"{name}.zip"
        synthesize(p, truth, seed=11, fs=20.0, legs=legs, index_turns=turns, omega_in_fn=geometric_truth(truth))
        out[name] = analyze(p)
    assert "k_not_identified" in out["none"]["flags"] and "k_not_identified" in out["flip"]["flags"]
    f = out["vertical"]["fit"]
    assert "imu_turned_in_flight" in out["vertical"]["flags"] and f["identifiability"]["identified"]
    assert [round(e["turn"]["angle_deg"]) for e in out["vertical"]["mount_epochs"] if e["turn"]] == [180, 180, 180]
    assert not f["rejected"][truth] and sum(f["rejected"].values()) == len(models.MODELS) - 1, f["p_vs_free"]
    assert f["k_sd"]["k_curv"] < 0.3 * out["none"]["fit"]["k_sd"]["k_curv"]


@pytest.mark.parametrize("truth", list(models.MODELS))
def test_ground_calibration_measures_earth_rate(synth_results, truth):
    from lll.calib import ground_model_predictions
    r = synth_results[truth]
    c = r["calibration"]["pre"]
    up_pred, h_pred = ground_model_predictions(c["lat_deg"])[truth]
    assert abs(c["earth_up_dph"] - up_pred) < 3.0
    # horizontal magnitude carries a positive noise bias of a few °/h
    assert -1.0 < c["earth_h_dph"] - h_pred < 5.0


@pytest.mark.parametrize("truth", ["sphere_rotating", "flat_still"])
def test_horizontal_ground_rate_is_immune_to_g_sensitivity(tmp_path, truth):
    """Gyro error that follows gravity (here up to 40 °/h per g, with cross-axis terms) corrupts the
    vertical ground rate, which no stationary test can avoid, but cancels within the 180° pairs."""
    from lll.calib import calibrate, ground_model_predictions
    from lll.format import read_session
    G = [[30, 10, -8], [5, -25, 12], [-6, 9, 40]]
    p = tmp_path / "g.zip"
    synthesize(p, truth, seed=4, fs=20.0, cal=("pre",), legs=((90.0, 12.0),), g_sens_dph_per_g=G)
    c = calibrate(read_session(p), "cal_pre")
    up_pred, h_pred = ground_model_predictions(40.5)[truth]
    assert c["sequence"] == "palindrome" and c["visits"] == 7
    assert abs(c["earth_h_dph"] - h_pred) < 3 * c["earth_h_sd_dph"] + 0.5, c
    assert abs(c["earth_up_dph"] - up_pred) > 20      # the vertical is aliased, and the result says so
    assert c["earth_up_aliased_with_g_sensitivity"]


def test_unit_quality_tier_uses_instrument_criteria_only(tmp_path):
    p = tmp_path / "q.zip"
    synthesize(p, "flat_still", seed=8, fs=20.0, legs=((10.0, 30.0), (190.0, 30.0)), drift_runs=True)
    q = analyze(p)["unit_quality"]
    assert q["unit_id"] == "synthetic-spp" and q["adev_300s_dph"] is not None
    assert q["tier"] in ("qualified", "usable")


def test_calibration_recovers_bias(synth_results):
    c = synth_results["sphere_rotating"]["calibration"]["pre"]
    np.testing.assert_allclose(c["bias_dph"], np.array([0.3, -0.2, 0.15]) * 3600, atol=3.0)


def test_window_mount_ble_variant_and_vertical_only_fallback(tmp_path):
    p = tmp_path / "w.zip"
    synthesize(p, "sphere_rotating", seed=5, fs=20.0, mount="window", variant="ble")
    r = analyze(p)
    assert r["fit"]["best_model"] == "sphere_rotating"
    assert r["imu"]["decode"]["variant"] == "ble" and "imu_link_gaps" not in r["flags"]
    # one long straight leg: no banked turns → no heading reference → vertical-only fit
    p2 = tmp_path / "straight.zip"
    # With no heading reference only the vertical channel is left, and on a straight leg a constant
    # vertical rate looks like bias: the fallback must say so and must not be confidently wrong.
    synthesize(p2, "flat_still", seed=6, fs=20.0, legs=((90.0, 60.0),))
    r = analyze(p2)
    assert "no_heading_reference_vertical_only" in r["flags"]
    assert r["fit"]["mode"] == "vertical_only"
    assert not r["fit"]["rejected"]["flat_still"] and "k_not_identified" in r["flags"]


def test_cli_analyze_and_collate(tmp_path):
    for i, truth in enumerate(("sphere_rotating", "sphere_rotating", "flat_still")):
        synthesize(tmp_path / f"s{i}.zip", truth, seed=20 + i, fs=20.0)
        html = analyze_to(tmp_path / f"s{i}.zip", tmp_path / "out")
        assert html.read_text().startswith("<!doctype html>")
    col_html = collate_to([tmp_path / "out"], tmp_path / "col")
    col = json.loads((tmp_path / "col" / "collated.json").read_text())
    assert col["n_sessions"] == 3 and col["n_primary"] == 0      # synthetic data never enters the primary result
    assert all("synthetic" in r["excluded_because"] for r in col["rows"])
    assert (tmp_path / "col" / "sessions.csv").read_text().count("\n") == 4
    assert "collated" in col_html.read_text()
    collate_to([tmp_path / "out"], tmp_path / "col2", allow_synthetic=True)
    col2 = json.loads((tmp_path / "col2" / "collated.json").read_text())
    assert col2["n_primary"] + col2["n_exploratory"] == 3


def _fake(unit, k, sd, flags=(), cruise=90.0, tier="usable"):
    from lll.fit import TERM_NAMES
    from lll import __version__
    return {"analysis_version": __version__, "input_sha256": __import__("uuid").uuid4().hex * 2, "flight_started_utc": "2026-03-01T00:00:00Z", "heading_diversity": {"adequate": True}, "session_id": f"{unit}-{k}", "flags": list(flags), "cruise_minutes": cruise,
            "imu": {"unit_id": unit, "variant": "spp", "config": {"rate_hz": 100, "gyro_range_dps": 2000, "accel_range_g": 16, "auto_zero": False}}, "unit_quality": {"unit_id": unit, "tier": tier},
            "fit": {"convergence": {"converged": True}, "k": dict(zip(TERM_NAMES, k)), "k_sd": dict(zip(TERM_NAMES, sd)),
                    "rejected": {m: False for m in models.MODELS}}}


def _approvals(results):
    from lll.policy import BENCH_CHECKS
    return {r["input_sha256"]: {"sha256": r["input_sha256"], "status": "approved", "unit_id": r["imu"]["unit_id"], "bench": {"unit_id": r["imu"]["unit_id"], "tier": "usable", "approved_at": "2026-02-01T00:00:00Z", "checks": dict.fromkeys(BENCH_CHECKS, True), "config": r["imu"]["config"]}} for r in results}


def test_collation_gates():
    from lll.collate import collate
    res = [_fake("u1", (1, 1, 0), (0.1, 0.2, 0.2)),
           _fake("u1", (1, 1, 0), (0.1, 0.2, 0.2), flags=("k_not_identified",)),
           _fake("u2", (1, 1, 0), (0.1, 0.2, 0.2), cruise=30.0),
           _fake("u3", (1, 1, 0), (0.1, 0.2, 0.2), tier="exploratory"),
           _fake("u1", (1, 1, 0), (0.1, 0.2, 0.2), flags=("no_cal_post",))]
    col = collate(res, provenance=_approvals(res))
    why = [r["excluded_because"] for r in col["rows"]]
    assert col["n_primary"] == 1 and why[0] == ""
    assert "curvature not identified" in why[1] and "under 60 min" in why[2]
    assert "tier exploratory" in why[3] and "missing a calibration" in why[4]


def test_hierarchical_pooling_covers_the_truth_when_units_differ():
    """Units with their own systematic offsets (beyond their stated errors) must widen the pooled
    interval. Fixed-effects pooling would claim far more precision than the data have."""
    from lll.collate import pool_hierarchical
    rng = np.random.default_rng(0)
    cover_re, cover_fe = 0, 0
    trials = 200
    for _ in range(trials):
        items = []
        for u in range(8):
            offset = rng.normal(0, 0.3)                        # unit-level systematic error
            for _ in range(4):
                k = 1 + offset + rng.normal(0, 0.1)
                items.append((f"u{u}", {"k_rot_sphere": k, "k_curv": k, "k_disc": k},
                              {"k_rot_sphere": 0.1, "k_curv": 0.1, "k_disc": 0.1}))
        p = pool_hierarchical(items)["k_curv"]
        cover_re += p["ci95"][0] <= 1 <= p["ci95"][1]
        ks = np.array([i[1]["k_curv"] for i in items])
        cover_fe += abs(ks.mean() - 1) < 2 * 0.1 / np.sqrt(len(ks))
    assert cover_re / trials > 0.88          # nominal 95 %; DL with 8 units runs a little under
    assert cover_fe / trials < 0.5


# ---- adversarial simulations ----
from lll.synth import ADVERSE  # noqa: E402


@pytest.fixture(scope="module")
def adverse_results(tmp_path_factory):
    d = tmp_path_factory.mktemp("adverse")
    out = {}
    for truth in models.MODELS:
        synthesize(d / f"{truth}.zip", truth, seed=7, fs=20.0, omega_in_fn=geometric_truth(truth), **ADVERSE)
        out[truth] = analyze(d / f"{truth}.zip")
    return out


@pytest.mark.parametrize("truth", list(models.MODELS))
def test_adverse_conditions_still_recover_truth(adverse_results, truth):
    r = adverse_results[truth]
    f = r["fit"]
    assert "temperature_term" in r["flags"]
    assert 50 < r["cruise_minutes"] < 100          # climb, descent, turbulence, gap all excluded
    assert f["best_model"] == truth, f["delta_chi2"]
    for name, exp in zip(TERM_NAMES, models.EXPECTED_K[truth]):
        assert abs(f["k"][name] - exp) < 3.5 * f["k_sd"][name], (name, f["k"], f["k_sd"])


def test_temperature_term_removes_bias(tmp_path):
    from lll.segments import Thresholds
    p = tmp_path / "t.zip"
    # Low sensor noise and a fine gyro range, so the temperature effect stands well above the
    # noise. At the default noise, σ(k_curv) ≈ 0.2 and a single seed can't show the effect.
    synthesize(p, "sphere_rotating", seed=7, fs=20.0, temp_coef_dph_per_c=(1.0, -0.8, 0.6), flight_temp_rise_c=8.0,
               gyro_range_dps=250.0, noise_dps_rthz=0.002, rw_dph_sqrth=0.05)
    f = analyze(p)["fit"]
    g = analyze(p, Thresholds(min_temp_delta_c=1e9))["fit"]
    np.testing.assert_allclose(f["temp_coef_dph_per_c"], (1.0, -0.8, 0.6), atol=0.2)   # coefficients recovered
    assert f["sigma_bin_dph"] < 0.8 * g["sigma_bin_dph"]        # the term removes structured residual
    assert abs(f["k"]["k_curv"] - 1) < 2.5 * f["k_sd"]["k_curv"]


def test_no_calibration_is_not_confidently_wrong(tmp_path):
    p = tmp_path / "nocal.zip"
    synthesize(p, "flat_still", seed=9, fs=20.0, cal=())
    r = analyze(p)
    assert {"no_cal_pre", "no_cal_post"} <= set(r["flags"])
    f = r["fit"]
    for name, exp in zip(TERM_NAMES, models.EXPECTED_K["flat_still"]):
        assert abs(f["k"][name] - exp) < 3.5 * f["k_sd"][name], (name, f["k"], f["k_sd"])


def test_slip_watchdog_catches_yaw_slip_and_spares_clean_flights(tmp_path):
    """Slow yaw slip of the IMU in its mount goes straight into the vertical gyro channel. The
    magnetometer watchdog measures it with and without the declination model; the WMM version
    decides, at 1.5 °/h. A clean flight keeps all its data even though the no-declination
    cross-check reads the route's declination change as slip."""
    out = {}
    for slip in (0.0, 2.0):
        p = tmp_path / f"s{slip}.zip"
        synthesize(p, "flat_still", seed=7, fs=20.0, mount_slip_deg_per_h=(slip, 0.0))
        out[slip] = analyze(p)
    clean, slipped = out[0.0], out[2.0]
    assert all(abs(r["slip_dph"]) < 1.0 for r in clean["slip"]["variants"]["wmm"])
    assert clean["slip"]["exclude_segments"] == [] and clean["slip"]["decided_by"] == "wmm"
    assert "mount_slip_detected" in slipped["flags"]
    assert all("wmm" in v for v in slipped["slip"]["triggered_by"].values())
    assert len(slipped["slip"]["exclude_segments"]) == len(slipped["slip"]["variants"]["wmm"])


HARDWARE_FAULTS = dict(
    temp_coef_dph_per_c=(1.0, -0.8, 0.6), flight_temp_rise_c=8.0, temp_quad_dph_per_c2=(0.08, -0.05, 0.06),
    temp_lag_s=600.0, bias_jumps=((70, (2.0, -1.0, 1.5)),), gyro_scale_ppm=(2000, -1500, 1000), gyro_misalign_mrad=2.0,
    vre_dph=(3.0, -2.0, 4.0), link_dropouts=((55, 20),), g_sens_dph_per_g=[[10, 3, -2], [2, -8, 4], [-3, 2, 12]])


@pytest.mark.parametrize("truth", list(models.MODELS))
def test_hardware_faults_never_make_it_confidently_wrong(tmp_path, truth):
    """Every fault at once: nonlinear temperature dependence with a lagging sensor, a bias jump,
    scale and misalignment errors, vibration rectification, a Bluetooth dropout, g-sensitivity.
    The true model must never be rejected, and every k stays within 3.5σ of its true value."""
    p = tmp_path / "hw.zip"
    synthesize(p, truth, seed=7, fs=20.0, legs=NES_LEGS, omega_in_fn=geometric_truth(truth), **HARDWARE_FAULTS)
    r = analyze(p)
    f = r["fit"]
    assert "imu_link_gaps" in r["flags"]
    assert not f["rejected"][truth], f["p_vs_free"]
    for name, exp in zip(TERM_NAMES, models.EXPECTED_K[truth]):
        assert abs(f["k"][name] - exp) < 3.5 * f["k_sd"][name], (name, f["k"], f["k_sd"])


def test_single_heading_airliner_needs_turns_of_the_imu(tmp_path):
    """A typical long-haul cruise: one course change onto the track (which gives the forward axis),
    then one heading for five hours. Without turning the IMU the curvature can't be told from bias
    and the analysis must say so. With a turn about the vertical every hour, the same flight
    separates the models."""
    legs = ((120.0, 20.0), (75.0, 300.0))
    out = {}
    for name, turns in (("none", ()), ("hourly", tuple((m, "z") for m in (60, 120, 180, 240)))):
        p = tmp_path / f"{name}.zip"
        synthesize(p, "sphere_still", seed=3, fs=10.0, legs=legs, index_turns=turns, omega_in_fn=geometric_truth("sphere_still"))
        out[name] = analyze(p)
    assert "k_not_identified" in out["none"]["flags"]
    assert not out["none"]["fit"]["rejected"]["sphere_still"]
    f = out["hourly"]["fit"]
    assert f["identifiability"]["identified"], f["identifiability"]
    assert not f["rejected"]["sphere_still"] and f["rejected"]["flat_still"] and f["rejected"]["sphere_rotating"], f["p_vs_free"]


def test_decoder_uses_the_range_the_imu_reported(tmp_path):
    """If the IMU ignored a range write, decoding at the intended full scale would rescale every rate
    by up to 8×. The app logs the device's own readback, and the analysis decodes with that."""
    import gzip
    import zipfile
    p = tmp_path / "r.zip"
    synthesize(p, "sphere_rotating", seed=2, fs=20.0, cal=("pre",), legs=((90.0, 12.0),), gyro_range_dps=500.0)
    truth_mean = read_session(p).streams["gyro"]["x"].mean()
    # same bytes, but the manifest claims ±2000 °/s while the device's readback says ±500 (code 1)
    q = tmp_path / "r2.zip"
    with zipfile.ZipFile(p) as src, zipfile.ZipFile(q, "w") as dst:
        for n in src.namelist():
            data = src.read(n)
            if n == "manifest.json":
                m = json.loads(data)
                m["imu"]["config"]["gyro_range_dps"] = 2000.0
                data = json.dumps(m).encode()
            if n == "events.csv.gz":
                data = data + gzip.compress(b"t_ns,kind,detail\n1,imu_config,0x03=0x9 0x63=0x1 0x20=0x1 ok=false\n")
            dst.writestr(n, data)
    s = read_session(q)
    assert s.imu_stats["gyro_range_used_dps"] == 500.0 and s.imu_stats["gyro_range_intended_dps"] == 2000.0
    assert s.streams["gyro"]["x"].mean() == pytest.approx(truth_mean)


def test_fast_turn_beyond_full_scale_is_flagged_and_not_used(tmp_path):
    """At ±250 °/s a half-second hand turn clips. Its integrated angle is wrong, so the IMU's
    orientation afterwards is unknown: the analysis flags it and leaves the later data out."""
    out = {}
    for name, secs in (("slow", 4.0), ("fast", 0.5)):
        p = tmp_path / f"{name}.zip"
        synthesize(p, "sphere_still", seed=11, fs=20.0, legs=((50.0, 30.0), (90.0, 60.0)), index_turns=((50, "z"),),
                   gyro_range_dps=250.0, turn_seconds=secs)
        out[name] = analyze(p)
    slow = [e["turn"] for e in out["slow"]["mount_epochs"] if e["turn"]][0]
    assert abs(slow["angle_deg"] - 180) < 0.5 and slow["saturated_samples"] == 0
    assert "imu_turn_saturated" in out["fast"]["flags"] and "excluded_after_saturated_turn_s" in out["fast"]
    assert "imu_turn_saturated" not in out["slow"]["flags"]



def test_decoder_uses_the_accel_range_the_imu_reported(tmp_path):
    import gzip
    import zipfile
    p = tmp_path / "a.zip"
    synthesize(p, "sphere_still", seed=2, fs=20.0, cal=("pre",), legs=((90.0, 12.0),), accel_range_g=4.0)
    ref = read_session(p).streams["accel"]["z"].mean()
    q = tmp_path / "a2.zip"
    with zipfile.ZipFile(p) as src, zipfile.ZipFile(q, "w") as dst:
        for n in src.namelist():
            data = src.read(n)
            if n == "manifest.json":
                m = json.loads(data)
                m["imu"]["config"]["accel_range_g"] = 16.0
                data = json.dumps(m).encode()
            if n == "events.csv.gz":
                data = data + gzip.compress(b"t_ns,kind,detail\n1,imu_config,0x21=0x1 ok=false\n")
            dst.writestr(n, data)
    s = read_session(q)
    assert s.imu_stats["accel_range_used_g"] == 4.0
    assert s.streams["accel"]["z"].mean() == pytest.approx(ref)


def test_crab_angle_no_longer_rejects_the_true_globe(tmp_path):
    """In a crosswind the fuselage points off the GNSS track. Using the course as the heading
    rotates the globe's horizontal predictions; on a precise flight an 8° crab then rejected the true
    rotating globe. A heading offset per course leg, with a 5° prior, keeps it."""
    from lll.segments import Thresholds  # noqa: F401
    import lll.fit as F
    p = tmp_path / "crab.zip"
    synthesize(p, "sphere_rotating", seed=11, fs=20.0, legs=((50.0, 30.0), (90.0, 110.0)),
               index_turns=((50, "z"), (80, "z"), (110, "z")), crab_deg=(8.0, 8.0), omega_in_fn=geometric_truth("sphere_rotating"))
    f = analyze(p)["fit"]
    assert not f["rejected"]["sphere_rotating"], f["p_vs_free"]
    assert f["crab"]["per_segment_deg"] is not None
    for name, exp in zip(TERM_NAMES, models.EXPECTED_K["sphere_rotating"]):
        assert abs(f["k"][name] - exp) < 3.0 * f["k_sd"][name], (name, f["k"], f["k_sd"])
    # without the crab term the same data rejects the truth
    orig = F.fit
    try:
        F.fit = lambda *a, **k: orig(*a, **{**k, "crab_sigma_deg": 0.0})
        import lll.analyze as A
        A.fit.fit = F.fit
        g = analyze(p)["fit"]
    finally:
        F.fit = orig
        A.fit.fit = orig
    assert g["rejected"]["sphere_rotating"]



@pytest.mark.parametrize("truth", ["sphere_rotating", "flat_still"])
def test_reversal_test_measures_horizontal_rate_and_its_repeatability(tmp_path, truth):
    """Six same-face 0°/180° reversals, with g-sensitivity present. Each pair gives the horizontal
    ground rate; the scatter between pairs is the unit's repeatability for this experiment."""
    from lll.calib import ground_model_predictions
    p = tmp_path / "rev.zip"
    synthesize(p, truth, seed=5, fs=20.0, cal=("pre",), legs=((90.0, 12.0),), reversal_pairs=6,
               g_sens_dph_per_g=[[30, 10, -8], [5, -25, 12], [-6, 9, 40]], omega_in_fn=geometric_truth(truth))
    r = analyze(p)
    rv = r["reversal"]
    _, h_pred = ground_model_predictions(40.5)[truth]
    assert rv["pairs"] == 6
    assert abs(rv["h_mean_dph"] - h_pred) < 3 * rv["h_sem_dph"] + 1.5    # noise biases a norm upward
    assert r["unit_quality"]["horizontal_repeatability_from"] == "reversal test"


# ---- third review ----

def test_pooled_model_test_uses_the_joint_covariance():
    """k_rot and k_curv trade against each other on the same flight. Summing per-term z² as if they
    were independent gives the wrong χ²; the test must use dᵀ V⁻¹ d."""
    from lll.collate import collate
    sd = np.array([0.1, 0.1, 0.2])
    rho = 0.9
    cov = np.diag(sd ** 2)
    cov[0, 1] = cov[1, 0] = rho * sd[0] * sd[1]
    k = (1.15, 0.85, 0.0)                       # opposite shifts: unlikely under positive correlation
    r = _fake("u1", k, tuple(sd))
    r["fit"]["k_cov"] = cov.tolist()
    col = collate([r], provenance=_approvals([r]))
    t = col["model_tests"]["sphere_rotating"]
    d = np.array(k) - np.array(models.EXPECTED_K["sphere_rotating"])
    assert t["chi2"] == pytest.approx(float(d @ np.linalg.inv(cov) @ d), rel=1e-6)
    assert t["chi2"] > 2 * float(np.sum((d / sd) ** 2))   # far beyond the independent sum


def test_temperature_coefficient_is_not_confused_with_drift():
    from lll.drift import temp_regression
    t = np.arange(0, 4 * 3600, 60.0)
    drift = 2.0 / RAD2DPH * t / 3600.0                 # 2 °/h per hour of plain drift
    means = np.column_stack([drift] * 3)
    warm = 20 + 8 * t / t[-1]                          # monotonic warm-up: T follows t
    r = temp_regression(t, warm, means)
    assert r["bias_temp_confounded"]
    cycled = 25 + 4 * np.sin(2 * np.pi * t / 3600.0)   # warm and cool several times
    beta = 0.5 / RAD2DPH
    r = temp_regression(t, cycled, means + beta * (cycled - 25)[:, None])
    assert not r["bias_temp_confounded"]
    assert np.allclose(r["bias_temp_coef_dph_per_c"], 0.5, atol=1e-6)
    assert np.allclose(r["bias_drift_dph_per_h"], 2.0, atol=1e-6)


def test_missing_gnss_bearing_never_becomes_north():
    from lll.segments import gnss_kinematics
    n = 600
    t = np.arange(n, dtype=float)
    lon = -100 + 250.0 * t / (111320 * np.cos(np.radians(40)))   # due east at 250 m/s
    brg = np.full(n, 90.0)
    brg[200:220] = np.nan                              # receiver lost the course
    acc = np.full(n, 0.5)
    acc[400:420] = 20.0                                # receiver says its course is poor
    gn = {"t_ns": (t * 1e9).astype(np.int64), "lat": np.full(n, 40.0), "lon": lon, "alt_m": np.full(n, 11000.0),
          "speed_mps": np.full(n, 250.0), "bearing_deg": brg, "bearing_acc_deg": acc, "h_acc_m": np.full(n, 5.0)}
    k = gnss_kinematics(gn)
    assert not k["bearing_ok"][200:220].any() and not k["bearing_ok"][400:420].any()
    assert k["bearing_ok"][50:150].all()
    assert np.allclose(np.degrees(k["psi"][200:220]), 90.0)    # interpolated, not 0
    gn["bearing_deg"] = np.where(np.arange(n) >= 300, 0.0, 90.0)  # bearing disagrees with the track
    assert not gnss_kinematics(gn)["bearing_ok"][320:].any()


def test_unit_tier_is_taken_as_of_the_session():
    """A unit qualified later must not promote a flight recorded before it was qualified."""
    from lll.collate import collate
    flight = _fake("u1", (1, 1, 0), (0.1, 0.2, 0.2), tier="unknown")
    flight["created_utc"] = "2026-01-01T00:00:00Z"
    bench = {"session_id": "bench", "flags": [], "created_utc": "2026-02-01T00:00:00Z",
             "imu": {"unit_id": "u1"}, "unit_quality": {"unit_id": "u1", "tier": "qualified"}}
    later = _fake("u1", (1, 1, 0), (0.1, 0.2, 0.2), tier="unknown")
    later["created_utc"] = "2026-03-01T00:00:00Z"
    later["session_id"] = "later"
    col = collate([flight, bench, later])
    rows = {r["session_id"]: r for r in col["rows"]}
    assert "tier unknown" in rows[flight["session_id"]]["excluded_because"]
    assert rows["later"]["unit_tier"] == "qualified"
    assert "unverified provenance" in rows["later"]["excluded_because"]


def test_ground_rate_interval_is_honest_near_zero():
    from lll.calib import rice_interval
    rng = np.random.default_rng(3)
    ps, lows = [], []
    for _ in range(300):
        v = rng.normal(0, 1.0, (2, 2))                  # two faces, zero true rate, σ = 1
        r = rice_interval(np.linalg.norm(v, axis=1), [1.0, 1.0])
        ps.append(r["p_zero"])
        lows.append(r["ci95"][0])
    assert 0.02 < np.mean(np.array(ps) < 0.05) < 0.09   # p of zero rate is calibrated
    assert np.mean(np.array(lows) == 0.0) > 0.9         # the interval reaches zero
    r = rice_interval([10.3, 9.8], [1.0, 1.0])
    assert r["ci95"][0] < 10 < r["ci95"][1] and r["p_zero"] < 1e-10
