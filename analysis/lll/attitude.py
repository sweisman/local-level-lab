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
    if gain < 0.3 or corr < 0.05:
        q["reason"] = "roll/bank correlation too weak"
        return None, q
    return f / gain, q
