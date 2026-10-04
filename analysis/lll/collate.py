# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pool the per-session results from many recordings.

The experimental unit is not a 60-s bin, and not even a flight: sessions recorded with the same
IMU share its quirks. So pooling is hierarchical, with random effects at each level
(REML with Hartung–Knapp intervals):

    sessions → per IMU unit → population of units

Each level adds the scatter it sees between its members (τ²) to their error bars before
averaging. Flights or units that disagree beyond their stated errors widen the result instead of
being averaged away.

Only sessions that pass hard quality gates enter the primary result. The rest are listed as
exploratory, with the reasons. Breakdowns by heading, mount, IMU variant and unit are consistency
checks: a significant disagreement between groups is flagged, never averaged over.

The three k terms come from the same flights, so their errors are correlated (crab, for one, trades
globe rotation against curvature). The model tests therefore use the joint 3×3 covariance, pooled
by precision weighting, never a sum of per-term z² as if the terms were independent.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import __version__
from .fit import TERM_NAMES, sf_chi2
from .models import EXPECTED_K, MODELS

MIN_CRUISE_MIN = 60.0
GOOD_TIERS = ("qualified", "usable")
P_REJECT = 0.0027


def random_effects(y, sd):
    """Random-effects pool: REML for the between-member variance τ², and the modified
    Hartung–Knapp standard error (never narrower than the classic one) with t intervals on
    n − 1 degrees of freedom. DerSimonian–Laird is known to be overconfident with few members.
    Returns {mu, se, se_classic, tau2, Q, p_het, n, df, ci95}."""
    from scipy.stats import chi2, t as tdist
    y, v = np.asarray(y, float), np.asarray(sd, float) ** 2
    n = len(y)
    if n == 0:
        return None
    if n == 1:
        se = float(np.sqrt(v[0]))
        return {"mu": float(y[0]), "se": se, "se_classic": se, "tau2": 0.0, "Q": 0.0, "p_het": 1.0, "n": 1, "df": 0,
                "ci95": [float(y[0] - 1.96 * se), float(y[0] + 1.96 * se)]}
    w0 = 1 / v
    Q = float(np.sum(w0 * (y - np.sum(w0 * y) / np.sum(w0)) ** 2))
    tau2 = 0.0
    for _ in range(200):                       # REML by fixed-point iteration (Viechtbauer 2005)
        w = 1 / (v + tau2)
        mu = np.sum(w * y) / np.sum(w)
        new = max(0.0, float(np.sum(w ** 2 * ((y - mu) ** 2 - v)) / np.sum(w ** 2) + 1 / np.sum(w)))
        if abs(new - tau2) < 1e-12 * max(1.0, tau2):
            tau2 = new
            break
        tau2 = new
    w = 1 / (v + tau2)
    mu = float(np.sum(w * y) / np.sum(w))
    se_c = float(np.sqrt(1 / np.sum(w)))
    q = float(np.sum(w * (y - mu) ** 2) / (n - 1))
    se = se_c * np.sqrt(max(q, 1.0))
    tc = float(tdist.ppf(0.975, n - 1))
    return {"mu": mu, "se": float(se), "se_classic": se_c, "tau2": tau2, "Q": Q, "p_het": float(chi2.sf(Q, n - 1)),
            "n": n, "df": n - 1, "ci95": [mu - tc * se, mu + tc * se]}


def load_results(paths) -> list[dict]:
    res = []
    for p in paths:
        p = Path(p)
        files = sorted(p.rglob("*.result.json")) if p.is_dir() else [p]
        for f in files:
            res.append(json.loads(f.read_text()))
    return res


def unit_tiers(results) -> dict:
    """Every quality tier measured per IMU unit, oldest first: {unit: [(created_utc, tier dict)]}."""
    hist = defaultdict(list)
    for r in results:
        q = r.get("unit_quality") or {}
        u, tier = q.get("unit_id"), q.get("tier")
        if not u or tier in (None, "unknown"):
            continue
        hist[u].append((r.get("created_utc") or "", {"tier": tier, **q}))
    return {u: sorted(h, key=lambda x: x[0]) for u, h in hist.items()}


def tier_as_of(tiers, unit, when) -> dict:
    """The unit's latest tier measured at or before `when`. A later bench test never re-rates an
    earlier flight. Sessions with no timestamp use only tiers that have none either."""
    when = when or ""
    past = [q for t, q in tiers.get(unit, []) if t <= when]
    return past[-1] if past else {"tier": "unknown"}


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
    if "wmm_selection_sensitive" in fl:
        why.append("depends on the WMM slip exclusion")
    tier = tier_as_of(tiers, (r.get("imu") or {}).get("unit_id"), r.get("created_utc"))["tier"]
    if tier not in GOOD_TIERS:
        why.append(f"IMU unit tier {tier}")
    return why


def _heading(r):
    tr = r.get("track") or {}
    if not tr.get("lat"):
        return None
    la, lo = tr["lat"], tr["lon"]
    hd = np.degrees(np.arctan2(np.radians(lo[-1] - lo[0]) * np.cos(np.radians(np.mean(la))), np.radians(la[-1] - la[0]))) % 360
    return ["northbound", "eastbound", "southbound", "westbound"][int(((hd + 45) % 360) // 90)]


def _precision_pool(members, tau2):
    """Precision-weighted pool of vectors with covariances. members: [(k (NK,), cov (NK, NK), mask (NK,))];
    only the masked terms of each member carry information. tau2 (NK,) is added to each member's
    diagonal. Returns (mean, cov, mask of terms informed by any member)."""
    nk = len(TERM_NAMES)
    P, b = np.zeros((nk, nk)), np.zeros(nk)
    for k, c, m in members:
        idx = np.where(m)[0]
        if not len(idx):
            continue
        Pi = np.linalg.pinv(c[np.ix_(idx, idx)] + np.diag(tau2[idx]))
        P[np.ix_(idx, idx)] += Pi
        b[idx] += Pi @ k[idx]
    have = np.diag(P) > 0
    mu, V = np.full(nk, np.nan), np.full((nk, nk), np.nan)
    if have.any():
        h = np.where(have)[0]
        Vh = np.linalg.pinv(P[np.ix_(h, h)])
        V[np.ix_(h, h)] = Vh
        mu[h] = Vh @ b[h]
    return mu, V, have


def _with_marginal_sd(V, sd):
    """Keep V's correlations, but never let a term's variance be smaller than its own pooled
    (Hartung–Knapp) variance."""
    d = np.sqrt(np.diag(V))
    s = np.fmax(d, np.nan_to_num(np.asarray(sd, float), nan=0.0))
    with np.errstate(invalid="ignore", divide="ignore"):
        R = V / np.outer(d, d)
    return R * np.outer(s, s)


def pool_multivariate(items, per_term):
    """Joint pool of the three k terms: sessions → units → population, like pool_hierarchical, but
    each member carries its 3×3 covariance. Between-member variances τ² come from the per-term
    pools (per_term = pool_hierarchical's output) and go on the diagonal. Terms a session didn't
    identify carry no weight from it. Returns {k, cov, terms, assumed_diagonal}."""
    nk = len(TERM_NAMES)
    by_unit = defaultdict(list)
    diag_only = 0
    for it in items:
        unit, k, sd = it[:3]
        ident = it[3] if len(it) > 3 else {}
        cov = it[4] if len(it) > 4 else None
        kv = np.array([k[n] for n in TERM_NAMES], float)
        sv = np.array([sd[n] for n in TERM_NAMES], float)
        if cov is None:
            diag_only += 1
            c = np.diag(sv ** 2)
        else:
            c = np.asarray(cov, float)
        by_unit[unit].append((kv, c, np.array([ident.get(n, True) for n in TERM_NAMES])))
    units = []
    for u, mem in by_unit.items():
        tw = np.array([((per_term.get(n) or {}).get("tau2_within_units") or {}).get(str(u), 0.0) for n in TERM_NAMES])
        mu, V, have = _precision_pool(mem, tw)
        if have.any():
            units.append((np.nan_to_num(mu), np.nan_to_num(V), have))
    if not units:
        return None
    tb = np.array([(per_term.get(n) or {}).get("tau2_units", 0.0) for n in TERM_NAMES])
    mu, V, have = _precision_pool(units, tb)
    V = _with_marginal_sd(V, [(per_term.get(n) or {}).get("sd", np.nan) for n in TERM_NAMES])
    return {"terms": [n for n, h in zip(TERM_NAMES, have) if h],
            "k": {n: float(mu[i]) for i, n in enumerate(TERM_NAMES) if have[i]},
            "cov": [[float(V[i, j]) for j in range(nk) if have[j]] for i in range(nk) if have[i]],
            "sessions_without_covariance": diag_only}


def joint_model_tests(joint, per_term):
    """Each model's expected k against the jointly pooled k: χ² = dᵀ V⁻¹ d. With few units the
    variances are estimated on few degrees of freedom, so the statistic is referred to
    F(p, df) with the smallest per-term df (Hotelling-style) instead of χ²(p)."""
    from scipy.stats import f as fdist
    terms = joint["terms"]
    V = np.array(joint["cov"], float)
    Vi = np.linalg.pinv(V)
    dfs = [(per_term.get(n) or {}).get("df", 0) for n in terms]
    df = min(dfs) if dfs else 0
    tests = {}
    for m in MODELS:
        e = dict(zip(TERM_NAMES, EXPECTED_K[m]))
        d = np.array([joint["k"][n] - e[n] for n in terms])
        x2 = float(d @ Vi @ d)
        p = len(terms)
        pv = (float(fdist.sf(x2 / p, p, df)) if df > 0 else sf_chi2(x2, p)) if p else 1.0
        tests[m] = {"chi2": x2, "dof": p, "df_denominator": df or None, "p": pv, "rejected": pv < P_REJECT,
                    "z_marginal": {n: float(d[i] / np.sqrt(V[i, i])) for i, n in enumerate(terms)}}
    return tests


def pool_hierarchical(items):
    """items: [(unit, k dict, sd dict[, identified dict])]. Pools within units, then across units,
    per term. A session contributes to a term only where that term was identified on its flight."""
    out = {}
    by_unit = defaultdict(list)
    for it in items:
        unit, k, sd = it[:3]
        ident = it[3] if len(it) > 3 else {}
        by_unit[unit].append((k, sd, ident))
    for n in TERM_NAMES:
        units = {}
        for u, its in by_unit.items():
            use = [(k, s) for k, s, ident in its if ident.get(n, True)]
            p = random_effects([k[n] for k, s in use], [s[n] for k, s in use])
            if p:
                units[u] = p
        pop = random_effects([p["mu"] for p in units.values()], [p["se"] for p in units.values()])
        out[n] = {"k": pop["mu"], "sd": pop["se"], "df": pop["df"], "ci95": pop["ci95"],
                  "tau2_units": pop["tau2"], "p_het_units": pop["p_het"],
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
            "imu_unit": imu.get("unit_id"),
            "unit_tier": tier_as_of(tiers, imu.get("unit_id"), r.get("created_utc"))["tier"],
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
        item = (imu.get("unit_id"), fit["k"], fit["k_sd"], fit.get("identifiability", {}).get("identified_by_term", {}),
                fit.get("k_cov"))
        (primary if not why else explore).append(item)
        if not why:
            groups["heading"][_heading(r)].append(item)
            groups["mount"][r.get("mount", {}).get("type")].append(item)
            groups["imu variant"][imu.get("variant")].append(item)
            groups["imu unit"][imu.get("unit_id")].append(item)

    out = {"analysis_version": __version__, "n_sessions": len(results), "n_primary": len(primary),
           "n_exploratory": len(explore), "unit_tiers": tiers, "rows": rows, "ground": ground,
           "gates": {"min_cruise_min": MIN_CRUISE_MIN, "unit_tiers": list(GOOD_TIERS),
                     "requires": ["both calibrations", "curvature identified", "not prior-dominated",
                                  "not dependent on the WMM slip exclusion", "unit tier as of the session",
                                  "not synthetic"]}}
    if primary:
        pk = pool_hierarchical(primary)
        out["pooled_k"] = pk
        joint = pool_multivariate(primary, pk)
        out["pooled_k_joint"] = joint
        # each model's expected k against the jointly pooled k, with the terms' covariance
        out["model_tests"] = joint_model_tests(joint, pk) if joint else {}
        cons = {}
        for dim, gs in groups.items():
            gs = {g: its for g, its in gs.items() if g is not None}
            if len(gs) < 2:
                continue
            per = {str(g): pool_hierarchical(its) for g, its in gs.items()}
            dis = {}
            for n in TERM_NAMES:
                vals = [(p[n]["k"], p[n]["sd"]) for p in per.values() if p[n]]
                d = random_effects([a for a, _ in vals], [b for _, b in vals])
                dis[n] = {"Q": d["Q"], "p": d["p_het"], "disagree": d["p_het"] < 0.01}
            cons[dim] = {"groups": per, "heterogeneity": dis,
                         "disagreement": any(v["disagree"] for v in dis.values())}
        out["consistency"] = cons
        out["flags"] = [f"groups disagree by {d}" for d, c in cons.items() if c["disagreement"]]
        nu = max((v["n_units"] for v in pk.values() if v), default=0)
        # one or two IMU units are not a population: say so instead of extrapolating
        out["scope"] = {1: "single-unit", 2: "two-unit"}.get(nu, "population")
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
