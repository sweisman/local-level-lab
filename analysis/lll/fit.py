# SPDX-License-Identifier: AGPL-3.0-or-later
"""In-flight fit of measured gyro rates against the model terms.

For each bin, in the phone frame:

    y = m - b_cal(t) - omega_nb
      = b_res + C_bn (k_rot * E_sphere + k_rotflat * E_flat + k_curv * T) + noise

- m is the raw gyro mean and b_cal the calibrated bias.
- omega_nb is the aircraft's own rotation relative to local level. That's the tilt rate from the
  accelerometer, plus the GNSS course rate about the vertical.
- b_res is the residual bias, held near zero by a prior whose width comes from how much the bias
  drifted between calibrations.

There are two outputs. One is the free scale factors k, with confidence intervals. The other is a
chi-squared comparison of the four models with their k values fixed.
"""
from __future__ import annotations

import numpy as np

from . import models
from .attitude import c_bn
from .calib import RAD2DPH

TERM_NAMES = ("k_rot_sphere", "k_rot_flat", "k_curv")


def build_rows(bins, fwd_b, bias_fn, vertical_only=False, temp_ref=None):
    """Returns y (n,), X (n, 6 or 9), bin index per row, and per-bin C_bn matrices.

    Columns: residual bias (3), k terms (3), and, when temp_ref is given, bias change per °C (3)
    multiplied by (battery temperature − temp_ref)."""
    es, ef, tr = models.terms(bins["lat"], bins["h"], bins["v_n"], bins["v_e"])
    ys, xs, idx, cbns = [], [], [], []
    for j in range(len(bins["t"])):
        u = bins["up"][j]
        d_b = -u
        # aircraft rotation relative to local level, phone frame
        w_nb = np.cross(bins["dup_dt"][j], u) + bins["psi_dot"][j] * d_b
        y = bins["gyro"][j] - bias_fn(bins["t"][j]) - w_nb
        dT = (bins["temp"][j] - temp_ref) if temp_ref is not None else None
        if vertical_only:
            X = np.concatenate([d_b, [es[j][2], ef[j][2], tr[j][2]]] + ([d_b * dT] if dT is not None else []))
            ys.append(y @ d_b)
            xs.append(X)
            idx.append(j)
            cbns.append(None)
            continue
        C = c_bn(u, fwd_b, bins["psi"][j])
        X = np.hstack([np.eye(3), np.column_stack([C @ es[j], C @ ef[j], C @ tr[j]])]
                      + ([np.eye(3) * dT] if dT is not None else []))
        ys.extend(y)
        xs.extend(X)
        idx.extend([j] * 3)
        cbns.append(C)
    return np.array(ys), np.array(xs), np.array(idx), cbns


def _solve(y, X, w, prior, fixed_k=None):
    """Weighted least squares with zero-mean Gaussian priors (prior[i] = 1σ for column i, inf = no
    prior). Returns theta, cov, chi2. With fixed_k the three k columns are held at those values."""
    sw = np.sqrt(w)
    prior = np.asarray(prior, dtype=float)
    if fixed_k is not None:
        y = y - X[:, 3:6] @ np.asarray(fixed_k)
        keep = [i for i in range(X.shape[1]) if not 3 <= i < 6]
        X, prior = X[:, keep], prior[keep]
    p = X.shape[1]
    idx = np.where(np.isfinite(prior))[0]
    P = np.zeros((len(idx), p))
    P[np.arange(len(idx)), idx] = 1.0 / prior[idx]
    A = np.vstack([X * sw[:, None], P])
    b = np.concatenate([y * sw, np.zeros(len(idx))])
    theta, *_ = np.linalg.lstsq(A, b, rcond=None)
    r = b - A @ theta
    cov = np.linalg.pinv(A.T @ A)
    return theta, cov, float(r @ r)


def fit(bins, fwd_b, bias_fn, prior_sigma, vertical_only=False, n_boot=300, seed=0,
        temp_ref=None, temp_prior=None):
    y, X, idx, cbns = build_rows(bins, fwd_b, bias_fn, vertical_only, temp_ref)
    if temp_ref is not None and temp_prior is None:
        temp_prior = np.inf  # temperature term with no prior
    prior = np.concatenate([np.asarray(prior_sigma, dtype=float), np.full(3, np.inf)]
                           + ([np.broadcast_to(np.asarray(temp_prior, dtype=float), (3,))] if temp_ref is not None else []))
    prior_sigma = prior
    n_bins = len(bins["t"])
    # pass 1: rough sigma; pass 2: sigma = residual RMS (bias instability included)
    w = np.full(len(y), 1.0 / (3.0 / RAD2DPH) ** 2)
    theta, _, _ = _solve(y, X, w, prior_sigma)
    resid = y - X @ theta
    sigma = max(float(np.sqrt(np.mean(resid ** 2))), 1e-9)
    w = np.full(len(y), 1.0 / sigma ** 2)
    theta, cov, chi2 = _solve(y, X, w, prior_sigma)
    k, k_sd = theta[3:6], np.sqrt(np.diag(cov)[3:6])

    # moving-block bootstrap over bins, since bias wander makes neighbouring bins correlated
    rng = np.random.default_rng(seed)
    fitted = X @ theta
    resid = y - fitted
    blk = max(2, min(10, n_bins // 5))
    boots = []
    if n_bins >= 2 * blk:
        starts = np.arange(n_bins - blk + 1)
        for _ in range(n_boot):
            order = np.concatenate([np.arange(s, s + blk) for s in rng.choice(starts, n_bins // blk + 1)])[:n_bins]
            rb = np.concatenate([resid[idx == j] for j in order])
            yb = fitted + rb[:len(fitted)] if len(rb) >= len(fitted) else fitted
            tb, _, _ = _solve(yb, X, w, prior_sigma)
            boots.append(tb[3:6])
    k_sd_boot = np.std(boots, axis=0) if boots else np.full(3, np.nan)
    k_sd_final = np.fmax(k_sd, np.nan_to_num(k_sd_boot))

    corr = cov / np.sqrt(np.outer(np.diag(cov), np.diag(cov)))
    comparison = {}
    for name, kk in models.EXPECTED_K.items():
        _, _, c2 = _solve(y, X, w, prior_sigma, fixed_k=kk)
        comparison[name] = c2
    best = min(comparison.values())
    rel = {n: float(np.exp(-(c - best) / 2)) for n, c in comparison.items()}
    tot = sum(rel.values())
    return {
        "mode": "vertical_only" if vertical_only else "3-axis",
        "n_bins": n_bins, "n_rows": len(y),
        "sigma_bin_dph": sigma * RAD2DPH,
        "k": dict(zip(TERM_NAMES, k.tolist())),
        "k_sd": dict(zip(TERM_NAMES, k_sd_final.tolist())),
        "k_sd_analytic": dict(zip(TERM_NAMES, k_sd.tolist())),
        "bias_residual_dph": (theta[:3] * RAD2DPH).tolist(),
        "max_bias_k_corr": float(np.max(np.abs(np.delete(corr[3:6], [3, 4, 5], axis=1)))),
        "temp_coef_dph_per_c": (theta[6:] * RAD2DPH).tolist() if temp_ref is not None else None,
        "chi2": {n: float(c) for n, c in comparison.items()},
        "delta_chi2": {n: float(c - best) for n, c in comparison.items()},
        "model_weight": {n: v / tot for n, v in rel.items()},
        "best_model": min(comparison, key=comparison.get),
        "_rows": (y, X, idx, cbns, theta),
    }


def accumulated(bins, cbns, y_rows, idx, vertical_only=False):
    """Measured rotation of local level in NED, accumulated per segment (deg), next to each
    model's prediction. Measured = C_nb (m - b_cal - omega_nb); no fitted terms are used."""
    n = len(bins["t"])
    meas = np.zeros((n, 3))
    for j in range(n):
        if vertical_only:
            meas[j] = [np.nan, np.nan, y_rows[idx == j][0]]
        else:
            meas[j] = cbns[j].T @ y_rows[idx == j]
    out = {"t": bins["t"].tolist(), "seg": bins["seg"].tolist(), "measured_dph": (meas * RAD2DPH).tolist()}
    pred = {}
    for m in models.MODELS:
        pred[m] = models.predict(m, bins["lat"], bins["h"], bins["v_n"], bins["v_e"])
    out["predicted_dph"] = {m: (p * RAD2DPH).tolist() for m, p in pred.items()}
    segs = []
    for s in np.unique(bins["seg"]):
        sel = bins["seg"] == s
        dt = bins["dt"][sel][:, None]
        rec = {"seg": int(s), "duration_min": float(dt.sum() / 60),
               "measured_deg": np.degrees((meas[sel] * dt).sum(axis=0)).tolist()}
        for m, p in pred.items():
            rec[m + "_deg"] = np.degrees((p[sel] * dt).sum(axis=0)).tolist()
        segs.append(rec)
    out["segments"] = segs
    return out
