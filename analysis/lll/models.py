# SPDX-License-Identifier: AGPL-3.0-or-later
"""The three Earth models: a globe that rotates, a globe that is still, and a still flat disc.
(A spinning disc is not a model here: the flat-Earth model assumes no rotation, and a constant spin
about the vertical can't be told from gyro error along gravity anyway. See docs/MATH.md.) Every rate is in the local NED frame (north, east, down), in rad/s.

Earth rotation and transport rate (rotation of local level caused by moving over the surface)
are kept as separate terms so each can be tested on its own. See docs/MATH.md.

The flat models are an azimuthal-equidistant disc centred on the north pole: latitude φ sits at
radius proportional to the colatitude, and north points to the centre. Moving east on that disc
means circling the centre, so local level turns about the vertical once per 360° of longitude,
at −dλ/dt. That is the disc's own transport term. It needs no disc scale. It was missing before v0.2; the independent geometric check (analysis/tests/truthgen.py)
found it.
"""
from __future__ import annotations

import numpy as np

OMEGA_E = 7.2921150e-5          # rad/s, sidereal rotation (15.041 deg/h)
WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3
G0 = 9.80665
MIN_COS_LAT = 1e-3              # the longitude rate is singular at the poles

MODELS = {
    # name: (earth rotation term, transport term)
    "sphere_rotating": ("sphere", "sphere"),
    "sphere_still": (None, "sphere"),
    "flat_still": (None, "disc"),
}
MODEL_LABELS = {
    "sphere_rotating": "Sphere, rotating",
    "sphere_still": "Sphere, still",
    "flat_still": "Flat, still",
}
# Expected (k_rot_sphere, k_curv, k_disc) for each model, used by fit.py.
EXPECTED_K = {
    "sphere_rotating": (1.0, 1.0, 0.0),
    "sphere_still": (0.0, 1.0, 0.0),
    "flat_still": (0.0, 0.0, 1.0),
}


def radii(lat_rad):
    """Meridian (R_M) and prime-vertical (R_N) radii of curvature, WGS-84."""
    s2 = np.sin(lat_rad) ** 2
    d = 1.0 - WGS84_E2 * s2
    return WGS84_A * (1 - WGS84_E2) / d ** 1.5, WGS84_A / np.sqrt(d)


def earth_rate_sphere(lat_rad):
    """omega_ie in NED on a rotating globe: Omega (cos lat, 0, -sin lat)."""
    lat = np.asarray(lat_rad, dtype=float)
    return np.stack([OMEGA_E * np.cos(lat), np.zeros_like(lat), -OMEGA_E * np.sin(lat)], axis=-1)



def transport_rate(lat_rad, h_m, v_n, v_e):
    """omega_en in NED: how fast local level turns as you move over the WGS-84 ellipsoid."""
    lat = np.asarray(lat_rad, dtype=float)
    rm, rn = radii(lat)
    return np.stack([v_e / (rn + h_m), -v_n / (rm + h_m), -v_e * np.tan(lat) / (rn + h_m)], axis=-1)


def transport_rate_disc(lat_rad, h_m, v_e, lon_rate=None):
    """Transport on the pole-centred disc, NED: (0, 0, −dλ/dt). The disc never tilts local
    level, so there is no horizontal part.

    The analysis passes lon_rate, the rate of change of the GNSS longitude itself (rad/s), so the
    disc prediction depends only on successive coordinates and time. Without it (the app's live
    display) dλ/dt is recovered from the east velocity by undoing the receiver's WGS-84
    conversion, which assumes the receiver derived its velocity from coordinates."""
    lat = np.asarray(lat_rad, dtype=float)
    if lon_rate is None:
        _, rn = radii(lat)
        lon_rate = np.asarray(v_e, dtype=float) / ((rn + h_m) * np.maximum(np.cos(lat), MIN_COS_LAT))
    lon_rate = np.asarray(lon_rate, dtype=float) + np.zeros_like(lat)
    z = np.zeros_like(lon_rate)
    return np.stack([z, z, -lon_rate], axis=-1)


def terms(lat_rad, h_m=0.0, v_n=0.0, v_e=0.0, lon_rate=None):
    """The three regressors (globe Earth rate, globe transport, disc transport), each NED (..., 3)."""
    lat = np.asarray(lat_rad, dtype=float)
    return (earth_rate_sphere(lat), transport_rate(lat, h_m, v_n, v_e),
            transport_rate_disc(lat, h_m, v_e, lon_rate))


def predict(model: str, lat_rad, h_m=0.0, v_n=0.0, v_e=0.0, lon_rate=None):
    """Predicted rotation of local level relative to inertial space (omega_in), NED."""
    k = EXPECTED_K[model]
    return sum(ki * term for ki, term in zip(k, terms(lat_rad, h_m, v_n, v_e, lon_rate)))
