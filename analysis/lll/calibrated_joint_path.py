# SPDX-License-Identifier: AGPL-3.0-or-later
"""Whole-path GLS prediction under a supplied Gaussian covariance shape."""

import math

import numpy as np
from scipy.stats import chi2, f

from .calibrated_linear_prediction import predict


def prepare(operator, design, earlier, *, training_epochs, parameter_scales,
            prediction_scales=None, rank_rtol=1e-10, estimability_rtol=1e-9,
            estimability_atol=1e-12):
    """Fit the unrestricted affine mean on the earlier data and save its forecast."""
    d = operator.observation_dimension
    past_rows = d*training_epochs
    later_rows = d*operator.epoch_count-past_rows
    if earlier is None or later_rows <= 0:
        raise ValueError('earlier residuals and a later design are required')
    units = np.ones(later_rows) if prediction_scales is None else prediction_scales
    result = predict(operator, design, earlier, training_epochs=training_epochs,
        parameter_scales=parameter_scales, prediction_scales=units, rank_rtol=rank_rtol,
        estimability_rtol=estimability_rtol, estimability_atol=estimability_atol, maximum_parameters=27)
    result['operator_configuration'] = operator.configuration
    if result['status'] != 'estimable':
        return result
    fitted = np.asarray(design)[:past_rows] @ result['minimum_norm_parameter_estimate']
    innovation = operator.prefix(training_epochs).whiten(np.asarray(earlier)-fitted)
    prior_dof = result['training_residual_degrees_of_freedom']
    early_energy = float(innovation@innovation)
    result['training_variance_scale_estimate'] = early_energy/prior_dof if prior_dof > 0 else None
    return result


def _joint_quadratic(innovations, calibration):
    if not calibration.shape[1]:
        return float(innovations@innovations), 0.
    basis, singular, _ = np.linalg.svd(calibration, full_matrices=False)
    along = basis.T@innovations
    across = innovations-basis@along
    scale = np.hypot(1., singular)
    correction = along/scale
    return float(across@across+correction@correction), float(2.*np.log(scale).sum())


def score(operator, forecast, later):
    """Score later errors with the calibration term in the full covariance.

    The fixed-scale chi-square and earlier-estimated-scale F references are
    repeated-history results for an exact affine mean and proportional
    Gaussian covariance. Fitting a nonlinear or bounded calibration and
    choosing a common error law from competing fits require separate checks.
    """
    if forecast['operator_configuration'] != operator.configuration or forecast['later_observations_used'] is not False:
        raise ValueError('same earlier-only operator and forecast required')
    if forecast['status'] != 'estimable':
        return dict(status=forecast['status'], scientific_decision='abstain')
    d = operator.observation_dimension
    cut = forecast['training_epochs']
    rows = d*(operator.epoch_count-cut)
    observed = np.asarray(later, float)
    if observed.shape not in ((rows,), (rows//d,d)) or not np.isfinite(observed).all():
        raise ValueError('finite later observations on the frozen support required')
    residual = observed.reshape(rows)-forecast['mean'].reshape(rows)
    contrasts = np.column_stack((residual, forecast['calibration_loading']))
    _, checkpoint = operator.apply_block(np.zeros((d*cut, contrasts.shape[1])), first_epoch=0)
    whitened, _ = operator.apply_block(contrasts, first_epoch=cut, state=checkpoint)
    quadratic, added_logdet = _joint_quadratic(whitened[:,0], whitened[:,1:])
    logdet = operator.log_determinant-operator.prefix(cut).log_determinant+added_logdet
    if not (math.isfinite(quadratic) and math.isfinite(logdet)):
        raise ValueError('unrepresentable joint forecast error')
    scale = forecast['training_variance_scale_estimate']
    prior_dof = forecast['training_residual_degrees_of_freedom']
    available = scale is not None and math.isfinite(scale) and scale > 0.
    pivot = quadratic/(rows*scale) if available else None
    return dict(status='scored', squared_standardized_error=quadratic,
        conditional_log_determinant=logdet, future_coordinates=rows,
        calibration_log_determinant_increase=added_logdet,
        fixed_scale_reference_band=chi2.ppf([.025,.975],rows).tolist(),
        training_variance_scale_estimate=scale, training_residual_degrees_of_freedom=prior_dof,
        estimated_scale_f_statistic=pivot,
        estimated_scale_reference_band=f.ppf([.025,.975],rows,prior_dof).tolist() if available else None,
        fitted_calibration_uncertainty_included=True, aircraft_coverage_established=False,
        scientific_decision='abstain')
