# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.geodesic_step import corrected_trial


def test_corrected_trial_changes_direction_to_follow_a_known_quadratic_valley():
    point = np.zeros(2)
    residual = np.array([-1., 0.])
    jacobian = np.diag([1., 10.])
    direction = np.array([1., 0.])
    proposal, predicted, fraction = corrected_trial(point, residual, jacobian, direction, np.array([0., -5.]))
    np.testing.assert_allclose(proposal, [1., .5])
    assert predicted == 1. and fraction == 1.


def test_corrected_trial_preserves_the_original_parameter_box():
    point = np.array([0., .9])
    residual = np.array([-1., 0.])
    jacobian = np.diag([1., 10.])
    direction = np.array([1., 0.])
    proposal, predicted, fraction = corrected_trial(point, residual, jacobian, direction, np.array([0., -5.]))
    assert np.max(abs(proposal)) <= 1
    assert fraction < 1.
    assert predicted > 0.


def test_corrected_trial_requires_an_actual_transverse_bend():
    assert corrected_trial(np.zeros(2), np.array([-1., 0.]), np.eye(2),
                           np.array([1., 0.]), np.zeros(2)) is None
