# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local training-only identifiability of known-answer covariance parameters.

This is restricted-likelihood expected information for a declared linear mean.
It diagnoses covariance directions in a simplified known-answer model; it does
not estimate a flight's error law or establish prediction coverage.
"""
from dataclasses import fields as dataclass_fields, replace
import math


def _covariance(law, times, speed_mps):
    import numpy as np
    from .prediction_error_known_answer import operator
    root = operator(law, times, speed_mps=speed_mps).unwhiten(
        np.eye(len(times)))
    return root@root.T


def local_information(law, times, *, speed_mps, training_epochs,
                      training_design, fields, rank_rtol):
    """Return rank of the local *log-parameter* covariance information.

    Future sample times and observations are excluded. At most 64 training
    epochs are allowed because this diagnostic deliberately forms dense
    matrices. Its eigenvalues are design expectations, not observed evidence.
    """
    import numpy as np
    from .prediction_error_known_answer import Law
    valid_fields = {field.name for field in dataclass_fields(Law)}
    times = np.asarray(times, dtype=float)
    x = np.asarray(training_design, dtype=float)
    if (not isinstance(law, Law) or type(training_epochs) is not int or
            not 2 <= training_epochs <= 64 or times.ndim != 1 or
            len(times) <= training_epochs or x.ndim != 2 or
            x.shape[0] != training_epochs or not 1 <= x.shape[1] < training_epochs or
            not np.all(np.isfinite(x)) or not isinstance(fields, tuple) or
            not 1 <= len(fields) <= 8 or len(set(fields)) != len(fields) or
            any(name not in valid_fields or getattr(law, name) <= 0 for name in fields)
            or not math.isfinite(rank_rtol) or not 0 < rank_rtol < 1):
        raise ValueError('bounded training schedule, complete mean and positive unique law fields required')
    # The operator receives the prefix only; no future schedule can affect this.
    training_times = times[:training_epochs]
    covariance = _covariance(law, training_times, speed_mps)
    cholesky = np.linalg.cholesky(covariance)
    inverse_root = np.linalg.solve(cholesky, np.eye(training_epochs))
    inverse = inverse_root.T@inverse_root
    u, singular, _ = np.linalg.svd(x, full_matrices=False)
    mean_rank = int(np.count_nonzero(singular > singular[0]*rank_rtol))
    if mean_rank >= training_epochs:
        raise ValueError('no residual degrees of freedom')
    basis = u[:, :mean_rank]
    weighted = inverse@basis
    projection = inverse-weighted@np.linalg.solve(basis.T@weighted, weighted.T)
    step = 1e-4
    derivatives = []
    for name in fields:
        value = getattr(law, name)
        high = _covariance(replace(law, **{name:value*math.exp(step)}),
                           training_times, speed_mps)
        low = _covariance(replace(law, **{name:value*math.exp(-step)}),
                          training_times, speed_mps)
        derivatives.append((high-low)/(2*step))
    information = np.empty((len(fields), len(fields)))
    for i, left in enumerate(derivatives):
        for j, right in enumerate(derivatives):
            information[i, j] = .5*np.trace(projection@left@projection@right)
    information = (information+information.T)/2
    eigenvalues = np.linalg.eigvalsh(information)[::-1]
    if (not np.all(np.isfinite(eigenvalues)) or eigenvalues[0] <= 0 or
            eigenvalues[-1] < -1e-8*eigenvalues[0]):
        raise ValueError('invalid local covariance information')
    return dict(fields=list(fields), information=information.tolist(),
                eigenvalues=eigenvalues.tolist(),
                rank=int(np.count_nonzero(eigenvalues > eigenvalues[0]*rank_rtol)),
                mean_rank=mean_rank,
                residual_degrees_of_freedom=training_epochs-mean_rank,
                training_epochs=training_epochs, later_observations_used=False,
                statistical_identification_established=False,
                coverage_calibrated=False)


def classify_training_laws(operators, design, training_residual, *,
                           training_epochs, parameter_scales, prediction_scales,
                           rank_rtol, estimability_rtol, estimability_atol,
                           maximum_parameters, compatible_delta_nll,
                           material_sigma_ratio, material_mean_spread=1.):
    """Screen fixed laws using training data and compare their future forecasts.

    Compatibility and materiality cutoffs are explicit development choices,
    not likelihood confidence bounds or calibrated decision thresholds.
    """
    import numpy as np
    from .prediction_error_law import (profiled_forecast_law_spread,
                                       score_profiled_training_laws)
    if (not math.isfinite(compatible_delta_nll) or compatible_delta_nll < 0 or
            not math.isfinite(material_sigma_ratio) or material_sigma_ratio <= 1 or
            not math.isfinite(material_mean_spread) or material_mean_spread <= 0):
        raise ValueError('finite explicit nonnegative compatibility and positive materiality required')
    x = np.asarray(design, dtype=float)
    if x.ndim != 2 or not 1 <= x.shape[1] <= maximum_parameters:
        raise ValueError('complete fixed mean design required')
    scores = score_profiled_training_laws(
        operators, training_residual, x[:training_epochs],
        training_epochs=training_epochs, rank_rtol=rank_rtol,
        parameter_scales=parameter_scales)
    compatible = [row['law_id'] for row in scores['laws']
                  if row['delta_restricted_nll'] <= compatible_delta_nll]
    spread = profiled_forecast_law_spread(
        {name:operators[name] for name in compatible}, x, training_residual,
        training_epochs=training_epochs, parameter_scales=parameter_scales,
        prediction_scales=prediction_scales, rank_rtol=rank_rtol,
        estimability_rtol=estimability_rtol, estimability_atol=estimability_atol,
        maximum_parameters=maximum_parameters)
    if spread['status'] == 'abstain':
        status, reason = 'abstain', 'future_mean_unidentifiable'
    elif (len(compatible) > 1 and
          (spread['max_forecast_sigma_ratio'] > material_sigma_ratio or
           spread['max_forecast_mean_spread_in_smallest_sigma'] > material_mean_spread)):
        status, reason = 'abstain', 'training_compatible_forecasts_disagree'
    elif len(compatible) > 1:
        status, reason = 'equivalent_forecast', 'multiple_training_compatible_laws'
    else:
        status, reason = 'provisional_minimum', 'one_law_within_development_radius'
    return dict(status=status, reason=reason, compatible_laws=compatible,
                training_scores=scores, forecast_spread=spread,
                compatible_delta_nll=float(compatible_delta_nll),
                material_sigma_ratio=float(material_sigma_ratio),
                material_mean_spread=float(material_mean_spread),
                later_observations_used=False, coverage_calibrated=False,
                statistical_identification_established=False)
