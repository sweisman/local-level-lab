# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np


def test_rescaling_preserves_the_residual_constraints_and_score():
    from lll.esa_linked_scaled_proposals import scaled_problem

    rng = np.random.default_rng(834)
    lower = np.array([30., -0.005, 4., 8.])
    upper = np.array([90., 0.001, 4., 10.])
    start = np.array([70., 0., 4., 8.])
    design, residual = rng.normal(size=(7, 4)), rng.normal(size=7)
    cuts, limits = rng.normal(size=(3, 4)), rng.normal(size=3)
    objective = rng.normal(size=4)
    problem = scaled_problem(design, residual, lower, upper, cuts, limits, objective, start)
    scaled_design, scaled_residual, lo, hi, scaled_cuts, shifted_limits, scaled_score, point = problem
    np.testing.assert_array_equal(lo, [-1., -1., 0., -1.])
    np.testing.assert_array_equal(hi, [1., 1., 0., 1.])
    np.testing.assert_allclose(scaled_residual + scaled_design @ point, residual + design @ start)
    np.testing.assert_allclose(scaled_cuts @ point - shifted_limits, cuts @ start - limits)
    np.testing.assert_allclose(scaled_score @ point, objective @ (start - (lower + upper) / 2))
    np.testing.assert_allclose(scaled_residual + scaled_design @ lo, residual + design @ lower)
    np.testing.assert_allclose(scaled_residual + scaled_design @ hi, residual + design @ upper)
