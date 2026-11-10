# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only linear prediction with explicitly estimated mean uncertainty.

This is fixed-design Gaussian GLS with unrestricted mean parameters. It is
not nonlinear confidence, a bounded-calibration approximation, an archive
noise estimate or permission to reinterpret failed physical-accuracy checks.
"""


def predict(operator, design, training_residual, *, training_epochs,
            parameter_scales, prediction_scales, rank_rtol, estimability_rtol,
            estimability_atol, maximum_parameters):
    """Return estimable future marginal moments, keeping every nuisance column.

    A training-null mean direction that changes future observations makes the
    prediction unidentifiable. No finite covariance is then returned. With
    redundant parameters but estimable predictions, the representative parameter
    point is minimum-norm in the declared scaled coordinates; its null directions
    are not claimed to be known. The added calibration loading retains common
    uncertainty across future epochs without forming a dense future covariance.
    """
    import numpy as np
    from scipy.linalg import svd
    from .state_space_covariance import LinearInnovations
    if (not isinstance(operator, LinearInnovations) or type(training_epochs) is not int
            or not 1 <= training_epochs < operator.epoch_count
            or type(maximum_parameters) is not int or not 1 <= maximum_parameters <= 27
            or not np.all(np.isfinite([rank_rtol, estimability_rtol, estimability_atol]))
            or not 0 < rank_rtol < 1 or not 0 <= estimability_rtol < 1 or estimability_atol < 0):
        raise ValueError('explicit fixed operator, training split and numerical tolerances required')
    d = operator.observation_dimension; n = d*operator.epoch_count; m = d*training_epochs
    x = np.array(design, dtype=float, copy=True)
    r = np.array(training_residual, dtype=float, copy=True)
    if (x.ndim != 2 or x.shape[0] != n or not 1 <= x.shape[1] <= maximum_parameters
            or not np.all(np.isfinite(x)) or r.shape != (m,) or not np.all(np.isfinite(r))):
        raise ValueError('complete design and earlier residuals only required')
    p = x.shape[1]
    scales = np.array(parameter_scales, dtype=float, copy=True)
    units = np.array(prediction_scales, dtype=float, copy=True)
    if (scales.shape != (p,) or units.shape != (n-m,)
            or not np.all(np.isfinite(scales)) or not np.all(np.isfinite(units))
            or np.any(scales <= 0) or np.any(units <= 0)):
        raise ValueError('positive finite parameter and prediction coordinate scales required')
    x *= scales[None, :]
    if not np.all(np.isfinite(x)):
        raise ValueError('unrepresentable scaled design')
    a, _ = operator.apply_block(x[:m], first_epoch=0)
    y, _ = operator.apply_block(r, first_epoch=0)
    u, singular, vh = svd(a, full_matrices=False, check_finite=False)
    if not np.all(np.isfinite(singular)):
        raise ValueError('unrepresentable training information')
    rank = int(np.count_nonzero(singular > singular[0]*rank_rtol))
    retained = vh[:rank].T
    # Inverse whitening of earlier design innovations with zero later
    # innovations gives C_future,train C_train,train^-1 X_train. These are
    # deterministic design columns, never later observed residuals.
    known = np.zeros((n, p)); known[:m] = a
    contrast = x[m:]-operator.unwhiten(known)[m:]
    null = np.zeros((p, p)) if rank == p else np.eye(p)-retained@retained.T
    unknown_effect = (contrast@null)*units[:, None]
    effect_norm = np.linalg.norm(unknown_effect, axis=1)
    contrast_norm = np.linalg.norm(contrast*units[:, None], axis=1)
    limit = estimability_atol+estimability_rtol*contrast_norm
    if not np.all(np.isfinite(effect_norm)) or not np.all(np.isfinite(contrast_norm)):
        raise ValueError('unrepresentable prediction estimability calculation')
    summary = dict(status='unidentifiable', training_rank=rank, parameter_count=p,
        calibration_fully_identified=rank == p, training_epochs=training_epochs,
        prediction_epochs=operator.epoch_count-training_epochs,
        training_residual_degrees_of_freedom=m-rank,
        maximum_unknown_prediction_effect=float(np.max(effect_norm)),
        rank_rtol=float(rank_rtol), estimability_rtol=float(estimability_rtol),
        estimability_atol=float(estimability_atol), later_observations_used=False,
        calibration_bounds_used=False, nonlinear_coverage_established=False,
        error_law_calibrated=False,
        uncertainty_scope='linear fixed-design Gaussian law with unrestricted calibration')
    if np.any(effect_norm > limit):
        summary['parameter_uncertainty_included'] = False
        return summary
    coefficients = retained@((u[:, :rank].T@y)/singular[:rank])
    fitted_residual = r-x[:m]@coefficients
    _, checkpoint = operator.apply_block(fitted_residual, first_epoch=0)
    forecast = operator.conditional_marginals(state=checkpoint)
    loading = (contrast@retained)/singular[:rank]
    blocks = loading.reshape(operator.epoch_count-training_epochs, d, rank)
    covariance = forecast['covariance']+blocks@np.swapaxes(blocks, 1, 2)
    mean = (x[m:]@coefficients).reshape(-1, d)+forecast['mean']
    point = coefficients*scales
    if any(not np.all(np.isfinite(value)) for value in (loading, covariance, mean, point)):
        raise ValueError('unrepresentable calibrated linear prediction')
    summary.update(status='estimable', mean=mean, covariance=covariance,
        calibration_loading=loading, minimum_norm_parameter_estimate=point,
        parameter_uncertainty_included=True)
    return summary
