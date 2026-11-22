# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_mixed_calibration import combinations, interaction, inward_rays


def test_full_step_has_declared_norm_and_remains_in_box():
    point = np.array([-1., 0., 0.])
    rays = np.eye(3)
    steps = combinations(point, rays, radius=.1)
    assert len(steps) == 7
    assert np.linalg.norm(steps[(0, 1, 2)]-point) == pytest.approx(.1)
    assert min(x[0] for x in steps.values()) >= -1.


def test_feasible_separate_axes_do_not_imply_feasible_combination():
    rays = np.array([[.8, .6, 0.], [.6, -.8, 0.], [0., 0., 1.]])
    with pytest.raises(ValueError, match='combined'):
        combinations(np.array([.94, 0., 0.]), rays, radius=.1)


def test_finite_interactions_separate_pair_and_triple_terms():
    values = {}
    for axes in combinations(np.zeros(3), np.eye(3), radius=.1):
        a, b, c = (int(index in axes) for index in range(3))
        values[axes] = np.array([a + 2*b + 3*c + 4*a*b + 5*a*b*c])
    np.testing.assert_array_equal(interaction(values, (0, 1)), [4.])
    np.testing.assert_array_equal(interaction(values, (0, 2)), [0.])
    np.testing.assert_array_equal(interaction(values, (0, 1, 2)), [5.])


def test_inward_projection_keeps_every_subset_feasible_at_two_active_faces():
    point = np.array([-1., -1., 0.])
    rays = np.array([[.8, -.6, 0.], [.6, .8, 0.], [0., 0., 1.]])
    projected = inward_rays(point, rays)
    assert np.min(projected[:, :2]) >= 0
    assert np.linalg.norm(projected[0]) < 1
    assert len(combinations(point, projected, radius=.1)) == 7
