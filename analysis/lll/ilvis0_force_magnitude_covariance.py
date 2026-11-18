# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional joint receiver-error propagation for gyro-free force magnitude.

The caller supplies one common epoch-major receiver covariance and embeds each
local derivative operator in that same coordinate vector. This preserves error
shared by overlapping windows. The calculation linearizes a declared physical
force model; it does not estimate the covariance or prove nonlinear coverage.
"""

import math

import numpy as np

from .ilvis0_receiver_force import evaluate


VERSION = 'ilvis0-force-magnitude-joint-covariance-v2'
MAX_RECEIVER_EPOCHS = 128
MIN_FORCE_MAGNITUDE_MPS2 = 1e-3
_SCALES = np.array([1., 1., 1000., 1e-4, 1e-4, 10.,
                    1e-6, 1e-6, 1.])


def _magnitude(jet, *, model, background_rate_rads, gravity_mps2,
               disc_radius_m):
    force = evaluate(jet[:3], jet[3:6], jet[6:9], model=model,
                     background_rate_rads=background_rate_rads,
                     gravity_mps2=gravity_mps2,
                     disc_radius_m=disc_radius_m)['specific_force_ned_mps2']
    return float(np.linalg.norm(force))


def _gradient(jet, *, model, background_rate_rads, gravity_mps2,
              disc_radius_m):
    if _magnitude(jet, model=model,
                  background_rate_rads=background_rate_rads,
                  gravity_mps2=gravity_mps2,
                  disc_radius_m=disc_radius_m) <= MIN_FORCE_MAGNITUDE_MPS2:
        raise ValueError('near-zero required force has no stable magnitude tangent')
    gradient = np.empty(9)
    for index, scale in enumerate(_SCALES):
        step = 1e-5*max(scale, abs(jet[index]))
        values = []
        for multiple in (-2., -1., 1., 2.):
            changed = jet.copy()
            changed[index] += multiple*step
            values.append(_magnitude(
                changed, model=model,
                background_rate_rads=background_rate_rads,
                gravity_mps2=gravity_mps2,
                disc_radius_m=disc_radius_m))
        minus_two, minus_one, plus_one, plus_two = values
        gradient[index] = (minus_two-8.*minus_one+8.*plus_one-plus_two)/(12.*step)
    if not np.all(np.isfinite(gradient)):
        raise ValueError('finite force-magnitude tangent required')
    return gradient


def propagate(jets, embedded_weights, coordinate_covariance, *, model,
              background_rate_rads, gravity_mps2, disc_radius_m):
    """Propagate a supplied joint receiver covariance through force magnitudes.

    ``jets`` contains rows of position, rate and acceleration in the
    latitude/longitude/height chart. ``embedded_weights`` maps the same global
    receiver-coordinate vector to each nine-component jet. Its last dimension
    must match the supplied covariance exactly; overlapping supports therefore
    retain their cross-covariance. The returned matrix is a first-order
    conditional covariance in (m/s²)², with no calibrated-coverage claim.
    """
    jets = np.asarray(jets, dtype=float)
    weights = np.asarray(embedded_weights, dtype=float)
    covariance = np.asarray(coordinate_covariance, dtype=float)
    if (jets.ndim != 2 or jets.shape[1:] != (9,) or not len(jets) or
            weights.ndim != 3 or weights.shape[:2] != (len(jets), 9) or
            covariance.ndim != 2 or covariance.shape[0] != covariance.shape[1] or
            covariance.shape[0] < 3 or covariance.shape[0] % 3 or
            covariance.shape[0] > 3*MAX_RECEIVER_EPOCHS or
            weights.shape[2] != covariance.shape[0] or
            not all(np.all(np.isfinite(value)) for value in
                    (jets, weights, covariance))):
        raise ValueError('finite matching joint receiver support required')
    if not np.allclose(covariance, covariance.T, rtol=1e-12, atol=0.):
        raise ValueError('symmetric joint receiver covariance required')
    try:
        np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError as error:
        raise ValueError('positive definite joint receiver covariance required') from error
    if (not all(math.isfinite(value) for value in
                (background_rate_rads, gravity_mps2, disc_radius_m)) or
            gravity_mps2 <= 0 or disc_radius_m <= 0):
        raise ValueError('finite physical constants required')
    magnitudes = np.asarray([
        _magnitude(row, model=model,
                   background_rate_rads=background_rate_rads,
                   gravity_mps2=gravity_mps2,
                   disc_radius_m=disc_radius_m)
        for row in jets])
    gradient = np.vstack([_gradient(
        row, model=model, background_rate_rads=background_rate_rads,
        gravity_mps2=gravity_mps2, disc_radius_m=disc_radius_m)
        for row in jets])
    joint = np.einsum('mi,mij->mj', gradient, weights)
    propagated = joint@covariance@joint.T
    propagated = (propagated+propagated.T)/2.
    if not np.all(np.isfinite(propagated)):
        raise ValueError('finite propagated force covariance required')
    return dict(version=VERSION, model=model, gradient=gradient,
                receiver_sensitivity=joint,
                required_force_magnitude_mps2=magnitudes,
                conditional_covariance_mps4=propagated,
                gradient_method='five-point central finite difference',
                maximum_receiver_epochs=MAX_RECEIVER_EPOCHS,
                minimum_force_magnitude_mps2=MIN_FORCE_MAGNITUDE_MPS2,
                receiver_covariance_calibrated=False,
                linearization_coverage_established=False,
                gyro_observations_used=False,
                fused_navigation_used=False,
                scientific_decision='abstain')
