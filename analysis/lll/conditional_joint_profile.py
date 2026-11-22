# SPDX-License-Identifier: AGPL-3.0-or-later
"""Condition a complete path and all nuisance columns before future profiling."""

VERSION = 'conditioned-joint-future-innovations-v1'


def whiten_conditioned_future(operator, residual, design, *, training_epochs):
    """Return future innovations under one fixed training-conditioned law."""
    import numpy as np
    from .state_space_covariance import LinearInnovations

    if (not isinstance(operator, LinearInnovations)
            or operator.observation_dimension != 3
            or type(training_epochs) is not int
            or not 1 <= training_epochs < operator.epoch_count):
        raise ValueError('fixed three-coordinate operator and nonempty split required')
    n = operator.epoch_count
    observed = np.asarray(residual, dtype=float)
    jacobian = np.asarray(design, dtype=float)
    if (observed.shape != (n, 3) or jacobian.ndim != 2
            or jacobian.shape[0] != 3 * n
            or not 1 <= jacobian.shape[1] <= 27
            or not np.all(np.isfinite(observed))
            or not np.all(np.isfinite(jacobian))):
        raise ValueError('complete finite path and all nuisance columns required')
    whitened = operator.whiten(observed.ravel())
    whitened_design = operator.whiten(jacobian)
    first = 3 * training_epochs
    return dict(version=VERSION, operator_configuration=operator.configuration,
                training_epochs=training_epochs,
                future_epochs=n - training_epochs,
                retained_columns=jacobian.shape[1],
                future_residual=whitened[first:],
                future_design=whitened_design[first:],
                later_observations_used=True,
                error_law_calibrated=False)
