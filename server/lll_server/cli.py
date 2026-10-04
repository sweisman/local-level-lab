# SPDX-License-Identifier: AGPL-3.0-or-later
"""lll-server: serve, list, process, collate, export."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from .app import PUBLIC_COLS, Store, create_app


def process(store: Store, ids=None) -> list[str]:
    from lll.cli import analyze_to
    done = []
    for r in store.all():
        if ids and r["id"] not in ids:
            continue
        if not ids and r["status"] == "processed":
            continue
        try:
            html = analyze_to(store.raw_path(r["id"]), store.root / "reports")
            res = (store.root / "reports" / f"{r['id']}.result.json").read_text()
            status = "processed"
        except Exception as e:  # keep going; record the failure
            res, status, html = json.dumps({"error": repr(e)}), "failed", None
        with store.db() as c:
            c.execute("UPDATE sessions SET status=?, result=? WHERE id=?", (status, res, r["id"]))
        done.append(f"{r['id']} {status} {html or ''}")
    return done


def export(store: Store, out: Path) -> Path:
    """Copy the whole public corpus (raw zips + index + SHA-256 checksums) to a directory."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir(exist_ok=True)
    index, sums = [], []
    for r in store.all():
        src = store.raw_path(r["id"])
        shutil.copy2(src, out / "raw" / src.name)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        if digest != r["sha256"]:
            raise RuntimeError(f"checksum mismatch for {r['id']}: stored file was modified")
        sums.append(f"{digest}  raw/{src.name}")
        index.append({k: r[k] for k in PUBLIC_COLS})
    (out / "index.json").write_text(json.dumps(index, indent=1))
    from .registry import approvals
    (out / "provenance.json").write_text(json.dumps(approvals(store), indent=1))
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    (out / "LICENSE-DATA.txt").write_text("All session data in this export is dedicated to the public domain "
                                          "under CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/\n")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lll-server")
    ap.add_argument("--data", default="data", help="data directory (default ./data)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    sub.add_parser("list")
    p = sub.add_parser("process", help="analyze unprocessed sessions (or the given ids)")
    p.add_argument("ids", nargs="*")
    sub.add_parser("collate", help="pool all processed results into data/collated/")
    e = sub.add_parser("export", help="dump the public dataset with checksums")
    e.add_argument("out")
    r = sub.add_parser("register-unit", help="register a physical instrument; operator identity stays private")
    r.add_argument("operator")
    r = sub.add_parser("certify-unit", help="approve complete bench evidence now, before any eligible flight")
    r.add_argument("unit")
    r.add_argument("evidence", help="JSON with checks, tier, config and source_sha256")
    r = sub.add_parser("approve-session", help="attest physical provenance of a processed session")
    r.add_argument("session")
    r.add_argument("certificate")
    r = sub.add_parser("revoke-session")
    r.add_argument("session")
    args = ap.parse_args(argv)
    if args.cmd == "serve":
        import uvicorn
        uvicorn.run(create_app(args.data), host=args.host, port=args.port)
        return
    store = Store(Path(args.data))
    from . import registry
    if args.cmd == "list":
        for r in store.all():
            print(r["id"], r["status"], r["airline"], r["flight_number"], r["flight_date"], r["seat"], r["mount"], r["imu_variant"])
    elif args.cmd == "process":
        print("\n".join(process(store, args.ids)) or "nothing to process")
    elif args.cmd == "collate":
        from lll.cli import collate_to
        from lll import __version__
        inputs = [store.root / "reports" / f"{r['id']}.result.json" for r in store.all()
                  if r["status"] == "processed" and json.loads(r["result"]).get("analysis_version") == __version__]
        print(collate_to(inputs, store.root / "collated", provenance=registry.approvals(store)))
    elif args.cmd == "export":
        print(export(store, Path(args.out)))
    elif args.cmd == "register-unit":
        print(registry.register(store, args.operator))
    elif args.cmd == "certify-unit":
        print(registry.certify(store, args.unit, json.loads(Path(args.evidence).read_text())))
    elif args.cmd == "approve-session":
        registry.approve(store, args.session, args.certificate)
    elif args.cmd == "revoke-session":
        registry.revoke(store, args.session)


if __name__ == "__main__":
    main()
