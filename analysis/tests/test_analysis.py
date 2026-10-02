# SPDX-License-Identifier: AGPL-3.0-or-later
import json

import numpy as np
import pytest

from lll import models
from lll.analyze import analyze
from lll.calib import RAD2DPH
from lll.cli import analyze_to, collate_to
from lll.format import read_session, write_session
from lll.synth import synthesize

VECTORS = json.loads((__import__("pathlib").Path(__file__).parents[2] / "docs" / "test_vectors.json").read_text())


@pytest.mark.parametrize("v", VECTORS["transport"], ids=lambda v: v["name"])
def test_transport_vectors(v):
    got = models.transport_rate(np.radians(v["lat_deg"]), v["h_m"], v["v_n"], v["v_e"])
    np.testing.assert_allclose(got, v["omega_en"], rtol=1e-9, atol=1e-15)


@pytest.mark.parametrize("v", VECTORS["earth_rate"], ids=lambda v: v["name"])
def test_earth_rate_vectors(v):
    np.testing.assert_allclose(models.earth_rate_sphere(np.radians(v["lat_deg"])), v["sphere"], atol=1e-15)
    np.testing.assert_allclose(models.earth_rate_flat(np.radians(v["lat_deg"])), v["flat"], atol=1e-15)


def test_headline_numbers():
    # 224 m/s (~500 mph) due north at the equator → ~3.5e-5 rad/s ≈ 7.3 °/h
    w = models.transport_rate(0.0, 0.0, 224.0, 0.0)
    assert abs(w[1]) == pytest.approx(3.536e-5, rel=1e-3)
    assert abs(w[1]) * RAD2DPH == pytest.approx(7.29, rel=1e-2)
    assert models.OMEGA_E * RAD2DPH == pytest.approx(15.041, rel=1e-4)


def test_float32_round_trip_is_bit_exact(tmp_path):
    rng = np.random.default_rng(3)
    vals = (rng.normal(0, 1, (500, 3)) * 10.0 ** rng.integers(-8, 3, (500, 3))).astype(np.float32)
    t = np.arange(500, dtype=np.int64) * 10_000_000 + 123_456_789_012_345
    z = np.zeros(500, np.float32)
    write_session(tmp_path / "s.zip", {"schema_version": 1, "phases": []},
                  {"gyro_uncal": {"t_ns": t, "x": vals[:, 0], "y": vals[:, 1], "z": vals[:, 2], "bx": z, "by": z, "bz": z}})
    s = read_session(tmp_path / "s.zip").streams
    g = s["gyro_uncal"]
    assert np.array_equal(g["t_ns"], t)
    for i, c in enumerate("xyz"):
        assert np.array_equal(g[c].astype(np.float32).view(np.uint32), vals[:, i].view(np.uint32))


def test_reads_kotlin_style_floats(tmp_path):
    # Kotlin's Float.toString writes exponents like "1.0E-5"
    import gzip
    import zipfile
    with zipfile.ZipFile(tmp_path / "k.zip", "w") as zf:
        zf.writestr("manifest.json", json.dumps({"schema_version": 1, "phases": []}))
        zf.writestr("pressure.csv.gz", gzip.compress(b"t_ns,hpa\n1,1.0E-5\n2,1013.25\n") +
                    gzip.compress(b"t_ns,hpa\n3,-2.5E3\n"))
    p = read_session(tmp_path / "k.zip").streams["pressure"]
    assert p["t_ns"].tolist() == [1, 2, 3]
    assert p["hpa"].astype(np.float32).tolist() == [np.float32(1e-5), np.float32(1013.25), np.float32(-2500)]


@pytest.fixture(scope="module")
def synth_results(tmp_path_factory):
    d = tmp_path_factory.mktemp("synth")
    out = {}
    for truth in models.MODELS:
        p = d / f"{truth}.zip"
        synthesize(p, truth, seed=11, fs=20.0)
        out[truth] = analyze(p)
    return out


@pytest.mark.parametrize("truth", list(models.MODELS))
def test_recovers_true_model(synth_results, truth):
    r = synth_results[truth]
    f = r["fit"]
    assert f["mode"] == "3-axis"
    assert f["best_model"] == truth
    assert f["delta_chi2"][truth] == 0
    others = sorted(v for m, v in f["delta_chi2"].items() if m != truth)
    assert others[0] > 9, f["delta_chi2"]   # every wrong model is worse by at least 3σ
    for name, exp in zip(("k_rot_sphere", "k_rot_flat", "k_curv"), models.EXPECTED_K[truth]):
        assert abs(f["k"][name] - exp) < 3.5 * f["k_sd"][name], (name, f["k"], f["k_sd"])


@pytest.mark.parametrize("truth", list(models.MODELS))
def test_ground_calibration_measures_earth_rate(synth_results, truth):
    from lll.calib import ground_model_predictions
    r = synth_results[truth]
    c = r["calibration"]["pre"]
    up_pred, h_pred = ground_model_predictions(c["lat_deg"])[truth]
    assert abs(c["earth_up_dph"] - up_pred) < 3.0
    # horizontal magnitude carries a positive noise bias of a few °/h
    assert -1.0 < c["earth_h_dph"] - h_pred < 5.0


def test_calibration_recovers_bias(synth_results):
    c = synth_results["sphere_rotating"]["calibration"]["pre"]
    np.testing.assert_allclose(c["bias_dph"], np.array([0.3, -0.2, 0.15]) * 3600, atol=3.0)


def test_window_mount_and_vertical_only_fallback(tmp_path):
    p = tmp_path / "w.zip"
    synthesize(p, "sphere_rotating", seed=5, fs=20.0, mount="window")
    assert analyze(p)["fit"]["best_model"] == "sphere_rotating"
    # one long straight leg: no banked turns → no heading reference → vertical-only fit
    p2 = tmp_path / "straight.zip"
    synthesize(p2, "flat_rotating", seed=6, fs=20.0, legs=((280.0, 60.0),))  # westbound: vertical channels differ by ~11 deg/h
    r = analyze(p2)
    assert "no_heading_reference_vertical_only" in r["flags"]
    assert r["fit"]["mode"] == "vertical_only"
    assert r["fit"]["best_model"] == "flat_rotating"


def test_cli_analyze_and_collate(tmp_path):
    for i, truth in enumerate(("sphere_rotating", "sphere_rotating", "flat_still")):
        synthesize(tmp_path / f"s{i}.zip", truth, seed=20 + i, fs=20.0)
        html = analyze_to(tmp_path / f"s{i}.zip", tmp_path / "out")
        assert html.read_text().startswith("<!doctype html>")
    col_html = collate_to([tmp_path / "out"], tmp_path / "col")
    col = json.loads((tmp_path / "col" / "collated.json").read_text())
    assert col["n_with_fit"] == 3 and col["n_cal"] == 6
    assert col["best_counts"] == {"sphere_rotating": 2, "flat_still": 1}
    assert (tmp_path / "col" / "sessions.csv").read_text().count("\n") == 4
    assert "collated" in col_html.read_text()
