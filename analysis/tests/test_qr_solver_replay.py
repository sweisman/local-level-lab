# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
from scipy.optimize import lsq_linear

from lll.qr_solver_replay import reduced_system


def test_qr_preserves_objective_differences_with_a_large_perpendicular_residual():
    design = np.array([[2., 1.], [1., 3.], [-4., 2.], [0., 0.]])
    residual = np.array([.5, -.75, .25, 102.])
    compressed, short = reduced_system(design, residual)
    candidates = np.array([[0., 0.], [.75, -.5], [-.9, 1.]])
    for point in candidates:
        reference = residual+design@point
        projected = short+compressed@point
        np.testing.assert_allclose(reference@reference-residual@residual,
                                   projected@projected-short@short, atol=2e-12)


def test_qr_keeps_a_weak_direction_and_the_original_coordinate_bounds():
    design = np.array([[1., 1.], [1., 1.+1e-7], [0., 0.], [0., 0.]])
    residual = -(design@np.array([2., -2.])) + [0., 0., 102., 0.]
    compressed, short = reduced_system(design, residual)
    fit = lsq_linear(compressed, -short, bounds=(-1., 1.), method='bvls', tol=1e-14)
    np.testing.assert_allclose(fit.x, [1., -1.], atol=1e-6)
