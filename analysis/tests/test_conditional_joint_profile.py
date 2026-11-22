"""Future innovations match an independent dense conditional covariance."""

import numpy as np
import pytest


def fixture():
    from lll.state_space_covariance import LinearInnovations
    h = np.array([[1.], [.4], [-.2]])
    steps = [dict(transition=np.array([[.7]]),
                  process_loading=np.array([[.1]]), observation=h,
                  white_loading=np.eye(3) * .3) for _ in range(3)]
    operator = LinearInnovations(steps, epoch_count=3, state_dimension=1,
        observation_dimension=3, initial_loading=np.array([[.2]]),
        maximum_bytes=1024 * 1024, design_is_fixed=True,
        error_distribution='gaussian')
    state = np.zeros(13)
    state[0] = .2
    loading = []
    for i in range(3):
        state = .7 * state
        state[i + 1] += .1
        value = h @ state[None, :]
        value[:, 4 + 3*i:7 + 3*i] += np.eye(3) * .3
        loading.append(value)
    matrix = np.vstack(loading)
    return operator, matrix @ matrix.T


def test_future_innovations_match_dense_conditional_quadratic():
    from lll.conditional_joint_profile import whiten_conditioned_future
    operator, covariance = fixture()
    residual = np.array([.1, -.2, .3, .4, .5, -.1, .6, -.3, .2])
    design = np.sin(np.arange(18).reshape(9, 2)) * .1
    result = whiten_conditioned_future(operator, residual.reshape(3, 3),
                                       design, training_epochs=1)
    for correction in (np.zeros(2), np.array([.2, -.3]), np.array([1., 0.])):
        whitened = result['future_residual'] - result['future_design'] @ correction
        error = residual - design @ correction
        ctt = covariance[:3, :3]
        cft = covariance[3:, :3]
        conditional = covariance[3:, 3:] - cft @ np.linalg.solve(ctt, cft.T)
        centered = error[3:] - cft @ np.linalg.solve(ctt, error[:3])
        expected = centered @ np.linalg.solve(conditional, centered)
        assert whitened @ whitened == pytest.approx(expected, rel=2e-11)


def test_training_only_column_changes_conditional_future():
    from lll.conditional_joint_profile import whiten_conditioned_future
    operator, _ = fixture()
    design = np.zeros((9, 1))
    design[0, 0] = 1.
    result = whiten_conditioned_future(operator, np.zeros((3, 3)), design,
                                       training_epochs=1)
    assert np.linalg.norm(result['future_design']) > 0


def test_bounded_profile_matches_independent_dense_conditional_solve():
    from scipy.optimize import lsq_linear
    from lll.conditional_joint_profile import whiten_conditioned_future
    from lll.joint_future_profile import profile_future
    operator, covariance = fixture()
    residual = np.cos(np.arange(9)) * .2
    design = np.sin(np.arange(18).reshape(9, 2)) * .08
    wrapped = whiten_conditioned_future(operator, residual.reshape(3, 3),
                                        design, training_epochs=1)
    result = profile_future(wrapped['future_residual'], wrapped['future_design'],
                            lower=[-.5, -.5], upper=[.5, .5], rank_rtol=1e-10)
    ctt, cft = covariance[:3, :3], covariance[3:, :3]
    conditional = covariance[3:, 3:] - cft @ np.linalg.solve(ctt, cft.T)
    mean_residual = residual[3:] - cft @ np.linalg.solve(ctt, residual[:3])
    mean_design = design[3:] - cft @ np.linalg.solve(ctt, design[:3])
    factor = np.linalg.cholesky(conditional)
    matrix = np.linalg.solve(factor, mean_design)
    target = np.linalg.solve(factor, mean_residual)
    independent = lsq_linear(matrix, target, bounds=(-.5, .5), method='bvls',
                             tol=1e-12, max_iter=200)
    expected = np.sum((target - matrix @ independent.x) ** 2)
    assert result['profiled_squared_residual'] == pytest.approx(expected, rel=2e-10)
    assert result['scientific_decision'] == 'abstain'


def test_incomplete_future_or_wrong_operator_fails():
    from lll.conditional_joint_profile import whiten_conditioned_future
    operator, _ = fixture()
    with pytest.raises(ValueError):
        whiten_conditioned_future(operator, np.zeros((3, 3)),
                                   np.zeros((8, 1)), training_epochs=1)
    with pytest.raises(ValueError):
        whiten_conditioned_future(operator, np.zeros((3, 3)),
                                   np.zeros((9, 1)), training_epochs=3)
