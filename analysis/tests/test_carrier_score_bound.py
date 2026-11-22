# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll.carrier_score_bound import carrier_score_bound, score_interpolation
from lll.esa_carrier_score_bound import range_gradients
from lll.gnss_position import ecef
from lll.shared_motion_carrier import range_shift


def test_off_grid_score_interpolation_matches_quadratic_error():
    weights, bound = score_interpolation([0., 2., 5.], [0.5, 1., 4., 5.],
                                         [[2., 0., 0.], [-1., 0., 0.], [1., 0., 0.], [2., 0., 0.]])
    assert weights[:, 0] == pytest.approx([1., 1./3., 8./3.])
    assert weights[:, 1:] == pytest.approx(np.zeros((3, 2)))
    assert bound >= abs(2*.5**2-1.+4.**2+2*5.**2 - weights[:, 0]@[0., 4., 25.])/math.sqrt(20)


def test_carrier_certificate_is_sharp_for_simple_centered_geometry():
    gradients = np.array([[1., 0., 0.], [-1., 0., 0.], [0., 1., 0.], [0., -1., 0.],
                          [0., 0., 1.], [0., 0., -1.]])
    pairs = [(gradients, gradients)]*2
    result = carrier_score_bound([0., 1., 2.], pairs, [0, 2], [1.], [[1., 0., 0.]])
    assert result['range_rms_to_score'] == pytest.approx(math.sqrt(3.))
    assert result['acceleration_rms_to_score'] == pytest.approx(0., abs=1e-14)
    assert result['dual_weights'] == pytest.approx(np.r_[-gradients[:, 0], gradients[:, 0]]/4.)


def test_unobserved_direction_remains_in_acceleration_bound():
    gradients = np.array([[1., 0., 0.], [-1., 0., 0.]])
    result = carrier_score_bound([0., 1., 2.], [(gradients, gradients)]*2,
                                 [0, 2], [1.], [[0., 0., 1.]])
    assert result['range_rms_to_score'] == 0.
    assert result['acceleration_rms_to_score'] == pytest.approx(1./math.sqrt(3.))


def test_range_gradient_agrees_with_signed_exact_range_change():
    position = np.array([1.1, -0.8, 1200.])
    metric = np.array([6.37e6, 2.6e6, 1.])
    satellites = np.array([[21e6, 10e6, 12e6], [22e6, -15e6, 6e6], [10e6, 8e6, 22e6]])
    steps = np.eye(3)*0.25/metric
    differences = [(range_shift(ecef(*position), ecef(*(position+step)), satellites) -
                    range_shift(ecef(*position), ecef(*(position-step)), satellites))/0.5 for step in steps]
    assert range_gradients(position, satellites, metric) == pytest.approx(np.array(differences).T, abs=8e-9)
