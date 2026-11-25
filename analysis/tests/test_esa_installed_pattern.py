# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_installed_pattern import angular_change, slope_coefficient


def test_installed_pattern_sensitivity_centers_the_interval_weights():
    angular = [np.array([.2, .1]), np.array([.3, .4])]
    assert slope_coefficient(angular, [5., 5., 8., 8.]) == 0.
    assert slope_coefficient(angular, [2., 0., 1., -1.]) == pytest.approx(1.)


def test_installed_pattern_ray_change_is_stable_for_tiny_and_opposed_rays():
    rays = np.array([[1., 0., 0.], [1., 0., 0.]])
    shifted = np.array([[1., 1e-9, 0.], [-1., 0., 0.]])
    np.testing.assert_allclose(angular_change(rays, shifted), [1e-9, np.pi], rtol=1e-13)
