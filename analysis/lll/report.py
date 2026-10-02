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
    "flat_rotating": ("#1baf7a", "-."),
    "flat_still": ("#eda100", ":"),
}
K_LABELS = {"k_rot_sphere": "Earth rotation\n(globe form)", "k_rot_flat": "Earth rotation\n(flat-disc form)",
            "k_curv": "Curvature\n(transport rate)"}

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
        w = fit["model_weight"]
        out.append("<h2>Result</h2><div class=tiles>"
                   f"<div class=tile><span class=sub>Best-fitting model</span><b>{MODEL_LABELS[fit['best_model']]}</b></div>"
                   f"<div class=tile><span class=sub>Stable cruise analysed</span><b>{res.get('cruise_minutes', 0):.0f} min</b></div>"
                   f"<div class=tile><span class=sub>Noise per 60-s bin</span><b>{fit['sigma_bin_dph']:.1f} °/h</b></div>"
                   "</div>")
        out.append(_table(["Model", "Δχ² vs best", "relative weight", "expected k (rot globe, rot flat, curv)"],
                          [[MODEL_LABELS[m], _f(fit["delta_chi2"][m], 1), _f(w[m], 3), str(tuple(fit["expected_k"][m]))]
                           for m in MODEL_LABELS]))
        out.append("<h3>Separate scale factors</h3>" + _k_figure(fit["k"], fit["k_sd"]))
        out.append(f"<p class=sub>Fit mode: {fit['mode']}. The largest |correlation| between the residual bias and any k "
                   f"is {fit['max_bias_k_corr']:.2f}. Values near 1 mean the data can't tell bias from signal, and more turns "
                   "or better calibration would help. Residual bias: "
                   + ", ".join(f"{v:.2f}" for v in fit["bias_residual_dph"]) + " °/h.</p>")

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
    out = ["<h1>Local Level Lab — collated results</h1>",
           f"<p class=sub>{col['n_sessions']} sessions, {col['n_with_fit']} with an in-flight fit, "
           f"{col['n_cal']} ground calibrations · analysis v{col['analysis_version']}</p>"]
    if col.get("pooled_k"):
        pk = col["pooled_k"]
        out.append("<h2>Pooled scale factors (inverse-variance)</h2>"
                   + _k_figure({n: v["k"] for n, v in pk.items()}, {n: v["sd"] for n, v in pk.items()}))
        out.append("<h2>Pooled model comparison (Σχ² over sessions)</h2>"
                   + _table(["Model", "Σ Δχ² vs best", "sessions where best"],
                            [[MODEL_LABELS[m], _f(col["pooled_delta_chi2"][m], 1), col["best_counts"].get(m, 0)]
                             for m in MODEL_LABELS]))
    for dim, groups in col.get("breakdowns", {}).items():
        rows = [[html.escape(str(g)), v["n"]] + [f"{_f(v['k'][n])} ± {_f(v['sd'][n])}" for n in K_LABELS]
                for g, v in groups.items()]
        out.append(f"<h3>By {dim}</h3>" + _table([dim, "n", "k rot (globe)", "k rot (flat)", "k curv"], rows))
    g = col.get("ground")
    if g and g["lat"]:
        from .calib import ground_model_predictions
        lat = np.array(g["lat"])
        L = np.linspace(-90, 90, 181)
        preds = {m: np.array([ground_model_predictions(x)[m] for x in L]) for m in MODEL_LABELS}
        fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
        for i, (key, lab) in enumerate((("up", "rotation about local up (°/h)"), ("h", "horizontal rotation (°/h)"))):
            ax = axs[i]
            for m, p in preds.items():
                c, ls = MODEL_STYLE[m]
                ax.plot(L, p[:, i], color=c, ls=ls, label=MODEL_LABELS[m])
            ax.errorbar(lat, g[key], yerr=g[key + "_sd"], fmt="o", color=INK, ms=4, lw=1, capsize=2, label="calibrations")
            ax.set_xlabel("latitude (°)")
            ax.set_ylabel(lab)
        axs[0].legend(fontsize=7)
        fig.tight_layout()
        out.append("<h2>Ground Earth-rate vs latitude (all calibrations)</h2>" + _png(fig))
        if g.get("fit"):
            f = g["fit"]
            out.append(f"<p>Least-squares fit: up = {_f(f['A_sin'])}·sin φ + {_f(f['B_const'])} °/h; horizontal = "
                       f"{_f(f['C_cos'])}·|cos φ| °/h. A globe rotating once a sidereal day gives A = C = 15.04, B = 0. "
                       "A rotating flat disc gives A = C = 0, B = 15.04. A still Earth of either shape gives all zero.</p>")
    out.append("<h2>Per-session results</h2>" + _table(
        ["session", "flight", "mount", "device", "cruise min", "best model", "k rot", "k curv"],
        [[html.escape(str(r["session_id"])[:8]), html.escape(r["flight"]), html.escape(str(r["mount"])),
          html.escape(str(r["device"])), _f(r["cruise_min"], 0), MODEL_LABELS.get(r["best_model"], "–"),
          _f(r["k_rot_sphere"]), _f(r["k_curv"])] for r in col["rows"]]))
    return page("LLL collated", "".join(out))
