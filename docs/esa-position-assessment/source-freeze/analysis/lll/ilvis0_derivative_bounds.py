# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic Taylor remainder and coordinate-error propagation for a jet."""
import math

import numpy as np


def jet_error_bounds(weights, times_s, target_s, *, derivative_envelopes,
                     coordinate_error_bounds):
    """Bound nine estimated position/rate/acceleration components.

    weights uses the frozen LocalPolynomial convention: epoch-major input
    coordinates, then derivative-order-major three-axis output. Envelopes have
    shape (p+2,3) for degree p in {2,3,4}. Orders 0..p bound the absolute true
    derivatives at target; order p+1 bounds them throughout the support.
    Coordinates must be smooth/unwrapped on that support. Input units are the
    caller's coordinate units (e.g. radians, radians, metres), never mixed into
    a single norm. coordinate_error_bounds is an explicit componentwise bound
    on each observed coordinate, not a covariance standard deviation.

    Retain every cross-coordinate weight. Taylor remainder, coordinate error
    and the stored operator's polynomial reproduction defect add as worst-case
    bounds. Floating-point arithmetic is checked for finiteness, but this is
    not interval-certified roundoff or calibrated probabilistic coverage.
    """
    weights = np.asarray(weights, float)
    times = np.asarray(times_s, float)
    envelopes = np.asarray(derivative_envelopes, float)
    errors = np.asarray(coordinate_error_bounds, float)
    if (times.ndim != 1 or len(times) < 3 or not np.all(np.isfinite(times))
            or np.any(np.diff(times) <= 0.) or not np.isfinite(target_s)
            or not times[0] <= target_s <= times[-1]):
        raise ValueError('finite ordered interpolation support and target required')
    if weights.shape != (9, 3*len(times)) or not np.all(np.isfinite(weights)):
        raise ValueError('finite nine-output epoch-major coordinate operator required')
    if (envelopes.ndim != 2 or envelopes.shape[1] != 3
            or envelopes.shape[0] not in (4, 5, 6) or len(times) < envelopes.shape[0]-1
            or not np.all(np.isfinite(envelopes)) or np.any(envelopes < 0.)):
        raise ValueError('nonnegative finite derivative envelopes through degree+1 required')
    if (errors.shape != (len(times), 3) or not np.all(np.isfinite(errors))
            or np.any(errors < 0.)):
        raise ValueError('nonnegative finite componentwise coordinate-error bounds required')
    degree = len(envelopes)-2
    with np.errstate(over='ignore', invalid='ignore'):
        tau = times-target_s
        design = np.kron(np.column_stack([tau**k/math.factorial(k)
            for k in range(degree+1)]), np.eye(3))
        remainder = (abs(tau[:, None])**(degree+1)
            * envelopes[-1]/math.factorial(degree+1))
        exact = np.eye(9, 3*(degree+1))
        reproduction = abs(weights@design-exact)@envelopes[:-1].ravel()
        truncation = abs(weights)@remainder.ravel()
        measurement = abs(weights)@errors.ravel()
        total = reproduction+truncation+measurement
    if not np.all(np.isfinite(total)):
        raise ValueError('derivative bound exceeds finite range')
    return dict(total_jet_error_bounds=total, truncation_bounds=truncation,
        coordinate_error_bounds=measurement, polynomial_reproduction_bounds=reproduction,
        degree=degree, derivative_envelopes=envelopes.copy(),
        higher_derivative_is_assumed=True, statistical_coverage_calibrated=False,
        roundoff_interval_enclosed=False, scientific_decision='abstain')
