# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated checks for the gravity law used by the archived ESA integrator."""
import ctypes
from fractions import Fraction
from itertools import product

import numpy as np
import pytest

from lll import ilvis0_geographic_bounds as geo
from lll.ilvis0_local_step_bounds import Matrix, Value


@pytest.mark.parametrize('center', [-50., 1482.531, 3300.])
@pytest.mark.parametrize('departure', [False, True])
def test_gravity_interval_encloses_exact_values_and_reference_tangent(center, departure):
    anchor = 1482.531
    height = geo.Scalar.interval(center, center - 31., center + 72., remainder=.2)
    gravity = geo.Scalar.interval(9.81, 9.73, 9.97, remainder=.003)
    bound = geo.gravity_at_height(gravity, height, anchor_height_m=anchor, departure=departure)
    radius = 6_371_000
    numerator = Fraction(float(radius + anchor))
    denominator = radius + Fraction(center)
    factor = (numerator / denominator)**2
    for g, h, g_error, h_error in product(
        map(Fraction, (gravity.lower, gravity.center, gravity.upper)),
        map(Fraction, (height.lower, height.center, height.upper)),
        map(Fraction, (-.003, .003)), map(Fraction, (-.2, .2)),
    ):
        actual = g * ((numerator / (radius + h))**2 - int(departure))
        tangent = (
            Fraction(float(bound.center))
            + (factor - int(departure)) * (g - Fraction(gravity.center) - g_error)
            - 2 * Fraction(gravity.center) * factor / denominator
            * (h - Fraction(center) - h_error)
        )
        assert bound.lower <= actual <= bound.upper
        assert abs(actual - tangent) <= bound.value.remainder


def test_gravity_requires_positive_supported_radii_and_gravity():
    good = geo.Scalar.fixed(9.81)
    zero = geo.Scalar.fixed(0.)
    for gravity, height, anchor in (
        (zero, zero, 0.),
        (good, zero, -6_371_000.),
        (good, zero, float('nan')),
        (good, geo.Scalar.interval(-6_370_999., -6_371_001., -6_370_999.), 0.),
    ):
        with pytest.raises(ValueError):
            geo.gravity_at_height(gravity, height, anchor_height_m=anchor)
    assert geo.gravity_at_height(good, zero, anchor_height_m=0.) == good


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    from lll.ilvis0_wide_tangent import load

    return load(tmp_path_factory.mktemp('height-gravity'), gravity_anchor_height_m=1482.531)[0]


@pytest.mark.parametrize('model_index,model', [
    (0, 'sphere_rotating'), (1, 'sphere_still'), (2, 'flat_still'),
])
def test_height_gravity_matches_native_for_full_and_partial_packets(native, model_index, model):
    # Vary initial down speed, initial height, gravity and the report clock
    # while keeping the report inside its original packet.
    n = 20
    dt = np.full(n, .125)
    theta = np.tile([3e-5, -2e-5, 1e-5], (n, 1))
    dv = dt[:, None] * np.tile([.1, .05, -9.81], (n, 1))
    c = np.array([.7, 1.2, 3200.])
    v = np.array([100., 15., -3.])
    attitude = np.eye(3)
    limits = np.zeros(27)
    axes = [5, 8, 24, 25]
    limits[axes] = [.025, 5., .002, .005]
    f = geo.Scalar.fixed
    anchor = 1482.531
    start = geo.State(
        geo.Coordinates(f(c[0]), f(c[1]), geo.Scalar.interval(c[2], c[2] - 5., c[2] + 5.)),
        Value(v, .025), Matrix(attitude, 0., 0., 'rotation'),
    )
    common = dict(
        removal=f(0.), gravity=geo.Scalar.interval(9.81, 9.808, 9.812),
        model=model, disc_radius_m=6_371_000., gravity_anchor_height_m=anchor,
    )
    for k in range(n - 1):
        start = geo.step(start, Value(theta[k]), Value(dv[k]), period=f(dt[k]), **common)
    state = geo.partial_packet(
        start, Value(theta[-1]), Value(dv[-1]), packet_dt=dt[-1],
        fraction=geo.Scalar.interval(.5, .46, .54), **common,
    )
    time = np.array([19.5 * dt[-1]])

    def forecast(point):
        values = np.empty((1, 3))
        derivative = np.empty((3, 27))
        assert native(n, theta, dv, dt, 1, time, c, v, attitude, limits, point,
                      model_index, 0, 9.81, 6_371_000., values, derivative,
                      ctypes.byref(ctypes.c_int())) == 0
        return values[0], derivative

    center, jac = forecast(np.zeros(27))
    np.testing.assert_allclose(state.position.center, center, rtol=0., atol=2e-11)
    remainder = np.array([s.value.remainder for s in (
        state.position.latitude, state.position.longitude, state.position.height,
    )])
    for corners in product((-1., 1.), repeat=len(axes)):
        p = np.zeros(27)
        p[axes] = corners
        trial, _ = forecast(p)
        assert np.all(np.abs(trial - center - jac @ p) <= remainder + [2e-15, 2e-15, 2e-11])
