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
    else:
        assert f["rejected"]["sphere_rotating"], f["p_vs_free"]


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
    assert q["unit_id"] == "synthetic-spp" and q["bias_instability_dph"] is not None
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
    return {"session_id": f"{unit}-{k}", "flags": list(flags), "cruise_minutes": cruise,
            "imu": {"unit_id": unit, "variant": "spp"}, "unit_quality": {"unit_id": unit, "tier": tier},
            "fit": {"k": dict(zip(TERM_NAMES, k)), "k_sd": dict(zip(TERM_NAMES, sd)),
                    "rejected": {m: False for m in models.MODELS}}}


def test_collation_gates():
    from lll.collate import collate
    res = [_fake("u1", (1, 1, 0), (0.1, 0.2, 0.2)),
           _fake("u1", (1, 1, 0), (0.1, 0.2, 0.2), flags=("k_not_identified",)),
           _fake("u2", (1, 1, 0), (0.1, 0.2, 0.2), cruise=30.0),
           _fake("u3", (1, 1, 0), (0.1, 0.2, 0.2), tier="exploratory"),
           _fake("u1", (1, 1, 0), (0.1, 0.2, 0.2), flags=("no_cal_post",))]
    col = collate(res)
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
        cover_re += abs(p["k"] - 1) < 2 * p["sd"]
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
    magnetometer watchdog measures it, with and without the declination model, and segments where
    both agree on slip above 2 °/h are left out of the gyro fit."""
    out = {}
    for slip in (0.0, 8.0):
        p = tmp_path / f"s{slip}.zip"
        synthesize(p, "flat_still", seed=7, fs=20.0, mount_slip_deg_per_h=(slip, 0.0))
        out[slip] = analyze(p)
    clean, slipped = out[0.0], out[8.0]
    assert clean["slip"]["exclude_segments"] == [] and "mount_slip_detected" not in clean["flags"]
    assert all(abs(r["slip_dph"]) < 1.0 for r in clean["slip"]["variants"]["wmm"])
    assert "mount_slip_detected" in slipped["flags"]
    assert all(abs(r["slip_dph"] - 8.0) < 1.0 for r in slipped["slip"]["variants"]["wmm"])


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
