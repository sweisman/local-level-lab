# SPDX-License-Identifier: AGPL-3.0-or-later
"""Gyro bias stability: Allan deviation from the still drift runs, the change in bias from pre to
post calibration, and bias against IMU chip temperature."""
from __future__ import annotations

import numpy as np

from .calib import RAD2DPH


FIXED_TAUS_S = (60.0, 300.0, 900.0, 1800.0)


def allan_deviation(x, fs, n_taus=20, taus_s=None):
    """Overlapping Allan deviation of a rate series x (N, 3) sampled at fs Hz, on a log grid of
    averaging times, or at the given taus_s (those longer than a third of the run are skipped)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 100:
        return np.array([]), np.empty((0, 3))
    theta = np.vstack([np.zeros(3), np.cumsum(x, axis=0)]) / fs
    m_max = n // 3
    if taus_s is not None:
        ms = np.array([int(round(t * fs)) for t in taus_s if 1 <= round(t * fs) <= m_max], int)
    else:
        ms = np.unique(np.logspace(0, np.log10(m_max), n_taus).astype(int))
    taus, adev = [], []
    for m in ms:
        tau = m / fs
        d = theta[2 * m:] - 2 * theta[m:-m] + theta[:-2 * m]
        adev.append(np.sqrt(np.mean(d ** 2, axis=0) / (2 * tau ** 2)))
        taus.append(tau)
    return np.array(taus), np.array(adev)


def drift_run(sess, name):
    ph = sess.phase(name)
    if ph is None:
        return None
    s = sess.slice(sess.gyro_stream(), ph["start_ns"], ph["end_ns"])
    if s is None or len(s["t_ns"]) < 1000:
        return None
    g = np.column_stack([s["x"], s["y"], s["z"]])
    fs = 1e9 / np.median(np.diff(s["t_ns"]))
    taus, adev = allan_deviation(g, fs)
    ft, fa = allan_deviation(g, fs, taus_s=FIXED_TAUS_S)
    out = {"duration_s": float((s["t_ns"][-1] - s["t_ns"][0]) / 1e9),
           "tau_s": taus.tolist(), "adev_dph": (adev * RAD2DPH).tolist(),
           # The minimum of the curve is descriptive only: it depends on run length and estimator.
           # Fixed averaging times are comparable between units and runs.
           "bias_instability_dph": (adev.min(axis=0) * RAD2DPH).tolist() if len(adev) else None,
           "adev_at_dph": {f"{t:.0f}": (a * RAD2DPH).tolist() for t, a in zip(ft, fa)}}
    # bias vs temperature, using 60-s bins against the IMU chip temperature
    bat = sess.slice("imu_temp", ph["start_ns"], ph["end_ns"])
    if bat is not None and len(bat["t_ns"]) > 5 and np.ptp(bat["temp_c"]) >= 1.0:
        edges = np.arange(s["t_ns"][0], s["t_ns"][-1], int(60e9))
        mids, means = [], []
        for a, b in zip(edges[:-1], edges[1:]):
            m = (s["t_ns"] >= a) & (s["t_ns"] < b)
            if m.sum() > 10:
                mids.append((a + b) / 2)
                means.append(g[m].mean(axis=0))
        temp = np.interp(mids, bat["t_ns"], bat["temp_c"])
        coef = np.polyfit(temp, np.array(means), 1)[0]
        out["bias_temp_coef_dph_per_c"] = (coef * RAD2DPH).tolist()
    return out


def bias_model(cal_pre, cal_post, floor_dph=1.0, vre_dph=5.0, gsens_dph=5.0):
    """Gyro bias as a function of time (linear between the two calibrations), plus a per-axis 1σ
    prior on the residual bias the in-flight fit can't see.

    The prior is deliberately wide. Besides the change between calibrations it includes two
    in-flight effects the ground calibration can't see: vibration rectification (engines and
    airflow) and g-sensitivity times gravity (the 4-position bias estimate cancels it by design).
    A tight prior would let those offsets leak into k."""
    floor = np.sqrt(floor_dph ** 2 + vre_dph ** 2 + gsens_dph ** 2) / RAD2DPH
    if cal_pre and cal_post:
        b0, b1 = cal_pre["bias"], cal_post["bias"]
        t0, t1 = cal_pre["t_mid_s"], cal_post["t_mid_s"]
        sigma = np.sqrt((np.abs(b1 - b0) / 2) ** 2 + cal_pre["bias_sem"] ** 2 + floor ** 2)

        def f(t_s):
            w = np.clip((np.asarray(t_s) - t0) / (t1 - t0), 0, 1)[..., None]
            return b0 + w * (b1 - b0)
        return f, sigma, "pre+post"
    cal = cal_pre or cal_post
    if cal:
        # one calibration: assume typical MEMS in-run stability (few deg/h) as prior
        sigma = np.sqrt(cal["bias_sem"] ** 2 + (5.0 / RAD2DPH) ** 2 + floor ** 2)
        return (lambda t_s: np.broadcast_to(cal["bias"], np.shape(t_s) + (3,))), sigma, "single"
    return (lambda t_s: np.zeros(np.shape(t_s) + (3,))), np.full(3, 3600.0 / RAD2DPH), "none"
