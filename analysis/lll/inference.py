# SPDX-License-Identifier: AGPL-3.0-or-later
"""Opt-in inference candidates; production selection requires independent validation."""
import numpy as np
from scipy.optimize import least_squares

from . import models
from .calib import RAD2DPH
from .inference_policy import INFERENCE_POLICY
from .fit import (NK, K, TERM_NAMES, P_REJECT, PRIOR_WIDEN, CRAB_SWEEP_DEG,
                  CORR_NOT_IDENTIFIED, build_rows, _solve, _crab_columns,
                  _autocorr_scale, bootstrap_order, sf_chi2)


def crab_basis(bins, model, knot_seconds=300.):
    """Angle and rate bases. Dynamic angles remain continuous across gaps and mount turns."""
    t = np.asarray(bins["t"], float)
    if model == "dynamic":
        if not np.isfinite(knot_seconds) or knot_seconds <= 0:
            raise ValueError("crab knot spacing must be positive")
        knots = t.min() + np.arange(max(1, int(np.ceil(np.ptp(t) / knot_seconds))) + 1) * knot_seconds
        j = np.clip(np.searchsorted(knots, t, side="right") - 1, 0, len(knots)-2)
        fraction = (t-knots[j]) / np.diff(knots)[j]
        B = np.zeros((len(t), len(knots)))
        D = np.zeros_like(B)
        B[np.arange(len(t)), j] = 1-fraction
        B[np.arange(len(t)), j+1] = fraction
        D[np.arange(len(t)), j] = -1/np.diff(knots)[j]
        D[np.arange(len(t)), j+1] = 1/np.diff(knots)[j]
        return B, D, knots
    ids = np.unique(bins["seg"])
    refs, groups = [], []
    for s in ids:
        c = np.angle(np.mean(np.exp(1j*bins["psi"][bins["seg"] == s])))
        match = next((i for i, r in enumerate(refs) if abs(np.angle(np.exp(1j*(c-r)))) < np.radians(10)), None)
        if match is None:
            match = len(refs)
            refs.append(c)
        groups.append(match)
    index = np.asarray(groups)[np.searchsorted(ids, bins["seg"])]
    B = np.eye(len(refs))[index]
    return B, np.zeros_like(B), None


def residual_weights(residual, bins, model, shrinkage=20.):
    """Per-axis/segment residual second moments shrunk toward the global second moment."""
    if not np.isfinite(shrinkage) or shrinkage <= 0:
        raise ValueError("variance shrinkage must be positive")
    r = np.asarray(residual).reshape(len(bins["t"]), -1)
    floor = INFERENCE_POLICY["sigma_floor_rad_s"] ** 2
    global_var = max(float(np.mean(r*r)), floor)
    v = np.full_like(r, global_var)
    groups = [np.ones(len(r), bool)] if model == "axis" else [bins["seg"] == s for s in np.unique(bins["seg"])]
    counts = []
    if model != "global":
        for mask in groups:
            n = int(mask.sum())
            v[mask] = np.maximum((np.sum(r[mask]**2, axis=0) + shrinkage*global_var)/(n+shrinkage), floor)
            counts.append(n)
    return 1/v.ravel(), {"model": model, "global_sigma_dph": np.sqrt(global_var)*RAD2DPH,
                         "sigma_by_bin_axis_dph": (np.sqrt(v)*RAD2DPH).tolist(),
                         "group_counts": counts, "shrinkage_bins": shrinkage, "frozen_from_free_fit": True}


def sensor_bias_basis(bins, knot_seconds=900., vertical_only=False):
    """Sensor-frame bias variations, anchored to zero at the first retained time.

    The existing residual offsets retain the unknown level. Knot increments are shared across
    all segments and mount/gravity orientations; rotating the sensor does not rotate its bias.
    Values use rad/s, with knot-major xyz coefficient ordering.
    """
    if not np.isfinite(knot_seconds) or knot_seconds <= 0:
        raise ValueError("bias knot spacing must be positive and finite")
    B, _, knots = crab_basis(bins, "dynamic", knot_seconds)
    B = B[:, 1:]  # remove the constant-level ambiguity with the existing residual bias
    H = (B[:, :, None]*(-np.asarray(bins["up"]))[:, None, :]).reshape(len(B), -1) if vertical_only else np.kron(B, np.eye(3))
    differences = np.diff(np.eye(len(knots)), axis=0)[:, 1:]
    # Unit random-walk scale: 1 (rad/s)/sqrt(hour). Actual scale is applied in penalty().
    P = np.kron(differences/np.sqrt(np.diff(knots)/3600)[:, None], np.eye(3))
    return H, B, knots, P


class CandidateProblem:
    """Nonlinear predictions and total-parameter Gaussian penalties, shared by all refits."""
    def __init__(self, bins, fwd, bias_fn, prior_sigma, settings, vertical_only=False,
                 temp_ref=None, temp_prior=None, temp_mean=None, crab_sigma_deg=5.,
                 forward_sigma_rad=None, forward_tangent=None):
        self.bins, self.fwd, self.bias_fn = bins, fwd, bias_fn
        self.settings, self.vertical = settings, vertical_only
        self.temp_ref, self.temp_mean = temp_ref, temp_mean
        self.y, self.X, self.idx, self.cb, self.layout = build_rows(bins, fwd, bias_fn, vertical_only, temp_ref, temp_mean)
        self.base_p = self.X.shape[1]
        self.prior = np.r_[np.full(NK, np.inf), np.tile(prior_sigma, self.layout["n_grav"]),
                           np.broadcast_to(np.inf if temp_prior is None else temp_prior, (3,)) if temp_ref is not None else []]
        self.dynamic_bias = settings.get("bias_model", "constant") == "dynamic"
        self.bias_columns = np.empty((len(self.y), 0))
        self.bias_knots = None
        if self.dynamic_bias:
            self.bias_rw_sigma = settings.get("bias_rw_sigma_dph_sqrth", INFERENCE_POLICY["bias_rw_sigma_dph_sqrth"])
            if not np.isfinite(self.bias_rw_sigma) or self.bias_rw_sigma <= 0:
                raise ValueError("bias random-walk scale must be positive and finite")
            self.bias_columns, self.bias_basis, self.bias_knots, self.bias_penalty = sensor_bias_basis(
                bins, settings.get("bias_knot_seconds", INFERENCE_POLICY["bias_knot_seconds"]), vertical_only)
            self.X = np.column_stack([self.X, self.bias_columns])
            self.prior = np.r_[self.prior, np.full(self.bias_columns.shape[1], np.inf)]
        self.p = self.X.shape[1]
        self.bias_drift_slice = slice(self.base_p, self.p)
        self.B, self.D, self.knots = crab_basis(bins, settings["crab_model"], settings["crab_knot_seconds"])
        self.use_crab = not vertical_only and crab_sigma_deg is not None and crab_sigma_deg > 0
        if not self.use_crab:
            self.B, self.D = self.B[:, :0], self.D[:, :0]
        self.nc = self.B.shape[1]
        self.forward = settings["forward_uncertainty"]
        if self.forward and (vertical_only or forward_sigma_rad is None or not np.isfinite(forward_sigma_rad) or forward_sigma_rad <= 0):
            raise ValueError("forward uncertainty unavailable: positive measured angle uncertainty required")
        self.forward_sigma = forward_sigma_rad
        self.tangent = forward_tangent
        if self.forward and self.tangent is None:
            self.tangent = np.cross(bins["up"], fwd)
        self.crab_sigma = np.radians(crab_sigma_deg) if self.use_crab else None
        self.npar = self.p + self.nc + int(self.forward)
        self.w = np.full(len(self.y), 1/(3/RAD2DPH)**2)
        self.convergence = []

    def penalty(self, bias=1., crab=1., temperature=1., rate=1., forward=1., bias_drift=1.):
        sd = self.prior.copy()
        sd[self.layout["bias"]] *= bias
        if self.temp_ref is not None:
            sd[self.layout["temp"]] *= temperature
        finite = np.flatnonzero(np.isfinite(sd))
        P = np.zeros((len(finite), self.npar))
        P[np.arange(len(finite)), finite] = 1/sd[finite]
        if self.dynamic_bias:
            drift = np.zeros((self.bias_penalty.shape[0], self.npar))
            drift[:, self.bias_drift_slice] = self.bias_penalty/(self.bias_rw_sigma/RAD2DPH*bias_drift)
            P = np.vstack([P, drift])
        if self.nc:
            amp = np.zeros((self.nc, self.npar))
            amp[:, self.p:self.p+self.nc] = np.eye(self.nc)/(self.crab_sigma*crab)
            P = np.vstack([P, amp])
            if self.knots is not None:
                diff = np.zeros((self.nc-1, self.npar))
                sd_rate = np.radians(self.settings["crab_rate_sigma_dph"])/3600 * rate
                if not np.isfinite(sd_rate) or sd_rate <= 0:
                    raise ValueError("crab rate prior must be positive")
                diff[:, self.p:self.p+self.nc] = np.diff(np.eye(self.nc), axis=0)/(np.diff(self.knots)[:, None]*sd_rate)
                P = np.vstack([P, diff])
        if self.forward:
            a = np.zeros((1, self.npar)); a[0, -1] = 1/(self.forward_sigma*forward)
            P = np.vstack([P, a])
        return P

    def prediction(self, z, jac=False):
        d = z[self.p:self.p+self.nc]
        fwd = self.fwd
        if self.forward:
            fwd = self.fwd*np.cos(z[-1]) + self.tangent*np.sin(z[-1])
        _, X, idx, cb, layout = build_rows(self.bins, fwd, self.bias_fn, self.vertical,
                                          self.temp_ref, self.temp_mean, dpsi=self.B @ d)
        if self.dynamic_bias:
            X = np.column_stack([X, self.bias_columns])
        # Extra fuselage heading rotation is about down, independent of the k terms.
        rate = (-self.bins["up"] * (self.D @ d)[:, None]).ravel() if not self.vertical else np.zeros(len(self.y))
        pred = X @ z[:self.p] + rate
        if not jac:
            return pred
        if self.nc:
            Jangle = _crab_columns(cb, layout, idx, z[K], np.arange(len(self.B)), len(self.B))
            Jcrab = Jangle @ self.B + (-self.bins["up"][:, :, None]*self.D[:, None, :]).reshape(len(self.y), self.nc)
        else:
            Jcrab = np.empty((len(self.y), 0))
        J = np.column_stack([X, Jcrab])
        if self.forward:
            h = 1e-6
            plus, minus = z.copy(), z.copy()
            plus[-1] += h; minus[-1] -= h
            J = np.column_stack([J, (self.prediction(plus)-self.prediction(minus))/(2*h)])
        return pred, J

    def solve(self, y=None, fixed=None, P=None, start=None, record=True):
        y = self.y if y is None else y
        P = self.penalty() if P is None else P
        keep = np.arange(self.npar) if fixed is None else np.arange(NK, self.npar)
        z = np.zeros(self.npar)
        initial = _solve(y, self.X, self.w, self.prior, fixed)[0]
        z[:self.p] = initial if fixed is None else np.r_[fixed, initial]
        if self.dynamic_bias:
            linear = np.arange(self.p) if fixed is None else np.arange(NK, self.p)
            offset = np.zeros(self.npar)
            if fixed is not None: offset[K] = fixed
            A = np.vstack([self.X[:, linear]*np.sqrt(self.w)[:, None], P[:, linear]])
            b = np.r_[(y-self.X @ offset[:self.p])*np.sqrt(self.w), -P @ offset]
            z[linear] = np.linalg.lstsq(A, b, rcond=None)[0]
        if start is not None:
            z = start.copy()
        if fixed is not None:
            z[K] = fixed
        sw = np.sqrt(self.w)
        def unpack(x):
            full = z.copy(); full[keep] = x
            return full
        def fun(x):
            full = unpack(x)
            return np.r_[(self.prediction(full)-y)*sw, P @ full]
        def jac(x):
            _, J = self.prediction(unpack(x), True)
            return np.vstack([J[:, keep]*sw[:, None], P[:, keep]])
        opt = least_squares(fun, z[keep], jac=jac, x_scale="jac", ftol=1e-10, xtol=1e-10,
                            gtol=1e-8, max_nfev=self.settings["max_nfev"])
        full = unpack(opt.x)
        pred, J = self.prediction(full, True)
        A = np.vstack([J[:, keep]*sw[:, None], P[:, keep]])
        info = {"converged": bool(opt.success), "evaluations": opt.nfev, "status": int(opt.status)}
        if record:
            self.convergence.append(info)
        column_scale = np.maximum(np.linalg.norm(A, axis=0), 1e-30)
        inverse = np.linalg.pinv(A/column_scale)
        covariance = (inverse @ inverse.T)/np.outer(column_scale, column_scale)
        return dict(z=full, pred=pred, J=J, P=P, objective=float(opt.fun @ opt.fun),
                    cov=covariance, success=bool(opt.success))

    def local(self, y, reference, fixed=None):
        z, J, P = reference["z"], reference["J"], reference["P"]
        keep = np.arange(self.npar) if fixed is None else np.arange(NK, self.npar)
        delta = np.zeros(self.npar)
        if fixed is not None:
            delta[K] = np.asarray(fixed)-z[K]
        A = np.vstack([J[:, keep]*np.sqrt(self.w)[:, None], P[:, keep]])
        b = np.r_[(y-reference["pred"]-J @ delta)*np.sqrt(self.w), -P @ (z+delta)]
        delta[keep] = np.linalg.lstsq(A, b, rcond=None)[0]
        residual = b-A @ delta[keep]
        return dict(z=z+delta, objective=float(residual @ residual), success=True)


def candidate_fit(bins, fwd_b, bias_fn, prior_sigma, *, settings, vertical_only=False,
                  n_boot=300, seed=0, temp_ref=None, temp_prior=None, temp_mean=None,
                  crab_sigma_deg=5., bootstrap_sampling="moving", block_length=None,
                  max_nfev=200, forward_sigma_rad=None, forward_tangent=None):
    problem = CandidateProblem(bins, fwd_b, bias_fn, prior_sigma, settings, vertical_only,
                               temp_ref, temp_prior, temp_mean, crab_sigma_deg, forward_sigma_rad, forward_tangent)
    preliminary = problem.solve()
    problem.w, noise = residual_weights(problem.y-preliminary["pred"], bins, settings["noise_model"], settings["variance_shrinkage_bins"])
    free = problem.solve(start=preliminary["z"])
    fixed = {m: problem.solve(fixed=k) for m, k in models.EXPECTED_K.items()}
    best_fixed = min(fixed.values(), key=lambda s: s["objective"])
    if free["objective"] > best_fixed["objective"]+1e-6:
        free = problem.solve(start=best_fixed["z"])
        if free["objective"] > best_fixed["objective"]+1e-6:
            problem.convergence.append({"converged": False, "reason": "free/fixed objectives are not nested"})
    z, cov, J = free["z"], free["cov"], free["J"]
    k, analytic_sd = z[K], np.sqrt(np.maximum(np.diag(cov)[K], 0))
    residual = problem.y-free["pred"]
    scale, rho = _autocorr_scale(residual*np.sqrt(problem.w), problem.idx, bins)
    n = len(bins["t"])
    block = max(2, min(30, n//5)) if block_length is None else int(block_length)
    if block < 1 or bootstrap_sampling not in ("moving", "segment") or n_boot < 0:
        raise ValueError("invalid bootstrap configuration")
    rng = np.random.default_rng(seed)
    standardized = (residual*np.sqrt(problem.w)).reshape(n, -1)
    standardized -= standardized.mean(axis=0)
    def sample(pred):
        order = bootstrap_order(rng, bins, block, bootstrap_sampling)
        return pred + standardized[order].ravel()/np.sqrt(problem.w)
    nonlinear = settings["bootstrap_refit"] == "nonlinear"
    def refit(y, reference, fixed_k=None):
        return (problem.solve(y, fixed=fixed_k, start=reference["z"], record=False) if nonlinear
                else problem.local(y, reference, fixed_k))
    boots, failures, nulls = [], [], {m: [] for m in fixed}
    attempted = n_boot if n >= 2*block else 0
    for i in range(attempted):
        try:
            b = refit(sample(free["pred"]), free)
            if not b["success"]:
                raise ValueError("free refit did not converge")
            boots.append(b["z"][K])
        except (ValueError, np.linalg.LinAlgError) as exc:
            failures.append({"replicate": i, "kind": "free", "error": str(exc)})
        for m, target in models.EXPECTED_K.items():
            try:
                yb = sample(fixed[m]["pred"])
                fb, mb = refit(yb, fixed[m]), refit(yb, fixed[m], target)
                if not (fb["success"] and mb["success"]) or fb["objective"] > mb["objective"]+1e-6:
                    raise ValueError("null refit failed convergence or nesting")
                nulls[m].append(max(0., mb["objective"]-fb["objective"]))
            except (ValueError, np.linalg.LinAlgError) as exc:
                failures.append({"replicate": i, "kind": m, "error": str(exc)})
    boot_sd = np.std(boots, axis=0, ddof=1) if len(boots)>1 else np.zeros(NK)
    sd = np.sqrt(np.maximum(analytic_sd, boot_sd)**2 + np.array([INFERENCE_POLICY["k_sys_floor"][m] for m in TERM_NAMES])**2)
    ck = cov[K, K]; denom = np.sqrt(np.outer(np.diag(ck), np.diag(ck)))
    corr = np.divide(ck, denom, out=np.eye(NK), where=denom>0)
    kcov = corr*np.outer(sd, sd)
    def likeness(N):
        out = {}
        for i, name in enumerate(TERM_NAMES):
            x = J[:, i]; r = x-N @ np.linalg.lstsq(N, x, rcond=None)[0]
            out[name] = float(np.sqrt(max(0., 1-float(r @ r)/float(x @ x)))) if x @ x else 1.
        return out
    bias_indices = np.r_[np.arange(problem.p)[problem.layout["bias"]], np.arange(problem.p)[problem.bias_drift_slice]]
    tie_bias = likeness(J[:, bias_indices]); tie = likeness(J[:, NK:])
    prior_k = ["bias"] + (["crab"] if problem.nc else []) + (["temperature"] if temp_ref is not None else [])
    if problem.nc and settings["crab_model"] == "dynamic": prior_k.append("rate")
    if problem.forward: prior_k.append("forward")
    if problem.dynamic_bias: prior_k.append("bias_drift")
    shifts = {key: (problem.solve(P=problem.penalty(**{key: PRIOR_WIDEN}), start=z)["z"][K]-k)/sd for key in prior_k}
    sweep = {}
    if problem.nc:
        for value in CRAB_SWEEP_DEG:
            s = problem.solve(P=problem.penalty(crab=value/crab_sigma_deg), start=z)
            sweep[f"{value:g}"] = {"k": dict(zip(TERM_NAMES, s["z"][K].tolist())),
                                   "k_sd_analytic": dict(zip(TERM_NAMES, np.sqrt(np.diag(s["cov"])[K]).tolist()))}
    span = np.ptp([[v["k"][m] for m in TERM_NAMES] for v in sweep.values()], axis=0)/sd if sweep else np.zeros(NK)
    raw = {m: max(0., s["objective"]-free["objective"]) for m, s in fixed.items()}
    inflation = {m: max(1., float(np.mean(v))/NK) for m, v in nulls.items() if v}
    asym = {m: sf_chi2(v*scale) for m, v in raw.items()}
    bootp = {m: sf_chi2(raw[m]/inflation[m]) for m in inflation}
    p = {m: max(asym[m], bootp.get(m, 0.)) for m in raw}
    best = min(s["objective"] for s in fixed.values())
    dbest = {m: (s["objective"]-best)*scale for m, s in fixed.items()}
    relative = {m: np.exp(-v/2) for m, v in dbest.items()}
    total = sum(relative.values())
    crab = z[problem.p:problem.p+problem.nc]
    course_groups = crab_basis(bins, "constant")[0].shape[1]
    bsl = problem.layout["bias"]
    crossden = np.sqrt(np.outer(np.diag(cov)[K], np.diag(cov)[bias_indices]))
    sensor_bias = {"model": "dynamic" if problem.dynamic_bias else "constant", "frame": "sensor"}
    if problem.dynamic_bias:
        drift = z[problem.bias_drift_slice].reshape(-1, 3)
        body_design = np.kron(problem.bias_basis, np.eye(3)).reshape(n, 3, -1)
        drift_cov = cov[problem.bias_drift_slice, problem.bias_drift_slice]
        variance = np.einsum("nai,ij,naj->na", body_design, drift_cov, body_design)
        sensor_bias.update(knot_times_s=problem.bias_knots.tolist(),
                           anchor="zero variation at first retained time; level is residual bias",
                           rw_sigma_dph_sqrth=problem.bias_rw_sigma,
                           knot_drift_dph=(np.vstack([np.zeros(3), drift])*RAD2DPH).tolist(),
                           per_bin_drift_dph=(problem.bias_basis @ drift*RAD2DPH).tolist(),
                           per_bin_drift_sd_dph=(np.sqrt(np.maximum(variance, 0))*RAD2DPH).tolist())
    return {"convergence": {"converged": all(v["converged"] for v in problem.convergence), "fits": problem.convergence},
            "mode": "vertical_only" if vertical_only else "3-axis", "n_bins": n, "n_rows": len(problem.y),
            "sigma_bin_dph": noise["global_sigma_dph"], "noise": noise,
            "sensor_bias": sensor_bias,
            "k": dict(zip(TERM_NAMES, k.tolist())), "k_sd": dict(zip(TERM_NAMES, sd.tolist())),
            "k_sd_analytic": dict(zip(TERM_NAMES, analytic_sd.tolist())), "k_cov": kcov.tolist(),
            "gravity_orientations": problem.layout["n_grav"],
            "crab": {"model": settings["crab_model"], "prior_sigma_deg": crab_sigma_deg, "groups": settings["crab_model"],
                     "per_segment_deg": np.degrees(crab).tolist(), "per_bin_deg": np.degrees(problem.B @ crab).tolist(),
                     "rate_dph": ((problem.D @ crab)*RAD2DPH).tolist(),
                     "knot_times_s": problem.knots.tolist() if problem.knots is not None else None,
                     "sd_deg": np.degrees(np.sqrt(np.diag(cov)[problem.p:problem.p+problem.nc])).tolist()},
            "forward_uncertainty": {"enabled": problem.forward, "prior_sigma_rad": forward_sigma_rad,
                                    "angle_rad": float(z[-1]) if problem.forward else None},
            "bias_residual_dph": (z[bsl].reshape(-1, 3)*RAD2DPH).tolist(),
            "temp_coef_dph_per_c": ((z[problem.layout["temp"]]+(0 if temp_mean is None else temp_mean))*RAD2DPH).tolist() if temp_ref is not None else None,
            "bootstrap": {"sampling": bootstrap_sampling, "block_length": block, "replicates": len(boots),
                          "attempted": attempted, "requested": n_boot, "failures": failures,
                          "null_replicates": {m: len(v) for m, v in nulls.items()},
                          "empirical_k_cov": np.cov(np.asarray(boots).T).tolist() if len(boots)>1 else None,
                          "refit": settings["bootstrap_refit"]},
            "max_bias_k_corr": float(np.max(np.abs(np.divide(cov[K][:, bias_indices], crossden, out=np.zeros_like(crossden), where=crossden>0)))),
            "identifiability": {"k_curv_bias_likeness": tie_bias["k_curv"], "bias_likeness_by_term": tie_bias,
                                "k_curv_nuisance_likeness": tie["k_curv"], "nuisance_likeness_by_term": tie,
                                "identified_by_term": {m: v<CORR_NOT_IDENTIFIED for m, v in tie.items()},
                                "identified": tie["k_curv"]<CORR_NOT_IDENTIFIED, "note": "all candidate nuisance columns, without priors"},
            "prior_sensitivity": {"widen": PRIOR_WIDEN, "k_shift_sigma": dict(zip(TERM_NAMES, shifts["bias"].tolist())),
                                  "k_shift_sigma_by_prior": {key: dict(zip(TERM_NAMES, v.tolist())) for key, v in shifts.items()},
                                  "prior_dominated": any(np.max(np.abs(v))>1 for v in shifts.values())},
            "crab_sensitivity": {"prior_sigma_deg": list(CRAB_SWEEP_DEG), "fits": sweep,
                                 "k_span_sigma": dict(zip(TERM_NAMES, span.tolist())), "crab_sensitive": bool(np.max(span)>1),
                                 "course_groups": course_groups} if problem.nc else None,
            "chi2_scaling": {"rho_lag1": rho, "scale": scale}, "chi2": {m: s["objective"] for m, s in fixed.items()},
            "chi2_free": free["objective"], "delta_chi2": dbest, "delta_chi2_ci_16_84": None,
            "delta_chi2_vs_free": {m: v*scale for m, v in raw.items()}, "p_vs_free": p,
            "p_asymptotic": asym, "p_bootstrap_calibrated": bootp or None, "bootstrap_inflation": inflation or None,
            "rejected": {m: v<P_REJECT for m, v in p.items()},
            "relative_likelihood": {m: float(v/total) for m, v in relative.items()}, "best_model": min(dbest, key=dbest.get),
            "_rows": (problem.y, J, problem.idx, problem.cb, z)}
