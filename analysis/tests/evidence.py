# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regenerate every simulation number quoted in docs/METHODOLOGY.md.

    python analysis/tests/evidence.py > evidence.md

Each section re-runs the synthetic scenarios behind one claim and prints a markdown table. Gyro
truth comes from the independent geometric generator (truthgen.py), never from lll.models. Seeds
are fixed, so the output is reproducible. It takes a few minutes.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

import truthgen  # noqa: E402
from conftest import geometric_truth  # noqa: E402
from lll import models  # noqa: E402
from lll.analyze import analyze  # noqa: E402
from lll.calib import calibrate, ground_model_predictions  # noqa: E402
from lll.collate import pool_hierarchical  # noqa: E402
from lll.fit import TERM_NAMES  # noqa: E402
from lll.format import read_session  # noqa: E402
from lll.synth import ADVERSE, synthesize  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="lll-evidence-"))
NES = ((10.0, 40.0), (100.0, 25.0), (190.0, 40.0))
ZIGZAG = ((60.0, 25.0), (100.0, 25.0), (20.0, 25.0))
STRAIGHT = ((50.0, 30.0), (90.0, 110.0))


def run(truth, **kw):
    p = TMP / "s.zip"
    synthesize(p, truth, omega_in_fn=geometric_truth(truth), **kw)
    return analyze(p)


def table(head, rows):
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for r in rows:
        print("| " + " | ".join(str(c) for c in r) + " |")
    print()


def f(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def models_vs_geometry():
    print("## 1. lll.models against independent geometry\n")
    worst = 0.0
    for world in models.MODELS:
        for lat0, lon0, vn, ve in [(40, -73.8, 0, 230), (40, -73.8, 230, 0), (-33.9, 151.2, -120, 200), (65, 10, 160, -160), (0.5, 30, 0, 250)]:
            def traj(t, lat0=lat0, lon0=lon0, vn=vn, ve=ve):
                t = np.asarray(t, float)
                return np.radians(lat0) + vn * t / 6.37e6, np.radians(lon0) + ve * t / 4.8e6, np.full_like(t, 11000.0)
            t = np.array([0.0, 600.0])
            w, _ = truthgen.truth(world, traj, t)
            _, v = truthgen.truth("sphere_still", traj, t)
            lat, lon, h = traj(t)
            worst = max(worst, float(np.max(np.abs(models.predict(world, lat, h, v[:, 0], v[:, 1]) - w))))
    print(f"Largest difference over 5 states × 3 models: {worst:.1e} rad/s ({worst * 206264.8 * 3600 / 3600:.1e} °/h).\n")


def routes():
    print("## 2. What a single flight can identify (truth: still globe)\n")
    rows = []
    for name, kw in [("north, east, south", dict(legs=NES)), ("zigzag 60°/100°/20°", dict(legs=ZIGZAG)),
                     ("straight, no IMU turns", dict(legs=STRAIGHT)),
                     ("straight, IMU turned about the vertical ×3", dict(legs=STRAIGHT, index_turns=((50, "z"), (80, "z"), (110, "z")))),
                     ("straight, IMU flipped ×3", dict(legs=STRAIGHT, index_turns=((50, "x"), (80, "x"), (110, "x"))))]:
        r = run("sphere_still", seed=11, fs=20.0, **kw)
        fi = r["fit"]
        like = fi["identifiability"]["bias_likeness_by_term"]
        rows.append([name, f(like["k_curv"]), f(like["k_disc"]), f"{f(fi['k']['k_curv'])} ± {f(fi['k_sd']['k_curv'])}",
                     f"{sum(v for m, v in fi['rejected'].items() if m != 'sphere_still')} of {len(models.MODELS) - 1}",
                     "yes" if "k_not_identified" in r["flags"] else "no"])
    table(["route", "bias-likeness k_curv", "bias-likeness k_disc", "k_curv", "wrong models rejected", "flagged not identified"], rows)


def ground_calibration():
    print("## 3. Ground calibration: horizontal rate against g-sensitivity\n")
    G = [[30, 10, -8], [5, -25, 12], [-6, 9, 40]]
    rows = []
    for truth in ("sphere_rotating", "flat_still"):
        for seq in ("single", "palindrome"):
            for gs in (None, G):
                p = TMP / "c.zip"
                synthesize(p, truth, seed=4, fs=20.0, cal=("pre",), legs=((90.0, 12.0),), cal_sequence=seq,
                           g_sens_dph_per_g=gs, omega_in_fn=geometric_truth(truth))
                c = calibrate(read_session(p), "cal_pre")
                up, h = ground_model_predictions(40.5)[truth]
                rows.append([truth, seq, "yes" if gs else "no", f"{f(c['earth_h_dph'])} ± {f(c['earth_h_sd_dph'])}", f(h),
                             f(c["earth_up_dph"]), f(up)])
    table(["truth", "sequence", "g-sensitivity up to 40 °/h/g", "horizontal measured (°/h)", "predicted", "vertical measured", "predicted"], rows)


def quantization():
    print("## 4. 16-bit quantization of the gyro\n")
    rows = []
    for rng in (2000.0, 500.0, 250.0):
        for gs in (None, [[30, 10, -8], [5, -25, 12], [-6, 9, 40]]):
            p = TMP / "q.zip"
            synthesize(p, "flat_still", seed=4, fs=20.0, cal=("pre",), legs=((90.0, 12.0),), gyro_range_dps=rng,
                       g_sens_dph_per_g=gs, omega_in_fn=geometric_truth("flat_still"))
            c = calibrate(read_session(p), "cal_pre")
            rows.append([f"±{rng:.0f} °/s", f"{rng / 32768 * 3600:.0f}", "yes" if gs else "no",
                         ", ".join(f(x, 1) for x in c["drift_dph_per_h"])])
    table(["gyro range", "one count (°/h)", "g-sensitivity", "fitted drift x, y, z (°/h per h)"], rows)
    print("By design, drift and position effects are separated, so g-sensitivity alone can't move the fitted drift. "
          "What moves it here is quantization: coarse counts interact with constant offsets. Compare the z column "
          "with and without g-sensitivity at each range.\n")


def temperature():
    print("## 5. Temperature\n")
    from lll.segments import Thresholds
    p = TMP / "t.zip"
    synthesize(p, "sphere_rotating", seed=7, fs=20.0, temp_coef_dph_per_c=(1.0, -0.8, 0.6), flight_temp_rise_c=8.0,
               gyro_range_dps=250.0, noise_dps_rthz=0.002, rw_dph_sqrth=0.05, omega_in_fn=geometric_truth("sphere_rotating"))
    a, b = analyze(p)["fit"], analyze(p, Thresholds(min_temp_delta_c=1e9))["fit"]
    table(["", "with term", "without"], [
        ["coefficient (°/h/°C), injected 1.0, −0.8, 0.6", ", ".join(f(x) for x in a["temp_coef_dph_per_c"]), "–"],
        ["noise per 60-s bin (°/h)", f(a["sigma_bin_dph"]), f(b["sigma_bin_dph"])],
        ["k_curv", f"{f(a['k']['k_curv'])} ± {f(a['k_sd']['k_curv'])}", f"{f(b['k']['k_curv'])} ± {f(b['k_sd']['k_curv'])}"]])


def slip():
    print("## 6. Mount slip watchdog\n")
    rows = []
    for s in (0.0, 2.0, 3.0, 8.0):
        r = run("flat_still", seed=7, fs=20.0, mount_slip_deg_per_h=(s, 0.0))
        sl = r["slip"]
        rows.append([f(s, 1), ", ".join(f(x["slip_dph"], 1) for x in sl["variants"]["wmm"]),
                     ", ".join(f(x["slip_dph"], 1) for x in sl["variants"]["no_declination"]),
                     str(sl["exclude_segments"] or "none")])
    table(["true slip (°/h)", "measured, WMM declination (per segment)", "measured, no declination model (cross-check)", "segments left out"], rows)
    print("The WMM version decides, at 1.5 °/h. The cross-check reads the route's declination change as slip.\n")


def faults():
    print("## 7. Hard conditions: the true model is never rejected\n")
    from test_analysis import HARDWARE_FAULTS
    rows = []
    for label, kw in (("adverse flight (temperature, turbulence, tilt slip, climb/descent, GNSS gaps)", ADVERSE),
                      ("hardware faults (all at once)", dict(legs=NES, **HARDWARE_FAULTS))):
        for truth in models.MODELS:
            fi = run(truth, seed=7, fs=20.0, **kw)["fit"]
            worst = max(abs(fi["k"][n] - e) / fi["k_sd"][n] for n, e in zip(TERM_NAMES, models.EXPECTED_K[truth]))
            rows.append([label, truth, "no" if not fi["rejected"][truth] else "YES",
                         ", ".join(m for m, v in fi["rejected"].items() if v) or "none", f(worst, 1)])
    table(["condition", "truth", "truth rejected?", "models rejected", "largest |k − true| / σ"], rows)


def airliner():
    print("## 8. Five-hour single-heading cruise\n")
    rows = []
    for name, turns in (("no IMU turns", ()), ("IMU turned about the vertical hourly", tuple((m, "z") for m in (60, 120, 180, 240)))):
        r = run("sphere_still", seed=3, fs=10.0, legs=((120.0, 20.0), (75.0, 300.0)), index_turns=turns)
        fi = r["fit"]
        rows.append([name, f(fi["identifiability"]["bias_likeness_by_term"]["k_curv"]),
                     f"{f(fi['k']['k_curv'])} ± {f(fi['k_sd']['k_curv'])}", ", ".join(m for m, v in fi["rejected"].items() if v) or "none"])
    table(["", "bias-likeness k_curv", "k_curv (truth 1)", "models rejected (truth: still globe)"], rows)


def pooling():
    print("## 9. Pooling when units differ\n")
    rng = np.random.default_rng(0)
    re_cov = fe_cov = 0
    trials = 400
    for _ in range(trials):
        items = []
        for u in range(8):
            off = rng.normal(0, 0.3)
            for _ in range(4):
                k = 1 + off + rng.normal(0, 0.1)
                items.append((f"u{u}", {n: k for n in TERM_NAMES}, {n: 0.1 for n in TERM_NAMES}))
        p = pool_hierarchical(items)["k_curv"]
        re_cov += abs(p["k"] - 1) < 2 * p["sd"]
        ks = np.array([i[1]["k_curv"] for i in items])
        fe_cov += abs(ks.mean() - 1) < 2 * 0.1 / np.sqrt(len(ks))
    table(["method", "95 % interval covers the truth"], [["random effects (REML, Hartung–Knapp), sessions → units → population", f"{100 * re_cov / trials:.0f} %"],
                                                        ["fixed effects (all sessions as independent)", f"{100 * fe_cov / trials:.0f} %"]])
    print("8 units × 4 sessions, unit offsets σ = 0.3, session errors σ = 0.1.\n")


def turns():
    print("## 10. IMU turns measured by the gyro\n")
    r = run("sphere_still", seed=11, fs=20.0, legs=STRAIGHT, index_turns=((50, "z"), (80, "z"), (110, "z")))
    print("Measured turn angles (true 180°): " + ", ".join(f"{e['turn']['angle_deg']:.2f}°" for e in r["mount_epochs"] if e["turn"]) + "\n")


def crab():
    print("## 11. Crab angle (fuselage off the GNSS track)\n")
    import lll.analyze as A
    import lll.fit as F
    orig = F.fit
    rows = []
    for truth in ("sphere_rotating", "sphere_still"):
        for label, crab_deg, sig in (("none", (), 5.0), ("8°, no crab term", (8.0, 8.0), 0.0), ("8°, crab term (5° prior)", (8.0, 8.0), 5.0)):
            try:
                F.fit = lambda *a, sig=sig, **k: orig(*a, **{**k, "crab_sigma_deg": sig})
                A.fit.fit = F.fit
                fi = run(truth, seed=11, fs=20.0, legs=STRAIGHT, index_turns=((50, "z"), (80, "z"), (110, "z")), crab_deg=crab_deg)["fit"]
            finally:
                F.fit = orig
                A.fit.fit = orig
            rows.append([truth, label, "YES" if fi["rejected"][truth] else "no",
                         f"{f(fi['k']['k_rot_sphere'])} ± {f(fi['k_sd']['k_rot_sphere'])}", f"{f(fi['k']['k_curv'])} ± {f(fi['k_sd']['k_curv'])}"])
    table(["truth", "crab", "truth rejected?", "k_rot", "k_curv"], rows)
    print("Straight route with three same-side-up IMU turns. A flat truth has no horizontal signal, so crab doesn't affect it.\n")


def ble_timing():
    print("## 12. BLE timing under lost notifications\n")
    from lll import witmotion as w
    rows = []
    for loss in (0.0, 0.001, 0.01, 0.03):
        rng = np.random.default_rng(4)
        rate, n = 100.0, 100 * 1800
        true_s = np.arange(n) / rate
        kept = rng.random(n) >= loss
        ts = true_s[kept]
        arr = np.round(np.maximum.accumulate(np.ceil(ts / 7.5e-3) * 7.5e-3 + rng.exponential(0.002, len(ts)) + 0.003) * 1e9).astype(np.int64)
        idx, nl = w.recover_lost_samples(arr, rate)
        t, _ = w.clock_map(idx / rate, arr, period_s=1 / rate)
        e = t / 1e9 - ts
        rows.append([f"{100 * loss:.1f} %", int(n - kept.sum()), nl, f"{1e3 * np.percentile(np.abs(e - np.median(e)), 95):.1f}"])
    table(["notification loss", "samples lost", "detected", "timing error, 95th percentile (ms)"], rows)
    print("30 min at 100 Hz, 7.5-ms connection interval.\n")


def reversal():
    print("## 13. Reversal test with strong g-sensitivity\n")
    rows = []
    for truth in ("sphere_rotating", "flat_still"):
        r = run(truth, seed=5, fs=20.0, cal=("pre",), legs=((90.0, 12.0),), reversal_pairs=6,
                g_sens_dph_per_g=[[30, 10, -8], [5, -25, 12], [-6, 9, 40]])
        rv = r["reversal"]
        rows.append([truth, rv["pairs"], f"{f(rv['h_mean_dph'])} ± {f(rv['h_sem_dph'])}", f(ground_model_predictions(40.5)[truth][1]),
                     f(rv["h_sd_dph"])])
    table(["truth", "pairs", "horizontal rate (°/h)", "predicted", "repeatability σ (°/h)"], rows)


if __name__ == "__main__":
    print("# Evidence for docs/METHODOLOGY.md\n\nRegenerate with `python analysis/tests/evidence.py`.\n")
    for fn in (models_vs_geometry, routes, ground_calibration, quantization, temperature, slip, faults, airliner, pooling, turns,
               crab, ble_timing, reversal):
        fn()
