# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic sessions in the exact app format, with a chosen true model. Used to check that the
pipeline recovers whichever model generated the data, without flying."""
from __future__ import annotations

import uuid

import numpy as np

from . import models
from .attitude import rot_x, rot_y, rot_z
from .format import write_session

# phone axes expressed in the aircraft frame (x fwd, y right, z down)
MOUNTS = {
    # flat on tray, face up, phone top (y) pointing forward
    "tray": np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], float),
    # standing against the left window, screen facing into the cabin (+y), phone top up
    "window": np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float),
}
# The phone→NED orientation for the 4 calibration positions, before the arbitrary table heading.
# Face up: x east, y north, z up. Face down: flipped about the phone's y axis.
_CAL_UP = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], float)
_CAL_DOWN = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], float)


# Everything a real flight throws at the pipeline at once (see docs/MATH.md, Validation).
ADVERSE = dict(
    temp_coef_dph_per_c=(1.0, -0.8, 0.6), flight_temp_rise_c=8.0,     # bias follows temperature
    turbulence=((40, 5, 0.7),),                                       # real attitude jitter
    mount_slip_deg_per_h=(0.0, 1.5),                                  # phone tilts slowly in its mount
    climb_min=20, descent_min=20,                                     # climb/descent excluded from cruise
    legs=((60.0, 35.0), (100.0, 25.0), (20.0, 25.0), (300.0, 30.0)),
    gnss_dropouts=((70, 4),),                                         # GNSS gap splits a segment
)


def _vee_batch(R):
    return np.stack([R[:, 2, 1] - R[:, 1, 2], R[:, 0, 2] - R[:, 2, 0], R[:, 1, 0] - R[:, 0, 1]], axis=1) / 2


def synthesize(path, truth="sphere_rotating", *, fs=25.0, seed=0, lat0=40.6, lon0=-73.8, h=11000.0,
               speed=230.0, legs=((60.0, 25.0), (100.0, 25.0), (20.0, 25.0)), mount="tray",
               mount_yaw_deg=20.0, mount_tilt_deg=4.0, cal_pos_s=180.0, gap_s=3600.0,
               bias0_dps=(0.3, -0.2, 0.15), drift_dph_per_h=(1.0, -0.8, 0.5), rw_dph_sqrth=0.3,
               noise_dps_rthz=0.007, accel_noise_g_rthz=160e-6, pitch_trim_deg_per_h=0.5,
               cal=("pre", "post"), drift_runs=False,
               temp_coef_dph_per_c=(0.0, 0.0, 0.0), flight_temp_rise_c=0.0, turbulence=(),
               mount_slip_deg_per_h=(0.0, 0.0), climb_min=0.0, descent_min=0.0, gnss_dropouts=()):
    """Write a synthetic session zip. legs = ((course_deg, minutes), ...), with rate-one turns
    (3°/s) between them.

    Adversarial options:
      temp_coef_dph_per_c, flight_temp_rise_c: gyro bias depends on temperature, and the phone
          warms by this much during the flight (calibrations happen at 25 °C)
      turbulence: ((start_min, minutes, attitude_rms_deg), ...) bursts of real attitude
          jitter plus vertical bumps
      mount_slip_deg_per_h: (yaw, tilt) slow creep of the phone in its mount through the flight
      climb_min, descent_min: climb from 1 km to cruise at the start, descend at the end
      gnss_dropouts: ((start_min, minutes), ...) with no GNSS fixes
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / fs
    t0_ns = 10 ** 12
    sig_g = np.radians(noise_dps_rthz) * np.sqrt(fs)
    sig_a = accel_noise_g_rthz * models.G0 * np.sqrt(fs)
    g_vec = np.array([0, 0, models.G0])

    # timeline
    phases = []
    t = 0.0
    if "pre" in cal:
        for p in ("up0", "up180", "down0", "down180"):
            phases.append((f"cal_pre.{p}", t, t + cal_pos_s))
            t += cal_pos_s + 20
    if drift_runs:
        phases.append(("drift_pre", t, t + 1800))
        t += 1800
    t += gap_s
    fl_start = t
    turn_rate = np.radians(3.0)
    fl_dur = sum(m for _, m in legs) * 60 + 600  # + 10 min slack for turns
    phases.append(("flight", fl_start, fl_start + fl_dur))
    t = fl_start + fl_dur + gap_s
    if "post" in cal:
        for p in ("up0", "up180", "down0", "down180"):
            phases.append((f"cal_post.{p}", t, t + cal_pos_s))
            t += cal_pos_s + 20
    t_end = t

    # bias: offset + linear drift + random walk on a 1-s grid
    tg = np.arange(0, t_end + 2, 1.0)
    rw = np.cumsum(rng.normal(0, np.radians(rw_dph_sqrth / 3600) / 60, (len(tg), 3)), axis=0)  # per sqrt(s)
    bias_grid = np.radians(np.array(bias0_dps)) + np.outer(tg / 3600, np.radians(np.array(drift_dph_per_h) / 3600)) + rw

    # battery temperature: 25 °C on the ground, rising towards 25 + rise in flight
    fl_s = np.clip(tg - fl_start, 0, fl_dur)
    after = np.clip(tg - fl_start - fl_dur, 0, None)
    temp_grid = 25.0 + flight_temp_rise_c * (1 - np.exp(-fl_s / 900.0)) * np.exp(-after / 900.0)
    bias_grid = bias_grid + np.outer(temp_grid - 25.0, np.radians(np.array(temp_coef_dph_per_c) / 3600))

    def bias(ts):
        return np.column_stack([np.interp(ts, tg, bias_grid[:, i]) for i in range(3)])

    gyro_rows, acc_rows, gnss_rows = [], [], []

    def add_sensor(ts, C_bn, w_ib_b, f_n):
        n = len(ts)
        g = w_ib_b + bias(ts) + rng.normal(0, sig_g, (n, 3))
        a = np.einsum("nij,nj->ni", C_bn, f_n) + rng.normal(0, sig_a, (n, 3))
        tns = t0_ns + np.round(ts * 1e9).astype(np.int64)
        gyro_rows.append((tns, g.astype(np.float32)))
        acc_rows.append((tns, a.astype(np.float32)))

    lat_cal = np.radians(lat0)
    w_ground = models.predict(truth, lat_cal) if truth.endswith("rotating") else np.zeros(3)
    table_heading = np.radians(37.0)
    for name, a, b in phases:
        if not name.startswith(("cal", "drift")):
            continue
        ts = np.arange(a, b, dt)
        pos = name.split(".")[-1] if "." in name else "up0"
        base = _CAL_UP if pos.startswith("up") else _CAL_DOWN
        yaw = table_heading + (np.pi if pos.endswith("180") else 0) + rng.normal(0, np.radians(2))
        C_nb = rot_z(yaw) @ rot_x(rng.normal(0, 0.01)) @ base
        C = np.broadcast_to(C_nb.T, (len(ts), 3, 3))
        add_sensor(ts, C, np.tile(C_nb.T @ w_ground, (len(ts), 1)), np.tile(-g_vec, (len(ts), 1)))

    # flight
    ts = np.arange(fl_start, fl_start + fl_dur, dt)
    n = len(ts)
    psi_dot = np.zeros(n)
    psi0 = np.radians(legs[0][0])
    tc = fl_start + 300.0
    for (c0, m0), (c1, _) in zip(legs[:-1], legs[1:]):
        tc += m0 * 60
        d = (np.degrees(np.radians(c1 - c0)) + 180) % 360 - 180
        dur = abs(np.radians(d)) / turn_rate
        ramp = 5.0
        prof = np.clip(np.minimum(ts - tc, tc + dur + ramp - ts) / ramp, 0, 1)
        psi_dot += np.sign(d) * turn_rate * prof
        tc += dur + ramp
    psi = psi0 + np.cumsum(psi_dot) * dt
    v_n, v_e = speed * np.cos(psi), speed * np.sin(psi)
    lat = np.empty(n)
    lon = np.empty(n)
    lat[0], lon[0] = np.radians(lat0), np.radians(lon0)
    rm, rn = models.radii(lat[0])
    for i in range(1, n):
        if i % 250 == 1:
            rm, rn = models.radii(lat[i - 1])
        lat[i] = lat[i - 1] + v_n[i - 1] / (rm + h) * dt
        lon[i] = lon[i - 1] + v_e[i - 1] / ((rn + h) * np.cos(lat[i - 1])) * dt
    bank = np.arctan(speed * psi_dot / models.G0)
    tf = ts - fl_start
    pitch = np.radians(2.0 + pitch_trim_deg_per_h * tf / 3600) + np.radians(0.1) * np.sin(2 * np.pi * ts / 400)
    # climb / descent profile
    hh = np.full(n, float(h))
    vz = np.zeros(n)
    if climb_min > 0:
        m = tf < climb_min * 60
        vz[m] = (h - 1000.0) / (climb_min * 60)
        pitch[m] += np.radians(3.0)
    if descent_min > 0:
        m = tf > fl_dur - descent_min * 60
        vz[m] = -(h - 1000.0) / (descent_min * 60)
        pitch[m] -= np.radians(1.5)
    if climb_min > 0 or descent_min > 0:
        # Ramp vz over 30 s at each transition. A step in vz would differentiate into a one-sample
        # ~8 g spike in the vertical accelerometer, which is unphysical and trips the vibration gate.
        k = max(1, int(round(30.0 / dt)))
        vz = np.convolve(vz, np.full(k, 1.0 / k), mode="same")
        hh = (h if climb_min == 0 else 1000.0) + np.cumsum(vz) * dt
    # turbulence: low-passed attitude jitter and vertical bumps
    a_vert = np.zeros(n)
    for start, dur, rms in turbulence:
        m = (tf >= start * 60) & (tf < (start + dur) * 60)
        k = max(1, int(fs * 2))
        for arr in (pitch, bank):
            jit = np.convolve(rng.normal(0, 1, n), np.ones(k) / np.sqrt(k), mode="same")
            arr[m] += np.radians(rms) * jit[m]
        a_vert[m] += rng.normal(0, 1.5, m.sum())
    slip_yaw = np.radians(mount_slip_deg_per_h[0]) * tf / 3600
    slip_tilt = np.radians(mount_slip_deg_per_h[1]) * tf / 3600
    C_na = np.einsum("nij,njk,nkl->nil", np.array([rot_z(p) for p in psi]),
                     np.array([rot_y(p) for p in pitch]), np.array([rot_x(p) for p in bank]))
    if any(mount_slip_deg_per_h):
        C_ab = np.einsum("nij,njk,kl->nil", np.array([rot_z(np.radians(mount_yaw_deg) + y) for y in slip_yaw]),
                         np.array([rot_y(np.radians(mount_tilt_deg) + x) for x in slip_tilt]), MOUNTS[mount])
    else:
        C_ab = rot_z(np.radians(mount_yaw_deg)) @ rot_y(np.radians(mount_tilt_deg)) @ MOUNTS[mount]
    C_nb = C_na @ C_ab
    C_bn = np.transpose(C_nb, (0, 2, 1))
    R_rel = np.einsum("nji,njk->nik", C_nb[:-1], C_nb[1:])
    w_nb = _vee_batch(R_rel) / dt
    w_nb = np.vstack([w_nb, w_nb[-1:]])
    w_in = models.predict(truth, lat, hh, v_n, v_e)
    w_ib = np.einsum("nij,nj->ni", C_bn, w_in) + w_nb
    a_n = np.column_stack([np.gradient(v_n, dt), np.gradient(v_e, dt), np.gradient(-vz, dt) + a_vert])
    add_sensor(ts, C_bn, w_ib, a_n - g_vec)

    # GNSS at 1 Hz
    gi = np.arange(0, n, int(round(fs)))
    for start, dur in gnss_dropouts:
        gi = gi[(tf[gi] < start * 60) | (tf[gi] >= (start + dur) * 60)]
    g_t = t0_ns + np.round(ts[gi] * 1e9).astype(np.int64)
    gnss = {
        "t_ns": g_t, "utc_ms": 1_790_000_000_000 + (g_t - t0_ns) // 10 ** 6,
        "lat": np.degrees(lat[gi]) + rng.normal(0, 2e-5, len(gi)),
        "lon": np.degrees(lon[gi]) + rng.normal(0, 2e-5, len(gi)),
        "alt_m": hh[gi] + rng.normal(0, 3, len(gi)),
        "speed_mps": (speed + rng.normal(0, 0.2, len(gi))).astype(np.float32),
        "bearing_deg": ((np.degrees(psi[gi]) + rng.normal(0, 0.1, len(gi))) % 360).astype(np.float32),
        "h_acc_m": np.full(len(gi), 5.0, np.float32), "v_acc_m": np.full(len(gi), 8.0, np.float32),
        "speed_acc_mps": np.full(len(gi), 0.3, np.float32), "bearing_acc_deg": np.full(len(gi), 0.5, np.float32),
        "sats_used": np.full(len(gi), 12, np.int64),
    }

    def cat(rows):
        tns = np.concatenate([r[0] for r in rows])
        v = np.concatenate([r[1] for r in rows])
        o = np.argsort(tns, kind="stable")
        return tns[o], v[o]

    gt, gv = cat(gyro_rows)
    at, av = cat(acc_rows)
    z = np.zeros(len(gt), np.float32)
    za = np.zeros(len(at), np.float32)
    streams = {
        "gyro_uncal": {"t_ns": gt, "x": gv[:, 0], "y": gv[:, 1], "z": gv[:, 2], "bx": z, "by": z, "bz": z},
        "accel_uncal": {"t_ns": at, "x": av[:, 0], "y": av[:, 1], "z": av[:, 2], "bx": za, "by": za, "bz": za},
        "gnss": gnss,
        "battery": {"t_ns": t0_ns + np.arange(0, int(t_end), 10, dtype=np.int64) * 10 ** 9,
                    "temp_c": np.interp(np.arange(0, int(t_end), 10), tg, temp_grid).astype(np.float32),
                    "level_pct": np.full(int(t_end) // 10 + (int(t_end) % 10 > 0), 80.0, np.float32),
                    "plugged": np.zeros(int(t_end) // 10 + (int(t_end) % 10 > 0), np.int64)},
    }
    manifest = {
        "schema_version": 1, "data_license": "CC0-1.0", "session_id": str(uuid.UUID(int=int(rng.integers(2 ** 63)))),
        "install_id": "synthetic", "created_utc": "2026-10-02T00:00:00Z",
        "app": {"name": "lll.synth", "version": "0", "build": 0},
        "device": {"manufacturer": "synthetic", "model": f"synth-{truth}", "android_sdk": 0, "android_release": ""},
        "sensors": {}, "sampling_period_us": int(1e6 / fs), "clock": {"elapsed_ns": t0_ns, "utc_ms": 1_790_000_000_000},
        "flight": {"airline": "SYN", "flight_number": f"SYN{seed}", "date": "2026-10-02", "origin": "", "destination": "",
                   "aircraft_type": "", "seat": "window", "row": "", "notes": f"synthetic truth={truth}"},
        "mount": {"type": mount, "orientation_note": "", "rotated_180_control": False},
        "privacy": {"cal_lat_deg": round(lat0 * 2) / 2},
        "phases": [{"name": nm, "start_ns": t0_ns + int(a * 1e9), "end_ns": t0_ns + int(b * 1e9), "still_s": b - a}
                   for nm, a, b in phases],
        "quality": {"cal_pre": "pre" in cal, "cal_post": "post" in cal, "placement_check": True, "flags": ["synthetic"]},
        "synthetic_truth": truth,
    }
    events = [(t0_ns + int(a * 1e9), "phase_start", nm) for nm, a, _ in phases]
    write_session(path, manifest, streams, events)
    return manifest
