# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.state_space_covariance import LinearInnovations


def process(n):
    return LinearInnovations((dict(transition=[[1.]], process_loading=[[.17]],
        observation=[[1.]], white_loading=[[.4]]) for _ in range(n)),
        epoch_count=n, state_dimension=1, observation_dimension=1,
        initial_loading=[[.2]], maximum_bytes=10000, design_is_fixed=True,
        error_distribution='gaussian')


def test_split_scores_match_dense_independent_innovation_calculation():
    from lll.split_contrast_prediction import prepare, predict, score

    n, choice, cut = 13, 3, 9
    t = np.arange(1., n + 1)
    x = np.column_stack((np.ones(n), np.sin(t)))
    y = np.cos(t) + x @ [2., -.3]
    direction = np.arange(1., n - cut + 1)[:, None]
    covariance = .2**2 + .17**2 * np.minimum.outer(t, t) + .4**2 * np.eye(n)
    earlier, cross = covariance[:cut, :cut], covariance[cut:, :cut]
    base_whitening = np.linalg.cholesky(covariance)
    innovation_x = np.linalg.solve(base_whitening, x)
    innovation_y = np.linalg.solve(base_whitening, y)
    design_b = innovation_x[choice:cut]
    v = np.linalg.inv(design_b.T @ design_b)
    coefficients = v @ design_b.T @ innovation_y[choice:cut]
    variance = np.linalg.norm(innovation_y[choice:cut] - design_b @ coefficients)**2 / (cut - choice - 2)
    conditional = covariance[cut:, cut:] - cross @ np.linalg.solve(earlier, cross.T)
    true_x = innovation_x[cut:]
    full_covariance = np.eye(n - cut) + true_x @ v @ true_x.T
    innovation_direction = np.linalg.solve(np.linalg.cholesky(conditional), direction)[:, 0]
    delta = innovation_y[cut:] - true_x @ coefficients
    precision_direction = np.linalg.solve(full_covariance, innovation_direction)
    projected_energy = (delta @ precision_direction)**2 / (innovation_direction @ precision_direction)
    total = delta @ np.linalg.solve(full_covariance, delta)

    frozen = prepare(process(n), x, direction, choice_epochs=choice, training_epochs=cut)
    forecast = predict(frozen, y[:cut])
    result = score(forecast, y[cut:])
    assert forecast['parameter_estimate'] == pytest.approx(coefficients)
    assert result['training_variance_scale'] == pytest.approx(variance)
    assert result['contrast_squared_error'] == pytest.approx(projected_energy)
    assert result['orthogonal_squared_error'] == pytest.approx(total - projected_energy)
    assert result['contrast_f'] == pytest.approx(projected_energy / variance)


def test_calibration_window_must_identify_future_sensitive_parameters():
    from lll.split_contrast_prediction import prepare, predict, score

    operator = process(10)
    designs = np.column_stack((np.ones(10), [1., 2., 0., 0., 0., 0., 1., 2., 3., 4.]))
    setup = prepare(operator, operator.unwhiten(designs), np.ones((4, 1)),
                    choice_epochs=2, training_epochs=6)
    assert predict(setup, np.ones(6))['status'] == 'unidentifiable'
    assert score(predict(setup, np.ones(6)), np.ones(4))['scientific_decision'] == 'abstain'


def test_missing_direction_cannot_be_scored_as_a_distinction():
    from lll.split_contrast_prediction import prepare, predict, score

    setup = prepare(process(10), np.ones((10, 1)), np.zeros((4, 1)),
                    choice_epochs=2, training_epochs=6)
    result = score(predict(setup, np.arange(6.)), np.arange(6., 10.))
    assert result['contrast_coordinates'] == 0
    assert result['contrast_f'] is None
    assert result['orthogonal_f'] > 0.
