# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_linked_floor_witness import affine_violation, residual_point


def test_lp_reconstructs_a_residual_with_coupled_constraints():
    design = np.array([[1., 0.], [1., 1.], [0., 3.], [1., -2.]])
    residual = np.array([1., 2., 3., 4.])
    target = residual + design @ [.3, -.2]
    point = residual_point(design, residual, [-1, -1], [1, 1], [[1, 1]], [.25], target, 1e-9)
    assert point is not None
    np.testing.assert_allclose(point, [.3, -.2], atol=1e-8)
    assert affine_violation(point, [-1, -1], [1, 1], [[1, 1]], [.25]) == 0


def test_exact_check_flags_a_single_ulp_violation():
    assert affine_violation([.25], [0], [1], [[1]], [.25]) == 0
    assert affine_violation([np.nextafter(.25, 1.)], [0], [1], [[1]], [.25]) > 0
