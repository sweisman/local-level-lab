# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.stats import f


def _inputs():
    from lll.state_space_covariance import LinearInnovations

    n, cut = 9, 5
    epochs = np.arange(1.0, n + 1)
    config = dict(transition=[[1.0]], process_loading=[[0.3]],
                  observation=[[1.0]], white_loading=[[0.4]])
    operator = LinearInnovations((config for _ in epochs),
        epoch_count=n, state_dimension=1, observation_dimension=1, initial_loading=[[0.2]],
        maximum_bytes=10_000, design_is_fixed=True, error_distribution='gaussian')
    covariance = 0.2**2 + 0.3**2 * np.minimum.outer(epochs, epochs) + 0.4**2 * np.eye(n)
    design = np.column_stack((np.ones(n), epochs / 3))
    observed = np.array([1.0, 2.2, 1.3, 3.5, 4.0, 7.1, 4.2, 8.6, 5.0])
    return operator, cut, covariance, design, observed


def _bracket(operator, cut, design, earlier, white, walk):
    from lll.future_covariance_bracket import prepare

    return prepare(operator, design, earlier, training_epochs=cut, parameter_scales=[1., 1.],
                   future_white_loading=white, future_walk_loading=walk, maximum_bytes=20_000)


def test_bound_scores_match_independent_dense_covariances():
    from lll.future_covariance_bracket import score

    operator, cut, covariance, design, observed = _inputs()
    count = len(observed) - cut
    white, walk = np.array([0.2, 0.6, 0.9, 0.0]), np.array([0.0, 0.1, 0.4, 0.2])
    forecast = _bracket(operator, cut, design, observed[:cut],
                        white[:, None, None], walk[:, None, None])
    past = covariance[:cut, :cut]
    response = np.linalg.solve(past, covariance[:cut, cut:]).T
    design_earlier = design[:cut]
    precision_design = np.linalg.solve(past, design_earlier)
    term = np.linalg.inv(design_earlier.T @ precision_design)
    beta = term @ precision_design.T @ observed[:cut]
    contrast = design[cut:] - response @ design_earlier
    residual = observed[cut:] - response @ observed[:cut] - contrast @ beta
    conditional = covariance[cut:, cut:] - response @ covariance[:cut, cut:] + contrast @ term @ contrast.T
    added = np.diag(white**2) + np.minimum.outer(np.cumsum(walk**2), np.cumsum(walk**2))
    expected = [residual @ np.linalg.solve(conditional + added, residual),
                residual @ np.linalg.solve(conditional, residual)]
    result = score(forecast, observed[cut:])
    assert result['quadratic_range'] == pytest.approx(expected, rel=1e-10)
    errors = observed[:cut] - design_earlier @ beta
    scale = errors @ np.linalg.solve(past, errors) / (cut - len(beta))
    assert result['pivot_range'] == pytest.approx(np.asarray(expected) / (count * scale))
    assert result['reference_band'] == pytest.approx(f.ppf([.025, .975], count, 3))


def test_zero_future_extra_covariance_reduces_to_original_score():
    from lll.calibrated_joint_path import prepare as prepare_original, score as score_original
    from lll.future_covariance_bracket import score

    operator, cut, _, design, observed = _inputs()
    zeros = np.zeros((len(observed) - cut, 1, 1))
    forecast = _bracket(operator, cut, design, observed[:cut], zeros, zeros)
    original = prepare_original(operator, design, observed[:cut],
                                training_epochs=cut, parameter_scales=[1., 1.])
    reference = score_original(operator, original, observed[cut:])
    assert score(forecast, observed[cut:])['quadratic_range'] == pytest.approx(
        [reference['squared_standardized_error']] * 2)


def test_unidentified_future_stays_unsupported_and_missing_bound_fails():
    from lll.future_covariance_bracket import score

    operator, cut, _, design, observed = _inputs()
    design[:cut, 1] = 0.0
    white = np.ones((len(observed) - cut, 1, 1))
    forecast = _bracket(operator, cut, design, observed[:cut], white, white)
    assert score(forecast, observed[cut:])['status'] == 'unidentifiable'
    with pytest.raises(ValueError):
        _bracket(operator, cut, design, observed[:cut], None, white)
