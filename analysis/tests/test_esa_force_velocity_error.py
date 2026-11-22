# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.esa_doppler_force import coordinate_rates, predicted_force_batch, rate_operator
from lll.esa_force_velocity_error import propagated_sd, velocity_sensitivity


def test_shared_velocity_error_cancels_for_difference_of_two_reports():
    sensitivity = np.array([[[1., 0., 0.], [-1., 0., 0.]]])
    covariance_factor = np.broadcast_to(np.eye(3), (2, 3, 3))
    result = propagated_sd(sensitivity, covariance_factor, [0., 5.])
    assert result['independent'].tolist() == pytest.approx([np.sqrt(2.)])
    assert result['5_s'].tolist() == pytest.approx([np.sqrt(2.*(1.-np.exp(-1.)))])
    assert result['shared'].tolist() == [0.]
    assert result['unrestricted_bound'].tolist() == [2.]


def test_velocity_derivative_matches_direct_raw_report_perturbation():
    time = np.arange(-5., 6.)
    coordinates = np.tile([1., -.3, 2000.], (len(time), 1))
    speed = np.column_stack((60.+time, 22.+.2*time**2, 1.-.35*time))
    scale = coordinate_rates(coordinates, np.ones_like(speed))
    weights, kernel = rate_operator(time)
    center = coordinates[5]
    nominal, gradient = velocity_sensitivity(time, kernel, center, weights, speed, scale,
        'sphere_rotating', 'height_dependent', 2000.)

    def force(values):
        return predicted_force_batch(time, kernel, center, weights@(values*scale),
                                     'sphere_rotating', 'height_dependent', 2000.)

    perturbation = np.column_stack((.1*time, np.sin(time), .7*np.cos(time*.2)))
    explicit = (force(speed+.005*perturbation)-force(speed-.005*perturbation))/.01
    assert nominal == pytest.approx(force(speed), abs=1e-12)
    assert (gradient*perturbation).sum() == pytest.approx(explicit, abs=2e-9)
