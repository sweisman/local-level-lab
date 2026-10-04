# SPDX-License-Identifier: AGPL-3.0-or-later
"""Magnetometer watchdog for slow yaw slip of the IMU in its mount.

The accelerometer sees any tilt of the IMU, but not a slow turn about the vertical. Such a creep
goes straight into the vertical gyro channel, where it looks like signal. The magnetometer can see
it: the horizontal field, as seen by the IMU, turns with the IMU.

What the IMU measures, horizontally, in a level frame fixed to it (complex numbers, east of the
first axis counter-clockwise about up):

    z(t) = e^{iδ(t)} (e^{iθ(t)} H + c) + d

- θ = ψ − D: the aircraft's course minus the magnetic declination, the angle of the Earth's field
  relative to the airframe. ψ comes from GNSS.
- H: the Earth's horizontal field, c: the airframe's own field near the seat. Both turn with the
  airframe, so both turn with any slip δ of the IMU relative to it.
- d: the IMU's own magnetic offset (hard iron). It is fixed in the IMU, so it doesn't turn with
  slip. The ground calibration measures it (calib.py) and it is removed first.

H and c are fitted per mount epoch from the aircraft's own heading changes. Without enough heading
change (under 45°) the airframe field is assumed small (c = 0), and the result says so. Then, per
cruise segment, the slip rate is the slope of the leftover angle, arg(z / (e^{iθ} H + c)).

Declination comes from the World Magnetic Model, which is built on a globe. So the watchdog also
runs with no declination correction at all (D held constant), as a cross-check. A segment is
excluded from the gyro fit when the WMM version detects slip; that choice uses only magnetometer and
GPS data, so the declination model can only drop data, never favour a model. Both results are
reported. The gyro fit itself never
uses the magnetometer, and the raw magnetometer data is kept, untouched, in imu.bin.gz.
"""
from __future__ import annotations

import numpy as np

from .attitude import unit

MIN_HEADING_RANGE_DEG = 45.0


def declination_deg(lat_deg, lon_deg, alt_m, year):
    """Declination (°) and horizontal intensity (nT) from the World Magnetic Model."""
    from pygeomag import GeoMag
    g = GeoMag()
    r = [g.calculate(glat=float(a), glon=float(o), alt=float(h) / 1000.0, time=float(year))
         for a, o, h in zip(lat_deg, lon_deg, alt_m)]
    return np.array([x.d for x in r]), np.array([x.h for x in r])


def _basis(up):
    u = unit(up)
    ref = np.array([1.0, 0, 0]) if abs(u[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = unit(ref - (ref @ u) * u)
    return e1, np.cross(u, e1)


def _slope(t_h, y):
    """OLS slope and its 1σ error."""
    if len(t_h) < 4:
        return np.nan, np.nan
    A = np.column_stack([np.ones_like(t_h), t_h - t_h.mean()])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    r = y - A @ beta
    s2 = (r @ r) / max(len(y) - 2, 1)
    return float(beta[1]), float(np.sqrt(s2 / np.sum((t_h - t_h.mean()) ** 2)))


def watchdog(bins, hard_iron, year, max_slip_dph):
    """Returns {"available", "variants": {"wmm": [...], "no_declination": [...]}, "exclude_segments"}."""
    if hard_iron is None or not np.isfinite(bins["mag"]).all():
        return {"available": False, "reason": "no magnetometer data or no calibration to remove the IMU's own field"}
    lat, lon = np.degrees(bins["lat"]), np.degrees(bins["lon"])
    D = {"no_declination": (np.zeros(len(lat)), np.ones(len(lat)))}
    try:
        D["wmm"] = declination_deg(lat, lon, bins["h"], year)
    except ValueError as e:      # date outside the model's validity
        D["wmm"] = None
        wmm_error = str(e)
    m = bins["mag"] - np.asarray(hard_iron)
    out = {"available": True, "max_slip_dph": max_slip_dph, "variants": {}}
    if D["wmm"] is None:
        out["wmm_unavailable"] = wmm_error
        del D["wmm"]
    for variant, (d, hint) in D.items():
        theta = bins["psi"] - np.radians(d)
        scale = hint / np.mean(hint)       # the Earth's horizontal field changes along the route
        rows = []
        for e in np.unique(bins["epoch"]):
            ie = bins["epoch"] == e
            # project each bin with its own measured up, so slow pitch changes can't leak the strong
            # vertical field into the horizontal; the reference axis is carried along
            e1, _ = _basis(np.median(bins["up"][ie], axis=0))
            ups = unit(bins["up"][ie])
            a1 = unit(e1 - (ups @ e1)[:, None] * ups)
            a2 = np.cross(ups, a1)
            z = np.einsum("ij,ij->i", m[ie], a1) + 1j * np.einsum("ij,ij->i", m[ie], a2)
            th = theta[ie]
            sc = scale[ie]
            span = np.degrees(np.ptp(np.unwrap(th)))
            if span >= MIN_HEADING_RANGE_DEG:
                A = np.column_stack([sc * np.exp(1j * th), np.ones_like(th)])
                (H, c), *_ = np.linalg.lstsq(A, z, rcond=None)
                calibrated = True
            else:
                H, c = np.mean(z * np.exp(-1j * th) / sc), 0.0
                calibrated = False
            zp = sc * np.exp(1j * th) * H + c
            ang = np.unwrap(np.angle(z / zp))
            for s in np.unique(bins["seg"][ie]):
                js = bins["seg"][ie] == s
                rate, sd = _slope(bins["t"][ie][js] / 3600.0, np.degrees(ang[js]))
                rows.append({"seg": int(s), "epoch": int(e), "slip_dph": rate, "sd_dph": sd,
                             "airframe_field_calibrated": calibrated,
                             "slip": bool(np.isfinite(rate) and abs(rate) > max_slip_dph and abs(rate) > 3 * sd)})
        out["variants"][variant] = rows
    # The WMM version decides (Scott, 2026-10-04). The decision uses only the magnetometer and GPS,
    # never the gyro, so the declination model can only drop segments, never push k towards a model.
    # The no-declination version is reported as a cross-check; on its own it reads real declination
    # change along the route as slip (several °/h on many routes) and would discard clean data.
    # If the WMM can't be used (date outside its validity), the no-declination version decides.
    by = {v: {r["seg"] for r in rows if r["slip"]} for v, rows in out["variants"].items()}
    out["decided_by"] = "wmm" if "wmm" in by else "no_declination"
    excluded = by.get(out["decided_by"], set())
    either = sorted({r["seg"] for v in out["variants"].values() for r in v if r["slip"]})
    out["exclude_segments"] = sorted(excluded)
    out["triggered_by"] = {str(s): sorted(v for v, segs in by.items() if s in segs) for s in sorted(excluded)}
    # without a declination model, a change of declination along the route looks like slip
    out["no_declination_only_segments"] = sorted(by.get("no_declination", set()) - by.get("wmm", set()))
    return out
