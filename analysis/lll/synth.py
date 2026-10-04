# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic sessions in the exact app format, with a chosen true model. Used to check that the
pipeline recovers whichever model generated the data, without flying."""
from __future__ import annotations

import uuid

import numpy as np

from . import models, witmotion
from .attitude import rot_x, rot_y, rot_z
from .format import write_session

# Earth's field near New York, NED, µT; the synthetic magnetometer's counts per µT (the real
# scale is unverified until a device is on the bench).
MAG_COUNTS_PER_UT = 10.0
MAG_HARD_IRON_UT = (8.0, -5.0, 3.0)      # the IMU's own magnetized parts, fixed in its frame
MAG_AIRFRAME_UT = (6.0, -2.0, 4.0)       # the aircraft structure near the seat, fixed in the airframe


def wmm_ned_ut(lat_deg, lon_deg, alt_m, year=2026.75):
    """Earth's field from the World Magnetic Model, NED, µT. Synth only uses it to make realistic
    magnetometer data; the gyro analysis never sees the magnetometer."""
    from pygeomag import GeoMag
    g = GeoMag()
    out = []
    for la, lo, a in zip(np.atleast_1d(lat_deg), np.atleast_1d(lon_deg), np.atleast_1d(alt_m)):
        r = g.calculate(glat=float(la), glon=float(lo), alt=float(a) / 1000.0, time=year)
        out.append((r.x / 1000.0, r.y / 1000.0, r.z / 1000.0))
    return np.array(out)

# IMU axes expressed in the aircraft frame (x fwd, y right, z down)
MOUNTS = {
    # flat on tray, face up, IMU +y pointing forward
    "tray": np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], float),
    # standing against the left window, face +z towards the cabin
    "window": np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float),
}
# The IMU→NED orientation for the 4 calibration positions, before the arbitrary table heading.
# Face up: x east, y north, z up. Face down: flipped about the IMU's y axis.
_CAL_UP = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], float)
_CAL_DOWN = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], float)


# Ground calibration sequences: (position, length multiple). The palindrome visits every position
# twice in mirror order, so a linear bias drift averages out of each position and can be fitted.
# The middle position is one double-length stay. A ".b" suffix marks the second visit.
CAL_SEQUENCES = {
    "palindrome": (("up0", 1), ("up180", 1), ("down0", 1), ("down180", 2), ("down0.b", 1), ("up180.b", 1), ("up0.b", 1)),
    "single": (("up0", 1), ("up180", 1), ("down0", 1), ("down180", 1)),
}

# Everything a real flight throws at the pipeline at once (see docs/MATH.md, Validation).
ADVERSE = dict(
    temp_coef_dph_per_c=(1.0, -0.8, 0.6), flight_temp_rise_c=8.0,     # bias follows temperature
    turbulence=((40, 5, 0.7),),                                       # real attitude jitter
    mount_slip_deg_per_h=(0.0, 1.5),                                  # IMU tilts slowly in its mount
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
               cal=("pre", "post"), drift_runs=False, cal_sequence="palindrome", g_sens_dph_per_g=None,
               temp_coef_dph_per_c=(0.0, 0.0, 0.0), flight_temp_rise_c=0.0, turbulence=(),
               mount_slip_deg_per_h=(0.0, 0.0), climb_min=0.0, descent_min=0.0, gnss_dropouts=(), variant="spp", gyro_range_dps=2000.0, accel_range_g=16.0, index_turns=(),
               mag_hard_iron_ut=MAG_HARD_IRON_UT, mag_airframe_ut=MAG_AIRFRAME_UT, omega_in_fn=None,
               temp_quad_dph_per_c2=(0.0, 0.0, 0.0), temp_lag_s=0.0, bias_jumps=(), gyro_scale_ppm=(0, 0, 0),
               gyro_misalign_mrad=0.0, vre_dph=(0.0, 0.0, 0.0), link_dropouts=(), turn_seconds=4.0,
               spp_time_every=1, ble_loss=0.0, crab_deg=(), reversal_pairs=0, reversal_s=300.0,
               crab_trajectory=None, gyro_noise_cov=None, long_drift_dph=(0, 0, 0), long_drift_period_s=7200):
    """Write a synthetic session zip. legs = ((course_deg, minutes), ...), with rate-one turns
    (3°/s) between them. variant is the WitMotion link and protocol ("spp" or "ble"); the IMU
    data is written as the byte stream the app would store, so the decoder is exercised too.

    Adversarial options:
      temp_coef_dph_per_c, flight_temp_rise_c: gyro bias depends on temperature, and the IMU
          warms by this much during the flight (calibrations happen at 25 °C)
      turbulence: ((start_min, minutes, attitude_rms_deg), ...) bursts of real attitude
          jitter plus vertical bumps
      mount_slip_deg_per_h: (yaw, tilt) slow creep of the IMU in its mount through the flight
      climb_min, descent_min: climb from 1 km to cruise at the start, descend at the end
      gnss_dropouts: ((start_min, minutes), ...) with no GNSS fixes
      omega_in_fn: f(t_s, lat_rad, lon_rad, h_m) -> ω_in NED (n, 3). The true rotation of local level.
          Tests pass the independent geometric generator (analysis/tests/truthgen.py), so the data
          never come from the lll.models code the analysis uses. Default: lll.models.predict.
      Hardware faults (none by default):
      temp_quad_dph_per_c2: bias also depends on (T − 25 °C)²
      temp_lag_s: the reported chip temperature lags the temperature that drives the bias
      bias_jumps: ((minute_into_flight, (dx, dy, dz) °/h), ...) sudden bias steps
      gyro_scale_ppm, gyro_misalign_mrad: scale error per axis, and random cross-axis misalignment
      vre_dph: vibration rectification, a bias offset while the engines run (flight only)
      link_dropouts: ((minute_into_flight, seconds), ...) Bluetooth gaps in the IMU data
      crab_deg: (deg per leg, ...) the fuselage's angle off the ground track (crosswind); GNSS
          reports the course, so the analysis has to allow for it
      crab_trajectory: optional callable f(seconds into flight) -> degrees, added to crab_deg.
          The gyro includes its time derivative through the independent attitude matrices.
      gyro_noise_cov: optional 3x3 covariance multiplier for white gyro noise.
      long_drift_dph, long_drift_period_s: sinusoidal sensor bias amplitude and period.
      index_turns: ((minute, axis), ...) the participant turns the IMU 180° about its own axis
          "x", "y" or "z" over turn_seconds (default 4 s), then taps to confirm 15 s later. About z on a tray mount is a
          turn in its plane (gravity stays on z); about x is a flip.
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / fs
    g_sens = None if g_sens_dph_per_g is None else np.radians(np.asarray(g_sens_dph_per_g, float) / 3600)
    t0_ns = 10 ** 12
    sig_g = np.radians(noise_dps_rthz) * np.sqrt(fs)
    sig_a = accel_noise_g_rthz * models.G0 * np.sqrt(fs)
    g_vec = np.array([0, 0, models.G0])

    # timeline
    phases = []
    t = 0.0
    seq = CAL_SEQUENCES[cal_sequence]
    if "pre" in cal:
        for p, mult in seq:
            phases.append((f"cal_pre.{p}", t, t + cal_pos_s * mult))
            t += cal_pos_s * mult + 20
    for i in range(1, reversal_pairs + 1):      # repeated same-face 0°/180° reversals (bench)
        for pos in ("up0", "up180"):
            phases.append((f"rev.{pos}.{i}", t, t + reversal_s))
            t += reversal_s + 20
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
        for p, mult in seq:
            phases.append((f"cal_post.{p}", t, t + cal_pos_s * mult))
            t += cal_pos_s * mult + 20
    t_end = t

    # bias: offset + linear drift + random walk on a 1-s grid
    tg = np.arange(0, t_end + 2, 1.0)
    rw = np.cumsum(rng.normal(0, np.radians(rw_dph_sqrth / 3600) / 60, (len(tg), 3)), axis=0)  # per sqrt(s)
    bias_grid = np.radians(np.array(bias0_dps)) + np.outer(tg / 3600, np.radians(np.array(drift_dph_per_h) / 3600)) + rw
    bias_grid += np.outer(np.sin(2 * np.pi * tg / long_drift_period_s), np.radians(np.asarray(long_drift_dph) / 3600))

    # IMU chip temperature: 25 °C on the ground, rising towards 25 + rise in flight
    fl_s = np.clip(tg - fl_start, 0, fl_dur)
    after = np.clip(tg - fl_start - fl_dur, 0, None)
    temp_grid = 25.0 + flight_temp_rise_c * (1 - np.exp(-fl_s / 900.0)) * np.exp(-after / 900.0)
    if temp_lag_s > 0:   # the bias follows the true temperature; the chip reports a lagged one
        drive = temp_grid
        a = 1.0 / temp_lag_s
        temp_grid = np.empty_like(drive)
        temp_grid[0] = drive[0]
        for i in range(1, len(drive)):
            temp_grid[i] = temp_grid[i - 1] + a * (drive[i] - temp_grid[i - 1])
    else:
        drive = temp_grid
    dT = drive - 25.0
    bias_grid = (bias_grid + np.outer(dT, np.radians(np.array(temp_coef_dph_per_c) / 3600))
                 + np.outer(dT ** 2, np.radians(np.array(temp_quad_dph_per_c2) / 3600)))
    for minute, step in bias_jumps:
        bias_grid[tg >= fl_start + minute * 60] += np.radians(np.array(step) / 3600)
    eng = np.clip((tg - fl_start) / 60.0, 0, 1) * (tg <= fl_start + fl_dur)
    bias_grid = bias_grid + np.outer(eng, np.radians(np.array(vre_dph) / 3600))
    S = np.eye(3) + np.diag(np.asarray(gyro_scale_ppm, float) * 1e-6)
    if gyro_misalign_mrad:
        Mx = rng.normal(0, gyro_misalign_mrad * 1e-3, (3, 3))
        np.fill_diagonal(Mx, 0.0)
        S = S + Mx

    def bias(ts):
        return np.column_stack([np.interp(ts, tg, bias_grid[:, i]) for i in range(3)])

    rows = []  # (t_s, gyro rad/s, accel m/s², mag µT) per phase

    hard_iron = np.asarray(mag_hard_iron_ut, float)

    def add_sensor(ts, C_bn, w_ib_b, f_n, b_ned, b_air_b=0.0):
        n = len(ts)
        f_b = np.einsum("nij,nj->ni", C_bn, f_n)
        noise = rng.normal(0, sig_g, (n, 3))
        if gyro_noise_cov is not None:
            noise = noise @ np.linalg.cholesky(np.asarray(gyro_noise_cov)).T
        g = w_ib_b @ S.T + bias(ts) + noise
        if g_sens is not None:
            g = g + f_b @ g_sens.T / models.G0       # gyro error proportional to specific force
        a = f_b + rng.normal(0, sig_a, (n, 3))
        m = (np.einsum("nij,nj->ni", C_bn, np.broadcast_to(b_ned, (n, 3))) + hard_iron + b_air_b
             + rng.normal(0, 0.3, (n, 3)))
        rows.append((ts, g, a, m))

    lat_cal = np.radians(lat0)
    b_cal = wmm_ned_ut(lat0, lon0, 0.0)[0]
    if omega_in_fn is not None:
        w_ground = omega_in_fn(np.array([0.0]), np.array([lat_cal]), np.array([np.radians(lon0)]), np.array([0.0]))[0]
    else:
        w_ground = models.predict(truth, lat_cal) if truth.endswith("rotating") else np.zeros(3)
    table_heading = np.radians(37.0)
    for name, a, b in phases:
        if not name.startswith(("cal", "drift", "rev")):
            continue
        ts = np.arange(a, b, dt)
        pos = name.split(".")[1] if "." in name else "up0"
        base = _CAL_UP if pos.startswith("up") else _CAL_DOWN
        yaw = table_heading + (np.pi if pos.endswith("180") else 0) + rng.normal(0, np.radians(2))
        C_nb = rot_z(yaw) @ rot_x(rng.normal(0, 0.01)) @ base
        C = np.broadcast_to(C_nb.T, (len(ts), 3, 3))
        add_sensor(ts, C, np.tile(C_nb.T @ w_ground, (len(ts), 1)), np.tile(-g_vec, (len(ts), 1)), b_cal)

    # flight
    ts = np.arange(fl_start, fl_start + fl_dur, dt)
    n = len(ts)
    psi_dot = np.zeros(n)
    psi0 = np.radians(legs[0][0])
    tc = fl_start + 300.0
    switches = []
    for (c0, m0), (c1, _) in zip(legs[:-1], legs[1:]):
        tc += m0 * 60
        switches.append(tc)
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
    # Crab: in a crosswind the fuselage points crab_deg off the ground track. GNSS still reports the
    # course (psi); the aircraft's heading is psi + crab, changing over 30 s at each turn.
    heading = psi
    if crab_deg:
        leg = np.searchsorted(np.array(switches), ts)
        crab = np.radians(np.asarray(crab_deg, float))[np.minimum(leg, len(crab_deg) - 1)]
        k30 = max(1, int(round(30.0 / dt)))
        crab = np.convolve(np.pad(crab, (k30 // 2, k30 - 1 - k30 // 2), mode="edge"), np.full(k30, 1.0 / k30), mode="valid")
        heading = psi + crab
    if crab_trajectory is not None:
        heading = heading + np.radians(np.broadcast_to(crab_trajectory(tf), tf.shape))
    C_na = np.einsum("nij,njk,nkl->nil", np.array([rot_z(p) for p in heading]),
                     np.array([rot_y(p) for p in pitch]), np.array([rot_x(p) for p in bank]))
    if any(mount_slip_deg_per_h):
        C_ab = np.einsum("nij,njk,kl->nil", np.array([rot_z(np.radians(mount_yaw_deg) + y) for y in slip_yaw]),
                         np.array([rot_y(np.radians(mount_tilt_deg) + x) for x in slip_tilt]), MOUNTS[mount])
    else:
        C_ab = rot_z(np.radians(mount_yaw_deg)) @ rot_y(np.radians(mount_tilt_deg)) @ MOUNTS[mount]
    C_nb = C_na @ C_ab
    turn_events = []
    if index_turns:
        R_turn = np.broadcast_to(np.eye(3), (n, 3, 3)).copy()
        rot = {"x": rot_x, "y": rot_y, "z": rot_z}
        for minute, axis in sorted(index_turns):
            t0 = minute * 60.0
            frac = np.clip((tf - t0) / turn_seconds, 0.0, 1.0)
            R_turn = np.einsum("nij,njk->nik", R_turn, np.array([rot[axis](np.pi * f) for f in frac]))
            turn_events.append((t0_ns + int((fl_start + t0 + 19.0) * 1e9), "index_turn",
                                "plane180" if (axis == "z" and mount == "tray") else "flip"))
        C_nb = np.einsum("nij,njk->nik", C_nb, R_turn)
    C_bn = np.transpose(C_nb, (0, 2, 1))
    R_rel = np.einsum("nji,njk->nik", C_nb[:-1], C_nb[1:])
    w_nb = _vee_batch(R_rel) / dt
    w_nb = np.vstack([w_nb, w_nb[-1:]])
    w_in = omega_in_fn(ts, lat, lon, hh) if omega_in_fn is not None else models.predict(truth, lat, hh, v_n, v_e)
    w_ib = np.einsum("nij,nj->ni", C_bn, w_in) + w_nb
    a_n = np.column_stack([np.gradient(v_n, dt), np.gradient(v_e, dt), np.gradient(-vz, dt) + a_vert])
    grid = np.arange(0, n, max(1, int(60 * fs)))
    b_grid = wmm_ned_ut(np.degrees(lat[grid]), np.degrees(lon[grid]), hh[grid])
    b_ned = np.column_stack([np.interp(np.arange(n), grid, b_grid[:, i]) for i in range(3)])
    b_air = np.einsum("nij,njk,k->ni", C_bn, C_na, np.asarray(mag_airframe_ut, float))
    add_sensor(ts, C_bn, w_ib, a_n - g_vec, b_ned, b_air)

    # GNSS at 1 Hz
    gi = np.arange(0, n, int(round(fs)))
    for start, dur in gnss_dropouts:
        gi = gi[(tf[gi] < start * 60) | (tf[gi] >= (start + dur) * 60)]
    g_t = t0_ns + np.round(ts[gi] * 1e9).astype(np.int64)
    gnss = {
        "t_ns": g_t, "utc_ms": 1_790_000_000_000 + (g_t - t0_ns) // 10 ** 6,
        "lat": np.degrees(lat[gi]) + rng.normal(0, 2e-5, len(gi)),
        "lon": (np.degrees(lon[gi]) + rng.normal(0, 2e-5, len(gi)) + 180) % 360 - 180,
        "alt_m": hh[gi] + rng.normal(0, 3, len(gi)),
        "speed_mps": (speed + rng.normal(0, 0.2, len(gi))).astype(np.float32),
        "bearing_deg": ((np.degrees(psi[gi]) + rng.normal(0, 0.1, len(gi))) % 360).astype(np.float32),
        "h_acc_m": np.full(len(gi), 5.0, np.float32), "v_acc_m": np.full(len(gi), 8.0, np.float32),
        "speed_acc_mps": np.full(len(gi), 0.3, np.float32), "bearing_acc_deg": np.full(len(gi), 0.5, np.float32),
        "sats_used": np.full(len(gi), 12, np.int64),
    }

    if link_dropouts:   # Bluetooth gaps: the IMU data simply isn't there, and the app logs the drop
        r0 = rows[-1]
        keep = np.ones(len(r0[0]), bool)
        for minute, secs in link_dropouts:
            t0 = fl_start + minute * 60
            keep &= ~((r0[0] >= t0) & (r0[0] < t0 + secs))
            turn_events.append((t0_ns + int(t0 * 1e9), "imu_disconnect", "synthetic dropout"))
            turn_events.append((t0_ns + int((t0 + secs) * 1e9), "imu_connect", "synthetic dropout"))
        rows[-1] = tuple(x[keep] for x in r0)
    order = np.argsort(np.concatenate([r[0] for r in rows]), kind="stable")
    ts_all, gv, av, mv = (np.concatenate([r[i] for r in rows])[order] for i in range(4))
    temp = np.interp(ts_all, tg, temp_grid)
    imu = encode_imu(variant, t0_ns + np.round(ts_all * 1e9).astype(np.int64), gv, av, mv, temp, fs, rng,
                     gyro_range_dps=gyro_range_dps, accel_range_g=accel_range_g, spp_time_every=spp_time_every,
                     ble_loss=ble_loss)
    streams = {"gnss": gnss}
    manifest = {
        "schema_version": 3, "data_license": "CC0-1.0", "session_id": str(uuid.UUID(int=int(rng.integers(2 ** 63)))),
        "install_id": "synthetic", "created_utc": "2026-10-02T00:00:00Z",
        "app": {"name": "lll.synth", "version": "0", "build": 0},
        "device": {"manufacturer": "synthetic", "model": f"synth-{truth}", "android_sdk": 0, "android_release": ""},
        "imu": {"variant": variant, "model": "WT901 (synthetic)", "firmware": "", "unit_id": f"synthetic-{variant}",
                "config": {"rate_hz": fs, "gyro_range_dps": gyro_range_dps, "accel_range_g": accel_range_g, "auto_zero": False,
                           "packets": ["0x50", "0x51", "0x52", "0x54"] if variant == "spp" else ["0x61", "0x71@0x3a"]}},
        "clock": {"elapsed_ns": t0_ns, "utc_ms": 1_790_000_000_000},
        "flight": {"airline": "SYN", "flight_number": f"SYN{seed}", "date": "2026-10-02", "origin": "", "destination": "",
                   "aircraft_type": "", "seat_position": "window", "notes": f"synthetic truth={truth}"},
        "mount": {"type": mount, "orientation_note": "", "rotated_180_control": False},
        "privacy": {"cal_locations": {"cal_pre": {"lat_deg": round(lat0 * 2) / 2, "age_s": 0}, "cal_post": {"lat_deg": round(lat0 * 2) / 2, "age_s": 0}}},
        "phases": [{"name": nm, "start_ns": t0_ns + int(a * 1e9), "end_ns": t0_ns + int(b * 1e9), "still_s": b - a}
                   for nm, a, b in phases],
        "quality": {"cal_pre": "pre" in cal, "cal_post": "post" in cal, "placement_check": True, "flags": ["synthetic"]},
        "synthetic_truth": truth,
    }
    events = sorted([(t0_ns + int(a * 1e9), "phase_start", nm) for nm, a, _ in phases] + turn_events)
    # Simulated readbacks describe the actual generated settings. Synthetic provenance remains explicit.
    rate_code = {10: 6, 20: 7, 50: 8, 100: 9, 200: 11}.get(fs)
    if rate_code is not None:
        gyro_code = next(k for k, v in witmotion.GYRO_RANGE_DPS.items() if v == gyro_range_dps)
        accel_code = next(k for k, v in witmotion.ACC_RANGE_G.items() if v == accel_range_g)
        detail = f"0x02=0x17 0x03=0x{rate_code:x} 0x20=0x{gyro_code:x} 0x21=0x{accel_code:x} 0x63=0x1 ok=true"
        events = sorted(events + [(t0_ns + int(a * 1e9), "imu_config", detail) for _, a, _ in phases])
    write_session(path, manifest, streams, events, imu=imu)
    return manifest


def encode_imu(variant, t_ns, gyro, accel, mag_ut, temp_c, fs, rng, clock_ppm=40.0, gyro_range_dps=2000.0, accel_range_g=16.0,
               spp_time_every=1, ble_loss=0.0):
    """Turn true samples into what the app would store: Bluetooth read chunks, verbatim bytes,
    stamped with a phone arrival time that lags the sample by a random link latency.

    spp: one 0x50/0x51/0x52/0x54 cycle per sample, timed by a device clock running clock_ppm
         fast; reads end at random byte offsets, so packets straddle chunks.
    ble: one 0x61 notification per sample on a 7.5-ms connection interval, plus a 0x71 register
         reply (mag + temperature) about once a second.
    """
    n = len(t_ns)
    ts = (t_ns - t_ns[0]) / 1e9
    g_raw = witmotion.to_raw(np.degrees(gyro), gyro_range_dps)
    a_raw = witmotion.to_raw(accel / witmotion.G0, accel_range_g)
    m_raw = np.clip(np.round(mag_ut * MAG_COUNTS_PER_UT), -32768, 32767).astype(np.int16)
    t_raw = np.round(temp_c * 100).astype(np.int16)[:, None]
    if variant == "spp":
        dev_ms = np.round((ts * (1 + clock_ppm * 1e-6) + 86400 * 3 + 0.123) * 1000).astype(np.int64)
        full = np.concatenate([
            witmotion.spp_time_packets(dev_ms),
            witmotion.spp_packets(0x51, np.hstack([a_raw, t_raw])),
            witmotion.spp_packets(0x52, np.hstack([g_raw, np.full((n, 1), 390, np.int16)])),
            witmotion.spp_packets(0x54, np.hstack([m_raw, t_raw])),
        ], axis=1)
        has_t = np.arange(n) % max(1, spp_time_every) == 0      # the device clock packet, every N samples
        mask = np.ones(full.shape, bool)
        mask[~has_t, :11] = False
        lens = mask.sum(axis=1)
        buf = full[mask].tobytes()
        offs = np.concatenate([[0], np.cumsum(lens)])           # sample i occupies bytes offs[i]:offs[i+1]
        k = np.cumsum(rng.integers(1, 5, n))                     # sample whose bytes end each read
        k = k[k < n]
        ends = offs[k] + rng.integers(1, lens[k] + 1)
        # each phase is its own connection, so a read never spans two phases
        phase_ends = offs[np.where(np.diff(ts) > 1.0)[0] + 1]
        ends = np.unique(np.concatenate([ends, phase_ends, [offs[-1]]]))
        last = np.searchsorted(offs, ends, side="left") - 1      # sample still being sent at each read's end
        arrival = t_ns[last] + np.round((0.004 + rng.exponential(0.010, len(ends))) * 1e9).astype(np.int64)
        starts = np.concatenate([[0], ends[:-1]])
        chunks = [buf[a:b] for a, b in zip(starts.tolist(), ends.tolist())]
    elif variant == "ble":
        pk = witmotion.ble_packets(0x61, np.hstack([a_raw, g_raw, np.zeros((n, 3), np.int16)]))
        ci = 7.5e-3
        arr_s = np.maximum.accumulate(np.ceil(ts / ci) * ci + rng.exponential(0.002, n) + 0.003)  # BLE keeps order
        kept = rng.random(n) >= ble_loss                       # lost notifications never arrive
        pk, arr_s = pk[kept], arr_s[kept]
        chunks = [p.tobytes() for p in pk]
        reg_i = np.arange(0, n, max(1, int(round(fs))))
        regs = np.zeros((len(reg_i), 9), np.int16)
        regs[:, 0] = witmotion.REG_MAG
        regs[:, 1:4] = m_raw[reg_i]
        regs[:, 7] = t_raw[reg_i, 0]
        chunks += [p.tobytes() for p in witmotion.ble_packets(0x71, regs)]
        arr_s = np.concatenate([arr_s, ts[reg_i] + 0.02 + rng.exponential(0.005, len(reg_i))])
        arrival = t_ns[0] + np.round(arr_s * 1e9).astype(np.int64)
        o = np.argsort(arrival, kind="stable")
        arrival, chunks = arrival[o], [chunks[i] for i in o]
    else:
        raise ValueError(variant)
    return np.maximum.accumulate(arrival), chunks
