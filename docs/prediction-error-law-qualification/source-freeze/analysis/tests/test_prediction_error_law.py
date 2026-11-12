# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only scores for declared state-space error laws."""
import math

import numpy as np
import pytest

from lll.state_space_covariance import LinearInnovations
from lll.prediction_error_law import (score_training_laws, forecast_law_spread,
                                      score_profiled_training_laws,
                                      profiled_forecast_law_spread)


def independent_operator(variances):
    steps = [dict(transition=np.eye(1), process_loading=np.zeros((1, 0)),
                  observation=np.zeros((1, 1)),
                  white_loading=np.array([[math.sqrt(variance)]]))
             for variance in variances]
    return LinearInnovations(
        steps, epoch_count=len(steps), state_dimension=1,
        observation_dimension=1, initial_loading=np.zeros((1, 0)),
        maximum_bytes=10000, design_is_fixed=True,
        error_distribution='gaussian')


def test_training_scores_match_independent_normal_formula():
    residual = np.array([0.2, -0.3])
    result = score_training_laws(
        {'unit': independent_operator([1., 1., 1.]),
         'wide': independent_operator([4., 4., 4.])}, residual,
        training_epochs=2)
    by_id = {row['law_id']: row for row in result['laws']}
    for name, variance in [('unit', 1.), ('wide', 4.)]:
        expected = 0.5*(float(residual@residual)/variance
                        + 2*math.log(variance) + 2*math.log(2*math.pi))
        assert by_id[name]['negative_log_likelihood'] == pytest.approx(expected)
    assert result['training_epochs'] == 2
    assert result['later_observations_used'] is False
    assert result['coverage_calibrated'] is False


def test_equal_training_laws_remain_tied_when_future_covariance_differs():
    result = score_training_laws(
        {'future_narrow': independent_operator([1., 1., 1.]),
         'future_wide': independent_operator([1., 1., 100.])},
        np.array([0.1, -0.2]), training_epochs=2)
    assert len(result['laws']) == 2
    assert result['laws'][0]['delta_nll'] == pytest.approx(0.)
    assert result['laws'][1]['delta_nll'] == pytest.approx(0.)
    assert result['numerical_unique_minimum'] is False
    assert result['statistical_identification_assessed'] is False


def test_shared_offset_likelihood_matches_dense_independent_reference():
    steps = [dict(transition=np.eye(1), process_loading=np.zeros((1, 0)),
                  observation=np.eye(1),
                  white_loading=np.array([[math.sqrt(.2)]])) for _ in range(4)]
    operator = LinearInnovations(
        steps, epoch_count=4, state_dimension=1,
        observation_dimension=1, initial_loading=np.array([[math.sqrt(.5)]]),
        maximum_bytes=10000, design_is_fixed=True,
        error_distribution='gaussian')
    residual = np.array([.3, -.4, .7])
    covariance = .5*np.ones((3, 3)) + .2*np.eye(3)
    expected = .5*(residual@np.linalg.solve(covariance, residual)
                   + np.linalg.slogdet(covariance)[1]
                   + 3*math.log(2*math.pi))
    result = score_training_laws({'shared': operator}, residual,
                                 training_epochs=3)
    assert result['laws'][0]['negative_log_likelihood'] == pytest.approx(expected)


def test_one_training_epoch_cannot_separate_white_from_persistent_error():
    def offset_operator(white, offset):
        steps = [dict(transition=np.eye(1), process_loading=np.zeros((1, 0)),
                      observation=np.eye(1),
                      white_loading=np.array([[math.sqrt(white)]]))
                 for _ in range(3)]
        return LinearInnovations(
            steps, epoch_count=3, state_dimension=1,
            observation_dimension=1,
            initial_loading=np.array([[math.sqrt(offset)]]),
            maximum_bytes=10000, design_is_fixed=True,
            error_distribution='gaussian')
    laws = {'white': offset_operator(1., 0.),
            'persistent': offset_operator(.01, .99)}
    result = forecast_law_spread(laws, np.array([.2]), training_epochs=1)
    assert result['training_nll_span'] == pytest.approx(0., abs=1e-12)
    assert result['max_forecast_sigma_ratio'] == pytest.approx(math.sqrt(1/.0199))
    assert result['later_observations_used'] is False
    assert result['coverage_calibrated'] is False


def test_training_input_and_operator_dimensions_are_checked():
    operator = independent_operator([1., 1., 1.])
    with pytest.raises(ValueError):
        score_training_laws({'law': operator}, np.array([0., 0., 99.]),
                            training_epochs=2)
    with pytest.raises(ValueError):
        score_training_laws({'law': operator}, np.array([0., np.nan]),
                            training_epochs=2)
    with pytest.raises(ValueError):
        score_training_laws({'law': operator}, np.array([0., 0.]),
                            training_epochs=3)


def test_profiled_score_matches_mean_removed_normal_contrast():
    observed = np.array([1., 3.])
    design = np.ones((2, 1))
    laws = {'unit': independent_operator([1., 1., 1.]),
            'wide': independent_operator([4., 4., 4.])}
    result = score_profiled_training_laws(
        laws, observed, design, training_epochs=2, rank_rtol=1e-10,
        parameter_scales=np.ones(1))
    rows = {row['law_id']: row for row in result['laws']}
    for name, variance in [('unit', 1.), ('wide', 4.)]:
        expected = .5*(2./variance+math.log(variance)+math.log(2*math.pi))
        assert rows[name]['restricted_negative_log_likelihood'] == pytest.approx(expected)
    assert result['training_mean_rank'] == 1
    assert result['residual_degrees_of_freedom'] == 1
    assert result['nonlinear_fit_accounted_for'] is False


def test_profiled_score_is_invariant_to_redundant_mean_columns():
    laws = {'shared': independent_operator([1., 1., 1., 1.])}
    observed = np.array([.1, .3, -.2])
    plain = score_profiled_training_laws(
        laws, observed, np.ones((3, 1)), training_epochs=3,
        rank_rtol=1e-10, parameter_scales=np.ones(1))
    redundant = score_profiled_training_laws(
        laws, observed, np.column_stack((np.ones(3), 2*np.ones(3))),
        training_epochs=3, rank_rtol=1e-10,
        parameter_scales=np.array([1., .5]))
    assert redundant['training_mean_rank'] == 1
    assert redundant['laws'][0]['restricted_negative_log_likelihood'] == pytest.approx(
        plain['laws'][0]['restricted_negative_log_likelihood'])


def test_profiled_shared_error_matches_dense_residual_contrast():
    steps = [dict(transition=np.eye(1), process_loading=np.zeros((1, 0)),
                  observation=np.eye(1),
                  white_loading=np.array([[math.sqrt(.2)]])) for _ in range(4)]
    operator = LinearInnovations(
        steps, epoch_count=4, state_dimension=1,
        observation_dimension=1, initial_loading=np.array([[math.sqrt(.5)]]),
        maximum_bytes=10000, design_is_fixed=True,
        error_distribution='gaussian')
    y = np.array([.3, -.4, .7])
    x = np.column_stack((np.ones(3), np.arange(3.)))
    contrast = np.array([1., -2., 1.])/math.sqrt(6.)
    dense = .5*np.ones((3, 3))+.2*np.eye(3)
    variance = float(contrast@dense@contrast)
    expected = .5*((float(contrast@y)**2)/variance
                   + math.log(variance)+math.log(2*math.pi))
    result = score_profiled_training_laws(
        {'shared': operator}, y, x, training_epochs=3, rank_rtol=1e-10,
        parameter_scales=np.ones(2))
    assert result['laws'][0]['restricted_negative_log_likelihood'] == pytest.approx(expected)


def test_profiled_score_rejects_no_residual_degrees_of_freedom():
    with pytest.raises(ValueError, match='residual degrees'):
        score_profiled_training_laws(
            {'law': independent_operator([1., 1.])}, np.array([.2]),
            np.ones((1, 1)), training_epochs=1, rank_rtol=1e-10,
            parameter_scales=np.ones(1))


def test_profiled_score_requires_valid_physical_column_scales():
    laws = {'law': independent_operator([1., 1., 1.])}
    with pytest.raises(ValueError, match='scales'):
        score_profiled_training_laws(
            laws, np.array([.1, .2]), np.ones((2, 1)),
            training_epochs=2, rank_rtol=1e-10,
            parameter_scales=np.array([-1.]))


def test_profiled_forecast_keeps_white_persistent_alias_and_mean_uncertainty():
    def law(white, offset):
        steps = [dict(transition=np.eye(1), process_loading=np.zeros((1, 0)),
                      observation=np.eye(1),
                      white_loading=np.array([[math.sqrt(white)]])) for _ in range(3)]
        return LinearInnovations(
            steps, epoch_count=3, state_dimension=1,
            observation_dimension=1,
            initial_loading=np.array([[math.sqrt(offset)]]),
            maximum_bytes=10000, design_is_fixed=True,
            error_distribution='gaussian')
    result = profiled_forecast_law_spread(
        {'white': law(1., 0.), 'persistent': law(.01, .99)},
        np.ones((3, 1)), np.array([.2]), training_epochs=1,
        parameter_scales=np.ones(1), prediction_scales=np.ones(2),
        rank_rtol=1e-10, estimability_rtol=1e-10,
        estimability_atol=1e-12, maximum_parameters=1)
    assert result['status'] == 'estimable'
    assert result['max_forecast_sigma_ratio'] == pytest.approx(10.)
    assert result['parameter_uncertainty_included'] is True
    assert result['later_observations_used'] is False
    assert result['coverage_calibrated'] is False


def test_profiled_forecast_abstains_if_any_law_has_future_mean_null_direction():
    laws = {'law': independent_operator([1., 1., 1.])}
    design = np.array([[1., 1.], [1., 2.], [1., 3.]])
    result = profiled_forecast_law_spread(
        laws, design, np.array([.2]), training_epochs=1,
        parameter_scales=np.ones(2), prediction_scales=np.ones(2),
        rank_rtol=1e-10, estimability_rtol=1e-10,
        estimability_atol=1e-12, maximum_parameters=2)
    assert result['status'] == 'abstain'
    assert 'max_forecast_sigma_ratio' not in result
