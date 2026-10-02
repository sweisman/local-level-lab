# SPDX-License-Identifier: AGPL-3.0-or-later
"""Single-session analysis. Produces a JSON-serialisable result dict."""
from __future__ import annotations

import numpy as np

from . import __version__, calib, drift, fit, models
from .attitude import estimate_forward_axis
from .format import read_session
from .segments import Thresholds, find_segments, make_bins


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


def analyze(path, th: Thresholds | None = None) -> dict:
    th = th or Thresholds()
    sess = read_session(path)
    m = sess.manifest
    flags = list(m.get("quality", {}).get("flags", []))
    res = {
        "analysis_version": __version__,
        "input_sha256": sess.sha256,
        "session_id": m.get("session_id"),
        "flight": m.get("flight", {}),
        "mount": m.get("mount", {}),
        "device": m.get("device", {}),
        "gyro_stream": sess.gyro_stream(),
        "flags": flags,
    }
    if sess.gyro_stream() != "gyro_uncal":
        flags.append("no_uncalibrated_gyro")

    # calibration, ground Earth-rate measurement, drift
    cal_pre, cal_post = calib.calibrate(sess, "cal_pre"), calib.calibrate(sess, "cal_post")
    lat_cal = m.get("privacy", {}).get("cal_lat_deg")
    res["calibration"] = {}
    for name, c in (("pre", cal_pre), ("post", cal_post)):
        if c is None:
            flags.append(f"no_cal_{name}")
            continue
        rec = {k: v for k, v in c.items() if k not in ("bias", "bias_sem")}
        rec["bias_dph"] = (c["bias"] * calib.RAD2DPH).tolist()
        rec["bias_sem_dph"] = (c["bias_sem"] * calib.RAD2DPH).tolist()
        if lat_cal is not None:
            rec["lat_deg"] = lat_cal
            rec["predicted"] = calib.ground_model_predictions(lat_cal)
        res["calibration"][name] = rec
    res["drift"] = {n: drift.drift_run(sess, n) for n in ("drift_pre", "drift_post")}
    bias_fn, prior_sigma, bias_mode = drift.bias_model(cal_pre, cal_post)
    res["bias_model"] = {"mode": bias_mode, "prior_sigma_dph": (prior_sigma * calib.RAD2DPH).tolist()}
    if cal_pre and cal_post:
        res["bias_model"]["pre_post_change_dph"] = ((cal_post["bias"] - cal_pre["bias"]) * calib.RAD2DPH).tolist()

    flight = sess.phase("flight")
    if flight is None:
        flags.append("no_flight_phase")
        return _clean(res)
    segs, kin = find_segments(sess, flight, th)
    res["segments"] = [{"t0_s": a, "t1_s": b, "minutes": (b - a) / 60} for a, b in segs]
    if kin is not None:
        step = max(1, len(kin["t"]) // 2000)
        res["track"] = {k: np.asarray(kin[k][::step]).tolist() for k in ("t", "lat", "lon", "h", "speed", "vz")}
        res["track"]["lat"] = np.degrees(res["track"]["lat"]).tolist()
        res["track"]["lon"] = np.degrees(res["track"]["lon"]).tolist()
    if not segs:
        flags.append("no_stable_cruise")
        return _clean(res)
    bins = make_bins(sess, segs, kin, th)
    if bins is None:
        flags.append("no_bins")
        return _clean(res)

    # forward axis from banked turns over the whole flight
    gs = sess.slice(sess.gyro_stream(), flight["start_ns"], flight["end_ns"])
    G = np.column_stack([gs["x"], gs["y"], gs["z"]])
    up_ref = np.median(bins["up"], axis=0)
    fwd, fq = estimate_forward_axis(gs["t_ns"] / 1e9, G - bias_fn(gs["t_ns"] / 1e9), kin["t"],
                                    kin["speed"], np.degrees(kin["psi"]), up_ref)
    res["forward_axis"] = {"axis_b": None if fwd is None else fwd.tolist(), **fq}
    vertical_only = fwd is None
    if vertical_only:
        flags.append("no_heading_reference_vertical_only")

    f = fit.fit(bins, fwd, bias_fn, prior_sigma, vertical_only=vertical_only)
    y, X, idx, cbns, theta = f["_rows"]
    res["fit"] = f
    res["fit"]["expected_k"] = models.EXPECTED_K
    res["accumulated"] = fit.accumulated(bins, cbns, y, idx, vertical_only)
    res["cruise_minutes"] = float(bins["dt"].sum() / 60)
    return _clean(res)
