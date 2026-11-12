# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare supplied Gaussian error laws using only an earlier residual prefix.

This scores fixed laws. It does not estimate continuous law parameters, account
for the fitting of motion/calibration, or calibrate forecast coverage.
"""
import math

import numpy as np

from .state_space_covariance import LinearInnovations


def _validated_laws(operators, training_residual, training_epochs):
    if not isinstance(operators, dict) or not operators:
        raise ValueError('nonempty named law operators required')
    if type(training_epochs) is not int or training_epochs < 1:
        raise ValueError('positive earlier epoch count required')
    entries = list(operators.items())
    for law_id, operator in entries:
        if (not isinstance(law_id, str) or not law_id
                or not isinstance(operator, LinearInnovations)
                or training_epochs >= operator.epoch_count):
            raise ValueError('named fixed operators with a withheld period required')
    count = entries[0][1].epoch_count
    dimension = entries[0][1].observation_dimension
    if any(operator.epoch_count != count
           or operator.observation_dimension != dimension
           for _, operator in entries):
        raise ValueError('candidate laws must share epoch and observation support')
    observed = np.asarray(training_residual, dtype=float)
    if observed.shape != (training_epochs*dimension,) or not np.all(np.isfinite(observed)):
        raise ValueError('finite earlier-only residual prefix required')
    return entries, observed, dimension


def score_training_laws(operators, training_residual, *, training_epochs):
    """Return fixed-law likelihoods; no withheld residual is accepted.

    ``operators`` may encode the full declared observation schedule, but the
    likelihood calculation uses their earlier-only PrefixInnovations views.
    A numerical minimum is deliberately not called a statistically identified
    or calibrated error law.
    """
    entries, observed, dimension = _validated_laws(
        operators, training_residual, training_epochs)
    rows = []
    for law_id, operator in entries:
        prefix = operator.prefix(training_epochs)
        whitened = prefix.whiten(observed)
        quadratic = float(whitened@whitened)
        log_determinant = prefix.log_determinant
        score = .5*(quadratic+log_determinant+len(observed)*math.log(2*math.pi))
        if not math.isfinite(score):
            raise ValueError('unrepresentable training likelihood')
        rows.append(dict(law_id=law_id, negative_log_likelihood=float(score),
                         quadratic=quadratic, log_determinant=log_determinant))
    rows.sort(key=lambda row: (row['negative_log_likelihood'], row['law_id']))
    best = rows[0]['negative_log_likelihood']
    for row in rows:
        row['delta_nll'] = row['negative_log_likelihood']-best
    unique = len(rows) > 1 and rows[1]['delta_nll'] > (
        16*np.finfo(float).eps*max(1., abs(best), abs(rows[1]['negative_log_likelihood'])))
    return dict(training_epochs=training_epochs, observation_dimension=dimension,
                laws=rows, numerical_unique_minimum=bool(unique),
                statistical_identification_assessed=False,
                later_observations_used=False, coverage_calibrated=False,
                fitted_calibration_uncertainty_included=False)


def forecast_law_spread(operators, training_residual, *, training_epochs):
    """Compare future scales implied by supplied laws after the same prefix.

    This is a diagnostic of possible training-law ambiguity. Its ratio has no
    acceptance threshold and is not a coverage statement.
    """
    scores = score_training_laws(operators, training_residual,
                                 training_epochs=training_epochs)
    sigmas = []
    means = []
    for row in scores['laws']:
        operator = operators[row['law_id']]
        _, state = operator.apply_block(training_residual, first_epoch=0)
        conditional = operator.conditional_marginals(state=state)
        sigmas.append(np.sqrt(np.diagonal(conditional['covariance'], axis1=1, axis2=2)))
        means.append(conditional['mean'])
    sigma = np.stack(sigmas)
    mean = np.stack(means)
    if not np.all(np.isfinite(sigma)) or np.any(sigma <= 0) or not np.all(np.isfinite(mean)):
        raise ValueError('finite positive forecast scales required')
    ratio = float(np.max(np.max(sigma, axis=0)/np.min(sigma, axis=0)))
    mean_spread = float(np.max((np.max(mean, axis=0)-np.min(mean, axis=0))
                               /np.min(sigma, axis=0)))
    nll = [row['negative_log_likelihood'] for row in scores['laws']]
    return dict(training_epochs=training_epochs,
                forecast_epochs=operators[scores['laws'][0]['law_id']].epoch_count-training_epochs,
                training_nll_span=float(max(nll)-min(nll)),
                max_forecast_sigma_ratio=ratio,
                max_forecast_mean_spread_in_smallest_sigma=mean_spread,
                law_ids=[row['law_id'] for row in scores['laws']],
                later_observations_used=False, coverage_calibrated=False,
                statistical_identification_assessed=False,
                fitted_calibration_uncertainty_included=False)


def score_profiled_training_laws(operators, training_residual, training_design,
                                  *, training_epochs, rank_rtol,
                                  parameter_scales):
    """Restricted Gaussian scores after removing a fixed linear mean design.

    The column space of the complete scaled training design is removed once
    for every candidate covariance. An orthonormal basis makes the restricted
    likelihood independent of redundant columns when the declared rank stays
    the same. The caller supplies physical column scales before rank testing.
    This does not model nonlinear calibration or active physical bounds.
    """
    if not math.isfinite(rank_rtol) or not 0 < rank_rtol < 1:
        raise ValueError('explicit relative mean-design rank tolerance required')
    entries, observed, dimension = _validated_laws(
        operators, training_residual, training_epochs)
    n = len(observed)
    x = np.asarray(training_design, dtype=float)
    if (x.ndim != 2 or x.shape[0] != n or not 1 <= x.shape[1] <= 27
            or not np.all(np.isfinite(x))):
        raise ValueError('complete finite earlier mean design required')
    scales = np.asarray(parameter_scales, dtype=float)
    if (scales.shape != (x.shape[1],) or not np.all(np.isfinite(scales))
            or np.any(scales <= 0)):
        raise ValueError('positive finite physical mean-parameter scales required')
    x = x*scales[None, :]
    if not np.all(np.isfinite(x)):
        raise ValueError('unrepresentable scaled mean design')
    u, singular, _ = np.linalg.svd(x, full_matrices=False)
    rank = int(np.count_nonzero(singular > singular[0]*rank_rtol))
    if rank >= n:
        raise ValueError('no residual degrees of freedom for error-law scoring')
    mean_basis = u[:, :rank]
    rows = []
    for law_id, operator in entries:
        prefix = operator.prefix(training_epochs)
        z = prefix.whiten(observed)
        if rank:
            a = prefix.whiten(mean_basis)
            singular_a = np.linalg.svd(a, compute_uv=False)
            if np.any(singular_a <= 0) or not np.all(np.isfinite(singular_a)):
                raise ValueError('unrepresentable mean information')
            q, _ = np.linalg.qr(a, mode='reduced')
            z = z-q@(q.T@z)
            log_information = float(2*np.log(singular_a).sum())
        else:
            log_information = 0.
        quadratic = float(z@z)
        score = .5*(quadratic+prefix.log_determinant+log_information
                    +(n-rank)*math.log(2*math.pi))
        if not math.isfinite(score):
            raise ValueError('unrepresentable restricted training likelihood')
        rows.append(dict(law_id=law_id,
                         restricted_negative_log_likelihood=float(score),
                         residual_quadratic=quadratic,
                         covariance_log_determinant=prefix.log_determinant,
                         mean_information_log_determinant=log_information))
    rows.sort(key=lambda row: (row['restricted_negative_log_likelihood'], row['law_id']))
    best = rows[0]['restricted_negative_log_likelihood']
    for row in rows:
        row['delta_restricted_nll'] = row['restricted_negative_log_likelihood']-best
    return dict(training_epochs=training_epochs,
                training_mean_rank=rank, residual_degrees_of_freedom=n-rank,
                observation_dimension=dimension, laws=rows,
                rank_rtol=float(rank_rtol), parameter_scales=scales.tolist(),
                later_observations_used=False,
                nonlinear_fit_accounted_for=False, active_bounds_accounted_for=False,
                error_law_calibrated=False, coverage_calibrated=False)


def profiled_forecast_law_spread(operators, design, training_residual, *,
                                 training_epochs, parameter_scales,
                                 prediction_scales, rank_rtol,
                                 estimability_rtol, estimability_atol,
                                 maximum_parameters):
    """Compare fixed-law future scales with a fitted linear mean.

    If any candidate has a training-null mean direction that changes the
    future prediction, withhold the aggregate scale. This is a diagnostic,
    not selection of a noise law or calibrated coverage.
    """
    from .calibrated_linear_prediction import predict
    _validated_laws(operators, training_residual, training_epochs)
    outputs = {}
    for law_id, operator in operators.items():
        outputs[law_id] = predict(
            operator, design, training_residual,
            training_epochs=training_epochs,
            parameter_scales=parameter_scales,
            prediction_scales=prediction_scales,
            rank_rtol=rank_rtol, estimability_rtol=estimability_rtol,
            estimability_atol=estimability_atol,
            maximum_parameters=maximum_parameters)
    unidentifiable = sorted(
        name for name, result in outputs.items()
        if result['status'] != 'estimable')
    common = dict(training_epochs=training_epochs,
                  candidate_laws=sorted(outputs),
                  later_observations_used=False,
                  error_law_calibrated=False,
                  coverage_calibrated=False,
                  nonlinear_fit_accounted_for=False,
                  active_bounds_accounted_for=False)
    if unidentifiable:
        return dict(common, status='abstain',
                    unidentifiable_laws=unidentifiable,
                    parameter_uncertainty_included=False)
    names = sorted(outputs)
    mean = np.stack([outputs[name]['mean'] for name in names])
    sigma = np.stack([
        np.sqrt(np.diagonal(outputs[name]['covariance'], axis1=1, axis2=2))
        for name in names])
    if not np.all(np.isfinite(mean)) or not np.all(np.isfinite(sigma)) or np.any(sigma <= 0):
        raise ValueError('finite positive profiled forecast scales required')
    return dict(common, status='estimable', unidentifiable_laws=[],
                forecast_epochs=operators[names[0]].epoch_count-training_epochs,
                max_forecast_sigma_ratio=float(np.max(np.max(sigma, axis=0)/np.min(sigma, axis=0))),
                max_forecast_mean_spread_in_smallest_sigma=float(np.max(
                    (np.max(mean, axis=0)-np.min(mean, axis=0))/np.min(sigma, axis=0))),
                parameter_uncertainty_included=True)
