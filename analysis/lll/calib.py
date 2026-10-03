# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stationary ground calibration: sensor bias, plus a ground-level Earth-rate measurement.

The IMU lies still in four positions: label up, label up turned 180° about vertical, label down,
and label down turned 180°. The app records them as a palindrome (up0 up180 down0 down180
down180 down0 up180 up0, the middle one a single double-length stay), so every position is
visited twice in mirror order. Older sessions have the four positions once.

Model, per axis, for each visit k at mid-time t_k in position p_k:

    m_k = b + d (t_k − t̄) + w_{p_k},   with  Σ_p w_p = 0

b is the bias at t̄, d a linear drift (fitted only when there are more visits than positions), and
w_p is whatever the sensor sees in position p beyond its bias: the Earth's rotation, whatever its
form, plus any gyro error that depends on gravity (g-sensitivity).

- Bias. Every term that is fixed in the local frame or follows gravity flips sign between up and
  down or between the 180° pairs, so Σ w_p = 0 holds and b is the pure sensor bias.
- Horizontal Earth rate. Within a 180° pair (up0/up180, or down0/down180) gravity sits on the same
  sensor axis, so g-sensitivity is identical and cancels in (w_0 − w_180)/2. The Earth's horizontal
  component reverses. So this measurement is immune to g-sensitivity: a rotating globe gives
  Ω|cos φ|, a disc or a still Earth gives zero.
- Vertical. Rotation about the plumb line can't be separated from g-sensitivity along it in any
  stationary test, because both follow the plumb line. It is reported, but flagged as aliased.
"""
from __future__ import annotations

import numpy as np

from .attitude import unit

POSITIONS = ("up0", "up180", "down0", "down180")
RAD2DPH = np.degrees(1.0) * 3600.0   # rad/s → deg/h


def _still_mean(sess, stream, start, end, trim_s=10.0):
    s = sess.slice(stream, start + int(trim_s * 1e9), end - int(trim_s * 1e9))
    if s is None or len(s["t_ns"]) < 10:
        return None, None, 0
    v = np.column_stack([s["x"], s["y"], s["z"]])
    return v.mean(axis=0), v.std(axis=0) / np.sqrt(len(v)), len(v)


def _visits(sess, prefix):
    """Usable visits {name: dict}. A redone visit (same name) replaces the earlier try."""
    phs = {}
    for ph in sess.phases(prefix + "."):
        phs[ph["name"]] = ph
    out = []
    for name, ph in phs.items():
        pos = name.split(".")[1]
        if pos not in POSITIONS:
            continue
        g, g_sem, n = _still_mean(sess, sess.gyro_stream(), ph["start_ns"], ph["end_ns"])
        a, _, _ = _still_mean(sess, "accel", ph["start_ns"], ph["end_ns"])
        mg, _, _ = _still_mean(sess, "mag", ph["start_ns"], ph["end_ns"], trim_s=5.0) if "mag" in sess.streams else (None, 0, 0)
        if g is None or a is None:
            continue
        out.append({"name": name, "pos": pos, "g": g, "g_sem": g_sem, "up": unit(a), "n": n, "mag": mg,
                    "t": (ph["start_ns"] + ph["end_ns"]) / 2e9})
    return out


def calibrate(sess, prefix: str) -> dict | None:
    """Analyse cal_pre or cal_post. Returns None unless every position has at least one visit."""
    vis = _visits(sess, prefix)
    if {v["pos"] for v in vis} != set(POSITIONS):
        return None
    t = np.array([v["t"] for v in vis])
    tbar = t.mean()
    fit_drift = len(vis) > len(POSITIONS)
    # design: b, [d], w_up0, w_up180, w_down0 (w_down180 = −the sum of the other three)
    cols = 1 + fit_drift + 3
    X = np.zeros((len(vis), cols))
    X[:, 0] = 1.0
    if fit_drift:
        X[:, 1] = (t - tbar) / 3600.0
    for i, v in enumerate(vis):
        j = POSITIONS.index(v["pos"])
        if j < 3:
            X[i, 1 + fit_drift + j] = 1.0
        else:
            X[i, 1 + fit_drift:] = -1.0
    M = np.array([v["g"] for v in vis])                       # (visits, 3 axes)
    theta, *_ = np.linalg.lstsq(X, M, rcond=None)              # (cols, 3)
    XtX_inv = np.linalg.pinv(X.T @ X)
    resid = M - X @ theta
    dof = len(vis) - cols
    sem = np.sqrt(np.mean([v["g_sem"] ** 2 for v in vis], axis=0))   # white-noise floor per visit
    if dof > 0:
        sig = np.maximum(np.sqrt((resid ** 2).sum(axis=0) / dof), sem)  # includes re-placement scatter
    else:
        sig = sem
    cov_scale = np.diag(XtX_inv)
    b = theta[0]
    d = theta[1] if fit_drift else np.zeros(3)
    wk = theta[1 + fit_drift:]
    w = {p: wk[i] for i, p in enumerate(POSITIONS[:3])}
    w["down180"] = -wk.sum(axis=0)
    # per-position variance (per axis), ignoring covariances: good enough for error bars
    var_w = {p: sig ** 2 * cov_scale[1 + fit_drift + i] for i, p in enumerate(POSITIONS[:3])}
    var_w["down180"] = sig ** 2 * np.sum(XtX_inv[1 + fit_drift:, 1 + fit_drift:])
    up = {p: unit(np.mean([v["up"] for v in vis if v["pos"] == p], axis=0)) for p in POSITIONS}

    pairs = {}
    for face in ("up", "down"):
        a, c = f"{face}0", f"{face}180"
        u = unit(up[a] + up[c])
        h = (w[a] - w[c]) / 2
        h = h - (h @ u) * u
        var_h = (var_w[a] + var_w[c]) / 4
        raw = float(np.linalg.norm(h))
        noise2 = float(var_h.sum())                        # E|noise|² across the horizontal plane
        pairs[face] = {"raw": raw, "debiased": float(np.sqrt(max(raw ** 2 - noise2, 0.0))),
                       "sd": float(np.sqrt(noise2 / 2)), "vertical": float((w[a] + w[c]) @ u / 2)}
    h_raw = np.mean([pairs[f]["raw"] for f in pairs])
    h_est = np.mean([pairs[f]["debiased"] for f in pairs])
    h_sd = max(np.sqrt(sum(pairs[f]["sd"] ** 2 for f in pairs)) / 2, abs(pairs["up"]["raw"] - pairs["down"]["raw"]) / 2)
    v_est = np.mean([pairs[f]["vertical"] for f in pairs])
    v_sd = max(abs(pairs["up"]["vertical"] - pairs["down"]["vertical"]) / 2,
               float(np.sqrt(np.mean([var_w[p] @ (up[p] ** 2) for p in POSITIONS]) / 4)))
    # The IMU's own magnetic offset (hard iron): the Earth's field cancels over the four positions
    # exactly as the Earth's rotation does, leaving the field fixed in the IMU.
    mags = {p: [v["mag"] for v in vis if v["pos"] == p and v["mag"] is not None] for p in POSITIONS}
    hard_iron = (np.mean([np.mean(mags[p], axis=0) for p in POSITIONS], axis=0)
                 if all(mags[p] for p in POSITIONS) else None)
    return {
        "mag_hard_iron_counts": None if hard_iron is None else hard_iron.tolist(),
        "bias": b,
        "bias_sem": sig * np.sqrt(cov_scale[0]),
        "t_mid_s": float(tbar),
        "visits": len(vis),
        "sequence": "palindrome" if fit_drift else "single",
        "drift_dph_per_h": (d * RAD2DPH).tolist() if fit_drift else None,
        "earth_h_dph": float(h_est * RAD2DPH),
        "earth_h_raw_dph": float(h_raw * RAD2DPH),
        "earth_h_sd_dph": float(h_sd * RAD2DPH),
        "earth_up_dph": float(v_est * RAD2DPH),
        "earth_up_sd_dph": float(v_sd * RAD2DPH),
        "earth_up_aliased_with_g_sensitivity": True,
        "positions": {p: {"up": up[p].tolist(), "w_dph": (w[p] * RAD2DPH).tolist()} for p in POSITIONS},
    }


def ground_model_predictions(lat_deg):
    """Predicted (up, horizontal) ground rotation, deg/h, for each model at this latitude."""
    from .models import OMEGA_E
    w = OMEGA_E * RAD2DPH
    lat = np.radians(lat_deg)
    return {
        "sphere_rotating": (w * np.sin(lat), w * abs(np.cos(lat))),
        "sphere_still": (0.0, 0.0),
        "flat_still": (0.0, 0.0),
    }
