# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propagate calibration changes through a fixed earlier-conditioned error law."""


def conditioned_tangent(operator, nominal, design, earlier_residual, *, training_epochs):
    """Condition on receiver-minus-model error, with residual supplied as model minus receiver."""
    import numpy as np
    from .state_space_covariance import LinearInnovations

    if (not isinstance(operator, LinearInnovations)
            or type(training_epochs) is not int
            or not 1 <= training_epochs < operator.epoch_count):
        raise ValueError('fixed full operator and explicit earlier support required')
    nominal, design, earlier_residual = (np.asarray(v, float)
                                         for v in (nominal, design, earlier_residual))
    length = operator.epoch_count*operator.observation_dimension
    cut = training_epochs*operator.observation_dimension
    if (nominal.shape != (length,) or design.ndim != 2 or design.shape[0] != length
            or earlier_residual.shape != (cut,)
            or any(not np.all(np.isfinite(v)) for v in (nominal, design, earlier_residual))):
        raise ValueError('finite full coordinates and derivatives with earlier residual only required')
    training = np.column_stack((earlier_residual, design[:cut]))
    innovations = np.zeros((length, training.shape[1]))
    innovations[:cut] = operator.prefix(training_epochs).whiten(training)
    transferred = operator.unwhiten(innovations)[cut:]
    return dict(mean=nominal[cut:]-transferred[:, 0],
                design=design[cut:]-transferred[:, 1:], receiver_adjustment=-transferred[:, 0])
