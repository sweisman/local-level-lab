# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local physics for the separate matched-geometry and geographic-field control."""

import math

import numpy as np

from .ilvis0_channel_controls import navigation_specific_force
from .ilvis0_receiver_force import evaluate as zero_field_trajectory
from .models import earth_rate_sphere


def _metric_model(geometry, field, removed_fraction):
    if geometry not in ('globe', 'disc') or field not in ('zero', 'geographic'):
        raise ValueError('explicit globe/disc geometry and zero/geographic field required')
    if not math.isfinite(removed_fraction) or not 0. <= removed_fraction <= 1.:
        raise ValueError('onboard removal fraction must be between zero and one')
    return 'sphere_still' if geometry == 'globe' else 'flat_still'


def _field_vectors(latitude, field, removed_fraction):
    conventional = earth_rate_sphere(latitude)
    physical = conventional if field == 'geographic' else np.zeros(3)
    return physical, removed_fraction * conventional


def evaluate(coordinates, coordinate_rate, coordinate_acceleration, *,
             geometry, field, removed_fraction, gravity_mps2, disc_radius_m):
    """Return force and local frame rate with geometry and field crossed.

    The disc with the prescribed geographic field is a diagnostic model.
    The same hypothetical onboard removal acts on logged angular motion in
    all four cases. It never changes the physical Coriolis term. The logged
    frame rate excludes the aircraft's rotation relative to that frame.
    """
    model = _metric_model(geometry, field, removed_fraction)
    result = zero_field_trajectory(
        coordinates, coordinate_rate, coordinate_acceleration,
        model=model, background_rate_rads=0., gravity_mps2=gravity_mps2,
        disc_radius_m=disc_radius_m)
    background, removed = _field_vectors(float(coordinates[0]), field, removed_fraction)
    transport = result['transport_ned_rads']
    force = navigation_specific_force(
        velocity_ned=result['velocity_ned_mps'],
        acceleration_ned=result['acceleration_ned_mps2'],
        gravity_ned=[0., 0., gravity_mps2], background_ned=background,
        transport_ned=transport)
    return dict(result, background_ned_rads=background,
                specific_force_ned_mps2=force,
                logged_frame_ned_rads=transport + background - removed)


def propagate_step(state, theta, dv, dt, *, geometry, field, removed_fraction,
                   gravity_mps2, disc_radius_m):
    """Integrate calibrated increments using the matched midpoint reference.

    The field acts in the attitude and Coriolis equations. Upstream
    removal applies to attitude propagation in all four candidates.
    """
    from . import ilvis0_forward as forward

    model = _metric_model(geometry, field, removed_fraction)
    if not (math.isfinite(dt) and dt > 0. and
            math.isfinite(gravity_mps2) and gravity_mps2 > 0.):
        raise ValueError('positive finite integration period and gravity required')
    coordinates = forward.vector([state[key] for key in
                                  ('latitude_rad', 'longitude_rad', 'height_m')])
    velocity = forward.vector(state['velocity_ned_mps'])
    attitude = forward.rotation(state['attitude_body_to_ned'])
    theta, dv = map(forward.vector, (theta, dv))
    rate = forward.coordinate_rates(model, coordinates[0], coordinates[2],
                                    velocity, disc_radius_m)
    middle = coordinates + rate * dt / 2.
    background, removed = _field_vectors(middle[0], field, removed_fraction)
    gravity_delta = np.array([0., 0., gravity_mps2 * dt])
    eye = np.eye(3)

    def local_step(rate):
        transport = forward.coordinate_kinematics(
            model, middle[0], middle[2], rate, disc_radius_m)['transport_rate_ned_rads']
        logged_angle = -(background + transport - removed) * dt
        half_attitude = forward.exp(logged_angle / 2.) @ attitude @ forward.exp(theta / 2.)
        next_attitude = forward.exp(logged_angle) @ attitude @ forward.exp(theta)
        coriolis = forward.skew(2. * background + transport) * dt / 2.
        rhs = (eye - coriolis) @ velocity + half_attitude @ dv + gravity_delta
        return next_attitude, np.linalg.solve(eye + coriolis, rhs)

    _, velocity_estimate = local_step(rate)
    center_velocity = (velocity + velocity_estimate) / 2.
    rate = forward.coordinate_rates(model, middle[0], middle[2], center_velocity, disc_radius_m)
    attitude, velocity = local_step(rate)
    coordinates += rate * dt
    return dict(latitude_rad=coordinates[0], longitude_rad=coordinates[1],
                height_m=coordinates[2], velocity_ned_mps=velocity,
                attitude_body_to_ned=attitude)


def propagate_queries(initial, theta, dv, dt, times, *, geometry, field,
                      removed_fraction, gravity_mps2, disc_radius_m):
    """Reference predictions at receiver times from a single inertial path.

    A query inside a packet integrates the corresponding fraction from its
    start. The full packet advances the main path once, so querying extra
    times cannot change subsequent states. The receiver supplies timestamps.
    """
    from . import ilvis0_forward as forward

    model = _metric_model(geometry, field, removed_fraction)
    coordinate_keys = ('latitude_rad', 'longitude_rad', 'height_m')
    coordinates = forward.vector([initial[key] for key in coordinate_keys])
    forward.coordinate_rates(model, coordinates[0], coordinates[2],
                             initial['velocity_ned_mps'], disc_radius_m)
    forward.rotation(initial['attitude_body_to_ned'])
    if not math.isfinite(gravity_mps2) or gravity_mps2 <= 0.:
        raise ValueError('positive finite gravity required')
    theta, dv, dt, times = (np.asarray(value, dtype=float)
                            for value in (theta, dv, dt, times))
    if (dt.ndim != 1 or not len(dt) or theta.shape != (len(dt), 3) or
            dv.shape != theta.shape or times.ndim != 1 or not len(times) or
            not all(np.isfinite(value).all() for value in (theta, dv, dt, times)) or
            np.any(dt <= 0.) or times[0] < 0. or np.any(np.diff(times) <= 0.)):
        raise ValueError('finite positive packet periods and ordered query times required')
    ends = np.cumsum(dt)
    if not np.isfinite(ends[-1]) or times[-1] > ends[-1]:
        raise ValueError('query outside complete packet support')
    options = dict(geometry=geometry, field=field, removed_fraction=removed_fraction,
                   gravity_mps2=gravity_mps2, disc_radius_m=disc_radius_m)
    output = np.empty((len(times), 3))
    state = initial
    query = 0
    start = 0.
    for index, end in enumerate(ends):
        next_state = None
        while query < len(times) and times[query] <= end:
            duration = times[query] - start
            if duration == 0.:
                observed_state = state
            elif times[query] == end:
                next_state = propagate_step(state, theta[index], dv[index], dt[index], **options)
                observed_state = next_state
            else:
                fraction = duration / dt[index]
                observed_state = propagate_step(
                    state, theta[index] * fraction, dv[index] * fraction, duration, **options)
            output[query] = [observed_state[key] for key in coordinate_keys]
            query += 1
        if query == len(times):
            return output
        state = next_state if next_state is not None else propagate_step(
            state, theta[index], dv[index], dt[index], **options)
        start = end


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
