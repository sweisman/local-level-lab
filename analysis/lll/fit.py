# SPDX-License-Identifier: AGPL-3.0-or-later
"""In-flight fit of measured gyro rates against the model terms.

For each bin, in the IMU frame:

    y = m − b_cal(t) − ω_nb
      = C_bn (k_rot·E_sphere + k_curv·T + k_disc·T_disc) + b_res[g] + noise

- m is the raw gyro mean and b_cal the calibrated bias, interpolated between calibrations.
- ω_nb is the aircraft's own rotation relative to local level: the tilt rate from the
  accelerometer, plus the GNSS course rate about the vertical.
- b_res[g] is the residual bias for gravity orientation g. Gyro error that depends on gravity
  (g-sensitivity) is a constant while the IMU's attitude is fixed, but it changes when the IMU is
  flipped. So each orientation gets its own residual bias. Turns that keep gravity on the same
  sensor axis share one, and those are the turns that separate signal from bias.
- The residual-bias prior is wide on purpose (drift.bias_model): it covers the pre/post change,
  g-sensitivity and vibration rectification, none of which the ground calibration sees.

Outputs:
- the free scale factors k, with confidence intervals (the larger of analytic and moving-block
  bootstrap);
- an identifiability check: how strongly k is tied to the residual bias with no prior at all;
- a prior-sensitivity check: how far k moves when the bias prior is widened 3×;
- a test of each model against the free fit. χ² is scaled by an effective-sample factor from the
  residual autocorrelation, and Δχ² against the free fit is χ² with 3 degrees of freedom under
  that model. A model is rejected at p < 0.0027 (3σ). Relative likelihoods are reported too, but
  they are not probabilities.
"""
from __future__ import annotations

import numpy as np

from . import models
from .attitude import c_bn
from .calib import RAD2DPH

TERM_NAMES = ("k_rot_sphere", "k_curv", "k_disc")
NK = len(TERM_NAMES)
K = slice(0, NK)                # the k terms are always the first columns
P_REJECT = 0.0027               # two-sided 3σ
CORR_NOT_IDENTIFIED = 0.95
PRIOR_WIDEN = 3.0


def sf_chi2(x, dof=NK):
    """Survival function of χ² with 3 or 4 degrees of freedom (closed forms)."""
    from math import erfc, exp, pi, sqrt
    x = max(float(x), 0.0)
    if dof == 3:
        return erfc(sqrt(x / 2)) + sqrt(2 * x / pi) * exp(-x / 2)
    if dof == 4:
        return exp(-x / 2) * (1 + x / 2)
    raise ValueError(dof)


def build_rows(bins, fwd_b, bias_fn, vertical_only=False, temp_ref=None, temp_mean=None):
    """Returns y (n,), X (n, p), bin index per row, per-bin C_bn matrices, and the column layout.

    Columns: k terms (3), residual bias (3 per gravity orientation), and, when temp_ref is given,
    bias change per °C (3) multiplied by (IMU chip temperature − temp_ref). temp_mean, when known
    from a drift run, is subtracted first, so the fitted coefficient is the residual around it."""
    es, tr, td = models.terms(bins["lat"], bins["h"], bins["v_n"], bins["v_e"])
    grav = np.asarray(bins.get("grav", np.zeros(len(bins["t"]), int)), int)
    ng = int(grav.max()) + 1
    nb = NK + 3 * ng
    p = nb + (3 if temp_ref is not None else 0)
    ys, xs, idx, cbns = [], [], [], []
    for j in range(len(bins["t"])):
        u = bins["up"][j]
        d_b = -u
        # aircraft rotation relative to local level, IMU frame
        w_nb = np.cross(bins["dup_dt"][j], u) + bins["psi_dot"][j] * d_b
        dT = (bins["temp"][j] - temp_ref) if temp_ref is not None else None
        y = bins["gyro"][j] - bias_fn(bins["t"][j]) - w_nb
        if dT is not None and temp_mean is not None:
            y = y - np.asarray(temp_mean) * dT
        g0 = NK + 3 * grav[j]
        if vertical_only:
            X = np.zeros(p)
            X[:NK] = [es[j][2], tr[j][2], td[j][2]]
            X[g0:g0 + 3] = d_b
            if dT is not None:
                X[nb:] = d_b * dT
            ys.append(y @ d_b); xs.append(X); idx.append(j); cbns.append(None)
            continue
        C = c_bn(u, fwd_b if np.ndim(fwd_b) == 1 else fwd_b[j], bins["psi"][j])
        X = np.zeros((3, p))
        X[:, :NK] = np.column_stack([C @ es[j], C @ tr[j], C @ td[j]])
        X[:, g0:g0 + 3] = np.eye(3)
        if dT is not None:
            X[:, nb:] = np.eye(3) * dT
        ys.extend(y); xs.extend(X); idx.extend([j] * 3); cbns.append(C)
    layout = {"n_grav": ng, "bias": slice(NK, nb), "temp": slice(nb, p) if temp_ref is not None else None}
    return np.array(ys), np.array(xs), np.array(idx), cbns, layout


def _solve(y, X, w, prior, fixed_k=None):
    """Weighted least squares with zero-mean Gaussian priors (prior[i] = 1σ for column i, inf = no
    prior). Returns theta, cov, chi2. With fixed_k the k columns are held at those values."""
    sw = np.sqrt(w)
    prior = np.asarray(prior, dtype=float)
    if fixed_k is not None:
        y = y - X[:, K] @ np.asarray(fixed_k)
        keep = [i for i in range(X.shape[1]) if not K.start <= i < K.stop]
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


def _autocorr_scale(resid, idx, bins):
    """Effective-sample factor for χ² from the lag-1 autocorrelation of per-bin residuals within
    segments (AR(1): n_eff / n = (1 − ρ) / (1 + ρ)). Returns (scale, ρ)."""
    n = len(bins["t"])
    r = np.array([np.mean(resid[idx == j]) for j in range(n)])
    seg = np.asarray(bins["seg"])
    num, den = 0.0, float(np.sum((r - r.mean()) ** 2)) or 1.0
    for s in np.unique(seg):
        x = r[seg == s] - r.mean()
        num += float(np.sum(x[1:] * x[:-1]))
    rho = float(np.clip(num / den, 0.0, 0.95))
    return (1 - rho) / (1 + rho), rho


def fit(bins, fwd_b, bias_fn, prior_sigma, vertical_only=False, n_boot=300, seed=0,
        temp_ref=None, temp_prior=None, temp_mean=None):
    y, X, idx, cbns, lay = build_rows(bins, fwd_b, bias_fn, vertical_only, temp_ref, temp_mean)
    ng = lay["n_grav"]
    if temp_ref is not None and temp_prior is None:
        temp_prior = np.inf  # temperature term with no prior
    bias_prior = np.tile(np.asarray(prior_sigma, dtype=float), ng)

    def priors(bias_scale=1.0, bias_free=False):
        bp = np.full(3 * ng, np.inf) if bias_free else bias_prior * bias_scale
        return np.concatenate([np.full(NK, np.inf), bp]
                              + ([np.broadcast_to(np.asarray(temp_prior, dtype=float), (3,))] if temp_ref is not None else []))

    prior = priors()
    n_bins = len(bins["t"])
    # pass 1: rough sigma; pass 2: sigma = residual RMS (bias instability included)
    w = np.full(len(y), 1.0 / (3.0 / RAD2DPH) ** 2)
    theta, _, _ = _solve(y, X, w, prior)
    resid = y - X @ theta
    sigma = max(float(np.sqrt(np.mean(resid ** 2))), 1e-9)
    w = np.full(len(y), 1.0 / sigma ** 2)
    theta, cov, chi2_free = _solve(y, X, w, prior)
    k, k_sd = theta[K], np.sqrt(np.diag(cov)[K])
    resid = y - X @ theta
    scale, rho = _autocorr_scale(resid, idx, bins)

    def compare(yy):
        c = {name: _solve(yy, X, w, prior, fixed_k=kk)[2] for name, kk in models.EXPECTED_K.items()}
        return c

    comparison = compare(y)

    # moving-block bootstrap over bins, since bias wander makes neighbouring bins correlated
    rng = np.random.default_rng(seed)
    fitted = X @ theta
    blk = max(2, min(10, n_bins // 5))
    boots, boot_dchi = [], []
    if n_boot and n_bins >= 2 * blk:
        starts = np.arange(n_bins - blk + 1)
        for _ in range(n_boot):
            order = np.concatenate([np.arange(s, s + blk) for s in rng.choice(starts, n_bins // blk + 1)])[:n_bins]
            rb = np.concatenate([resid[idx == j] for j in order])
            yb = fitted + rb[:len(fitted)] if len(rb) >= len(fitted) else fitted
            tb, _, _ = _solve(yb, X, w, prior)
            boots.append(tb[K])
            if len(boot_dchi) < 100:
                cb = compare(yb)
                lo = min(cb.values())
                boot_dchi.append({m: (v - lo) * scale for m, v in cb.items()})
    k_sd_boot = np.std(boots, axis=0) if boots else np.full(NK, np.nan)
    k_sd_final = np.fmax(k_sd, np.nan_to_num(k_sd_boot))

    # Identifiability: how much of each term's predicted signal a constant residual bias (one per
    # gravity orientation) could mimic. 1 means indistinguishable from bias by the flight data
    # alone; then only the bias prior (the ground calibration) constrains that term. A constant
    # rotation about the vertical is always 1 in level flight: it lies along gravity, exactly like
    # gyro bias and g-sensitivity on that axis.
    B = X[:, lay["bias"]]
    tie_k = {}
    for i, n in enumerate(TERM_NAMES):
        xi = X[:, i]
        e = float(xi @ xi)
        if e == 0:
            tie_k[n] = 1.0
            continue
        beta, *_ = np.linalg.lstsq(B, xi, rcond=None)
        r = xi - B @ beta
        tie_k[n] = float(np.sqrt(max(0.0, 1 - (r @ r) / e)))
    tie = tie_k["k_curv"]
    # prior sensitivity: widen the bias prior and see how far k moves
    tw, _, _ = _solve(y, X, w, priors(bias_scale=PRIOR_WIDEN))
    shift = (tw[K] - k) / k_sd_final

    corr = cov / np.sqrt(np.outer(np.diag(cov), np.diag(cov)))
    best = min(comparison.values())
    d_best = {n: (c - best) * scale for n, c in comparison.items()}
    d_free = {n: max(c - chi2_free, 0.0) * scale for n, c in comparison.items()}
    p_free = {n: float(sf_chi2(v)) for n, v in d_free.items()}
    rel = {n: float(np.exp(-v / 2)) for n, v in d_best.items()}
    tot = sum(rel.values())
    ci = None
    if boot_dchi:
        ci = {m: [float(np.percentile([b[m] for b in boot_dchi], q)) for q in (16, 84)] for m in comparison}
    return {
        "mode": "vertical_only" if vertical_only else "3-axis",
        "n_bins": n_bins, "n_rows": len(y),
        "sigma_bin_dph": sigma * RAD2DPH,
        "k": dict(zip(TERM_NAMES, k.tolist())),
        "k_sd": dict(zip(TERM_NAMES, k_sd_final.tolist())),
        "k_sd_analytic": dict(zip(TERM_NAMES, k_sd.tolist())),
        "gravity_orientations": ng,
        "bias_residual_dph": (theta[lay["bias"]].reshape(ng, 3) * RAD2DPH).tolist(),
        "max_bias_k_corr": float(np.max(np.abs(corr[K, lay["bias"]]))),
        "identifiability": {"k_curv_bias_likeness": tie, "bias_likeness_by_term": tie_k,
                            "identified_by_term": {n: v < CORR_NOT_IDENTIFIED for n, v in tie_k.items()},
                            "identified": tie < CORR_NOT_IDENTIFIED,
                            "note": "fraction of each term's signal a constant bias per gravity orientation could mimic"},
        "prior_sensitivity": {"widen": PRIOR_WIDEN, "k_shift_sigma": dict(zip(TERM_NAMES, shift.tolist())),
                              "prior_dominated": bool(np.max(np.abs(shift)) > 1.0)},
        "temp_coef_dph_per_c": ((theta[lay["temp"]] + (np.asarray(temp_mean) if temp_mean is not None else 0)) * RAD2DPH).tolist()
        if temp_ref is not None else None,
        "chi2_scaling": {"rho_lag1": rho, "scale": scale},
        "chi2": {n: float(c) for n, c in comparison.items()},
        "chi2_free": float(chi2_free),
        "delta_chi2": d_best,
        "delta_chi2_ci_16_84": ci,
        "delta_chi2_vs_free": d_free,
        "p_vs_free": p_free,
        "rejected": {n: p < P_REJECT for n, p in p_free.items()},
        "relative_likelihood": {n: v / tot for n, v in rel.items()},
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
