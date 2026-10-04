# SPDX-License-Identifier: AGPL-3.0-or-later
"""Single-session analysis. Produces a JSON-serialisable result dict."""
from __future__ import annotations

import platform
import subprocess
from pathlib import Path

import numpy as np

from . import __version__, calib, drift, fit, models, slip
from .attitude import epoch_of, estimate_forward_axis, mount_epochs
from .format import read_session
from .segments import Thresholds, find_segments, make_bins


def environment() -> dict:
    """What produced a result: the exact code and numerical libraries, so it can be reproduced."""
    import scipy
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent, capture_output=True,
                                text=True, timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        commit = None
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "git_commit": commit}


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


# Provisional until real units have been measured (docs/BENCH.md).
QUALIFIED_ADEV300_DPH, USABLE_ADEV300_DPH = 3.0, 6.0  # Allan deviation at 300 s, worst axis
QUALIFIED_H_SD_DPH, USABLE_H_SD_DPH = 2.0, 4.0        # repeatability of the horizontal ground rate


def unit_quality(res: dict, m: dict) -> dict:
    """A quality tier for the IMU unit from this session's stationary data.

    The criteria are about the instrument, never about which model wins:
    - Allan deviation at 300 s on the worst axis, from a still run (drift or bench) long enough to
      have that averaging time;
    - repeatability of the horizontal ground rate: the scatter between pairs of the reversal test
      when there is one, else the palindrome calibration's horizontal σ.
    Collation applies to each session the latest tier measured at or before it."""
    a300 = [max(d["adev_at_dph"]["300"]) for d in (res.get("drift") or {}).values()
            if d and d.get("adev_at_dph", {}).get("300")]
    rv = res.get("reversal")
    if rv:
        h, h_src = rv["h_sd_dph"], "reversal test"
    else:
        hsd = [c["earth_h_sd_dph"] for c in (res.get("calibration") or {}).values()]
        h, h_src = (min(hsd), "palindrome calibration") if hsd else (None, None)
    a = min(a300) if a300 else None
    if a is None and h is None:
        tier = "unknown"
    elif a is not None and a <= QUALIFIED_ADEV300_DPH and h is not None and h <= QUALIFIED_H_SD_DPH:
        tier = "qualified"
    elif (a is None or a <= USABLE_ADEV300_DPH) and (h is None or h <= USABLE_H_SD_DPH):
        tier = "usable"
    else:
        tier = "exploratory"
    return {"unit_id": (m.get("imu") or {}).get("unit_id"), "variant": (m.get("imu") or {}).get("variant"),
            "adev_300s_dph": a, "horizontal_repeatability_dph": h, "horizontal_repeatability_from": h_src,
            "tier": tier, "provisional": True,
            "criteria": {"qualified": f"Allan dev. at 300 s ≤ {QUALIFIED_ADEV300_DPH} °/h and horizontal repeatability ≤ {QUALIFIED_H_SD_DPH} °/h",
                         "usable": f"≤ {USABLE_ADEV300_DPH} °/h and ≤ {USABLE_H_SD_DPH} °/h, where measured"}}


def analyze(path, th: Thresholds | None = None) -> dict:
    th = th or Thresholds()
    sess = read_session(path)
    m = sess.manifest
    flags = list(m.get("quality", {}).get("flags", []))
    res = {
        "analysis_version": __version__,
        "environment": environment(),
        "input_sha256": sess.sha256,
        "session_id": m.get("session_id"),
        "created_utc": m.get("created_utc"),
        "kind": m.get("kind", "flight"),
        "flight": m.get("flight", {}),
        "mount": m.get("mount", {}),
        "device": m.get("device", {}),
        "imu": {**(m.get("imu") or {}), "decode": sess.imu_stats},
        "flags": flags,
    }
    st = sess.imu_stats
    if "gyro" not in sess.streams or "accel" not in sess.streams:
        flags.append("no_imu_data")
        return _clean(res)
    if st.get("bytes") and st.get("unparsed_bytes", 0) > 1e-3 * st["bytes"]:
        flags.append("imu_corrupt_bytes")
    if st.get("gyro_range_reported_dps") is not None and st["gyro_range_reported_dps"] != st.get("gyro_range_intended_dps"):
        flags.append("imu_range_differs_from_intended")      # decoded with the range the device reported
    if not st.get("gyro_range_readbacks_consistent", True):
        flags.append("imu_range_inconsistent")              # readbacks disagree: decoded with the intended range
    if st.get("accel_range_reported_g") is not None and st["accel_range_reported_g"] != st.get("accel_range_intended_g"):
        flags.append("imu_accel_range_differs_from_intended")
    if not st.get("accel_range_readbacks_consistent", True):
        flags.append("imu_accel_range_inconsistent")
    # Each phase is one connection. A gap inside a phase means the link dropped.
    gaps = 0
    for ph in m.get("phases", []):
        g = sess.slice("gyro", ph["start_ns"], ph["end_ns"])
        if g is not None and len(g["t_ns"]) > 1:
            gaps += int((np.diff(g["t_ns"]) > 1e9).sum())
    res["imu"]["gaps_in_phases"] = gaps
    if gaps:
        flags.append("imu_link_gaps")

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
    res["drift"] = {n: drift.drift_run(sess, n) for n in ("drift_pre", "drift_post", "bench")}
    res["reversal"] = calib.reversal_test(sess)
    res["unit_quality"] = unit_quality(res, m)
    bias_fn, prior_sigma, bias_mode = drift.bias_model(cal_pre, cal_post, vre_dph=th.vre_budget_dph,
                                                       gsens_dph=th.gsens_budget_dph)
    res["bias_model"] = {"mode": bias_mode, "prior_sigma_dph": (prior_sigma * calib.RAD2DPH).tolist()}
    if cal_pre and cal_post:
        res["bias_model"]["pre_post_change_dph"] = ((cal_post["bias"] - cal_pre["bias"]) * calib.RAD2DPH).tolist()

    flight = sess.phase("flight")
    if flight is None:
        flags.append("no_flight_phase")
        return _clean(res)
    # Mount epochs: deliberate turns of the IMU (and bumps) during the flight. The gyro measures each
    # turn, so later epochs are mapped back into the first epoch's frame exactly.
    gs = sess.slice(sess.gyro_stream(), flight["start_ns"], flight["end_ns"])
    gt = gs["t_ns"] / 1e9
    Gc = np.column_stack([gs["x"], gs["y"], gs["z"]]) - bias_fn(gt)
    ev = [(t / 1e9, kind) for t, kind, _ in sess.events if kind in ("index_turn", "placement_shift")
          and flight["start_ns"] <= t <= flight["end_ns"]]
    epochs, exclude = mount_epochs(gt, Gc, ev, sat=gs.get("sat"))
    res["mount_epochs"] = [{"t0_s": e["t0_s"], "t1_s": e["t1_s"], "turn": e["turn"]} for e in epochs]
    if any(e["turn"] and e["turn"]["kind"] == "index_turn" for e in epochs):
        flags.append("imu_turned_in_flight")
    if any(e["turn"] and e["turn"].get("saturated_samples") for e in epochs):
        flags.append("imu_turn_saturated")     # a hand turn exceeded the gyro's full scale; its angle is unreliable

    segs, kin = find_segments(sess, flight, th, exclude=exclude)
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
    bins["epoch"] = epoch_of(bins["t"], epochs)
    keep = bins["epoch"] >= 0
    # After a turn whose rate was clipped, the IMU's new orientation is unknown (the accelerometer
    # can't see a turn about the vertical), so later epochs can't be mapped and are left out.
    sat_epoch = next((i for i, e in enumerate(epochs) if e["turn"] and e["turn"].get("saturated_samples")), None)
    if sat_epoch is not None:
        keep &= bins["epoch"] < sat_epoch
        res["excluded_after_saturated_turn_s"] = float(epochs[sat_epoch]["t0_s"])
    if not keep.any():
        flags.append("no_bins")
        return _clean(res)
    bins = {k: (v[keep] if isinstance(v, np.ndarray) and len(v) == len(keep) else v) for k, v in bins.items()}
    R0 = np.array([e["R0"] for e in epochs])

    # magnetometer watchdog for slow yaw slip in the mount; segments where the WMM version sees slip
    # are left out of the gyro fit (the no-declination version is a reported cross-check). The choice
    # uses only magnetometer and GPS data, never the gyro. A globe-based selection rule can still
    # shift k if what it drops correlates with the model terms, so the fit is repeated without it.
    bins_all = bins
    hi = next((c.get("mag_hard_iron_counts") for c in (cal_pre, cal_post) if c and c.get("mag_hard_iron_counts")), None)
    gn = sess.streams.get("gnss")
    year = 1970 + float(np.median(gn["utc_ms"])) / 1000 / 86400 / 365.2425 if gn is not None and len(gn["utc_ms"]) else 2026.0
    res["slip"] = slip.watchdog(bins, hi, year, th.max_slip_dph)
    if res["slip"].get("available"):
        if res["slip"]["exclude_segments"]:
            flags.append("mount_slip_detected")
            keep = ~np.isin(bins["seg"], res["slip"]["exclude_segments"])
            bins = {k: (v[keep] if isinstance(v, np.ndarray) and len(v) == len(keep) else v) for k, v in bins.items()}
            if not len(bins["t"]):
                flags.append("no_bins")
                return _clean(res)
    else:
        flags.append("slip_watchdog_unavailable")

    # forward axis from banked turns over the whole flight, in the first epoch's frame
    ge = epoch_of(gt, epochs)
    ok = ge >= 0
    G0 = np.einsum("nij,nj->ni", R0[ge[ok]], Gc[ok])
    up_ref = np.median(np.einsum("nij,nj->ni", R0[bins["epoch"]], bins["up"]), axis=0)
    fwd0, fq = estimate_forward_axis(gt[ok], G0, kin["t"], kin["speed"], np.degrees(kin["psi"]), up_ref)
    res["forward_axis"] = {"axis_b": None if fwd0 is None else fwd0.tolist(), **fq}
    vertical_only = fwd0 is None
    # each bin's forward axis in its own epoch's frame: v_epoch = R0ᵀ v_0
    fwd = None if fwd0 is None else np.einsum("nji,j->ni", R0[bins["epoch"]], fwd0)
    if vertical_only:
        flags.append("no_heading_reference_vertical_only")

    # Temperature: if the IMU is noticeably warmer or colder in cruise than during calibration,
    # fit a per-axis bias-vs-temperature coefficient (prior from drift runs if available).
    temp_ref, temp_prior, temp_mean = None, None, None
    bat = sess.streams.get("imu_temp")
    cal_temps = []
    for ph in sess.phases("cal_"):
        b = sess.slice("imu_temp", ph["start_ns"], ph["end_ns"])
        if b is not None and np.isfinite(b["temp_c"]).any():
            cal_temps.append(np.nanmean(b["temp_c"]))
    if bat is not None and cal_temps and np.isfinite(bins["temp"]).all():
        t_ref = float(np.mean(cal_temps))
        # 90th percentile, not max: one glitchy temperature reading shouldn't switch the term on
        if np.percentile(np.abs(bins["temp"] - t_ref), 90) >= th.min_temp_delta_c:
            temp_ref = t_ref
            # only from drift runs where temperature wasn't confounded with elapsed time
            measured = [d["bias_temp_coef_dph_per_c"] for d in res["drift"].values()
                        if d and d.get("bias_temp_coef_dph_per_c") and not d.get("bias_temp_confounded")]
            if measured:
                # a drift run measured this unit's coefficient: apply it, and fit only the residual
                c = np.mean(measured, axis=0)
                temp_mean = c / calib.RAD2DPH
                temp_prior = np.maximum(0.3 * np.abs(c), 0.2) / calib.RAD2DPH
            else:
                temp_prior = th.temp_prior_dph_per_c / calib.RAD2DPH
            flags.append("temperature_term")
    res["temperature"] = {"cal_mean_c": float(np.mean(cal_temps)) if cal_temps else None,
                          "cruise_min_c": float(np.nanmin(bins["temp"])) if np.isfinite(bins["temp"]).any() else None,
                          "cruise_max_c": float(np.nanmax(bins["temp"])) if np.isfinite(bins["temp"]).any() else None,
                          "term_used": temp_ref is not None,
                          "coefficient_source": None if temp_ref is None else ("drift_run" if temp_mean is not None else "free_fit"),
                          "prior_dph_per_c": None if temp_prior is None else (np.asarray(temp_prior) * calib.RAD2DPH).tolist()}

    f = fit.fit(bins, fwd, bias_fn, prior_sigma, vertical_only=vertical_only, temp_ref=temp_ref, temp_prior=temp_prior,
                temp_mean=temp_mean)
    if temp_ref is not None and temp_mean is None:
        # A freely fitted temperature term can absorb signal. Report what k would be without it,
        # and flag the session when that moves any k by more than 1σ.
        f0 = fit.fit(bins, fwd, bias_fn, prior_sigma, vertical_only=vertical_only, n_boot=0)
        shift = {n: (f["k"][n] - f0["k"][n]) / f["k_sd"][n] for n in fit.TERM_NAMES}
        res["temperature"]["k_without_term"] = f0["k"]
        res["temperature"]["k_shift_sigma"] = shift
        if max(abs(v) for v in shift.values()) > 1.0:
            flags.append("temperature_sensitive")
    if not f["identifiability"]["identified"]:
        flags.append("k_not_identified")       # curvature indistinguishable from bias on this flight
    ibt = f["identifiability"]["identified_by_term"]
    if not ibt["k_rot_sphere"]:
        flags.append("k_rot_not_identified")
    if not ibt["k_disc"]:
        flags.append("k_disc_not_identified")  # e.g. no change in east velocity along the route
    if f["prior_sensitivity"]["prior_dominated"]:
        flags.append("prior_dominated")        # a nuisance prior (bias, crab, temperature), not the data, is setting k
    cs = f.get("crab_sensitivity")
    if cs and cs["crab_sensitive"]:
        # k moves by more than 1σ across crab priors of 3–15°. Informational only: the sweep shows how
        # much the error bars lean on the prior, not crab bias (EVIDENCE §11), so it isn't a gate.
        flags.append("crab_sensitive")
    if cs and cs["course_groups"] == 1:
        flags.append("single_heading")
    if bins_all is not bins:
        fa = None if fwd0 is None else np.einsum("nji,j->ni", R0[bins_all["epoch"]], fwd0)
        fw = fit.fit(bins_all, fa, bias_fn, prior_sigma, vertical_only=vertical_only, temp_ref=temp_ref,
                     temp_prior=temp_prior, temp_mean=temp_mean)
        moved = {n: (f["k"][n] - fw["k"][n]) / f["k_sd"][n] for n in fit.TERM_NAMES}
        res["fit_no_wmm_exclusion"] = {"k": fw["k"], "k_sd": fw["k_sd"], "rejected": fw["rejected"],
                                       "k_shift_sigma": moved}
        if fw["rejected"] != f["rejected"] or max(abs(v) for v in moved.values()) > 1.0:
            flags.append("wmm_selection_sensitive")
    y, X, idx, cbns, theta = f["_rows"]
    res["fit"] = f
    res["fit"]["expected_k"] = models.EXPECTED_K
    res["accumulated"] = fit.accumulated(bins, cbns, y, idx, vertical_only)
    res["cruise_minutes"] = float(bins["dt"].sum() / 60)
    return _clean(res)
