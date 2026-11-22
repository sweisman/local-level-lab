# SPDX-License-Identifier: AGPL-3.0-or-later
"""Whole-path score bounds for an independent post-cut covariance change."""

import math

import numpy as np
from scipy.stats import f

from .calibrated_joint_path import _joint_quadratic
from .calibrated_joint_path import prepare as prepare_base, score as score_base
from .state_space_covariance import LinearInnovations


def _future_operator(base, cut, white, walk):
    k, d = base.state_dimension, base.observation_dimension
    transition = np.eye(k + d)
    observation = np.column_stack((np.zeros((d, k)), np.eye(d)))
    process = np.zeros((k + d, 2 * d))
    for late_index in range(base.epoch_count - cut):
        i = cut + late_index
        lower = base._lower[i]
        transition[:k, :k] = base._transition[i]
        observation[:, :k] = base._observation[i]
        process[:k, :d] = base._gain[i] @ lower
        process[k:, d:] = walk[late_index]
        # Inverse innovations generate the exact conditional base error
        # starting at zero state after the cut. The offset walk is independent
        # and its current step contributes to both this report and its future.
        yield dict(transition=transition, process_loading=process,
                   observation=observation,
                   observation_process_loading=np.column_stack((lower, walk[late_index])),
                   white_loading=white[late_index])


def prepare(operator, design, earlier, *, training_epochs, parameter_scales,
            future_white_loading, future_walk_loading, maximum_bytes):
    """Fit on earlier data and freeze the upper additive covariance.

    Both per-report loadings apply to the future only. The declared range is
    between zero extra covariance and the sum of their independent Gaussian
    white-scatter and random-walk covariances. All covariances share the same
    unknown overall variance scale as the earlier error law.
    """
    if (not isinstance(operator, LinearInnovations) or type(training_epochs) is not int
            or not 1 <= training_epochs < operator.epoch_count):
        raise ValueError('fixed operator and nonempty chronological split required')
    d, k = operator.observation_dimension, operator.state_dimension
    later = operator.epoch_count - training_epochs
    white = np.asarray(future_white_loading, float)
    walk = np.asarray(future_walk_loading, float)
    if (white.shape != (later, d, d) or walk.shape != white.shape
            or not np.isfinite(white).all() or not np.isfinite(walk).all()):
        raise ValueError('complete finite post-cut noise loadings required')
    forecast = prepare_base(operator, design, earlier, training_epochs=training_epochs,
                            parameter_scales=parameter_scales)
    result = dict(status=forecast['status'], base_operator=operator, base_forecast=forecast,
                  later_observations_used=False)
    if forecast['status'] == 'estimable':
        upper = LinearInnovations(
            _future_operator(operator, training_epochs, white, walk),
            epoch_count=later, state_dimension=k+d, observation_dimension=d,
            initial_loading=None, maximum_bytes=maximum_bytes, design_is_fixed=True,
            error_distribution='gaussian', observation_form='before_transition_shared_noise',
            white_error_may_be_singular=True)
        result['upper_operator'] = upper
    return result


def score(prepared, later):
    """Return extrema of the joint score over the declared covariance range."""
    if prepared['status'] != 'estimable':
        return dict(status=prepared['status'], scientific_decision='abstain')
    forecast = prepared['base_forecast']
    original = score_base(prepared['base_operator'], forecast, later)
    scale = original['training_variance_scale_estimate']
    if original['estimated_scale_f_statistic'] is None:
        return dict(status='unavailable_training_scale', scientific_decision='abstain')
    delta = np.asarray(later, float).ravel() - forecast['mean'].ravel()
    columns = np.column_stack((delta, forecast['calibration_loading']))
    whitened = prepared['upper_operator'].whiten(columns)
    minimum, _ = _joint_quadratic(whitened[:, 0], whitened[:, 1:])
    maximum = original['squared_standardized_error']
    if not math.isfinite(minimum) or minimum > maximum + 1e-10 * (1.0 + maximum):
        raise ValueError('added covariance must not increase the quadratic score')
    minimum = min(minimum, maximum)
    n = len(delta)
    earlier_df = original['training_residual_degrees_of_freedom']
    q_lo, q_hi = minimum / (n * scale), maximum / (n * scale)
    lo, hi = map(float, f.ppf([.025, .975], n, earlier_df))
    return dict(status='scored', quadratic_range=[minimum, maximum], pivot_range=[q_lo, q_hi],
                reference_band=[lo, hi], training_variance_scale=scale,
                every_covariance_above_reference=q_lo > hi,
                every_covariance_below_reference=q_hi < lo,
                every_covariance_inside_reference=lo <= q_lo and q_hi <= hi,
                any_covariance_inside_reference=q_lo <= hi and q_hi >= lo,
                scientific_decision='abstain', aircraft_coverage_established=False)
