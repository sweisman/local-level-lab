# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local physics for the separate matched-geometry and geographic-field control."""

import math

import numpy as np

from .ilvis0_channel_controls import navigation_specific_force
from .ilvis0_receiver_force import evaluate as zero_field_trajectory
from .models import earth_rate_sphere


def evaluate(coordinates, coordinate_rate, coordinate_acceleration, *,
             geometry, field, removed_fraction, gravity_mps2, disc_radius_m):
    """Return force and local frame rate with geometry and field crossed.

    The disc with the prescribed geographic field is a diagnostic model.
    The same hypothetical onboard removal acts on logged angular motion in
    all four cases. It never changes the physical Coriolis term. The logged
    frame rate excludes the aircraft's rotation relative to that frame.
    """
    if geometry not in ('globe', 'disc') or field not in ('zero', 'geographic'):
        raise ValueError('explicit globe/disc geometry and zero/geographic field required')
    if not math.isfinite(removed_fraction) or not 0. <= removed_fraction <= 1.:
        raise ValueError('onboard removal fraction must be between zero and one')
    result = zero_field_trajectory(
        coordinates, coordinate_rate, coordinate_acceleration,
        model='sphere_still' if geometry == 'globe' else 'flat_still',
        background_rate_rads=0., gravity_mps2=gravity_mps2,
        disc_radius_m=disc_radius_m)
    conventional = earth_rate_sphere(float(coordinates[0]))
    background = conventional if field == 'geographic' else np.zeros(3)
    transport = result['transport_ned_rads']
    force = navigation_specific_force(
        velocity_ned=result['velocity_ned_mps'],
        acceleration_ned=result['acceleration_ned_mps2'],
        gravity_ned=[0., 0., gravity_mps2], background_ned=background,
        transport_ned=transport)
    return dict(result, background_ned_rads=background,
                specific_force_ned_mps2=force,
                logged_frame_ned_rads=transport + background - removed_fraction * conventional)


def profile_constant_gyro_offset(observed, expected, *, limit_dph, weights=None):
    """Minimize summed squared body-rate error with one offset per axis.

    The two rate histories must already be aligned in the same body axes.
    The optional positive sample weights are shared across axes. Each
    offset is the weighted mean difference clipped to its symmetric box.
    This check conditions on the supplied motion and has no fitted attitude
    or aircraft uncertainty model.
    """
    observed, expected = (np.asarray(value, dtype=float) for value in (observed, expected))
    if (observed.ndim != 2 or observed.shape[1:] != (3,) or len(observed) == 0 or
            expected.shape != observed.shape or not np.isfinite(observed).all() or
            not np.isfinite(expected).all() or not math.isfinite(limit_dph) or limit_dph <= 0.):
        raise ValueError('matching finite body-rate histories and positive offset limit required')
    weights = np.ones(len(observed)) if weights is None else np.asarray(weights, dtype=float)
    if (weights.shape != (len(observed),) or not np.isfinite(weights).all() or
            np.any(weights <= 0.)):
        raise ValueError('one finite positive weight per sample required')
    weights = weights / weights.max()
    limit = math.radians(limit_dph) / 3600.
    difference = observed - expected
    offset = np.clip(np.average(difference, axis=0, weights=weights), -limit, limit)
    residual = difference - offset
    mean_square = float(np.average(np.sum(residual ** 2, axis=1), weights=weights))
    if not math.isfinite(mean_square):
        raise ValueError('finite profiled rate error required')
    return dict(offset_dph=np.degrees(offset)*3600., residual_rads=residual,
                weighted_mean_square_rads2=mean_square)


def gyro_free_attitude_witness(problem, shared_calibration, twist_radians):
    """Realize the scalar force residual with a family of sampled attitudes.

    At each sample, aligning the two force directions minimizes the Euclidean
    force error by the reverse triangle inequality. The twist about the
    required force is free. The caller supplies one calibration for the
    entire history and any independently justified motion constraints must
    be tested separately.
    """
    from .ilvis0_gyro_free_path import attitude_histories

    body, target, measured, required, _ = problem.quantities(shared_calibration)
    if len(body) < 2 or np.any(measured <= 0.) or np.any(required <= 0.):
        raise ValueError('at least two samples with nonzero calibrated forces required')
    attitudes = attitude_histories(body / measured[:, None],
                                   target / required[:, None], twist_radians)
    error = np.einsum('nij,nj->ni', attitudes, body) - target
    return dict(body_to_ned=attitudes, force_error_ned_mps2=error,
                attitude_identified=False)
