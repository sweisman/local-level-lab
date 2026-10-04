# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pick out stable cruise and average it into fixed-length bins."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .attitude import course_rate, unit


class InvalidGnssData(ValueError):
    """Conflicting observations at the same monotonic timestamp."""


def unique_fixes(gn):
    order = np.argsort(gn["t_ns"], kind="stable")
    keep = []
    for i in order:
        if keep and gn["t_ns"][i] == gn["t_ns"][keep[-1]]:
            if not all(np.array_equal(np.asarray(v[i]), np.asarray(v[keep[-1]]), equal_nan=True)
                       for v in gn.values()):
                raise InvalidGnssData(f"conflicting fixes at t_ns={gn['t_ns'][i]}")
        else:
            keep.append(i)
    return {k: np.asarray(v)[keep] for k, v in gn.items()}


@dataclass
class Thresholds:
    min_speed_mps: float = 100.0
    max_vz_mps: float = 1.5
    max_turn_dps: float = 0.05        # deg/s (meridian convergence is << this, turns are ~3)
    max_accel_sd: float = 0.6         # m/s², 1-s RMS of |a|: light turbulence
    max_h_acc_m: float = 100.0
    min_segment_s: float = 600.0
    bin_s: float = 60.0
    min_temp_delta_c: float = 2.0         # cruise vs calibration temperature that switches on the temp term
    temp_prior_dph_per_c: float = 5.0     # 1σ prior on |bias change| per °C without drift-run data
    vre_budget_dph: float = 5.0           # vibration rectification: in flight only, unseen by ground calibration
    gsens_budget_dph: float = 5.0         # g-sensitivity × gravity: unseen by the 4-position bias estimate
    grav_cluster_cos: float = 0.9         # bins whose up directions agree this well share one residual bias
    max_slip_dph: float = 1.5             # mount yaw slip the watchdog tolerates (either version)
    max_bearing_acc_deg: float = 3.0      # receiver's own course accuracy, where it reports one
    max_course_mismatch_deg: float = 5.0  # receiver course against the course from the coordinates


def _smooth_grad(t, x, win_s):
    if len(t) < 3:
        return np.zeros_like(x)
    k = max(1, int(round(win_s / max(np.median(np.diff(t)), 1e-3) / 2)))
    g = np.zeros_like(x)
    if len(x) > 2 * k:
        g[k:-k] = (x[2 * k:] - x[:-2 * k]) / (t[2 * k:] - t[:-2 * k])
        g[:k], g[-k:] = g[k], g[-k - 1]
    return g


def _fill_course(t, brg, ok):
    """Course (deg) with the invalid epochs interpolated, unwrapped, from their valid neighbours.
    For smoothing only: those epochs are excluded from cruise anyway."""
    if ok.sum() < 2:
        return np.zeros_like(t)
    return np.degrees(np.interp(t, t[ok], np.unwrap(np.radians(brg[ok])))) % 360.0


def gnss_kinematics(gn, th: Thresholds | None = None):
    """GNSS kinematics, plus bearing_ok: the receiver gave a finite course, within its accuracy
    limit, that agrees with the course computed from successive coordinates. A missing course is
    never turned into north."""
    th = th or Thresholds()
    gn = unique_fixes(gn)
    t = gn["t_ns"] / 1e9
    lat, lon = np.radians(gn["lat"]), np.radians(gn["lon"])
    brg = np.asarray(gn["bearing_deg"], float)
    ok = np.isfinite(brg)
    acc = gn.get("bearing_acc_deg")
    if acc is not None:
        acc = np.asarray(acc, float)
        ok &= ~(np.isfinite(acc) & (acc > th.max_bearing_acc_deg))
    # course from the coordinates themselves, as a cross-check on the receiver's bearing
    dn = _smooth_grad(t, lat, 30.0)
    de = _smooth_grad(t, np.unwrap(lon), 30.0) * np.cos(lat)
    course_xy = np.degrees(np.arctan2(de, dn))
    moving = np.hypot(dn, de) > 0
    mism = np.abs((np.nan_to_num(brg) - course_xy + 180.0) % 360.0 - 180.0)
    ok &= ~(moving & (mism > th.max_course_mismatch_deg))
    # only missing courses are filled; a poor or mismatched one is kept for the turn detector
    # (which needs the real course through banked turns) and is merely excluded from cruise
    brg_f = _fill_course(t, brg, np.isfinite(brg))
    psi = np.radians(brg_f)
    spd = np.nan_to_num(gn["speed_mps"])
    return {
        "t": t, "lat": lat, "lon": lon, "h": gn["alt_m"],
        "speed": spd, "psi": psi, "v_n": spd * np.cos(psi), "v_e": spd * np.sin(psi),
        "vz": _smooth_grad(t, gn["alt_m"], 30.0),
        # dλ/dt straight from the coordinates, for the disc model (no velocity, no radius)
        "lon_rate": _smooth_grad(t, np.unwrap(lon), 30.0),
        "psi_dot": course_rate(t, brg_f, smooth_s=30.0),
        "h_acc": np.nan_to_num(gn["h_acc_m"], nan=999.0),
        "bearing_ok": ok,
    }


def find_segments(sess, flight, th: Thresholds, exclude=()):
    """Stable-cruise intervals [(t0_s, t1_s)] inside the flight phase, plus kinematics."""
    gn = sess.slice("gnss", flight["start_ns"], flight["end_ns"])
    if gn is not None:
        gn = unique_fixes(gn)
    if gn is None or len(gn["t_ns"]) < 60:
        return [], None
    kin = gnss_kinematics(gn, th)
    acc = sess.slice("accel", flight["start_ns"], flight["end_ns"])
    at = acc["t_ns"] / 1e9
    amag = np.sqrt(acc["x"] ** 2 + acc["y"] ** 2 + acc["z"] ** 2)
    # 1-s RMS of |a| around each GNSS epoch
    cs, cs2 = np.concatenate([[0], np.cumsum(amag)]), np.concatenate([[0], np.cumsum(amag ** 2)])
    lo, hi = np.searchsorted(at, kin["t"] - 0.5), np.searchsorted(at, kin["t"] + 0.5)
    n = np.maximum(hi - lo, 1)
    var = (cs2[hi] - cs2[lo]) / n - ((cs[hi] - cs[lo]) / n) ** 2
    a_sd = np.sqrt(np.maximum(var, 0))
    ok = ((kin["speed"] > th.min_speed_mps) & (np.abs(kin["vz"]) < th.max_vz_mps)
          & (np.abs(np.degrees(kin["psi_dot"])) < th.max_turn_dps) & (a_sd < th.max_accel_sd)
          & (kin["h_acc"] < th.max_h_acc_m) & kin["bearing_ok"] & (hi > lo))
    for a, b in exclude:   # while the IMU was being turned or bumped
        ok &= ~((kin["t"] >= a) & (kin["t"] <= b))
    # placement shifts, deliberate turns of the IMU and link drops all break segments
    shifts = [t / 1e9 for t, kind, _ in sess.events if kind in ("placement_shift", "index_turn", "imu_disconnect")]
    segs, start = [], None
    t = kin["t"]
    for i in range(len(t)):
        brk = start is not None and any(t[i - 1] < s <= t[i] for s in shifts)
        gap = i > 0 and t[i] - t[i - 1] > 5.0
        if ok[i] and start is None:
            start = i
        elif start is not None and (not ok[i] or brk or gap):
            segs.append((t[start], t[i - 1]))
            start = i if (ok[i] and not gap) else None
    if start is not None:
        segs.append((t[start], t[-1]))
    segs = [(a, b) for a, b in segs if b - a >= th.min_segment_s]
    return segs, kin


def make_bins(sess, segs, kin, th: Thresholds):
    """Average gyro, accel and kinematics into bins. Returns a dict of arrays (n_bins, ...)."""
    gs = sess.streams[sess.gyro_stream()]
    ac = sess.streams["accel"]
    gt, at = gs["t_ns"] / 1e9, ac["t_ns"] / 1e9
    bat = sess.streams.get("imu_temp")  # the IMU chip temperature
    bat_ok = bat is not None and np.isfinite(bat["temp_c"]).sum() >= 2
    mg = sess.streams.get("mag")
    mt = mg["t_ns"] / 1e9 if mg is not None else None
    M = np.column_stack([mg["x"], mg["y"], mg["z"]]) if mg is not None else None
    G = np.column_stack([gs["x"], gs["y"], gs["z"]])
    A = np.column_stack([ac["x"], ac["y"], ac["z"]])
    rows = []
    for si, (t0, t1) in enumerate(segs):
        nb = int((t1 - t0) // th.bin_s)
        for j in range(nb):
            a, b = t0 + j * th.bin_s, t0 + (j + 1) * th.bin_s
            gm = (gt >= a) & (gt < b)
            am = (at >= a) & (at < b)
            km = (kin["t"] >= a) & (kin["t"] < b)
            if gm.sum() < 10 or am.sum() < 10 or km.sum() < 5:
                continue
            g = G[gm]
            rows.append({
                "seg": si, "t": (a + b) / 2, "dt": b - a,
                "gyro": g.mean(axis=0), "gyro_sem": g.std(axis=0) / np.sqrt(len(g)),
                "up": unit(A[am].mean(axis=0)),
                "lat": kin["lat"][km].mean(), "lon": np.angle(np.mean(np.exp(1j * kin["lon"][km]))), "h": kin["h"][km].mean(),
                "mag": (M[(mt >= a) & (mt < b)].mean(axis=0) if M is not None and ((mt >= a) & (mt < b)).sum() >= 5
                        else np.full(3, np.nan)),
                "v_n": kin["v_n"][km].mean(), "v_e": kin["v_e"][km].mean(), "lon_rate": kin["lon_rate"][km].mean(),
                "psi": np.arctan2(np.sin(kin["psi"][km]).mean(), np.cos(kin["psi"][km]).mean()),
                "psi_dot": kin["psi_dot"][km].mean(),
                "speed": kin["speed"][km].mean(),
                "temp": float(np.interp((a + b) / 2, bat["t_ns"][np.isfinite(bat["temp_c"])] / 1e9,
                                        bat["temp_c"][np.isfinite(bat["temp_c"])])) if bat_ok else np.nan,
            })
    if not rows:
        return None
    out = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    # du/dt within each segment (central differences): the phone's tilt rate relative to the
    # plumb line, i.e. aircraft pitch/roll changes such as trim drift as fuel burns
    du = np.zeros_like(out["up"])
    for s in np.unique(out["seg"]):
        idx = np.where(out["seg"] == s)[0]
        if len(idx) >= 2:
            du[idx] = np.gradient(out["up"][idx], out["t"][idx], axis=0)
    out["dup_dt"] = du
    out["grav"] = gravity_clusters(out["up"], th.grav_cluster_cos)
    return out


def gravity_clusters(up, min_cos):
    """Label bins by the IMU's attitude relative to gravity. A flip, or a turn that moves gravity
    to another sensor axis, starts a new cluster; slow tilt within ~25° does not."""
    refs, lab = [], np.zeros(len(up), int)
    for i, u in enumerate(up):
        for c, r in enumerate(refs):
            if u @ r >= min_cos:
                lab[i] = c
                break
        else:
            refs.append(u)
            lab[i] = len(refs) - 1
    return lab
