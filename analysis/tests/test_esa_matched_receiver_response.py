# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.esa_doppler_force import rate_operator
from lll.esa_matched_receiver_response import paired_rate_coefficients
from lll import esa_gyro_force_direction as direction
from lll import esa_matched_gyro_direction as matched
from lll.ilvis0_receiver_force import evaluate


def test_positions_integrated_from_nodal_rates_recover_the_same_velocity_fit():
    t = np.arange(-5., 6.)+.08*np.sin(np.arange(11.))
    rates = np.column_stack((np.sin(t), np.cos(t), (t % 3.)**2))
    interval = .5*(rates[1:]+rates[:-1])*np.diff(t)[:, None]
    positions = [1., -.3, 3000.]+np.vstack((np.zeros(3), np.cumsum(interval, axis=0)))
    pos, vel = paired_rate_coefficients(positions, rates, t, np.arange(-5., 6.))
    np.testing.assert_allclose(pos, vel, atol=1e-12)


def test_alternating_velocity_component_is_unidentifiable_from_positions():
    t = np.arange(-5., 6.)
    rates = ((-1.)**np.arange(len(t)))[:, None]*np.array([3., -2., 1.])
    pos, vel = paired_rate_coefficients(np.zeros_like(rates), rates, t, t)
    np.testing.assert_allclose(pos, np.zeros((3, 3)), atol=1e-13)
    np.testing.assert_allclose(vel, np.zeros((3, 3)), atol=1e-13)
    with pytest.raises(ValueError):
        paired_rate_coefficients(rates, rates, t[::-1], t)


def test_quadratic_velocity_signal_survives_alternating_nuisance_fit():
    t = np.arange(-5., 6.)
    expected = np.array([[60., -30., 4.], [-.1, .2, -.3], [.04, -.01, .02]])
    rates = np.polynomial.polynomial.polyval(t, expected).T
    jittered = rates+((-1.)**np.arange(len(t)))[:, None]*np.array([5., -2., 1.])
    pos = np.vstack((np.zeros(3), np.cumsum(.5*(rates[1:]+rates[:-1]), axis=0)))
    a, b = paired_rate_coefficients(pos, jittered, t, t)
    np.testing.assert_allclose(a, expected, atol=1e-12)
    np.testing.assert_allclose(b, expected, atol=1e-12)


def test_batched_direction_prediction_matches_scalar_force_evaluation(monkeypatch):
    times = np.arange(-5., 6.)
    _, kernel = rate_operator(times)
    center = np.array([1.1, -.6, 2300.])
    rates = np.array([[8e-6, -9e-6, .25], [3e-8, 5e-9, -.07], [1e-9, 3e-9, .005]])
    args = (times, kernel, center, rates, 125.)
    previous = direction.predictions(*args)
    prior_support = matched.support(*args, matched.DISC_WITH_FIELD)

    def scalar(positions, velocity, acceleration, *, gravity_mps2, **kw):
        return {'specific_force_ned_mps2': np.asarray([
            evaluate(p, v, a, gravity_mps2=g, **kw)['specific_force_ned_mps2']
            for p, v, a, g in zip(positions, velocity, acceleration, gravity_mps2, strict=True)])}

    monkeypatch.setattr(direction, 'evaluate_batch', scalar)
    monkeypatch.setattr(matched, 'evaluate_batch', scalar)
    for name, value in direction.predictions(*args).items():
        np.testing.assert_allclose(value, previous[name], rtol=1e-13, atol=1e-13)
    np.testing.assert_allclose(matched.support(*args, matched.DISC_WITH_FIELD).forces,
                               prior_support.forces, rtol=1e-13, atol=1e-13)
