# SPDX-License-Identifier: AGPL-3.0-or-later
"""Analytic short motion controls, not flight simulations or sensor specifications."""
import numpy as np

from . import ilvis0_estimator as estimator, ilvis0_forward as forward


def fixture(bounds=None, *, acceleration=.2, jerk=0., bias=.04, gain=0., pitch=0.,
            offset=0., covariance=None, times=None):
    radius = 6371000.
    dt = np.full(200, .01)
    mid = np.cumsum(dt)-dt/2
    c = forward.exp([0., pitch, 0.])
    dv = np.array([c.T @ np.array([acceleration+jerk*t, 0., -9.81]) for t in mid])*dt[:, None]
    dv[:, 0] = dv[:, 0]*(1+gain)+bias*dt
    times = np.linspace(.25, 1.75, 7) if times is None else np.asarray(times)
    actual = times+offset
    north = .5*actual+acceleration*actual**2/2+jerk*actual**3/6
    gps = np.column_stack((.8+north/radius, np.zeros(len(times)), np.full(len(times), 20.)))
    sigma = np.tile([.001/radius, .001/radius, .001], len(times))
    return estimator.MotionProblem(np.zeros((len(dt), 3)), dv, dt, times, gps,
        np.diag(sigma**2) if covariance is None else covariance,
        dict(attitude_body_to_ned=np.eye(3), velocity_ned_mps=[.5, 0., 0.],
             latitude_rad=.8, longitude_rad=0., height_m=20.),
        estimator.Bounds({'accel_bias_x': .1}) if bounds is None else bounds,
        clock_hypothesis='header_elapsed', processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.015, gravity_mps2=9.81, disc_radius_m=radius)


CASES = {
    'bias': dict(bounds={'accel_bias_x': .1}, truth={'accel_bias_x': .04}, tolerance=2e-7),
    'effective_orientation': dict(bounds={'attitude_y': .01}, acceleration=0., bias=0., pitch=.002,
        truth={'attitude_y': .002}, tolerance=2e-7),
    'gain': dict(bounds={'accel_gain_x': .01}, jerk=.7, bias=0., gain=.003,
        truth={'accel_gain_x': .003}, tolerance=2e-5),
    'timing': dict(bounds={'time_offset': .08}, jerk=.7, bias=0., offset=.035,
        truth={'time_offset': .035}, tolerance=2e-5),
    'orientation_acceleration_ambiguity': dict(bounds={'attitude_y': .01,
        'accel_bias_x': .1, 'accel_bias_z': .1}, acceleration=0., bias=0., pitch=.002,
        truth={}, tolerance=None),
}


def problem_for(name):
    kwargs = {k:v for k,v in CASES[name].items() if k not in ('truth', 'tolerance')}
    kwargs['bounds'] = estimator.Bounds(kwargs['bounds'])
    return fixture(**kwargs)


def control_results():
    return {name: estimator.fit_control(problem_for(name), 'flat_still', maximum_evaluations=160)
            for name in CASES}


def controlled_pairwise_design():
    """Through-model pair diagnostics on a TWO-SECOND analytic control only.

    Each anchor has its own nuisance Jacobian, with the same observation covariance.
    This is neither the archived route design nor an empirical Earth comparison.
    """
    problem = fixture(estimator.Bounds({'gyro_bias_x': .0001, 'gyro_bias_y': .0001,
                                      'velocity_x': .2, 'accel_bias_x': .1}), bias=0.)
    predictions, jacobians = {}, {}
    calls = 0
    for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
        point = np.zeros(len(problem.bounds.active))
        base = problem.predict(point, model)
        calls += 1
        predictions[model] = problem.whiten(base-problem.gps)
        jac = np.empty((problem.gps.size, len(point)))
        for k in range(len(point)):
            perturbed = point.copy()
            perturbed[k] = .001
            jac[:, k] = problem.whiten(problem.predict(perturbed, model)-base)/.001
            calls += 1
        jacobians[model] = jac
    return dict(scope='two-second deterministic software control; not observed flight geometry',
        prediction_evaluations=calls, nuisance_bounds=problem.bounds.limits,
        models=estimator.pairwise_design(predictions, jacobians),
        empirical_earth_fit_attempts=0, calibrated=False)
