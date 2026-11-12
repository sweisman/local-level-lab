# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare later error scales with and without earlier receiver information."""


def compare(operator, *, training_epochs, physical_scales):
    """Use one fixed Gaussian operator for both information conditions."""
    import numpy as np
    from lll.state_space_covariance import LinearInnovations

    if (not isinstance(operator, LinearInnovations)
            or operator.observation_dimension != 3
            or type(training_epochs) is not int
            or not 1 <= training_epochs < operator.epoch_count):
        raise ValueError('complete later physical support required')
    scales = np.asarray(physical_scales, dtype=float)
    later_count = operator.epoch_count - training_epochs
    if (scales.shape != (later_count, 3)
            or not np.all(np.isfinite(scales)) or np.any(scales <= 0)):
        raise ValueError('complete later physical support required')

    unconditional = operator.conditional_marginals(state=None)
    _, checkpoint = operator.apply_block(
        np.zeros(3*training_epochs), first_epoch=0)
    conditioned = operator.conditional_marginals(state=checkpoint)
    before = np.diagonal(
        unconditional['covariance'][training_epochs:], axis1=1, axis2=2)
    after = np.diagonal(conditioned['covariance'], axis1=1, axis2=2)
    if (before.shape != (later_count, 3) or after.shape != before.shape
            or np.any(after > before * (1 + 1e-9) + 1e-10)):
        raise ValueError('conditioning increased a marginal variance')

    def summary(variances, epochs):
        physical = variances * scales**2
        return dict(conditioning_epochs=epochs,
                    horizontal_rms_scale_m=float(np.sqrt(np.mean(
                        physical[:, :2].sum(axis=1)))),
                    height_rms_scale_m=float(np.sqrt(np.mean(physical[:, 2]))),
                    later_variance_neu_m2=physical.tolist())

    return dict(version='same-operator-conditioning-comparison-v1',
                training_epochs=training_epochs, later_epochs=later_count,
                unconditional=summary(before, 0),
                conditioned=summary(after, training_epochs),
                realized_noise_used=False, fitted_calibration_used=False,
                confidence_calibrated=False, scientific_decision='abstain')
