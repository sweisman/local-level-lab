# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only affine envelope for one nonlinear aircraft forecast tangent.

This adapter carries all normalized calibration columns into the known-law
linear control. It makes no claim that a flight's nonlinear Taylor remainder
or actual error law is covered; those require separate generated validation.
"""


def diagnose(operator, coordinates, jacobian, training_residual, point, *,
             training_epochs, coordinate_chart, calibration_alpha,
             future_alpha, rank_rtol):
    import numpy as np
    from .bounded_linear_prediction import envelope
    from .state_space_covariance import LinearInnovations

    if (not isinstance(operator, LinearInnovations) or
            operator.observation_dimension != 3 or
            coordinate_chart != 'local_unwrapped_geodetic' or
            type(training_epochs) is not int or
            not 1 <= training_epochs < operator.epoch_count):
        raise ValueError('fixed three-coordinate error law and explicit local chart required')
    n = operator.epoch_count
    m = training_epochs
    path = np.asarray(coordinates, dtype=float)
    design = np.asarray(jacobian, dtype=float)
    earlier = np.asarray(training_residual, dtype=float)
    fitted = np.asarray(point, dtype=float)
    p = len(fitted) if fitted.ndim == 1 else -1
    if (not 1 <= p <= 27 or path.shape != (n, 3) or
            design.shape != (3*n, p) or earlier.shape != (m, 3) or
            any(not np.all(np.isfinite(item)) for item in
                (path, design, earlier, fitted)) or np.any(np.abs(fitted) > 1)):
        raise ValueError('complete finite path, tangent and in-box calibration required')
    whitened_design, _ = operator.apply_block(design[:3*m], first_epoch=0)
    whitened_residual, checkpoint = operator.apply_block(
        earlier.ravel(), first_epoch=0)
    known = np.zeros_like(design)
    known[:3*m] = whitened_design
    contrast = design[3*m:] - operator.unwhiten(known)[3*m:]
    fixed = operator.conditional_marginals(state=checkpoint)
    mean = path[m:] + fixed['mean']
    covariance = fixed['covariance']
    if (mean.shape != (n-m, 3) or covariance.shape != (n-m, 3, 3)
            or not np.all(np.isfinite(mean)) or
            not np.all(np.isfinite(covariance)) or
            np.any(np.diagonal(covariance, axis1=1, axis2=2) <= 0)):
        raise ValueError('finite earlier-conditioned forecast moments required')
    sigma = np.sqrt(np.diagonal(covariance, axis1=1, axis2=2)).ravel()
    result = envelope(whitened_design, whitened_residual, contrast,
                      mean.ravel(), sigma, -1-fitted, 1-fitted,
                      calibration_alpha=calibration_alpha,
                      future_alpha=future_alpha, rank_rtol=rank_rtol)
    result.update(training_epochs=m, prediction_epochs=n-m,
                  coordinate_chart=coordinate_chart,
                  retained_calibration_columns=p,
                  fitted_point_at_bound=bool(np.any(np.abs(fitted) == 1)),
                  later_observations_used=False,
                  nonlinear_aircraft_coverage_established=False,
                  scientific_decision='abstain')
    return result
