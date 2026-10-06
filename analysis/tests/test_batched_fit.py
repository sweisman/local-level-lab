# SPDX-License-Identifier: AGPL-3.0-or-later
"""Physical row mapping across tilt, orientation, temperature and vertical fallback."""
import numpy as np
import pytest

from lll.attitude import c_bn, unit
from lll.fit import build_rows, _crab_columns
from lll import models


@pytest.mark.parametrize("vertical", [False, True])
@pytest.mark.parametrize("varying_forward", [False, True])
@pytest.mark.parametrize("scalar_bias", [False, True])
def test_rows_reproduce_tilted_sensor_measurements(vertical, varying_forward, scalar_bias):
    n = 5
    up = unit(np.column_stack([np.linspace(.1, .3, n), np.full(n, .2), np.ones(n)]))
    fwd = np.array([1., .3, -.2])
    if varying_forward:
        fwd = np.column_stack([np.ones(n), np.linspace(-.3, .3, n), np.full(n, -.2)])
    bins = dict(t=np.arange(n, dtype=float), lat=np.linspace(.2, .7, n), h=np.full(n, 9000.),
                v_n=np.linspace(40., 240., n), v_e=np.linspace(-100., 120., n),
                up=up, dup_dt=np.full((n, 3), 1e-6), psi=np.linspace(-2., 2., n),
                psi_dot=np.linspace(-1e-5, 1e-5, n), temp=np.linspace(20., 24., n),
                grav=np.array([0, 1, 0, 1, 0]))
    k = np.array([.8, 1.1, .2])
    residual_bias = np.array([[1e-6, -2e-6, 3e-6], [-2e-6, 4e-6, 1e-6]])
    slope = np.array([2e-7, -3e-7, 4e-7])
    known_slope = np.array([-1e-7, 2e-7, 3e-7])
    crab = np.linspace(-.1, .1, n)
    def bias(t):
        assert np.ndim(t) == 0
        return 1e-7*t if scalar_bias else np.array([1., 2., -3.])*1e-7*t
    es, tr, td = models.terms(bins["lat"], bins["h"], bins["v_n"], bins["v_e"])
    measurements = []
    for j in range(n):
        C = c_bn(up[j], fwd[j] if varying_forward else fwd, bins["psi"][j]+crab[j])
        science = C @ (k[0]*es[j]+k[1]*tr[j]+k[2]*td[j])
        rotation = np.cross(bins["dup_dt"][j], up[j])-bins["psi_dot"][j]*up[j]
        measurements.append(science+residual_bias[bins["grav"][j]]+bias(bins["t"][j])
                            +rotation+(slope+known_slope)*(bins["temp"][j]-22.))
    bins["gyro"] = np.array(measurements)
    y, X, idx, cbns, layout = build_rows(bins, fwd, bias, vertical, 22., known_slope, crab)
    np.testing.assert_allclose(X @ np.r_[k, residual_bias.ravel(), slope], y, rtol=2e-14, atol=1e-19)
    np.testing.assert_array_equal(idx, np.arange(n) if vertical else np.repeat(np.arange(n), 3))
    assert layout["n_grav"] == 2
    if not vertical:
        groups = np.array([0, 0, 1, 1, 0])
        jac = _crab_columns(cbns, layout, idx, k, groups, 2)
        for group in range(2):
            offset = (groups == group)*1e-5
            plus = build_rows(bins, fwd, bias, False, 22., known_slope, crab+offset)[1]
            minus = build_rows(bins, fwd, bias, False, 22., known_slope, crab-offset)[1]
            np.testing.assert_allclose(jac[:, group], ((plus-minus)[:, :3] @ k)/2e-5,
                                       rtol=1e-9, atol=1e-15)
