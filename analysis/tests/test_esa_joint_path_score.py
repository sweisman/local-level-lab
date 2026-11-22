# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_joint_path_score import joint_score
from lll.state_space_covariance import LinearInnovations


def test_joint_score_matches_a_dense_conditional_distribution():
    n, cut = 5, 2
    initial, white, process = .25, .4, .15
    mixing = np.array([[1., 0.], [.7, .8]])
    identity = np.eye(2)
    system = LinearInnovations(iter(dict(transition=identity, process_loading=process*mixing,
        observation=identity, white_loading=white*identity) for _ in range(n)),
        epoch_count=n, state_dimension=2, observation_dimension=2,
        initial_loading=initial*mixing, maximum_bytes=10000,
        design_is_fixed=True, error_distribution='gaussian')
    epochs = np.arange(1., n+1)
    latent = (initial**2+process**2*np.minimum.outer(epochs, epochs))
    full = np.kron(latent, mixing @ mixing.T)+white**2*np.eye(2*n)
    border = 2*cut
    future = full[border:, border:]-full[border:, :border] @ np.linalg.solve(
        full[:border, :border], full[:border, border:])
    centered = np.array([[.4, -.9], [.2, -.3], [1.1, .2]])
    scored = joint_score(system, cut, centered, horizons=(2, 3))
    for horizon in (2, 3):
        expected = future[:2*horizon, :2*horizon]
        delta = centered[:horizon].ravel()
        square = delta @ np.linalg.solve(expected, delta)
        logdet = np.linalg.slogdet(expected)[1]
        row = scored[str(horizon)]
        np.testing.assert_allclose(row['squared_standardized_error'], square)
        np.testing.assert_allclose(row['conditional_log_determinant'], logdet)
        np.testing.assert_allclose(row['gaussian_negative_log_score'],
                                   (square+logdet+len(delta)*np.log(2*np.pi))/2.)
