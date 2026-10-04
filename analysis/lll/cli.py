# SPDX-License-Identifier: AGPL-3.0-or-later
"""lll: analyze one session, collate many, or synthesize test sessions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def analyze_to(zip_path, out_dir=None) -> Path:
    from .analyze import analyze
    from .report import session_report
    zip_path = Path(zip_path)
    out = Path(out_dir) if out_dir else zip_path.parent
    out.mkdir(parents=True, exist_ok=True)
    res = analyze(zip_path)
    stem = zip_path.name.removesuffix(".zip")
    (out / f"{stem}.result.json").write_text(json.dumps(res, indent=1))
    html_path = out / f"{stem}.report.html"
    html_path.write_text(session_report(res))
    return html_path


def collate_to(inputs, out_dir, allow_synthetic=False, provenance=None) -> Path:
    from .collate import collate, load_results, write_csv
    from .report import collation_report
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    col = collate(load_results(inputs), allow_synthetic=allow_synthetic, provenance=provenance)
    (out / "collated.json").write_text(json.dumps(col, indent=1))
    write_csv(col, out / "sessions.csv")
    (out / "collated.html").write_text(collation_report(col))
    return out / "collated.html"


def _gyro_metrics(t, G, lsb, cfg_rate, temp=None, sat=None):
    """Quantization, stability and temperature metrics for a still gyro record (rad/s)."""
    import numpy as np

    from .calib import RAD2DPH
    from .drift import FIXED_TAUS_S, allan_deviation
    counts = np.round(G / lsb).astype(np.int64)
    fs = 1 / np.median(np.diff(t))
    taus, adev = allan_deviation(G, fs)
    ft, fa = allan_deviation(G, fs, taus_s=FIXED_TAUS_S)
    runs = np.split(np.arange(len(t)), np.where(np.diff(t) > 1.0)[0] + 1)
    expected = sum((t[r[-1]] - t[r[0]]) * cfg_rate + 1 for r in runs if len(r))
    out = {
        "duration_s": float(t[-1] - t[0]), "rate_hz": float(fs),
        "samples_received": int(len(t)), "samples_expected": float(expected),
        "gyro_lsb_dph": float(lsb * RAD2DPH),
        "gyro_mean_dph": (G.mean(axis=0) * RAD2DPH).tolist(),
        "gyro_sd_lsb": counts.std(axis=0).tolist(),
        # fraction of samples on the most common count: near 1 means no dither, and averaging can't
        # resolve rates below one count
        "gyro_mode_fraction": [float(np.bincount(c - c.min()).max() / len(c)) for c in counts.T],
        "gyro_saturated_samples": int(np.sum(sat)) if sat is not None else None,
        "bias_instability_dph": (adev.min(axis=0) * RAD2DPH).tolist() if len(adev) else None,
        "adev_at_dph": {f"{x:.0f}": (a * RAD2DPH).tolist() for x, a in zip(ft, fa)},
        "allan_tau_s": taus.tolist(), "allan_dph": (adev * RAD2DPH).tolist(),
    }
    if temp is not None and len(temp[0]) > 5:
        tt, tc = temp
        out["temp_c"] = [float(tc.min()), float(tc.max())]
        edges = np.arange(t[0], t[-1], 60.0)
        mids, means = [], []
        for a, b in zip(edges[:-1], edges[1:]):
            m = (t >= a) & (t < b)
            if m.sum() > 10:
                mids.append((a + b) / 2)
                means.append(G[m].mean(axis=0))
        if len(mids) >= 5 and np.ptp(tc) >= 0.5:
            from .drift import temp_regression
            temp_b = np.interp(mids, tt, tc)
            r = temp_regression(mids, temp_b, np.array(means))
            means = np.array(means) * RAD2DPH
            # slope with a time term alongside, so slow drift during a warm-up isn't read as temperature
            out["bias_vs_temp"] = {"slope_dph_per_c": r["bias_temp_coef_dph_per_c"],
                                   "slope_sd_dph_per_c": r["bias_temp_coef_sd_dph_per_c"],
                                   "drift_dph_per_h": r["bias_drift_dph_per_h"],
                                   "temp_time_corr": r["temp_time_corr"], "confounded": r["bias_temp_confounded"],
                                   "correlation": [float(np.corrcoef(temp_b, means[:, i])[0, 1]) for i in range(3)]}
    return out


def bench(path, variant=None, rate_hz=100.0, gyro_range_dps=2000.0) -> dict:
    """Bench statistics for a raw WitMotion capture (imu.bin or imu.bin.gz, framed as the app
    writes it) or a session zip. See docs/BENCH.md for what each number should look like."""
    import gzip
    import zipfile

    import numpy as np

    from . import calib, witmotion
    p = Path(path)
    out = {"source": str(p)}
    if zipfile.is_zipfile(p):
        from .format import read_session
        sess = read_session(p)
        m = sess.manifest
        imu = m.get("imu") or {}
        out.update({"kind": m.get("kind"), "imu": imu, "bench": m.get("bench"), "decode": sess.imu_stats,
                    "config_readbacks": [d for _, k, d in sess.events if k == "imu_config"]})
        arrival, _ = witmotion.read_records(gzip.decompress(zipfile.ZipFile(p).read("imu.bin.gz")))
        g = sess.streams.get("gyro")
        # stability from the longest still phase (bench or drift), never across orientation changes
        still = [ph for ph in m.get("phases", []) if ph["name"] in ("bench", "drift_pre", "drift_post")]
        if still:
            ph = max(still, key=lambda q: q["end_ns"] - q["start_ns"])
            g = sess.slice("gyro", ph["start_ns"], ph["end_ns"])
            out["stability_phase"] = ph["name"]
        temp = sess.slice("imu_temp", g["t_ns"][0], g["t_ns"][-1] + 1) if g is not None and len(g["t_ns"]) else None
        rv = calib.reversal_test(sess)
        if rv:
            out["reversal"] = rv
        cal = calib.calibrate(sess, "cal_pre")
        if cal:
            out["calibration"] = {k: cal[k] for k in ("earth_h_dph", "earth_h_sd_dph", "earth_up_dph", "drift_dph_per_h", "visits")}
        cfg = imu.get("config") or {}
        rng = float(sess.imu_stats.get("gyro_range_used_dps", cfg.get("gyro_range_dps", gyro_range_dps)))
        rate = float(cfg.get("rate_hz", rate_hz))
    else:
        imu = {"variant": variant, "config": {"rate_hz": rate_hz, "gyro_range_dps": gyro_range_dps}}
        raw = p.read_bytes()
        raw = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw
        if variant not in witmotion.VARIANTS:
            raise SystemExit("give --variant spp or ble for a bare capture")
        arrival, chunks = witmotion.read_records(raw)
        s, st = witmotion.decode(arrival, chunks, imu)
        out["decode"] = st
        g = s.get("gyro")
        temp = s.get("imu_temp")
        rng, rate = gyro_range_dps, rate_hz
    if len(arrival) > 1:
        d = np.diff(arrival) / 1e6
        out["arrival_ms"] = {"median": float(np.median(d)), "p95": float(np.percentile(d, 95)), "max": float(d.max()),
                             "gaps_over_1s": int((d > 1000).sum())}
    if g is None or len(g["t_ns"]) < 100:
        return out
    t = g["t_ns"] / 1e9
    G = np.column_stack([g["x"], g["y"], g["z"]])
    tmp = (temp["t_ns"] / 1e9, temp["temp_c"]) if temp is not None and len(temp["t_ns"]) else None
    out.update(_gyro_metrics(t, G, np.radians(rng / 32768), rate, tmp, g.get("sat")))
    return out


COMPARE_KEYS = ("gyro_lsb_dph", "gyro_mean_dph", "gyro_sd_lsb", "gyro_mode_fraction", "bias_instability_dph")


def bench_compare(a, b) -> dict:
    """Two bench results side by side (for example auto-zero on against off, or two gyro ranges)."""
    def pick(r):
        out = {k: r.get(k) for k in COMPARE_KEYS}
        out["adev_300s_dph"] = (r.get("adev_at_dph") or {}).get("300")
        out["reversal_h_dph"] = (r.get("reversal") or {}).get("h_mean_dph")
        out["reversal_sd_dph"] = (r.get("reversal") or {}).get("h_sd_dph")
        out["calibration_h_dph"] = (r.get("calibration") or {}).get("earth_h_dph")
        out["bench"] = r.get("bench")
        return out
    return {"a": pick(a), "b": pick(b)}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lll", description="Local Level Lab analysis")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="analyze session zip(s): writes <name>.result.json + <name>.report.html")
    a.add_argument("zips", nargs="+")
    a.add_argument("-o", "--out", help="output directory (default: next to each zip)")
    c = sub.add_parser("collate", help="pool *.result.json files from directories/files")
    c.add_argument("inputs", nargs="+")
    c.add_argument("-o", "--out", default="collated")
    c.add_argument("--include-synthetic", action="store_true", help="let synthetic sessions into the primary result (testing only)")
    s = sub.add_parser("synth", help="write a synthetic session zip with a known true model")
    s.add_argument("out")
    s.add_argument("--truth", default="sphere_rotating",
                   choices=["sphere_rotating", "sphere_still", "flat_still"])
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--fs", type=float, default=50.0)
    s.add_argument("--mount", default="tray", choices=["tray", "window"])
    s.add_argument("--adverse", action="store_true",
                   help="add temperature-dependent bias, turbulence, mount slip, climb/descent and GNSS gaps")
    s.add_argument("--variant", default="spp", choices=["spp", "ble"])
    b = sub.add_parser("bench", help="decode a raw WitMotion capture or session zip and print bench statistics")
    b.add_argument("capture")
    b.add_argument("compare", nargs="?", help="a second capture or session to compare against")
    b.add_argument("--variant", choices=["spp", "ble"], help="needed for a bare capture")
    b.add_argument("--rate", type=float, default=100.0, help="configured output rate, Hz")
    b.add_argument("--gyro-range", type=float, default=2000.0, help="configured gyro full scale, °/s")
    args = ap.parse_args(argv)
    if args.cmd == "analyze":
        for z in args.zips:
            print(analyze_to(z, args.out))
    elif args.cmd == "collate":
        print(collate_to(args.inputs, args.out, args.include_synthetic))
    elif args.cmd == "synth":
        from .synth import ADVERSE, synthesize
        synthesize(args.out, args.truth, seed=args.seed, fs=args.fs, mount=args.mount, variant=args.variant,
                   **(ADVERSE if args.adverse else {}))
        print(args.out)
    elif args.cmd == "bench":
        r = bench(args.capture, args.variant, args.rate, args.gyro_range)
        if args.compare:
            r2 = bench(args.compare, args.variant, args.rate, args.gyro_range)
            print(json.dumps(bench_compare(r, r2), indent=1))
        else:
            print(json.dumps({k: v for k, v in r.items() if not k.startswith("allan_")}, indent=1))


if __name__ == "__main__":
    main()
