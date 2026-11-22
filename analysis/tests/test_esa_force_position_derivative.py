# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.esa_doppler_force import coordinate_rates, predicted_force_batch, rate_operator
from lll.esa_force_position_derivative import position_weights
from lll.esa_force_velocity_error import force_sensitivity


def test_position_weights_recover_exact_derivatives_on_shifted_clock():
    times = np.arange(-5., 6.)+.001*np.sin(np.arange(11.))+.0002
    position = 30.+2.*times-.3*times**2+.07*times**3
    np.testing.assert_allclose(position_weights(times)@(position-30.), [2., -.6, .21], atol=1e-13)


def test_position_uncertainty_derivative_matches_direct_sample_perturbation():
    time = np.arange(-5., 6.)
    center = np.asarray([1., -.4, 2000.])
    positions = center+np.column_stack((4e-6*time, -7e-6*time, time-.13*time**2))
    scale = coordinate_rates(positions, np.ones_like(positions))
    _, kernel = rate_operator(time)
    weights = position_weights(time)
    coeff = weights@(positions-center)
    options = ('sphere_still', 'height_dependent', 2000.)
    nominal, gradient = force_sensitivity(time, kernel, center, coeff, weights, scale, *options)

    def force(perturbed):
        return predicted_force_batch(time, kernel, center, weights@(perturbed-center), *options)

    direction = np.column_stack((time*.1, np.sin(time), np.cos(time*.25)))
    delta = direction*scale*.002
    observed = (force(positions+delta)-force(positions-delta))/.004
    assert nominal == pytest.approx(force(positions), abs=2e-12)
    assert (gradient*direction).sum() == pytest.approx(observed, abs=1e-8)
