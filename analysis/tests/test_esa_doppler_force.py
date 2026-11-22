# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import esa_doppler_force as force


def test_velocity_derivative_kernel_matches_known_piecewise_acceleration():
    times = np.arange(-5., 6.)
    operator, kernel = force.rate_operator(times)
    acceleration = np.array([1., 5., 8., 2., 1., 3., 5., 9., 2., 1.])
    velocity = np.r_[3., 3.+np.cumsum(acceleration)]
    assert np.all(kernel >= 0)
    assert kernel@np.diff(times) == pytest.approx(1.)
    assert operator[1]@velocity == pytest.approx(kernel@acceleration)
    dense = np.arange(-5., 5.25, .25)
    weights = force.matched_weights(dense, times, kernel)
    assert weights@np.repeat(acceleration, 4) == pytest.approx(operator[1]@velocity)


def test_coordinate_rates_recover_velocity_in_ellipsoid_chart():
    latitude = .7
    height = 2200.
    local = np.array([[120., -23., 3.]])
    coordinates = np.array([[latitude, 1., height]])
    rate = force.coordinate_rates(coordinates, local)[0]
    north, east = force.models.radii(latitude)
    assert rate == pytest.approx([120/(north+height), -23/((east+height)*np.cos(latitude)), 3.])


def test_matched_force_for_stationary_path_is_gravity_in_every_model():
    times = np.arange(-5., 6.)
    _, kernel = force.rate_operator(times)
    for model in force.MATCHED_MODELS:
        assert force.predicted_force(times, kernel, [.5, .2, 1500.], np.zeros((3, 3)),
                                     model, 'height_dependent', 1500.) == pytest.approx(9.81)
