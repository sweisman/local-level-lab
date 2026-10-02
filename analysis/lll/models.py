# SPDX-License-Identifier: AGPL-3.0-or-later
"""The four Earth models. Every rate is in the local NED frame (north, east, down), in rad/s.

Earth rotation and transport rate (rotation of local level caused by moving over a curved
surface) are kept as separate terms so each can be tested on its own. See docs/MATH.md.
"""
from __future__ import annotations

import numpy as np

OMEGA_E = 7.2921150e-5          # rad/s, sidereal rotation (15.041 deg/h)
WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3
G0 = 9.80665

MODELS = {
    # name: (earth rotation term, curvature term)
    "sphere_rotating": ("sphere", True),
    "sphere_still": (None, True),
    "flat_rotating": ("flat", False),
    "flat_still": (None, False),
}
MODEL_LABELS = {
    "sphere_rotating": "Sphere, rotating",
    "sphere_still": "Sphere, still",
    "flat_rotating": "Flat, rotating",
    "flat_still": "Flat, still",
}
# Expected (k_rot_sphere, k_rot_flat, k_curv) for each model, used by fit.py.
EXPECTED_K = {
    "sphere_rotating": (1.0, 0.0, 1.0),
    "sphere_still": (0.0, 0.0, 1.0),
    "flat_rotating": (0.0, 1.0, 0.0),
    "flat_still": (0.0, 0.0, 0.0),
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


def earth_rate_flat(lat_rad):
    """A flat disc spinning about its centre (the north pole) at the same sidereal rate. The
    rotation axis is vertical everywhere, so the gyro sees Omega about local vertical at
    every location, with no horizontal component."""
    lat = np.asarray(lat_rad, dtype=float)
    z = np.zeros_like(lat)
    return np.stack([z, z, -OMEGA_E + z], axis=-1)


def transport_rate(lat_rad, h_m, v_n, v_e):
    """omega_en in NED: how fast local level turns as you move over the WGS-84 ellipsoid."""
    lat = np.asarray(lat_rad, dtype=float)
    rm, rn = radii(lat)
    return np.stack([v_e / (rn + h_m), -v_n / (rm + h_m), -v_e * np.tan(lat) / (rn + h_m)], axis=-1)


def terms(lat_rad, h_m=0.0, v_n=0.0, v_e=0.0):
    """The three regressors (earth rate sphere, earth rate flat, transport), each NED (..., 3)."""
    lat = np.asarray(lat_rad, dtype=float)
    return earth_rate_sphere(lat), earth_rate_flat(lat), transport_rate(lat, h_m, v_n, v_e)


def predict(model: str, lat_rad, h_m=0.0, v_n=0.0, v_e=0.0):
    """Predicted rotation of local level relative to inertial space (omega_in), NED."""
    k = EXPECTED_K[model]
    es, ef, tr = terms(lat_rad, h_m, v_n, v_e)
    return k[0] * es + k[1] * ef + k[2] * tr
