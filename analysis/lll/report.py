# SPDX-License-Identifier: AGPL-3.0-or-later
"""Self-contained HTML reports (static matplotlib figures embedded as PNG)."""
from __future__ import annotations

import base64
import html
import io
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .models import MODEL_LABELS  # noqa: E402

# Fixed categorical order (never cycled): each model keeps the same colour and dash in every
# figure. Measured data is drawn in ink.
INK = "#1f2328"
MUTED = "#6e7781"
GRID = "#d8dee4"
MODEL_STYLE = {
    "sphere_rotating": ("#2a78d6", "-"),
    "sphere_still": ("#eb6834", "--"),
    "flat_still": ("#eda100", ":"),
}
K_LABELS = {"k_rot_sphere": "Earth rotation\n(globe)",
            "k_curv": "Globe transport\n(curvature)", "k_disc": "Disc transport\n(circling the centre)"}

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "lines.linewidth": 2, "figure.dpi": 110,
})

CSS = """
:root{--bg:#ffffff;--fg:#1f2328;--muted:#6e7781;--line:#d8dee4;--card:#f6f8fa;--good:#1a7f37;--bad:#cf222e}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--muted:#8d96a0;--line:#30363d;--card:#161b22}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--muted:#8d96a0;--line:#30363d;--card:#161b22}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:16px}
main{max-width:980px;margin:auto}
h1{font-size:1.5rem;margin:.2rem 0} h2{font-size:1.15rem;margin-top:2rem;border-bottom:1px solid var(--line)}
.sub{color:var(--muted)} table{border-collapse:collapse;width:100%;font-size:.9rem;overflow-x:auto;display:block}
td,th{border-bottom:1px solid var(--line);padding:4px 8px;text-align:left;white-space:nowrap}
th{color:var(--muted);font-weight:600} img{max-width:100%;background:#fff;border-radius:6px}
.tiles{display:flex;flex-wrap:wrap;gap:12px} .tile{background:var(--card);border-radius:8px;padding:10px 14px;min-width:160px}
.tile b{display:block;font-size:1.3rem} code{font-size:.85em} .flag{color:var(--bad)}
details{margin:.5rem 0}
"""


def _png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return f'<img alt="" src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}">'


def _table(head, rows) -> str:
    h = "".join(f"<th>{html.escape(str(c))}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def _f(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def page(title, body) -> str:
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport "
            f"content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title>"
            f"<style>{CSS}</style></head><body><main>{body}</main></body></html>")


def _k_figure(k, sd, expected_by_model=None):
    names = list(K_LABELS)
    fig, ax = plt.subplots(figsize=(7, 2.8))
    y = np.arange(len(names))[::-1]
    for i, n in enumerate(names):
        if k.get(n) is None:
            continue
        ax.errorbar(k[n], y[i], xerr=1.96 * (sd.get(n) or 0), fmt="o", color=INK, ms=7, capsize=3, lw=1.5)
        ax.annotate(f"{k[n]:.2f} ± {1.96 * (sd.get(n) or 0):.2f}", (k[n], y[i]), xytext=(0, 9),
                    textcoords="offset points", ha="center", color=INK, fontsize=8)
    ax.axvline(0, color=MUTED, lw=1)
    ax.axvline(1, color=MUTED, lw=1, ls="--")
    ax.set_yticks(y, [K_LABELS[n] for n in names])
    ax.set_xlabel("scale factor k  (0 = term absent, 1 = term present at full predicted size); bars = 95% CI")
    ax.set_ylim(-0.7, len(names) - 0.3)
    return _png(fig)


def session_report(res: dict) -> str:
    fl, mt = res.get("flight", {}), res.get("mount", {})
    title = f"{fl.get('airline', '')} {fl.get('flight_number', '')} {fl.get('date', '')}".strip() or res.get("session_id", "session")
    out = [f"<h1>Local Level Lab — {html.escape(title)}</h1>",
           f"<p class=sub>session {html.escape(str(res.get('session_id')))} · mount {html.escape(str(mt.get('type')))} · "
           f"device {html.escape(str(res.get('device', {}).get('model')))} · analysis v{res.get('analysis_version')} · "
           f"input sha256 <code>{res.get('input_sha256', '')[:16]}…</code></p>"]
    flags = res.get("flags", [])
    if flags:
        out.append("<p>Flags: " + ", ".join(f"<span class=flag>{html.escape(f)}</span>" for f in flags) + "</p>")

    fit = res.get("fit")
    if fit:
        idn = fit["identifiability"]
        not_rej = [MODEL_LABELS[m] for m in MODEL_LABELS if not fit["rejected"][m]]
        verdict = (" or ".join(not_rej) if not_rej else "none: check the flags") + (
            "" if idn["identified"] else " (curvature not identified on this flight)")
        out.append("<h2>Result</h2><div class=tiles>"
                   f"<div class=tile><span class=sub>Models not rejected at 3σ</span><b>{html.escape(verdict)}</b></div>"
                   f"<div class=tile><span class=sub>Stable cruise analysed</span><b>{res.get('cruise_minutes', 0):.0f} min</b></div>"
                   f"<div class=tile><span class=sub>Noise per 60-s bin</span><b>{fit['sigma_bin_dph']:.1f} °/h</b></div>"
                   "</div>")
        ci = fit.get("delta_chi2_ci_16_84") or {}
        out.append(_table(["Model", "Δχ² vs free fit", "p (3 dof)", "rejected at 3σ", "Δχ² vs best [16–84 %]",
                           "relative likelihood*", "expected k (rot globe, curv globe, disc)"],
                          [[MODEL_LABELS[m], _f(fit["delta_chi2_vs_free"][m], 1), f"{fit['p_vs_free'][m]:.2g}",
                            "yes" if fit["rejected"][m] else "no",
                            _f(fit["delta_chi2"][m], 1) + (f" [{_f(ci[m][0], 1)}–{_f(ci[m][1], 1)}]" if m in ci else ""),
                            _f(fit["relative_likelihood"][m], 3), str(tuple(fit["expected_k"][m]))]
                           for m in MODEL_LABELS]))
        sc = fit["chi2_scaling"]
        out.append(f"<p class=sub>χ² is scaled by {sc['scale']:.2f} for the correlation between neighbouring bins "
                   f"(lag-1 ρ = {sc['rho_lag1']:.2f}). Each model is tested against the free fit: Δχ² follows χ² with 3 degrees of "
                   "freedom if that model is true. *Relative likelihoods are exp(−Δχ²/2), normalized. They are not probabilities.</p>")
        out.append("<h3>Separate scale factors</h3>" + _k_figure(fit["k"], fit["k_sd"]))
        like = idn["bias_likeness_by_term"]
        ps = fit["prior_sensitivity"]
        out.append("<p class=sub>How much of each term a constant residual bias could mimic (1 = indistinguishable by the flight "
                   "data, so only the ground calibration constrains it): "
                   + ", ".join(f"{html.escape(n)} {v:.2f}" for n, v in like.items())
                   + ". A constant rotation about the vertical is always 1 in level flight, because it lies along gravity just like "
                   "gyro bias and g-sensitivity. Turning the IMU 180° about the vertical during the flight lowers the curvature value; "
                   f"flipping it does not. Widening the bias prior {ps['widen']:.0f}× moves k by "
                   + ", ".join(f"{v:+.1f}σ" for v in ps["k_shift_sigma"].values())
                   + (" (prior-dominated)." if ps["prior_dominated"] else ".")
                   + f" Gravity orientations: {fit['gravity_orientations']}. Residual bias per orientation: "
                   + "; ".join(", ".join(f"{v:.2f}" for v in b) for b in fit["bias_residual_dph"]) + " °/h.</p>")
        tm = res.get("temperature") or {}
        if tm.get("cal_mean_c") is not None:
            src = {"drift_run": "coefficient from a drift run, residual fitted", "free_fit": "coefficient fitted freely"}
            out.append(f"<p class=sub>IMU chip temperature: calibration {tm['cal_mean_c']:.1f} °C, cruise "
                       f"{_f(tm.get('cruise_min_c'), 1)}–{_f(tm.get('cruise_max_c'), 1)} °C. "
                       + ("Temperature term used (" + src.get(tm.get("coefficient_source"), "") + "): "
                          + ", ".join(_f(v) for v in fit["temp_coef_dph_per_c"]) + " °/h/°C."
                          if tm.get("term_used") else "Difference too small for a temperature term.") + "</p>")

    sl = res.get("slip") or {}
    if sl.get("available"):
        rows = []
        for v, label in (("wmm", "with WMM declination"), ("no_declination", "no declination model")):
            for r in sl["variants"].get(v, []):
                rows.append([label, r["seg"], r["epoch"], f"{_f(r['slip_dph'], 1)} ± {_f(r['sd_dph'], 1)}",
                             "yes" if r["slip"] else "no", "yes" if r["airframe_field_calibrated"] else "assumed small"])
        out.append("<h2>Mount slip watchdog (magnetometer)</h2>"
                   + _table(["version", "segment", "mount epoch", "slip (°/h)", "slip?", "airframe field"], rows)
                   + "<p class=sub>A slow turn of the IMU in its mount goes straight into the vertical gyro channel. The magnetometer sees "
                   "it as a turn of the horizontal field. A segment is left out of the gyro fit when the version with WMM declination sees "
                   f"slip above {_f(sl['max_slip_dph'], 1)} °/h (and 3σ). The choice uses only the magnetometer and GPS, never the gyro, so "
                   "the declination model can only drop data, never favour a model. The version without a declination model is a "
                   "cross-check; it also reads declination changes along the route as slip. "
                   f"Left out: {sl['exclude_segments'] or 'none'}"
                   + (f" (triggered by: {html.escape(str(sl.get('triggered_by')))})" if sl.get("triggered_by") else "") + ".</p>")
    turns = [e["turn"] for e in res.get("mount_epochs", []) if e.get("turn")]
    if turns:
        out.append("<p class=sub>IMU turns during the flight, measured by the gyro: "
                   + ", ".join(f"{html.escape(str(t['kind']))} {t['angle_deg']:.1f}°" for t in turns)
                   + ". Each later epoch is mapped back into the first epoch's frame.</p>")

    # calibration
    cal = res.get("calibration", {})
    if cal:
        out.append("<h2>Ground calibration: bias and Earth rate</h2>")
        rows = []
        for k, c in cal.items():
            pred = c.get("predicted", {})
            rows.append([k, ", ".join(_f(v) for v in c["bias_dph"]),
                         f"{_f(c['earth_up_dph'])} ± {_f(c['earth_up_sd_dph'])}",
                         f"{_f(c['earth_h_dph'])} ± {_f(c['earth_h_sd_dph'])}",
                         "<br>".join(f"{MODEL_LABELS[m]}: {_f(p[0])} / {_f(p[1])}" for m, p in pred.items())])
        out.append(_table(["cal", "bias x,y,z (°/h)", "rotation up (°/h)", "rotation horizontal (°/h)",
                           "predicted up / horizontal"], rows))
        out.append("<p class=sub>The horizontal magnitude is biased upward by noise, so a phone with no true horizontal "
                   "rotation still shows a few °/h here. Compare it with the 'still' predictions plus that noise floor.</p>")
    bm = res.get("bias_model", {})
    if bm:
        out.append(f"<p>Bias model: <b>{bm['mode']}</b>. Prior on the residual bias: "
                   + ", ".join(_f(v) for v in bm["prior_sigma_dph"]) + " °/h (1σ)."
                   + (f" Change from pre to post calibration: {', '.join(_f(v) for v in bm['pre_post_change_dph'])} °/h." if "pre_post_change_dph" in bm else "")
                   + "</p>")
    for name, d in (res.get("drift") or {}).items():
        if d and d.get("tau_s"):
            fig, ax = plt.subplots(figsize=(6, 3))
            a = np.array(d["adev_dph"])
            for i, (ax_name, ls) in enumerate(zip("xyz", ("-", "--", ":"))):
                ax.loglog(d["tau_s"], a[:, i], color=INK, ls=ls, lw=1.5, label=ax_name)
            ax.set_xlabel("averaging time τ (s)")
            ax.set_ylabel("Allan deviation (°/h)")
            ax.legend()
            ax.set_title(f"{name}: gyro stability, {d['duration_s'] / 60:.0f} min still", loc="left", fontsize=9)
            out.append(_png(fig))

    # track
    tr = res.get("track")
    if tr:
        out.append("<h2>Flight track and cruise segments</h2>")
        t = np.array(tr["t"])
        t_min = (t - t[0]) / 60
        fig, axs = plt.subplots(1, 3, figsize=(10, 2.8))
        axs[0].plot(tr["lon"], tr["lat"], color=INK, lw=1.5)
        axs[0].set_xlabel("longitude (°)")
        axs[0].set_ylabel("latitude (°)")
        axs[1].plot(t_min, np.array(tr["h"]) / 1000, color=INK, lw=1.5)
        axs[1].set_ylabel("GNSS altitude (km)")
        axs[2].plot(t_min, tr["speed"], color=INK, lw=1.5)
        axs[2].set_ylabel("ground speed (m/s)")
        for a in axs[1:]:
            a.set_xlabel("minutes")
            for s in res.get("segments", []):
                a.axvspan((s["t0_s"] - t[0]) / 60, (s["t1_s"] - t[0]) / 60, color="#2a78d6", alpha=0.12, lw=0)
        fig.tight_layout()
        out.append(_png(fig) + "<p class=sub>Shaded: stable-cruise segments used in the fit.</p>")

    acc = res.get("accumulated")
    if acc:
        out.append("<h2>Measured vs predicted rotation of local level</h2>")
        t = np.array(acc["t"])
        t_min = (t - t[0]) / 60
        meas = np.array(acc["measured_dph"], dtype=float)
        fig, axs = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
        for i, comp in enumerate(("north", "east", "down")):
            ax = axs[i]
            ax.plot(t_min, meas[:, i], "o", color=INK, ms=3, label="measured (60-s bins)")
            for m, p in acc["predicted_dph"].items():
                c, ls = MODEL_STYLE[m]
                ax.plot(t_min, np.array(p)[:, i], color=c, ls=ls, lw=2, label=MODEL_LABELS[m])
            ax.set_ylabel(f"{comp} (°/h)")
        axs[0].legend(ncol=5, loc="lower left", bbox_to_anchor=(0, 1.02), fontsize=8)
        axs[2].set_xlabel("minutes since first cruise bin (turns excluded)")
        fig.tight_layout()
        out.append(_png(fig))
        rows = []
        for s in acc["segments"]:
            r = [s["seg"], _f(s["duration_min"], 1), ", ".join(_f(v) for v in s["measured_deg"])]
            r += [", ".join(_f(v) for v in s[m + "_deg"]) for m in MODEL_LABELS]
            rows.append(r)
        out.append("<h3>Accumulated rotation per segment (N, E, D in degrees)</h3>"
                   + _table(["seg", "min", "measured"] + [MODEL_LABELS[m] for m in MODEL_LABELS], rows))
        out.append("<p class=sub>'Measured' subtracts only the calibrated bias and the aircraft's own motion "
                   "(accelerometer tilt rate, GNSS course rate). No fitted terms are used.</p>")

    out.append("<h2>Raw result</h2><details><summary>JSON</summary><pre style='white-space:pre-wrap;font-size:.75rem'>"
               + html.escape(json.dumps({k: v for k, v in res.items() if k not in ("track", "accumulated")}, indent=1))
               + "</pre></details>")
    return page(f"LLL {title}", "".join(out))


def collation_report(col: dict) -> str:
    g = col.get("ground") or {}
    out = ["<h1>Local Level Lab — collated results</h1>",
           f"<p class=sub>{col['n_sessions']} sessions: {col['n_primary']} in the primary result, "
           f"{col['n_exploratory']} exploratory · {len(g.get('lat', []))} ground calibrations · analysis v{col['analysis_version']}</p>",
           "<p class=sub>Primary sessions pass every gate: both calibrations, at least "
           f"{col['gates']['min_cruise_min']:.0f} min of cruise, curvature identified, not prior-dominated, an IMU unit rated "
           f"{' or '.join(col['gates']['unit_tiers'])}, and not synthetic.</p>"]
    for f in col.get("flags", []):
        out.append(f"<p><span class=flag>{html.escape(f)}</span></p>")
    if col.get("pooled_k"):
        pk = col["pooled_k"]
        out.append("<h2>Pooled scale factors (random effects, REML with Hartung–Knapp: sessions → IMU units → population)</h2>"
                   + _k_figure({n: v["k"] for n, v in pk.items() if v}, {n: v["sd"] for n, v in pk.items() if v}))
        gf = (col.get("ground") or {}).get("fit") or {}
        notes = {"k_curv": "headline: globe curvature (horizontal tilt of local level)",
                 "k_rot_sphere": "globe rotation in flight" + (f"; ground horizontal C = {_f(gf['C_cos'])} ± {_f(gf['C_cos_se'])} °/h (15.04 for a rotating globe)" if gf else ""),
                 "k_disc": "disc transport, from sessions where it was identified (heading-diverse) only"}
        scope = col.get("scope")
        if scope and scope != "population":
            out.append(f"<p><span class=flag>{html.escape(scope)} result</span> Fewer than three IMU units: this describes "
                       "those units, not a population of instruments.</p>")
        out.append(_table(["term", "pooled k", "95 % interval (t)", "units", "sessions", "τ² between units", "heterogeneity p", "note"],
                          [[html.escape(n), f"{_f(pk[n]['k'])} ± {_f(pk[n]['sd'])}", f"{_f(pk[n]['ci95'][0])} … {_f(pk[n]['ci95'][1])}",
                            pk[n]["n_units"], pk[n]["n_sessions"], _f(pk[n]["tau2_units"], 3), f"{pk[n]['p_het_units']:.2g}",
                            html.escape(notes[n])]
                           for n in ("k_curv", "k_rot_sphere", "k_disc") if pk.get(n)]))
        out.append("<p class=sub>Each term is pooled only from sessions where that term was identified on its flight.</p>")
        out.append("<h2>Each model against the pooled scale factors</h2>"
                   + _table(["Model", "χ² (3 dof)", "p", "rejected at 3σ"],
                            [[MODEL_LABELS[m], _f(t["chi2"], 1), f"{t['p']:.2g}", "yes" if t["rejected"] else "no"]
                             for m, t in col["model_tests"].items()]))
    for dim, c in (col.get("consistency") or {}).items():
        rows = [[html.escape(str(gname))] + [f"{_f(p[n]['k'])} ± {_f(p[n]['sd'])}" if p[n] else "–" for n in K_LABELS]
                for gname, p in c["groups"].items()]
        het = ", ".join(f"{n} p={v['p']:.2g}" for n, v in c["heterogeneity"].items())
        out.append(f"<h3>Consistency by {html.escape(dim)}</h3>" + _table([dim, "k rot (globe)", "k curv (globe)", "k disc"], rows)
                   + f"<p class=sub>Between-group heterogeneity: {het}." + (" <b>Groups disagree.</b>" if c["disagreement"] else "") + "</p>")
    if g and g.get("lat"):
        from .calib import ground_model_predictions
        lat = np.array(g["lat"])
        L = np.linspace(-90, 90, 181)
        preds = {m: np.array([ground_model_predictions(x)[m] for x in L]) for m in MODEL_LABELS}
        fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
        for i, (key, lab) in enumerate((("h", "horizontal rotation (°/h)"), ("up", "rotation about local up (°/h)"))):
            ax = axs[i]
            for m, p in preds.items():
                c, ls = MODEL_STYLE[m]
                ax.plot(L, p[:, 1 if key == "h" else 0], color=c, ls=ls, label=MODEL_LABELS[m])
            ax.errorbar(lat, g[key], yerr=g[key + "_sd"], fmt="o", color=INK, ms=4, lw=1, capsize=2, label="calibrations")
            ax.set_xlabel("latitude (°)")
            ax.set_ylabel(lab)
        axs[0].legend(fontsize=7)
        axs[1].set_title("aliased with g-sensitivity", loc="left", fontsize=9)
        fig.tight_layout()
        out.append("<h2>Ground Earth rate vs latitude</h2>" + _png(fig))
        f = g.get("fit")
        if f:
            out.append(f"<p>Horizontal (the clean test, immune to g-sensitivity): h = {_f(f['C_cos'])} ± {_f(f['C_cos_se'])} · |cos φ| °/h. "
                       "A rotating globe gives 15.04; a still globe or a flat disc gives 0.</p>"
                       f"<p class=sub>Vertical: up = {_f(f['A_sin'])} ± {_f(f['A_sin_se'])} · sin φ + an intercept per IMU unit. "
                       + ("" if f["A_identified"] else "No unit has been calibrated at more than one latitude yet, so A rests on the intercepts' assumptions. ")
                       + "Rotation about the plumb line can't be told from a unit's g-sensitivity along it, so each unit gets its own intercept.</p>")
    out.append("<h2>Sessions</h2>" + _table(
        ["session", "kind", "flight", "seat", "mount", "IMU", "tier", "cruise min", "not rejected", "k rot", "k curv", "k disc", "primary?"],
        [[html.escape(str(r["session_id"])[:8]), html.escape(str(r["kind"])), html.escape(r["flight"]), html.escape(str(r["seat"])),
          html.escape(str(r["mount"])), html.escape(str(r["imu_variant"])), html.escape(str(r["unit_tier"])), _f(r["cruise_min"], 0),
          html.escape(", ".join(MODEL_LABELS[m] for m in (r["not_rejected"] or "").split(";") if m) or "–"),
          _f(r["k_rot_sphere"]), _f(r["k_curv"]), _f(r["k_disc"]),
          "yes" if r["primary"] else html.escape(r["excluded_because"])] for r in col["rows"]]))
    return page("LLL collated", "".join(out))
