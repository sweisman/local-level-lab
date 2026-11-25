# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_rf04_force_average import common_support, evaluate_polynomial_jets, local_mean_force


def test_rf04_force_average_uses_polynomial_derivatives_at_each_quadrature_node():
    coefficients = np.array([[[1., 2., 3.], [2., 3., 4.], [4., 5., 6.]]])
    positions, velocities, accelerations = evaluate_polynomial_jets(coefficients, [[0., .5]])
    np.testing.assert_allclose(positions, [[[1., 2., 3.], [3., 4.75, 6.5]]])
    np.testing.assert_allclose(velocities, [[[2., 3., 4.], [6., 8., 10.]]])
    np.testing.assert_allclose(accelerations, [[[8., 10., 12.], [8., 10., 12.]]])


def test_rf04_force_average_requires_both_clocks_and_original_path_support():
    clocks = [np.arange(1, 301)*.005, np.arange(1, 301)*.005+.002]
    accepted = common_support(clocks, .6, .6, .25, 0, 300, (-.2, .2))
    assert len(accepted) == 2 and accepted[0][2] != accepted[1][2]
    assert common_support(clocks, .6, .6, .25, 0, 100, (-.2, .2)) is None
    assert common_support(clocks, .6, .6, .25, 0, 300, (-.1, .2)) is None


def test_rf04_force_average_preserves_stationary_force_in_center_local_axes():
    from lll.ilvis0_force_path_order import _settings

    coefficients = np.zeros((2, 5, 3))
    coefficients[:, 0, :] = [[.5, 2., 500.], [-.7, -1.5, 1000.]]
    nodes, weights = np.polynomial.legendre.leggauss(8)
    for model in ('sphere_still', 'flat_still'):
        result = local_mean_force(coefficients, np.zeros(2), np.tile(nodes, (2, 1)), weights/2, model)
        expected = np.tile([0., 0., -_settings(model)['gravity_mps2']], (2, 1))
        np.testing.assert_allclose(result, expected, atol=1e-12)
