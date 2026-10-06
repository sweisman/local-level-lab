# SPDX-License-Identifier: AGPL-3.0-or-later
"""Phone orientation relative to local level (NED).

- "Up" in the phone frame comes from the accelerometer (the specific-force direction). That's a
  physical plumb line, and it doesn't depend on any Earth model.
- The aircraft's forward axis in the phone frame comes from the roll rate during banked turns.
  Rolling happens about the longitudinal axis, so we correlate the gyro with the bank rate that
  GNSS implies.
- Azimuth comes from the GNSS course.
"""
from __future__ import annotations

import numpy as np

from .models import G0


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def skew(w):
    x, y, z = w
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])


def vee(m):
    return np.array([m[2, 1] - m[1, 2], m[0, 2] - m[2, 0], m[1, 0] - m[0, 1]]) / 2.0


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def c_bn(up_b, fwd_b, azimuth_rad):
    """NED→phone rotation matrix. Its columns are the north, east and down axes in phone coordinates.

    up_b: the up direction in the phone frame (accelerometer). fwd_b: the aircraft forward axis in
    the phone frame (it doesn't have to be exactly horizontal). azimuth_rad: the forward axis
    heading, clockwise from north.
    """
    u = unit(up_b)
    d = -u
    h1 = unit(fwd_b - np.dot(fwd_b, u) * u)
    h2 = np.cross(d, h1)
    ca, sa = np.cos(azimuth_rad), np.sin(azimuth_rad)
    n = ca * h1 - sa * h2
    e = sa * h1 + ca * h2
    return np.column_stack([n, e, d])


def course_rate(t_s, bearing_deg, smooth_s=5.0):
    """Heading rate (rad/s) from the GNSS bearing: unwrapped, then a centred finite difference."""
    psi = np.unwrap(np.radians(bearing_deg))
    if len(psi) < 3:
        return np.zeros_like(psi)
    k = max(1, int(round(smooth_s / max(np.median(np.diff(t_s)), 1e-3) / 2)))
    rate = np.zeros_like(psi)
    if len(psi) <= 2 * k:
        return rate
    rate[k:-k] = (psi[2 * k:] - psi[:-2 * k]) / (t_s[2 * k:] - t_s[:-2 * k])
    rate[:k], rate[-k:] = rate[k], rate[-k - 1]
    return rate


def estimate_forward_axis(gyro_t_s, gyro_b, gnss_t_s, speed, bearing_deg, up_b):
    """Find the aircraft's forward (roll) axis in the phone frame.

    In a coordinated turn, bank = atan(v * psi_dot / g). Rolling into and out of a bank rotates
    the phone about the forward axis, so the horizontal gyro component lines up with the bank
    rate. Positive bank means right wing down, which is positive roll about forward.

    Returns (forward_b or None, quality dict).
    """
    if len(gnss_t_s) < 30:
        return None, {"reason": "too little GNSS"}
    psi_dot = course_rate(gnss_t_s, bearing_deg)
    bank = np.arctan(speed * psi_dot / G0)
    bank_rate = np.gradient(bank, gnss_t_s)
    # gyro averaged into 1-s bins at the GNSS times
    u = unit(up_b)
    idx = np.searchsorted(gyro_t_s, gnss_t_s)
    cs = np.vstack([np.zeros(3), np.cumsum(gyro_b, axis=0)])
    lo = np.searchsorted(gyro_t_s, gnss_t_s - 0.5)
    hi = np.searchsorted(gyro_t_s, gnss_t_s + 0.5)
    n = np.maximum(hi - lo, 1)
    g = (cs[hi] - cs[lo]) / n[:, None]
    ok = (hi - lo) > 0
    ok &= np.isfinite(bank_rate) & (idx > 0) & (idx < len(gyro_t_s))
    g_h = g - (g @ u)[:, None] * u
    br = bank_rate[ok]
    energy = float(np.sum(br ** 2))
    if energy < 1e-4:   # less than about one 15-degree bank event
        return None, {"reason": "no banked turns found", "bank_energy": energy}
    f = (g_h[ok] * br[:, None]).sum(axis=0) / energy
    resid = g_h[ok] - br[:, None] * f
    corr = 1.0 - float(np.sum(resid ** 2) / max(np.sum(g_h[ok] ** 2), 1e-30))
    gain = float(np.linalg.norm(f))
    q = {"gain": gain, "r2": corr, "bank_energy": energy}
    if gain < 0.1 or corr < 0.05:   # only the direction is used; GNSS smoothing lowers the gain
        q["reason"] = "roll/bank correlation too weak"
        return None, q
    from .inference_policy import INFERENCE_POLICY
    # Newey-West covariance of the regression score, with no covariance across GNSS gaps.
    score = np.zeros_like(g_h)
    score[ok] = br[:, None] * resid
    meat = score.T @ score
    lags = min(INFERENCE_POLICY["forward_hac_lags"], len(score)-1)
    for lag in range(1, lags+1):
        continuous = (gnss_t_s[lag:] - gnss_t_s[:-lag]) <= 1.5*lag
        cross = score[lag:][continuous].T @ score[:-lag][continuous]
        meat += (1-lag/(lags+1)) * (cross+cross.T)
    covariance = meat / energy**2
    axis = f/gain
    jac = (np.eye(3)-np.outer(axis, axis))/gain
    axis_cov = jac @ covariance @ jac.T
    tangent = np.cross(u, axis)
    angle_variance = float(tangent @ axis_cov @ tangent)
    q.update(regression_cov=covariance.tolist(), axis_cov=axis_cov.tolist(),
             angle_sigma_rad=float(np.sqrt(max(0., angle_variance))),
             uncertainty_method="horizontal regression, Newey-West", hac_lags=lags)
    return axis, q


TURN_RATE_MIN = np.radians(10.0)   # rad/s: a hand turning the IMU, far above any aircraft rate


def expm_so3(w):
    """Rotation matrix for the rotation vector w (Rodrigues)."""
    a = float(np.linalg.norm(w))
    if a < 1e-12:
        return np.eye(3) + skew(w)
    k = skew(np.asarray(w) / a)
    return np.eye(3) + np.sin(a) * k + (1 - np.cos(a)) * k @ k


def turn_rotation(t_s, gyro_b, t_event, window_s=300.0, pad_s=1.0, sat=None, expected_period=None):
    """The IMU's rotation during a deliberate turn (or a bump), integrated from the gyro.

    The participant turns the IMU, then taps to confirm, so the fast rotation lies in the minutes
    before the event. Integrating the gyro over it is accurate to a small fraction of a degree:
    the rates are tens of °/s for a few seconds, so bias and noise barely matter.

    gyro_b must already have the calibrated bias removed.

    Returns (R, info). R maps vectors from the new IMU frame to the old one: v_old = R v_new.
    R is None if no fast rotation precedes the event (a bump that didn't turn the IMU)."""
    m = np.where((t_s >= t_event - window_s) & (t_s <= t_event))[0]
    if len(m) < 2:
        return None, {"reason": "no IMU data before the event"}
    fast = m[np.linalg.norm(gyro_b[m], axis=1) > TURN_RATE_MIN]
    if len(fast) == 0:
        return None, {"reason": "no fast rotation before the event"}
    # the last burst only: walk back from the latest fast sample while the gaps stay short, so a
    # turbulence jolt minutes earlier can't stretch the interval
    tf = t_s[fast]
    first = len(tf) - 1
    while first > 0 and tf[first] - tf[first - 1] < 3.0:
        first -= 1
    a, b = tf[first] - pad_s, tf[-1] + pad_s
    j = np.where((t_s >= a) & (t_s <= b))[0]
    period = expected_period if expected_period is not None else np.median(np.diff(t_s))
    gaps = np.diff(t_s[j])
    missing = (len(j) < 2 or np.any(gaps > 3 * period * (1 + 1e-6))
               or np.any(gaps <= 0) or t_s[j[0]] - a > 3 * period
               or b - t_s[j[-1]] > 3 * period)
    if missing:
        return np.eye(3), {"t0_s": float(a), "t1_s": float(b), "angle_deg": None,
                          "saturated_samples": 0, "unresolved_gap": True}
    R = np.eye(3)
    for k in j[:-1]:
        R = R @ expm_so3(gyro_b[k] * (t_s[k + 1] - t_s[k]))
    angle = float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))
    n_sat = int(np.sum(sat[j])) if sat is not None else 0
    # a rate beyond the gyro's full scale was clipped, so the integrated angle is too small
    return R, {"t0_s": float(a), "t1_s": float(b), "angle_deg": angle, "saturated_samples": n_sat}


def mount_epochs(t_s, gyro_b, events_s, sat=None, expected_period=None, aircraft_motion=None):
    """Split the flight at deliberate turns and bumps. Returns a list of epochs
    {t0_s, t1_s, R0}, where R0 maps that epoch's IMU frame to the first epoch's (v_0 = R0 v),
    plus the intervals to exclude while the IMU was being turned."""
    epochs = [{"t0_s": -np.inf, "R0": np.eye(3), "turn": None}]
    exclude = []
    consumed_until = -np.inf
    for te, kind in sorted(events_s):
        R, info = turn_rotation(t_s, gyro_b, te, sat=sat, expected_period=expected_period)
        if R is not None and info["t0_s"] <= consumed_until:
            continue  # the same physical burst was already confirmed
        if R is None:
            if kind == "index_turn":
                info["warning"] = "turn logged but no rotation found"
                epochs[-1]["t1_s"] = te
                epochs.append({"t0_s": te, "R0": epochs[-1]["R0"], "orientation_unresolved": True,
                               "turn": {"kind": kind, "angle_deg": None, **info}})
            # a bump: no measurable rotation, keep the frame but exclude the moment itself
            exclude.append((te - 5.0, te + 1.0))
            continue
        epochs[-1]["t1_s"] = info["t0_s"]
        consumed_until = info["t1_s"]
        if aircraft_motion is not None:
            from .maneuvers import turn_motion_check
            info['aircraft_motion'] = turn_motion_check(aircraft_motion, info['t0_s'], info['t1_s'])
        epochs.append({"t0_s": info["t1_s"], "R0": epochs[-1]["R0"] @ R, "turn": {"kind": kind, **info}})
        if (info.get("unresolved_gap") or info.get("saturated_samples") or
                info.get('aircraft_motion', {}).get('safe') is False):
            epochs[-1]["orientation_unresolved"] = True
        exclude.append((info["t0_s"], max(te, info["t1_s"]) + 1.0))
    epochs[-1]["t1_s"] = np.inf
    return epochs, exclude


def epoch_of(t, epochs):
    """Index of the epoch containing each time (−1 inside a turn)."""
    t = np.atleast_1d(t)
    out = np.full(len(t), -1)
    for i, e in enumerate(epochs):
        out[(t >= e["t0_s"]) & (t < e["t1_s"])] = i
    return out
