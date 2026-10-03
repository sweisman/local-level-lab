# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent truth generator. Must not import lll.models.

It computes the rotation of the local-level (north-east-down) frame relative to inertial space
from geometry alone. It builds the NED axes at the aircraft's position, expresses them in an
inertial frame, and differentiates that orientation numerically. No transport-rate or
Earth-rate formula is used, so a sign error, frame mistake or missing term in lll.models
can't be reproduced here by construction.

Worlds:
  sphere_*  WGS-84 ellipsoid, rotating about its axis at the sidereal rate or still.
  flat_*    Azimuthal-equidistant disc centred on the north pole: a point at latitude φ sits at
            radius R0·(π/2 − φ), and north points to the centre. The disc spins about its centre
            at the sidereal rate or is still.
"""
from __future__ import annotations

import numpy as np

WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563
WGS84_E2 = WGS84_F * (2 - WGS84_F)
SIDEREAL_RATE = 2 * np.pi / 86164.0905    # rad/s
DISC_R0 = 6371008.8                        # m per radian of colatitude on the disc


def _rz(a):
    c, s = np.cos(a), np.sin(a)
    z, o = np.zeros_like(a), np.ones_like(a)
    return np.stack([np.stack([c, -s, z], -1), np.stack([s, c, z], -1), np.stack([z, z, o], -1)], -2)


def _vee(m):
    return np.stack([m[..., 2, 1] - m[..., 1, 2], m[..., 0, 2] - m[..., 2, 0], m[..., 1, 0] - m[..., 0, 1]], -1) / 2


def ned_axes(world, lat, lon):
    """Columns N, E, D of the local frame, in the world-fixed frame (Earth-fixed or disc-fixed)."""
    sl, cl, so, co = np.sin(lat), np.cos(lat), np.sin(lon), np.cos(lon)
    if world.startswith("sphere"):
        n = np.stack([-sl * co, -sl * so, cl], -1)
        e = np.stack([-so, co, np.zeros_like(lat)], -1)
        d = np.stack([-cl * co, -cl * so, -sl], -1)
    else:  # disc, z up; east is counter-clockwise seen from above, like the Earth's rotation
        n = np.stack([-co, -so, np.zeros_like(lat)], -1)
        e = np.stack([-so, co, np.zeros_like(lat)], -1)
        d = np.stack([np.zeros_like(lat), np.zeros_like(lat), -np.ones_like(lat)], -1)
    return np.stack([n, e, d], -1)


def position(world, lat, lon, h):
    """World-fixed position, m."""
    if world.startswith("sphere"):
        rn = WGS84_A / np.sqrt(1 - WGS84_E2 * np.sin(lat) ** 2)
        return np.stack([(rn + h) * np.cos(lat) * np.cos(lon), (rn + h) * np.cos(lat) * np.sin(lon),
                         (rn * (1 - WGS84_E2) + h) * np.sin(lat)], -1)
    r = DISC_R0 * (np.pi / 2 - lat)
    return np.stack([r * np.cos(lon), r * np.sin(lon), h], -1)


def _c_in(world, t, lat, lon):
    spin = SIDEREAL_RATE * t if world.endswith("rotating") else np.zeros_like(t)
    return _rz(spin) @ ned_axes(world, lat, lon)


def truth(world, traj, t, dt=0.01):
    """Rotation of local level relative to inertial space, in NED, rad/s, at times t.

    traj(t) -> (lat, lon, h) in radians and metres, vectorized. Also returns the velocity
    relative to the world surface in NED (v_n, v_e), from the differentiated position."""
    t = np.asarray(t, float)
    lo, hi = traj(t - dt), traj(t + dt)
    c0 = _c_in(world, t, *traj(t)[:2])
    cdot = (_c_in(world, t + dt, *hi[:2]) - _c_in(world, t - dt, *lo[:2])) / (2 * dt)
    w = _vee(np.swapaxes(c0, -1, -2) @ cdot)
    v_world = (position(world, *hi) - position(world, *lo)) / (2 * dt)
    axes = ned_axes(world, *traj(t)[:2])
    v_ned = np.einsum("nji,nj->ni", axes, v_world)
    return w, v_ned
