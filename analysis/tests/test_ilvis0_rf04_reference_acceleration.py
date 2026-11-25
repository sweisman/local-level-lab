# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_rf04_reference_acceleration import acceleration_components, shared_windows
from lll.models import radii


def test_rf04_mean_acceleration_recovers_quadratic_route_in_receiver_axes():
    # At the equator the correction to the north radius is second order in
    # latitude. This small, independent trajectory keeps it below tolerance.
    north_radius, _ = radii(0.)
    coefficients = np.zeros((1, 5, 3))
    coefficients[0, 2, 0] = .5 / north_radius
    actual = acceleration_components(coefficients, np.array([0.]), 2.)
    np.testing.assert_allclose(actual, [[1., 0.]], atol=1e-12)


def test_rf04_acceleration_window_requires_both_endpoints_and_all_shifted_support():
    support = np.array([[-5.4, 5.4], [-5.39, 5.4], [-6., 6.]])
    seconds = np.array([5, 6, 8])
    offsets = np.zeros(3)
    result = shared_windows(seconds, offsets, support, half_width=5, epoch_count=13, shift=.4)
    np.testing.assert_array_equal(result, [True, False, False])
