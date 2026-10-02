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


def collate_to(inputs, out_dir) -> Path:
    from .collate import collate, load_results, write_csv
    from .report import collation_report
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    col = collate(load_results(inputs))
    (out / "collated.json").write_text(json.dumps(col, indent=1))
    write_csv(col, out / "sessions.csv")
    (out / "collated.html").write_text(collation_report(col))
    return out / "collated.html"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lll", description="Local Level Lab analysis")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="analyze session zip(s): writes <name>.result.json + <name>.report.html")
    a.add_argument("zips", nargs="+")
    a.add_argument("-o", "--out", help="output directory (default: next to each zip)")
    c = sub.add_parser("collate", help="pool *.result.json files from directories/files")
    c.add_argument("inputs", nargs="+")
    c.add_argument("-o", "--out", default="collated")
    s = sub.add_parser("synth", help="write a synthetic session zip with a known true model")
    s.add_argument("out")
    s.add_argument("--truth", default="sphere_rotating",
                   choices=["sphere_rotating", "sphere_still", "flat_rotating", "flat_still"])
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--fs", type=float, default=50.0)
    s.add_argument("--mount", default="tray", choices=["tray", "window"])
    s.add_argument("--adverse", action="store_true",
                   help="add temperature-dependent bias, turbulence, mount slip, climb/descent and GNSS gaps")
    args = ap.parse_args(argv)
    if args.cmd == "analyze":
        for z in args.zips:
            print(analyze_to(z, args.out))
    elif args.cmd == "collate":
        print(collate_to(args.inputs, args.out))
    elif args.cmd == "synth":
        from .synth import ADVERSE, synthesize
        synthesize(args.out, args.truth, seed=args.seed, fs=args.fs, mount=args.mount, **(ADVERSE if args.adverse else {}))
        print(args.out)


if __name__ == "__main__":
    main()
