# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare lll.models with the independent geometric truth generator."""
import numpy as np
import pytest

import truthgen as tg
from lll import models


def _traj(lat0_deg, lon0_deg, v_n, v_e, h=11000.0):
    """Constant north and east ground speed, written directly as lat/lon rates on each world."""
    def f(t):
        t = np.asarray(t, float)
        return (np.radians(lat0_deg) + v_n * t / 6.37e6, np.radians(lon0_deg) + v_e * t / 4.8e6, np.full_like(t, h))
    return f


CASES = [(40.0, -73.8, 0.0, 230.0), (40.0, -73.8, 230.0, 0.0), (-33.9, 151.2, -120.0, 200.0),
         (65.0, 10.0, 160.0, -160.0), (0.5, 30.0, 0.0, 250.0)]


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("world", ["sphere_rotating", "sphere_still"])
def test_sphere_models_match_geometry(world, case):
    traj = _traj(*case)
    t = np.array([0.0, 600.0, 1800.0])
    w_true, v = tg.truth(world, traj, t)
    lat, lon, h = traj(t)
    w_model = models.predict(world, lat, h, v[:, 0], v[:, 1])
    np.testing.assert_allclose(w_model, w_true, atol=1e-10)   # ≈ 2e-5 °/h


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("world", ["flat_rotating", "flat_still"])
def test_flat_geometry_has_disc_transport(world, case):
    """On the pole-centred disc, a constant-bearing track circles the centre: local level turns
    about the vertical at v_e / r, r = R0 (π/2 − φ). The disc never tilts local level."""
    traj = _traj(*case)
    t = np.array([0.0, 600.0])
    w_true, v = tg.truth(world, traj, t)
    lat = traj(t)[0]
    r = tg.DISC_R0 * (np.pi / 2 - lat)
    spin = tg.SIDEREAL_RATE if world == "flat_rotating" else 0.0
    np.testing.assert_allclose(w_true[:, :2], 0.0, atol=1e-12)
    np.testing.assert_allclose(w_true[:, 2], -spin - v[:, 1] / r, rtol=1e-6, atol=1e-12)


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("world", ["flat_still"])
def test_flat_models_match_geometry(world, case):
    """lll.models gets the GNSS-style velocity (metres on the ellipsoid), as the analysis does."""
    traj = _traj(*case)
    t = np.array([0.0, 600.0])
    w_true, _ = tg.truth(world, traj, t)
    _, v_gnss = tg.truth("sphere_still", traj, t)
    lat, lon, h = traj(t)
    np.testing.assert_allclose(models.predict(world, lat, h, v_gnss[:, 0], v_gnss[:, 1]), w_true, atol=1e-10)


@pytest.mark.parametrize("case", CASES)
def test_disc_from_longitude_rate_needs_no_velocity(case):
    """The analysis feeds the disc model dλ/dt from successive GNSS longitudes. With that, the
    prediction uses no velocity and no Earth radius at all, and still matches the geometry."""
    traj = _traj(*case)
    t = np.array([0.0, 600.0])
    w_true, _ = tg.truth("flat_still", traj, t)
    lat, lon, h = traj(t)
    lon_rate = (traj(t + 0.5)[1] - traj(t - 0.5)[1]) / 1.0
    w = models.predict("flat_still", lat, h, v_n=1e6, v_e=-1e6, lon_rate=lon_rate)   # absurd velocities: unused
    np.testing.assert_allclose(w, w_true, atol=1e-10)
