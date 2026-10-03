# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pool the per-session results from many recordings.

The experimental unit is not a 60-s bin, and not even a flight: sessions recorded with the same
IMU share its quirks. So pooling is hierarchical, with random effects at each level
(DerSimonian–Laird):

    sessions → per IMU unit → population of units

Each level adds the scatter it sees between its members (τ²) to their error bars before
averaging. Flights or units that disagree beyond their stated errors widen the result instead of
being averaged away.

Only sessions that pass hard quality gates enter the primary result. The rest are listed as
exploratory, with the reasons. Breakdowns by heading, mount, IMU variant and unit are consistency
checks: a significant disagreement between groups is flagged, never averaged over.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from math import erfc, sqrt
from pathlib import Path

import numpy as np

from . import __version__
from .fit import TERM_NAMES, sf_chi2
from .models import EXPECTED_K, MODELS

MIN_CRUISE_MIN = 60.0
GOOD_TIERS = ("qualified", "usable")
P_REJECT = 0.0027


def dersimonian_laird(y, sd):
    """Random-effects pool. Returns {mu, se, tau2, Q, p_het, n}."""
    y, v = np.asarray(y, float), np.asarray(sd, float) ** 2
    n = len(y)
    if n == 0:
        return None
    if n == 1:
        return {"mu": float(y[0]), "se": float(np.sqrt(v[0])), "tau2": 0.0, "Q": 0.0, "p_het": 1.0, "n": 1}
    w = 1 / v
    ybar = np.sum(w * y) / np.sum(w)
    Q = float(np.sum(w * (y - ybar) ** 2))
    C = float(np.sum(w) - np.sum(w ** 2) / np.sum(w))
    tau2 = max(0.0, (Q - (n - 1)) / C) if C > 0 else 0.0
    ws = 1 / (v + tau2)
    return {"mu": float(np.sum(ws * y) / np.sum(ws)), "se": float(1 / np.sqrt(np.sum(ws))), "tau2": tau2,
            "Q": Q, "p_het": _sf_chi2_df(Q, n - 1), "n": n}


def _sf_chi2_df(x, df):
    """χ² survival function for any integer df (Wilson–Hilferty approximation beyond the closed forms)."""
    if df <= 0:
        return 1.0
    if df == 1:
        return erfc(sqrt(max(x, 0) / 2))
    if df in (3, 4):
        return sf_chi2(x, df)
    z = ((x / df) ** (1 / 3) - (1 - 2 / (9 * df))) / sqrt(2 / (9 * df))
    return 0.5 * erfc(z / sqrt(2))


def load_results(paths) -> list[dict]:
    res = []
    for p in paths:
        p = Path(p)
        files = sorted(p.rglob("*.result.json")) if p.is_dir() else [p]
        for f in files:
            res.append(json.loads(f.read_text()))
    return res


def unit_tiers(results) -> dict:
    """The latest quality tier per IMU unit, from any session that measured one."""
    best = {}
    for r in results:
        q = r.get("unit_quality") or {}
        u, tier = q.get("unit_id"), q.get("tier")
        if not u or tier in (None, "unknown"):
            continue
        if u not in best or (r.get("created_utc") or "") >= (best[u][0] or ""):
            best[u] = (r.get("created_utc"), tier, q)
    return {u: {"tier": t, **q} for u, (_, t, q) in best.items()}


def gate(r, tiers, allow_synthetic=False) -> list[str]:
    """Reasons a session can't enter the primary result (empty = it can)."""
    why = []
    fl = set(r.get("flags", []))
    if not r.get("fit"):
        return ["no in-flight fit"]
    if "synthetic" in fl and not allow_synthetic:
        why.append("synthetic")
    if fl & {"no_cal_pre", "no_cal_post"}:
        why.append("missing a calibration")
    if (r.get("cruise_minutes") or 0) < MIN_CRUISE_MIN:
        why.append(f"under {MIN_CRUISE_MIN:.0f} min of cruise")
    if "k_not_identified" in fl:
        why.append("curvature not identified")
    if "prior_dominated" in fl:
        why.append("prior-dominated")
    unit = (r.get("imu") or {}).get("unit_id")
    if tiers.get(unit, {}).get("tier") not in GOOD_TIERS:
        why.append(f"IMU unit tier {tiers.get(unit, {}).get('tier', 'unknown')}")
    return why


def _heading(r):
    tr = r.get("track") or {}
    if not tr.get("lat"):
        return None
    la, lo = tr["lat"], tr["lon"]
    hd = np.degrees(np.arctan2(np.radians(lo[-1] - lo[0]) * np.cos(np.radians(np.mean(la))), np.radians(la[-1] - la[0]))) % 360
    return ["northbound", "eastbound", "southbound", "westbound"][int(((hd + 45) % 360) // 90)]


def pool_hierarchical(items):
    """items: [(unit, k dict, sd dict)]. Pools within units, then across units, per term."""
    out = {}
    by_unit = defaultdict(list)
    for unit, k, sd in items:
        by_unit[unit].append((k, sd))
    for n in TERM_NAMES:
        units = {}
        for u, its in by_unit.items():
            p = dersimonian_laird([k[n] for k, s in its], [s[n] for k, s in its])
            if p:
                units[u] = p
        pop = dersimonian_laird([p["mu"] for p in units.values()], [p["se"] for p in units.values()])
        out[n] = {"k": pop["mu"], "sd": pop["se"], "tau2_units": pop["tau2"], "p_het_units": pop["p_het"],
                  "n_units": pop["n"], "n_sessions": sum(p["n"] for p in units.values()),
                  "tau2_within_units": {str(u): p["tau2"] for u, p in units.items()}} if pop else None
    return out


def collate(results: list[dict], allow_synthetic: bool = False) -> dict:
    tiers = unit_tiers(results)
    rows, primary, explore = [], [], []
    groups = {"heading": defaultdict(list), "mount": defaultdict(list), "imu variant": defaultdict(list),
              "imu unit": defaultdict(list)}
    ground = {"lat": [], "up": [], "up_sd": [], "h": [], "h_sd": [], "unit": []}
    for r in results:
        fit = r.get("fit")
        fl = r.get("flight", {})
        imu = r.get("imu") or {}
        why = gate(r, tiers, allow_synthetic)
        rows.append({
            "session_id": r.get("session_id"), "kind": r.get("kind", "flight"),
            "flight": f"{fl.get('airline', '')} {fl.get('flight_number', '')}".strip(), "date": fl.get("date"),
            "seat": fl.get("seat"), "mount": r.get("mount", {}).get("type"), "imu_variant": imu.get("variant"),
            "imu_unit": imu.get("unit_id"), "unit_tier": tiers.get(imu.get("unit_id"), {}).get("tier"),
            "cruise_min": r.get("cruise_minutes"),
            "not_rejected": ";".join(m for m in MODELS if fit and not fit["rejected"][m]) if fit else None,
            **{n: fit["k"][n] if fit else None for n in TERM_NAMES},
            **{n + "_sd": fit["k_sd"][n] if fit else None for n in TERM_NAMES},
            "primary": not why, "excluded_because": "; ".join(why),
            "flags": ";".join(r.get("flags", [])), "input_sha256": r.get("input_sha256"),
        })
        if not ("synthetic" in r.get("flags", []) and not allow_synthetic):
            for c in r.get("calibration", {}).values():
                if c.get("lat_deg") is not None:
                    ground["lat"].append(c["lat_deg"])
                    ground["unit"].append(imu.get("unit_id"))
                    for key, src in (("up", "earth_up"), ("h", "earth_h")):
                        ground[key].append(c[src + "_dph"])
                        ground[key + "_sd"].append(c[src + "_sd_dph"])
        if not fit:
            continue
        item = (imu.get("unit_id"), fit["k"], fit["k_sd"])
        (primary if not why else explore).append(item)
        if not why:
            groups["heading"][_heading(r)].append(item)
            groups["mount"][r.get("mount", {}).get("type")].append(item)
            groups["imu variant"][imu.get("variant")].append(item)
            groups["imu unit"][imu.get("unit_id")].append(item)

    out = {"analysis_version": __version__, "n_sessions": len(results), "n_primary": len(primary),
           "n_exploratory": len(explore), "unit_tiers": tiers, "rows": rows, "ground": ground,
           "gates": {"min_cruise_min": MIN_CRUISE_MIN, "unit_tiers": list(GOOD_TIERS),
                     "requires": ["both calibrations", "curvature identified", "not prior-dominated", "not synthetic"]}}
    if primary:
        pk = pool_hierarchical(primary)
        out["pooled_k"] = pk
        # each model's expected k against the pooled k (independent terms): χ² with 3 dof
        tests = {}
        for m in MODELS:
            z = [(pk[n]["k"] - e) / pk[n]["sd"] for n, e in zip(TERM_NAMES, EXPECTED_K[m]) if pk[n]]
            x2 = float(np.sum(np.square(z)))
            p = sf_chi2(x2, len(z)) if len(z) in (3, 4) else _sf_chi2_df(x2, len(z))
            tests[m] = {"chi2": x2, "p": p, "rejected": p < P_REJECT, "z": dict(zip(TERM_NAMES, z))}
        out["model_tests"] = tests
        cons = {}
        for dim, gs in groups.items():
            gs = {g: its for g, its in gs.items() if g is not None}
            if len(gs) < 2:
                continue
            per = {str(g): pool_hierarchical(its) for g, its in gs.items()}
            dis = {}
            for n in TERM_NAMES:
                vals = [(p[n]["k"], p[n]["sd"]) for p in per.values() if p[n]]
                d = dersimonian_laird([a for a, _ in vals], [b for _, b in vals])
                dis[n] = {"Q": d["Q"], "p": d["p_het"], "disagree": d["p_het"] < 0.01}
            cons[dim] = {"groups": per, "heterogeneity": dis,
                         "disagreement": any(v["disagree"] for v in dis.values())}
        out["consistency"] = cons
        out["flags"] = [f"groups disagree by {d}" for d, c in cons.items() if c["disagreement"]]
    out["ground"]["fit"] = ground_fit(ground)
    return out


def ground_fit(g):
    """Horizontal: h = C |cos φ| (immune to g-sensitivity; primary). Vertical: up = A sin φ + B_unit,
    with a separate intercept per IMU unit, because rotation about the plumb line can't be told from
    that unit's g-sensitivity along it. A is informed only by units seen at several latitudes."""
    if len(g["lat"]) < 3:
        return None
    lat = np.radians(g["lat"])
    wh = 1 / np.maximum(np.array(g["h_sd"]), 0.1) ** 2
    cc = np.abs(np.cos(lat))
    C = float(np.sum(wh * cc * g["h"]) / np.sum(wh * cc ** 2))
    C_se = float(1 / np.sqrt(np.sum(wh * cc ** 2)))
    units = sorted({str(u) for u in g["unit"]})
    X = np.zeros((len(lat), 1 + len(units)))
    X[:, 0] = np.sin(lat)
    for i, u in enumerate(g["unit"]):
        X[i, 1 + units.index(str(u))] = 1.0
    wu = 1 / np.maximum(np.array(g["up_sd"]), 0.1)
    beta, *_ = np.linalg.lstsq(X * wu[:, None], np.array(g["up"]) * wu, rcond=None)
    cov = np.linalg.pinv((X * wu[:, None]).T @ (X * wu[:, None]))
    A_identified = any(np.ptp(lat[[str(u) == un for u in g["unit"]]]) > np.radians(5) for un in units)
    return {"C_cos": C, "C_cos_se": C_se, "A_sin": float(beta[0]), "A_sin_se": float(np.sqrt(cov[0, 0])),
            "A_identified": A_identified, "B_by_unit": {u: float(b) for u, b in zip(units, beta[1:])}}


def write_csv(col: dict, path):
    with open(path, "w", newline="") as f:
        if not col["rows"]:
            return
        w = csv.DictWriter(f, fieldnames=list(col["rows"][0]))
        w.writeheader()
        w.writerows(col["rows"])
