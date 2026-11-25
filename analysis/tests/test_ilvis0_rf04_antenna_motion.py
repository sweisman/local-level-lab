# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
from scipy.spatial.transform import Rotation

from lll.ilvis0_rf04_antenna_motion import fit_displacement, sampled_acceleration_design


def test_sampled_antenna_acceleration_vanishes_at_constant_attitude():
    attitudes = Rotation.from_euler('Z', np.full((13, 1), 35.), degrees=True).as_matrix()
    design = sampled_acceleration_design(attitudes, np.array([3, 6, 9]), 2)
    np.testing.assert_array_equal(design, np.zeros((3, 2, 3)))


def test_sampled_antenna_acceleration_matches_endpoint_differences_for_yaw():
    yaw = np.linspace(0., 1., 21)
    attitudes = Rotation.from_euler('Z', yaw[:, None]).as_matrix()
    design = sampled_acceleration_design(attitudes, np.array([10]), 3)
    arm = np.array([5., 0., 0.])
    positions = 5.*np.stack((np.cos(yaw), np.sin(yaw)), axis=1)
    expected = (positions[14]-positions[12]-positions[8]+positions[6])/12
    np.testing.assert_allclose((design@arm)[0], expected, atol=1e-14)


def test_antenna_displacement_respects_radius_and_keeps_rank():
    design = np.diag([3., 2., 1.])
    displacement, fit = fit_displacement(design, [6., -4., 1.], radius=5.)
    np.testing.assert_allclose(displacement, [2., -2., 1.])
    assert fit['rank'] == 3 and not fit['at_radius']
    clipped, fit = fit_displacement(design, [6., -4., 1.], radius=1.)
    np.testing.assert_allclose(np.linalg.norm(clipped), 1.)
    assert fit['at_radius'] and fit['rank'] == 3
    assert fit_displacement(np.zeros((4, 3)), np.ones(4), radius=5.)[1]['rank'] == 0
