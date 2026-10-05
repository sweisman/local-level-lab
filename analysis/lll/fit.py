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
- an identifiability check: how much of each term the nuisance terms together (residual bias,
  temperature, crab) could mimic with no priors at all;
- a prior-sensitivity check: how far k moves when the bias, crab or temperature prior is widened
  3×, and a sweep of the crab prior;
- the joint covariance of k, for pooling;
- a test of each model against the free fit. χ² is scaled by an effective-sample factor from the
  residual autocorrelation, and Δχ² against the free fit is χ² with 3 degrees of freedom under
  that model. A model is rejected at p < 0.0027, the nominal 3σ threshold (its real tail rate is
  checked by simulation, not assumed). Relative likelihoods are reported too, but
  they are not probabilities.
"""
from __future__ import annotations

import numpy as np

from . import models
from .attitude import c_bn
from .calib import RAD2DPH
from .inference_policy import INFERENCE_POLICY, provenance

TERM_NAMES = ("k_rot_sphere", "k_curv", "k_disc")
NK = len(TERM_NAMES)
K = slice(0, NK)                # the k terms are always the first columns
P_REJECT = 0.0027               # two-sided 3σ
CORR_NOT_IDENTIFIED = 0.95
PRIOR_WIDEN = 3.0
CRAB_SWEEP_DEG = (3.0, 5.0, 10.0, 15.0)   # crab priors refitted for the sensitivity sweep
K_SYS_FLOOR = INFERENCE_POLICY["k_sys_floor"]  # compatibility alias; provenance lives in policy


def sf_chi2(x, dof=NK):
    """Survival function of χ² with dof degrees of freedom."""
    from scipy.stats import chi2
    return float(chi2.sf(max(float(x), 0.0), dof))


def build_rows(bins, fwd_b, bias_fn, vertical_only=False, temp_ref=None, temp_mean=None, dpsi=None):
    """Returns y (n,), X (n, p), bin index per row, per-bin C_bn matrices, and the column layout.

    Columns: k terms (3), residual bias (3 per gravity orientation), and, when temp_ref is given,
    bias change per °C (3) multiplied by (IMU chip temperature − temp_ref). temp_mean, when known
    from a drift run, is subtracted first, so the fitted coefficient is the residual around it.
    dpsi (rad, per bin) is the aircraft heading minus its GNSS course (crab)."""
    es, tr, td = models.terms(bins["lat"], bins["h"], bins["v_n"], bins["v_e"], bins.get("lon_rate"))
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
        C = c_bn(u, fwd_b if np.ndim(fwd_b) == 1 else fwd_b[j], bins["psi"][j] + (dpsi[j] if dpsi is not None else 0.0))
        X = np.zeros((3, p))
        X[:, :NK] = np.column_stack([C @ es[j], C @ tr[j], C @ td[j]])
        X[:, g0:g0 + 3] = np.eye(3)
        if dT is not None:
            X[:, nb:] = np.eye(3) * dT
        ys.extend(y); xs.extend(X); idx.extend([j] * 3); cbns.append(C)
    layout = {"n_grav": ng, "bias": slice(NK, nb), "temp": slice(nb, p) if temp_ref is not None else None,
              "terms": (es, tr, td)}
    return np.array(ys), np.array(xs), np.array(idx), cbns, layout


def _solve(y, X, w, prior, fixed_k=None, prior_mean=None):
    """Weighted least squares with zero-mean Gaussian priors (prior[i] = 1σ for column i, inf = no
    prior). Returns theta, cov, chi2. With fixed_k the k columns are held at those values."""
    sw = np.sqrt(w)
    prior = np.asarray(prior, dtype=float)
    mean = np.zeros(len(prior)) if prior_mean is None else np.asarray(prior_mean)
    if fixed_k is not None:
        y = y - X[:, K] @ np.asarray(fixed_k)
        keep = [i for i in range(X.shape[1]) if not K.start <= i < K.stop]
        X, prior = X[:, keep], prior[keep]
        mean = mean[keep]
    p = X.shape[1]
    idx = np.where(np.isfinite(prior))[0]
    P = np.zeros((len(idx), p))
    P[np.arange(len(idx)), idx] = 1.0 / prior[idx]
    A = np.vstack([X * sw[:, None], P])
    b = np.concatenate([y * sw, mean[idx] / prior[idx]])
    theta, *_ = np.linalg.lstsq(A, b, rcond=None)
    r = b - A @ theta
    cov = np.linalg.pinv(A.T @ A)
    return theta, cov, float(r @ r)


def _autocorr_scale(resid, idx, bins):
    """Effective-sample factor for χ² from the lag-1 autocorrelation of per-bin residuals within
    segments (AR(1): n_eff / n = (1 − ρ) / (1 + ρ)). Each gyro axis is taken separately, since an
    average over axes can cancel axis-specific correlation, and the largest ρ is used. Returns
    (scale, ρ)."""
    n = len(bins["t"])
    seg = np.asarray(bins["seg"])
    per_bin = [resid[idx == j] for j in range(n)]
    n_ax = min(len(r) for r in per_bin) if per_bin else 0
    rho = 0.0
    for a in range(n_ax):
        r = np.array([p[a] for p in per_bin])
        num, den = 0.0, float(np.sum((r - r.mean()) ** 2)) or 1.0
        for s in np.unique(seg):
            x = r[seg == s] - r.mean()
            num += float(np.sum(x[1:] * x[:-1]))
        rho = max(rho, num / den)
    rho = float(np.clip(rho, 0.0, 0.95))
    return (1 - rho) / (1 + rho), rho


def _crab_columns(cbns, lay, idx, k, seg_index, n_seg):
    """∂(predicted IMU-frame rate)/∂δψ for each segment's crab angle. The azimuth derivative of
    C_bn maps a NED vector v to C_bn (v_E, −v_N, 0)."""
    es, tr, td = lay["terms"]
    J = np.zeros((len(idx), n_seg))
    for j, C in enumerate(cbns):
        v = k[0] * es[j] + k[1] * tr[j] + k[2] * td[j]
        rows = np.where(idx == j)[0]
        J[rows, seg_index[j]] = C @ np.array([v[1], -v[0], 0.0])
    return J


def bootstrap_order(rng, bins, length, sampling="moving"):
    """Residual blocks; experimental segment sampling never crosses a break in time or segment."""
    n = len(bins["t"])
    if sampling == "moving":
        starts = np.arange(n - length + 1)
        return np.concatenate([np.arange(s, s + length) for s in rng.choice(starts, n // length + 1)])[:n]
    if sampling != "segment":
        raise ValueError("bootstrap_sampling must be moving or segment")
    t, seg = np.asarray(bins["t"]), np.asarray(bins["seg"])
    breaks = np.flatnonzero((np.diff(seg) != 0) | (np.diff(t) > 1.5 * np.asarray(bins["dt"])[:-1])) + 1
    order = np.arange(n)
    for run in np.split(np.arange(n), breaks):
        size = min(length, len(run))
        starts = rng.integers(0, len(run) - size + 1, len(run) // size + 1)
        order[run] = np.concatenate([run[s:s + size] for s in starts])[:len(run)]
    return order


def _legacy_fit(bins, fwd_b, bias_fn, prior_sigma, vertical_only=False, n_boot=300, seed=0,
        temp_ref=None, temp_prior=None, temp_mean=None, crab_sigma_deg=5.0,
        bootstrap_sampling="moving", block_length=None, max_nfev=200):
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

    # Crab: the aircraft's heading differs from its GNSS course by a few degrees in a crosswind. Each
    # cruise segment gets a heading offset with a Gaussian prior, fitted by alternating with the
    # linear fit, then linearized into the design so k's uncertainty includes it. Each model's test
    # refits its own offsets, so none is favoured. (No effect on the vertical-only fallback.)
    # Crab comes from the wind on a leg, so segments on the same GNSS course (within 10°) share one
    # offset; a turn of the IMU splits segments but doesn't change the aircraft's crab.
    seg_ids = np.unique(bins["seg"])
    course = [np.angle(np.mean(np.exp(1j * bins["psi"][bins["seg"] == sg]))) for sg in seg_ids]
    group, ref = [], []
    for c in course:
        for gi, r in enumerate(ref):
            if abs(np.angle(np.exp(1j * (c - r)))) < np.radians(10):
                group.append(gi)
                break
        else:
            ref.append(c)
            group.append(len(ref) - 1)
    seg_index = np.array(group)[np.searchsorted(seg_ids, bins["seg"])]
    n_seg = len(ref)
    use_crab = (not vertical_only) and crab_sigma_deg and crab_sigma_deg > 0
    sig_crab = np.radians(crab_sigma_deg) if use_crab else None

    convergence = []
    base_X = X
    base_prior = prior.copy()

    def solve_with_crab(fixed_k=None, pri=None, sig=None):
        from scipy.optimize import least_squares
        pri = base_prior if pri is None else pri
        sig = sig_crab if sig is None else sig
        if not use_crab:
            th, cv, c2 = _solve(y, base_X, w, pri, fixed_k)
            return th, cv, c2, base_X, np.zeros(0), pri
        keep = np.arange(base_X.shape[1]) if fixed_k is None else np.arange(NK, base_X.shape[1])
        start = _solve(y, base_X, w, pri, fixed_k)[0]
        finite = np.flatnonzero(np.isfinite(pri[keep]))
        sw = np.sqrt(w)

        def evaluate(z, jac=False):
            d = z[len(keep):]
            _, design, ix, cb, layout = build_rows(
                bins, fwd_b, bias_fn, vertical_only, temp_ref, temp_mean, dpsi=d[seg_index])
            full = z[:len(keep)] if fixed_k is None else np.r_[fixed_k, z[:len(keep)]]
            if not jac:
                return np.r_[(design @ full - y) * sw,
                             full[keep[finite]] / pri[keep[finite]], d / sig]
            J = _crab_columns(cb, layout, ix, full[K], seg_index, n_seg)
            top = np.column_stack([design[:, keep], J]) * sw[:, None]
            bottom = np.zeros((len(finite) + n_seg, len(z)))
            bottom[np.arange(len(finite)), finite] = 1 / pri[keep[finite]]
            bottom[len(finite):, len(keep):] = np.eye(n_seg) / sig
            return np.vstack([top, bottom])

        opt = least_squares(evaluate, np.r_[start, np.zeros(n_seg)],
                            jac=lambda z: evaluate(z, True), x_scale="jac",
                            ftol=1e-10, xtol=1e-10, gtol=1e-8, max_nfev=max_nfev)
        convergence.append({"converged": bool(opt.success), "evaluations": opt.nfev,
                            "status": int(opt.status), "message": opt.message})
        d = opt.x[len(keep):]
        _, design, ix, cb, layout = build_rows(
            bins, fwd_b, bias_fn, vertical_only, temp_ref, temp_mean, dpsi=d[seg_index])
        full = opt.x[:len(keep)] if fixed_k is None else np.r_[fixed_k, opt.x[:len(keep)]]
        J = _crab_columns(cb, layout, ix, full[K], seg_index, n_seg)
        Xa = np.column_stack([design, J])
        pa = np.r_[pri, np.full(n_seg, sig)]
        # Local coordinates are increments about d. Their prior mean is -d.
        mean = np.r_[np.zeros(len(pri)), -d]
        _, cv, _ = _solve(y, Xa, w, pa, fixed_k, prior_mean=mean)
        th = np.r_[opt.x[:len(keep)], np.zeros(n_seg)]
        return th, cv, float(opt.fun @ opt.fun), Xa, d, pa

    theta, cov, chi2_free, X_free, crab_d, prior_aug = solve_with_crab()
    prior_mean = np.r_[np.zeros(len(base_prior)), -crab_d] if use_crab else np.zeros(len(base_prior))
    k, k_sd = theta[K], np.sqrt(np.diag(cov)[K])
    resid = y - X_free @ theta
    scale, rho = _autocorr_scale(resid, idx, bins)
    model_designs = {}

    def compare(yy):
        out = {}
        for name, kk in models.EXPECTED_K.items():
            if yy is y:
                th_m, _, c2, Xm, dm, pm = solve_with_crab(fixed_k=kk)
                model_designs[name] = (Xm, pm, np.r_[np.zeros(len(base_prior)), -dm] if use_crab else np.zeros(len(base_prior)))
                out[name] = c2
            else:    # bootstrap replicates reuse each model's crab offsets
                Xm, pm, mean = model_designs[name]
                out[name] = _solve(yy, Xm, w, pm, fixed_k=kk, prior_mean=mean)[2]
        return out

    comparison = compare(y)
    X = X_free
    if use_crab:
        prior = prior_aug

    # moving-block bootstrap over bins, since bias wander makes neighbouring bins correlated
    rng = np.random.default_rng(seed)
    fitted = X @ theta
    # blocks up to 30 min, since MEMS bias and temperature wander on that scale and longer
    blk = max(2, min(30, n_bins // 5)) if block_length is None else int(block_length)
    if blk < 1 or bootstrap_sampling not in ("moving", "segment"):
        raise ValueError("invalid bootstrap configuration")
    boots, boot_dchi = [], []
    if n_boot and n_bins >= 2 * blk:
        starts = np.arange(n_bins - blk + 1)
        for _ in range(n_boot):
            order = bootstrap_order(rng, bins, blk, bootstrap_sampling)
            rb = np.concatenate([resid[idx == j] for j in order])
            yb = fitted + rb[:len(fitted)] if len(rb) >= len(fitted) else fitted
            tb, _, _ = _solve(yb, X, w, prior, prior_mean=prior_mean)
            boots.append(tb[K])
            if len(boot_dchi) < 100:
                cb = compare(yb)
                lo = min(cb.values())
                boot_dchi.append({m: (v - lo) * scale for m, v in cb.items()})
    k_sd_boot = np.std(boots, axis=0) if boots else np.full(NK, np.nan)
    k_sd_final = np.fmax(k_sd, np.nan_to_num(k_sd_boot))
    k_sd_final = np.sqrt(k_sd_final ** 2 + np.array([K_SYS_FLOOR[n] for n in TERM_NAMES]) ** 2)

    # Bootstrap calibration of each model's test. Simulate that model's null (its fitted values plus
    # block-resampled free-fit residuals) and refit: in a well-calibrated test the mean Δχ² against the free fit equals the
    # degrees of freedom. Correlated noise inflates it; the observed Δχ² is divided by that inflation.
    # (A direct bootstrap p would need thousands of replicates to resolve p = 0.0027.)
    boot_cal = {}
    if n_boot and n_bins >= 2 * blk:
        starts = np.arange(n_bins - blk + 1)
        rng_n = np.random.default_rng(seed + 1)
        for name, kk in models.EXPECTED_K.items():
            Xm, pm, mean_m = model_designs[name]
            th_m, _, _ = _solve(y, Xm, w, pm, fixed_k=kk, prior_mean=mean_m)
            fit_m = Xm[:, K] @ np.asarray(kk) + np.delete(Xm, np.arange(K.start, K.stop), axis=1) @ th_m
            ds = []
            for _ in range(min(n_boot, 100)):
                # noise from the free fit's residuals (a wrong model's residuals would carry signal)
                order = bootstrap_order(rng_n, bins, blk, bootstrap_sampling)
                rb = np.concatenate([resid[idx == j] for j in order])
                yb = fit_m + rb[:len(fit_m)] if len(rb) >= len(fit_m) else fit_m
                # nested comparison on the model's own design (same crab offsets), so the ratio measures
                # only how correlated noise inflates Δχ²
                ds.append(_solve(yb, Xm, w, pm, fixed_k=kk, prior_mean=mean_m)[2] - _solve(yb, Xm, w, pm, prior_mean=mean_m)[2])
            boot_cal[name] = max(1.0, float(np.mean(ds)) / NK)

    # Identifiability: how much of each term's predicted signal a constant residual bias (one per
    # gravity orientation) could mimic. 1 means indistinguishable from bias by the flight data
    # alone; then only the bias prior (the ground calibration) constrains that term. A constant
    # rotation about the vertical is always 1 in level flight: it lies along gravity, exactly like
    # gyro bias and g-sensitivity on that axis.
    def likeness(N):
        out = {}
        for i, n in enumerate(TERM_NAMES):
            xi = X[:, i]
            e = float(xi @ xi)
            if e == 0 or N.shape[1] == 0:
                out[n] = 1.0 if e == 0 else 0.0
                continue
            beta, *_ = np.linalg.lstsq(N, xi, rcond=None)
            r = xi - N @ beta
            out[n] = float(np.sqrt(max(0.0, 1 - (r @ r) / e)))
        return out

    B = X[:, lay["bias"]]
    tie_bias = likeness(B)
    # The same against every nuisance column at once (bias, temperature, crab), with no priors: a
    # term that a combination of them can mimic is constrained only by their priors. Trade-offs
    # between the k terms themselves are not counted here; the joint covariance k_cov carries them.
    tie_k = likeness(X[:, NK:])
    tie = tie_k["k_curv"]

    # Prior sensitivity: widen each nuisance prior in turn and see how far k moves.
    def widened(bias=1.0, crab=1.0, temp=1.0):
        pw = priors(bias_scale=bias)
        if temp_ref is not None:
            pw[lay["temp"]] = pw[lay["temp"]] * temp
        return pw
    shifts = {"bias": (solve_with_crab(pri=widened(bias=PRIOR_WIDEN))[0][K] - k) / k_sd_final}
    if use_crab:
        shifts["crab"] = (solve_with_crab(sig=sig_crab * PRIOR_WIDEN)[0][K] - k) / k_sd_final
    if temp_ref is not None and np.all(np.isfinite(np.asarray(temp_prior, dtype=float))):
        shifts["temperature"] = (solve_with_crab(pri=widened(temp=PRIOR_WIDEN))[0][K] - k) / k_sd_final
    shift = shifts["bias"]
    worst_shift = max(float(np.max(np.abs(s))) for s in shifts.values())

    # Crab sweep: refit (no bootstrap) under several crab priors. On a single-heading route crab
    # trades against the split between globe rotation and curvature.
    crab_sweep = None
    if use_crab:
        crab_sweep = {}
        for sd in CRAB_SWEEP_DEG:
            th_s, cv_s, *_ = solve_with_crab(sig=np.radians(sd), pri=priors())
            crab_sweep[f"{sd:g}"] = {"k": dict(zip(TERM_NAMES, th_s[K].tolist())),
                                     "k_sd_analytic": dict(zip(TERM_NAMES, np.sqrt(np.diag(cv_s)[K]).tolist()))}
        ks = np.array([[v["k"][n] for n in TERM_NAMES] for v in crab_sweep.values()])
        crab_span = np.ptp(ks, axis=0) / k_sd_final
    else:
        crab_span = np.zeros(NK)

    # Joint covariance of k: the analytic correlation (crab columns included) scaled to the final σ,
    # so pooling can test the models jointly instead of treating the terms as independent.
    ck = cov[K, K]
    dk = np.sqrt(np.diag(ck))
    rk = ck / np.outer(dk, dk) if np.all(dk > 0) else np.eye(NK)
    k_cov = rk * np.outer(k_sd_final, k_sd_final)

    corr = cov / np.sqrt(np.outer(np.diag(cov), np.diag(cov)))
    best = min(comparison.values())
    d_best = {n: (c - best) * scale for n, c in comparison.items()}
    d_raw = {n: max(c - chi2_free, 0.0) for n, c in comparison.items()}
    d_free = {n: v * scale for n, v in d_raw.items()}
    p_asym = {n: float(sf_chi2(v)) for n, v in d_free.items()}
    p_boot = {n: float(sf_chi2(d_raw[n] / boot_cal[n])) for n in d_raw} if boot_cal else None
    # the conservative of the two: autocorrelation-scaled and bootstrap-calibrated
    p_free = {n: max(p_asym[n], p_boot[n]) if p_boot else p_asym[n] for n in d_raw}
    rel = {n: float(np.exp(-v / 2)) for n, v in d_best.items()}
    tot = sum(rel.values())
    ci = None
    if boot_dchi:
        ci = {m: [float(np.percentile([b[m] for b in boot_dchi], q)) for q in (16, 84)] for m in comparison}
    return {
        "convergence": {"converged": all(c["converged"] for c in convergence), "fits": convergence},
        "mode": "vertical_only" if vertical_only else "3-axis",
        "n_bins": n_bins, "n_rows": len(y),
        "sigma_bin_dph": sigma * RAD2DPH,
        "k": dict(zip(TERM_NAMES, k.tolist())),
        "k_sd": dict(zip(TERM_NAMES, k_sd_final.tolist())),
        "k_sd_analytic": dict(zip(TERM_NAMES, k_sd.tolist())),
        "gravity_orientations": ng,
        "crab": {"prior_sigma_deg": crab_sigma_deg if use_crab else None, "groups": "segments sharing a GNSS course within 10°",
                 "per_segment_deg": (np.degrees(crab_d + theta[-n_seg:])).tolist() if use_crab else None,
                 "sd_deg": (np.degrees(np.sqrt(np.diag(cov)[-n_seg:]))).tolist() if use_crab else None},
        "bias_residual_dph": (theta[lay["bias"]].reshape(ng, 3) * RAD2DPH).tolist(),
        "k_cov": k_cov.tolist(),
        "bootstrap": {"sampling": bootstrap_sampling, "block_length": blk, "replicates": len(boots),
                      "empirical_k_cov": np.cov(np.asarray(boots).T, ddof=1).tolist() if len(boots) > 1 else None,
                      "refit": "local linearization with total-angle prior"},
        "max_bias_k_corr": float(np.max(np.abs(corr[K, lay["bias"]]))),
        "identifiability": {"k_curv_bias_likeness": tie_bias["k_curv"], "bias_likeness_by_term": tie_bias,
                            "k_curv_nuisance_likeness": tie, "nuisance_likeness_by_term": tie_k,
                            "identified_by_term": {n: v < CORR_NOT_IDENTIFIED for n, v in tie_k.items()},
                            "identified": tie < CORR_NOT_IDENTIFIED,
                            "note": "fraction of each term's signal the nuisance terms (residual bias per gravity "
                                    "orientation, temperature, crab) could mimic together, with no priors"},
        "prior_sensitivity": {"widen": PRIOR_WIDEN, "k_shift_sigma": dict(zip(TERM_NAMES, shift.tolist())),
                              "k_shift_sigma_by_prior": {p: dict(zip(TERM_NAMES, s.tolist())) for p, s in shifts.items()},
                              "prior_dominated": worst_shift > 1.0},
        "crab_sensitivity": {"prior_sigma_deg": list(CRAB_SWEEP_DEG), "fits": crab_sweep,
                             "k_span_sigma": dict(zip(TERM_NAMES, crab_span.tolist())),
                             "crab_sensitive": bool(np.max(crab_span) > 1.0),
                             "course_groups": int(n_seg)} if use_crab else None,
        "temp_coef_dph_per_c": ((theta[lay["temp"]] + (np.asarray(temp_mean) if temp_mean is not None else 0)) * RAD2DPH).tolist()
        if temp_ref is not None else None,
        "chi2_scaling": {"rho_lag1": rho, "scale": scale},
        "chi2": {n: float(c) for n, c in comparison.items()},
        "chi2_free": float(chi2_free),
        "delta_chi2": d_best,
        "delta_chi2_ci_16_84": ci,
        "delta_chi2_vs_free": d_free,
        "p_vs_free": p_free,
        "p_asymptotic": p_asym,
        "p_bootstrap_calibrated": p_boot,
        "bootstrap_inflation": boot_cal or None,
        "rejected": {n: p < P_REJECT for n, p in p_free.items()},
        "relative_likelihood": {n: v / tot for n, v in rel.items()},
        "best_model": min(comparison, key=comparison.get),
        "_rows": (y, X, idx, cbns, theta),
    }


def fit(bins, fwd_b, bias_fn, prior_sigma, vertical_only=False, n_boot=300, seed=0,
        temp_ref=None, temp_prior=None, temp_mean=None, crab_sigma_deg=5.0,
        bootstrap_sampling="moving", block_length=None, max_nfev=200, *,
        crab_model="constant", noise_model="global", bootstrap_refit="linearized",
        forward_uncertainty=False, forward_sigma_rad=None, forward_tangent=None,
        crab_rate_sigma_dph=None, crab_knot_seconds=None, variance_shrinkage_bins=None,
        research_candidate=False, decision_thresholds=None, decision_policy_hash=None, decision_statistic=None, design_only=False,
        bias_model="constant", bias_knot_seconds=None, bias_rw_sigma_dph_sqrth=None):
    settings = dict(crab_model=crab_model, noise_model=noise_model, bootstrap_refit=bootstrap_refit,
                    forward_uncertainty=forward_uncertainty, crab_sigma_deg=crab_sigma_deg,
                    bootstrap_sampling=bootstrap_sampling, block_length=block_length, n_boot=n_boot,
                    max_nfev=max_nfev,
                    crab_rate_sigma_dph=INFERENCE_POLICY["crab_rate_sigma_dph"] if crab_rate_sigma_dph is None else crab_rate_sigma_dph,
                    crab_knot_seconds=INFERENCE_POLICY["wind_knot_seconds" if crab_model == "wind" else "crab_knot_seconds"] if crab_knot_seconds is None else crab_knot_seconds,
                    variance_shrinkage_bins=INFERENCE_POLICY["variance_shrinkage_bins"] if variance_shrinkage_bins is None else variance_shrinkage_bins)
    settings.update(bias_model=bias_model,
                    bias_knot_seconds=INFERENCE_POLICY["bias_knot_seconds"] if bias_knot_seconds is None else bias_knot_seconds,
                    bias_rw_sigma_dph_sqrth=INFERENCE_POLICY["bias_rw_sigma_dph_sqrth"] if bias_rw_sigma_dph_sqrth is None else bias_rw_sigma_dph_sqrth)
    if design_only and decision_thresholds is not None:
        raise ValueError("design-only evaluation cannot apply model decisions")
    if design_only:
        settings["design_only"] = True
    if crab_model not in ("constant", "dynamic", "wind") or noise_model not in ("global", "axis", "axis_segment") or bootstrap_refit not in ("linearized", "nonlinear"):
        raise ValueError("invalid inference candidate")
    if bias_model not in ("constant", "dynamic"):
        raise ValueError("bias_model must be constant or dynamic")
    candidate = design_only or research_candidate or crab_model != "constant" or noise_model != "global" or bootstrap_refit != "linearized" or forward_uncertainty or bias_model == "dynamic"
    settings["engine"] = "candidate-1" if candidate else "legacy"
    common = dict(vertical_only=vertical_only, n_boot=n_boot, seed=seed, temp_ref=temp_ref,
                  temp_prior=temp_prior, temp_mean=temp_mean, crab_sigma_deg=crab_sigma_deg,
                  bootstrap_sampling=bootstrap_sampling, block_length=block_length, max_nfev=max_nfev)
    if candidate:
        from .inference import candidate_fit
        result = candidate_fit(bins, fwd_b, bias_fn, prior_sigma, settings=settings,
                               forward_sigma_rad=forward_sigma_rad, forward_tangent=forward_tangent, **common)
    else:
        result = _legacy_fit(bins, fwd_b, bias_fn, prior_sigma, **common)
    result["inference_policy"] = provenance(settings)
    result["delta_chi2_raw"] = ({m: max(v - result["chi2_free"], 0.) for m, v in result["chi2"].items()}
                                if not design_only else None)
    if decision_thresholds is not None:
        if not decision_policy_hash or set(decision_thresholds) != set(models.MODELS) or any(not np.isfinite(v) or v < 0 for v in decision_thresholds.values()):
            raise ValueError("complete finite empirical thresholds and policy hash required")
        result["rejected_analytic"] = result["rejected"]
        field = decision_statistic or ("delta_chi2_identifiable" if candidate else "delta_chi2_raw")
        if field not in ("delta_chi2_identifiable", "delta_chi2_raw") or field not in result:
            raise ValueError("decision statistic is unavailable for this inference engine")
        statistic = result[field]
        valid = bool(result.get("model_test_rank", 3)) and result["convergence"]["converged"] and result["bootstrap"].get("bootstrap_valid", True)
        result["rejected"] = {m: (v > decision_thresholds[m] if valid else None)
                              for m, v in statistic.items()}
        result["decision_policy_hash"] = decision_policy_hash
        result["decision_valid"] = valid
        result["decision_statistic"] = field
        result["decision_rule"] = "experimental empirical identifiable-science threshold" if field == "delta_chi2_identifiable" else "experimental empirical delta_chi2_raw threshold"
    return result


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
        pred[m] = models.predict(m, bins["lat"], bins["h"], bins["v_n"], bins["v_e"], bins.get("lon_rate"))
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
