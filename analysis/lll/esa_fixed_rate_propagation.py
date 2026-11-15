# SPDX-License-Identifier: AGPL-3.0-or-later
"""One no-fit ESA forecast at a sealed point and fixed training initialization."""


def propagate(*, theta, dv, dt, training_prefix, training_times, training_gps,
              forecast_times, initial, gravity, point, active_parameters,
              limits, model, profile, clock, maximum_interval_s, tangent_kernel,
              reserve):
    """Propagate one input convention; the caller owns its frozen native charge.

    Identity covariance only satisfies the problem constructor. No residual,
    likelihood or uncertainty calculation uses it. All scientific parameters,
    initial state and gravity must be supplied from the sealed baseline.
    """
    import numpy as np
    from .ilvis0_estimator import Bounds
    from .ilvis0_forecast import native_forecast
    from .ilvis0_shape import TangentProblem

    theta, dv, dt = (np.asarray(value, dtype=float)
                     for value in (theta, dv, dt))
    train_time = np.asarray(training_times, dtype=float)
    train_gps = np.asarray(training_gps, dtype=float)
    full_time = np.asarray(forecast_times, dtype=float)
    point = np.asarray(point, dtype=float)
    if (model != 'sphere_rotating' or profile is not False or
            clock != 'header_elapsed' or
            type(training_prefix) is not int or
            not 1 <= training_prefix <= len(dt) or
            train_gps.shape != (len(train_time), 3) or
            len(train_time) < 2 or len(full_time) <= len(train_time) or
            not np.array_equal(train_time, full_time[:len(train_time)]) or
            theta.shape != (len(dt), 3) or dv.shape != theta.shape or
            point.shape != (len(active_parameters),) or
            not np.all(np.isfinite(point)) or
            not callable(tangent_kernel) or not callable(reserve)):
        raise ValueError('unchanged candidate, fixed point and complete training support required')
    # The covariance is unused by native_forecast; retain the receiver training
    # observations solely for the original time support and problem invariants.
    identity = np.eye(3*len(train_time), dtype=float)
    problem = TangentProblem(
        theta[:training_prefix], dv[:training_prefix], dt[:training_prefix],
        train_time, train_gps, identity, initial, Bounds(limits),
        tangent_kernel=tangent_kernel, kernel=None,
        fit_earth_removal=False, clock_hypothesis=clock,
        processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=maximum_interval_s, gravity_mps2=gravity,
        disc_radius_m=6371000.)
    if list(problem.bounds.active) != list(active_parameters):
        raise ValueError('saved active parameters differ from fixed forecast problem')
    forecast = native_forecast(
        problem, point, model, theta=theta, dv=dv, dt=dt,
        times=full_time, maximum_interval_s=maximum_interval_s,
        reserve=reserve)
    return dict(coordinates=forecast['coordinates'],
                boundary_counter=forecast['boundary_counter'],
                boundary_classification=forecast['boundary_classification'],
                active_parameters=forecast['active_parameters'],
                training_epochs=forecast['training_epochs'],
                prediction_epochs=forecast['prediction_epochs'],
                refits=0, receiver_covariance_used_for_score=False,
                scientific_decision='abstain')
