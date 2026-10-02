# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pool the per-session results from many recordings."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import __version__
from .fit import TERM_NAMES
from .models import MODELS


def _pool(items):
    """Inverse-variance pooling of a list of (k dict, sd dict)."""
    out = {"k": {}, "sd": {}, "n": len(items)}
    for n in TERM_NAMES:
        ks = np.array([k[n] for k, s in items if k.get(n) is not None and s.get(n)])
        ss = np.array([s[n] for k, s in items if k.get(n) is not None and s.get(n)])
        if len(ks) == 0:
            out["k"][n] = out["sd"][n] = None
            continue
        w = 1 / ss ** 2
        out["k"][n] = float((w * ks).sum() / w.sum())
        out["sd"][n] = float(1 / np.sqrt(w.sum()))
    return out


def load_results(paths) -> list[dict]:
    res = []
    for p in paths:
        p = Path(p)
        files = sorted(p.rglob("*.result.json")) if p.is_dir() else [p]
        for f in files:
            res.append(json.loads(f.read_text()))
    return res


def collate(results: list[dict]) -> dict:
    rows, fits, chi2, best = [], [], defaultdict(float), defaultdict(int)
    groups = {"mount type": defaultdict(list), "device model": defaultdict(list),
              "heading": defaultdict(list), "cruise duration": defaultdict(list),
              "calibration": defaultdict(list)}
    ground = {"lat": [], "up": [], "up_sd": [], "h": [], "h_sd": []}
    for r in results:
        fit = r.get("fit")
        fl = r.get("flight", {})
        rows.append({
            "session_id": r.get("session_id"), "flight": f"{fl.get('airline', '')} {fl.get('flight_number', '')}".strip(),
            "date": fl.get("date"), "mount": r.get("mount", {}).get("type"), "device": r.get("device", {}).get("model"),
            "cruise_min": r.get("cruise_minutes"), "best_model": fit["best_model"] if fit else None,
            "k_rot_sphere": fit["k"]["k_rot_sphere"] if fit else None, "k_rot_flat": fit["k"]["k_rot_flat"] if fit else None,
            "k_curv": fit["k"]["k_curv"] if fit else None, "k_curv_sd": fit["k_sd"]["k_curv"] if fit else None,
            "flags": ";".join(r.get("flags", [])), "input_sha256": r.get("input_sha256"),
        })
        for c in r.get("calibration", {}).values():
            if c.get("lat_deg") is not None:
                ground["lat"].append(c["lat_deg"])
                for key, src in (("up", "earth_up"), ("h", "earth_h")):
                    ground[key].append(c[src + "_dph"])
                    ground[key + "_sd"].append(c[src + "_sd_dph"])
        if not fit:
            continue
        item = (fit["k"], fit["k_sd"])
        fits.append(item)
        for m in MODELS:
            chi2[m] += fit["delta_chi2"][m]
        best[fit["best_model"]] += 1
        groups["mount type"][r.get("mount", {}).get("type")].append(item)
        groups["device model"][r.get("device", {}).get("model")].append(item)
        groups["cruise duration"]["< 60 min" if (r.get("cruise_minutes") or 0) < 60 else "≥ 60 min"].append(item)
        groups["calibration"][r.get("bias_model", {}).get("mode")].append(item)
        if r.get("track") and r["track"].get("lat"):
            la, lo = r["track"]["lat"], r["track"]["lon"]
            hd = np.degrees(np.arctan2(np.radians(lo[-1] - lo[0]) * np.cos(np.radians(np.mean(la))),
                                       np.radians(la[-1] - la[0]))) % 360
            groups["heading"][["northbound", "eastbound", "southbound", "westbound"][int(((hd + 45) % 360) // 90)]].append(item)
    out = {"analysis_version": __version__, "n_sessions": len(results), "n_with_fit": len(fits),
           "n_cal": len(ground["lat"]), "rows": rows, "ground": ground}
    if fits:
        p = _pool(fits)
        out["pooled_k"] = {n: {"k": p["k"][n], "sd": p["sd"][n]} for n in TERM_NAMES}
        lo = min(chi2.values())
        out["pooled_delta_chi2"] = {m: chi2[m] - lo for m in MODELS}
        out["best_counts"] = dict(best)
        out["breakdowns"] = {d: {str(g): _pool(items) for g, items in gs.items()} for d, gs in groups.items() if gs}
    if len(ground["lat"]) >= 3:
        lat = np.radians(ground["lat"])
        A = np.column_stack([np.sin(lat), np.ones_like(lat)])
        wu = 1 / np.maximum(np.array(ground["up_sd"]), 0.1)
        (a_sin, b_const), *_ = np.linalg.lstsq(A * wu[:, None], np.array(ground["up"]) * wu, rcond=None)
        wh = 1 / np.maximum(np.array(ground["h_sd"]), 0.1)
        c_cos = float(np.sum(wh ** 2 * np.abs(np.cos(lat)) * ground["h"]) / np.sum(wh ** 2 * np.cos(lat) ** 2))
        out["ground"]["fit"] = {"A_sin": float(a_sin), "B_const": float(b_const), "C_cos": c_cos}
    return out


def write_csv(col: dict, path):
    with open(path, "w", newline="") as f:
        if not col["rows"]:
            return
        w = csv.DictWriter(f, fieldnames=list(col["rows"][0]))
        w.writeheader()
        w.writerows(col["rows"])
