# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_phase_error_score import endpoint_weights


def test_phase_weights_telescope_and_respect_missing_satellites():
    steps = np.array([[2., 4.], [3., 0.], [3., 1.]])
    coefficients = endpoint_weights(steps)
    np.testing.assert_allclose(coefficients, [[-2, -4], [-1, 4], [0, -1], [3, 1]])
    phase = np.random.default_rng(7).normal(size=coefficients.shape)
    np.testing.assert_allclose(np.sum(coefficients * phase), np.sum(steps * np.diff(phase, axis=0)))


def test_endpoint_noise_differs_from_independent_step_noise():
    steps = np.ones((100, 1))
    coefficients = endpoint_weights(steps)
    np.testing.assert_allclose(np.linalg.norm(coefficients)**2, 2.)
    np.testing.assert_allclose(np.linalg.norm(steps)**2, 100.)
    np.testing.assert_allclose(coefficients.sum(axis=0), 0.)
