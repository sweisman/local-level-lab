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


def collate_to(inputs, out_dir, allow_synthetic=False) -> Path:
    from .collate import collate, load_results, write_csv
    from .report import collation_report
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    col = collate(load_results(inputs), allow_synthetic=allow_synthetic)
    (out / "collated.json").write_text(json.dumps(col, indent=1))
    write_csv(col, out / "sessions.csv")
    (out / "collated.html").write_text(collation_report(col))
    return out / "collated.html"


def bench(path, variant=None, rate_hz=100.0, gyro_range_dps=2000.0) -> dict:
    """Bench statistics for a raw WitMotion capture (imu.bin or imu.bin.gz, framed as the app
    writes it) or a session zip. Answers the Phase 0 questions: does the stream decode, is the
    rate right, is the gyro quantization dithered, and how stable is the bias."""
    import gzip
    import zipfile

    import numpy as np

    from . import witmotion
    from .calib import RAD2DPH
    from .drift import allan_deviation
    p = Path(path)
    imu = {"variant": variant, "config": {"rate_hz": rate_hz, "gyro_range_dps": gyro_range_dps}}
    if zipfile.is_zipfile(p):
        zf = zipfile.ZipFile(p)
        imu = json.loads(zf.read("manifest.json")).get("imu") or imu
        raw = gzip.decompress(zf.read("imu.bin.gz"))
    else:
        raw = p.read_bytes()
        raw = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw
    if imu.get("variant") not in witmotion.VARIANTS:
        raise SystemExit("give --variant spp or ble for a bare capture")
    arrival, chunks = witmotion.read_records(raw)
    s, st = witmotion.decode(arrival, chunks, imu)
    out = {"decode": st}
    g = s.get("gyro")
    if g is None or len(g["t_ns"]) < 100:
        return out
    t = g["t_ns"] / 1e9
    G = np.column_stack([g["x"], g["y"], g["z"]])
    lsb = np.radians(float((imu.get("config") or {}).get("gyro_range_dps", gyro_range_dps)) / 32768)
    counts = np.round(G / lsb).astype(np.int64)
    fs = 1 / np.median(np.diff(t))
    taus, adev = allan_deviation(G, fs)
    out.update({
        "duration_s": float(t[-1] - t[0]), "rate_hz": float(fs),
        "gyro_lsb_dph": float(lsb * RAD2DPH),
        "gyro_mean_dph": (G.mean(axis=0) * RAD2DPH).tolist(),
        "gyro_sd_lsb": (counts.std(axis=0)).tolist(),
        # fraction of samples on the most common count: near 1 means no dither, and averaging
        # can't resolve rates below one count
        "gyro_mode_fraction": [float(np.bincount(c - c.min()).max() / len(c)) for c in counts.T],
        "bias_instability_dph": (adev.min(axis=0) * RAD2DPH).tolist() if len(adev) else None,
        "allan_tau_s": taus.tolist(), "allan_dph": (adev * RAD2DPH).tolist(),
    })
    if "imu_temp" in s:
        tc = s["imu_temp"]["temp_c"]
        out["temp_c"] = [float(tc.min()), float(tc.max())]
    return out


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
        print(json.dumps({k: v for k, v in r.items() if not k.startswith("allan_")}, indent=1))


if __name__ == "__main__":
    main()
