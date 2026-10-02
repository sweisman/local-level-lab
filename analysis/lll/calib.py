# SPDX-License-Identifier: AGPL-3.0-or-later
"""4-position stationary calibration: sensor bias, plus a ground-level Earth-rate measurement.

The positions are face up, face up turned 180° about vertical, face down, and face down turned
180°. Any rotation that's constant in the local frame (Earth rotation, whatever its form)
projects onto the phone axes with signs that cancel across the four positions. So the mean of the
four is the sensor bias alone. What's left over in each position, split into the part along the
accelerometer's up and the part across it, gives the up and horizontal components of the ground
rotation rate. No compass or heading is needed.
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


def calibrate(sess, prefix: str) -> dict | None:
    """Analyse cal_pre or cal_post. Returns None if the phase is missing or incomplete."""
    gs = sess.gyro_stream()
    pos = {}
    for p in POSITIONS:
        ph = sess.phase(f"{prefix}.{p}")
        if ph is None:
            return None
        g, g_sem, n = _still_mean(sess, gs, ph["start_ns"], ph["end_ns"])
        a, _, _ = _still_mean(sess, "accel_uncal" if "accel_uncal" in sess.streams else "accel",
                              ph["start_ns"], ph["end_ns"])
        if g is None or a is None:
            return None
        pos[p] = {"g": g, "g_sem": g_sem, "up": unit(a), "n": n,
                  "t_mid_s": (ph["start_ns"] + ph["end_ns"]) / 2e9}
    bias = np.mean([pos[p]["g"] for p in POSITIONS], axis=0)
    up_rates, h_rates = [], []
    for p in POSITIONS:
        w = pos[p]["g"] - bias
        v = float(w @ pos[p]["up"])
        up_rates.append(v)
        h_rates.append(float(np.linalg.norm(w - v * pos[p]["up"])))
    up_rates, h_rates = np.array(up_rates), np.array(h_rates)
    # Uncertainty: the scatter of the four position estimates (bias instability shows up here),
    # floored by white-noise error.
    sem = np.sqrt(np.mean([pos[p]["g_sem"] ** 2 for p in POSITIONS], axis=0))
    return {
        "bias": bias,
        "bias_sem": sem,
        "t_mid_s": float(np.mean([pos[p]["t_mid_s"] for p in POSITIONS])),
        "earth_up_dph": float(up_rates.mean() * RAD2DPH),
        "earth_up_sd_dph": float(max(up_rates.std(ddof=1) / 2, np.linalg.norm(sem)) * RAD2DPH),
        "earth_h_dph": float(h_rates.mean() * RAD2DPH),
        "earth_h_sd_dph": float(max(h_rates.std(ddof=1) / 2, np.linalg.norm(sem)) * RAD2DPH),
        "positions": {p: {"up": pos[p]["up"].tolist(), "g_dph": (pos[p]["g"] * RAD2DPH).tolist()}
                      for p in POSITIONS},
    }


def ground_model_predictions(lat_deg):
    """Predicted (up, horizontal) ground rotation, deg/h, for each model at this latitude."""
    from .models import OMEGA_E
    w = OMEGA_E * RAD2DPH
    lat = np.radians(lat_deg)
    return {
        "sphere_rotating": (w * np.sin(lat), w * abs(np.cos(lat))),
        "sphere_still": (0.0, 0.0),
        "flat_rotating": (w, 0.0),
        "flat_still": (0.0, 0.0),
    }
