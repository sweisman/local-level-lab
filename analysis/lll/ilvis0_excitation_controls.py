# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent analytic longer/pitch controls; no archive fits or hardware claims."""
import math

import numpy as np

from . import ilvis0_estimator as estimator, ilvis0_gps_sensitivity as sensitivity

VERSION = 'ilvis0-duration-excitation-controls-v1'
DURATIONS = (2., 20., 60.)
MOTIONS = ('steady_orientation', 'brief_pitch')
ASSUMPTIONS = ('formal_only', 'h1_v3_tau60', 'h10_v30_tau300')
LIMITS = {'position_x': 5., 'velocity_x': .5, 'attitude_y': .01,
          'gyro_bias_y': 1e-5, 'gyro_gain_y': .01, 'accel_bias_x': .05,
          'accel_gain_x': .01, 'time_offset': .08}
UNITS = {'position_x': 'm', 'velocity_x': 'm/s', 'attitude_y': 'rad',
         'gyro_bias_y': 'rad/s', 'gyro_gain_y': 'fraction', 'accel_bias_x': 'm/s2',
         'accel_gain_x': 'fraction', 'time_offset': 's'}


def pitch_rotation(angle):
    # Independent one-axis construction, without calling the predictor's exp().
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, 0., s], [0., 1., 0.], [-s, 0., c]])


def pitch_at(t, duration, motion):
    if motion not in MOTIONS:
        raise ValueError('unsupported motion')
    if motion == 'steady_orientation':
        return 0.
    elapsed = t-(duration/2-.5)
    return math.radians(.1)*max(0., 1-abs(2*elapsed-1)) if 0 <= elapsed <= 1 else 0.


def acceleration_at(t):
    # Piecewise constant on exact half-second boundaries: varying excitation,
    # with analytically integrable GPS positions and no coarse jerk error.
    return .2+.3*math.cos(2*math.pi*(math.floor(t*2+1e-9)/2)/6)


def north_at(t, velocity=200.):
    if t < 0:
        raise ValueError('nonnegative analytic time required')
    displacement = velocity*t
    for index in range(int(math.ceil(2*t))):
        start = index/2; end = min(t, start+.5)
        displacement += acceleration_at(start)*(t*(end-start)-(end*end-start*start)/2)
    return displacement


def fixture(duration, motion, assumption, *, truth=None, limits=None):
    if duration not in DURATIONS or motion not in MOTIONS:
        raise ValueError('fixed duration/motion grid required')
    truth = {} if truth is None else dict(truth)
    bounds = estimator.Bounds(LIMITS if limits is None else limits)
    if set(truth)-set(bounds.active):
        raise ValueError('truth requires a declared active parameter')
    point = np.array([truth.get(name, 0.)/bounds.limits[name] for name in bounds.active])
    bounds.decode(point)
    # Coarse intervals are exact for constant orientation/acceleration. Resolve
    # the one-second pitch correction at 200Hz without downsampling archive data.
    edges = np.arange(0., duration+.25, .5).tolist()
    if motion == 'brief_pitch':
        begin = duration/2-.5
        edges.extend(begin+np.arange(201)*.005)
    edges = np.array(sorted({round(float(t), 9) for t in edges}))
    dt = np.diff(edges); mid = (edges[:-1]+edges[1:])/2
    theta = np.zeros((len(dt), 3)); dv = np.empty_like(theta)
    for index, (start, end, center) in enumerate(zip(edges[:-1], edges[1:], mid)):
        theta[index, 1] = pitch_at(end, duration, motion)-pitch_at(start, duration, motion)
        angle = (pitch_at(start, duration, motion)+pitch_at(end, duration, motion))/2
        angle += truth.get('attitude_y', 0.)
        force = np.array([acceleration_at(center), 0., -9.81])
        dv[index] = pitch_rotation(angle).T@force*dt[index]
    theta[:, 1] = theta[:, 1]*(1+truth.get('gyro_gain_y', 0.))+truth.get('gyro_bias_y', 0.)*dt
    dv[:, 0] = dv[:, 0]*(1+truth.get('accel_gain_x', 0.))+truth.get('accel_bias_x', 0.)*dt
    # Fractional, actual GPS epochs; explicit offset retains native support.
    gps_times = np.arange(.25, duration, .5)
    actual = gps_times+truth.get('time_offset', 0.)
    radius = 6371000.; phi = .8
    gps = np.column_stack((phi+(np.array([north_at(t, 200.+truth.get('velocity_x', 0.))
        for t in actual])+truth.get('position_x', 0.))/radius,
        np.zeros(len(actual)), np.full(len(actual), 20.)))
    k = sensitivity.correlation(gps_times, assumption.correlation_s)
    u = (gps_times-gps_times[0])/(gps_times[-1]-gps_times[0])
    block = 1e-6*np.array([[1., .25, .15], [.25, 1., .1], [.15, .1, 1.]])
    covariance = np.kron(np.eye(len(actual)), block)
    covariance += np.kron(k, np.diag(np.square(assumption.noise_neu_m)))
    covariance += np.kron(np.ones_like(k), np.diag(np.square(assumption.offset_neu_m)))
    covariance += np.kron(np.outer(u, u), np.diag(np.square(assumption.drift_neu_m)))
    metric = np.array([1/radius, 1/(radius*(math.pi/2-phi)), 1.])
    transform = np.tile(metric, len(actual))
    covariance *= transform[:, None]*transform[None, :]
    problem = estimator.MotionProblem(theta, dv, dt, gps_times, gps, covariance,
        dict(attitude_body_to_ned=np.eye(3), velocity_ned_mps=[200., 0., 0.],
             latitude_rad=phi, longitude_rad=0., height_m=20.), bounds,
        clock_hypothesis='header_elapsed', processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.501, gravity_mps2=9.81, disc_radius_m=radius)
    return problem, point, metric


def tangent(problem, point):
    base = problem.predict(point, 'flat_still'); calls = 1
    columns = []; coarse = []
    for i in range(len(point)):
        step = 1e-3 if point[i] <= 1-2e-3 else -1e-3
        p = point.copy(); p[i] += step
        columns.append(problem.whiten(problem.predict(p, 'flat_still')-base)/step)
        p[i] = point[i]+2*step
        coarse.append(problem.whiten(problem.predict(p, 'flat_still')-base)/(2*step))
        calls += 2
    result = jacobian_precision(np.column_stack(columns), np.column_stack(coarse),
        problem.bounds.active, problem.bounds.limits)
    result['prediction_evaluations'] = calls
    return result


def jacobian_precision(jac, other, names, limits):
    jac, other = np.asarray(jac, float), np.asarray(other, float)
    if jac.ndim != 2 or jac.shape != other.shape or jac.shape[1] != len(names) or not len(names):
        raise ValueError('matching nonempty finite Jacobians required')
    if not np.all(np.isfinite(jac)) or not np.all(np.isfinite(other)):
        raise ValueError('matching nonempty finite Jacobians required')
    _, singular, vt = np.linalg.svd(jac, full_matrices=False)
    disagreement = float(np.linalg.norm(jac-other, ord=2))
    cutoff = max(float(singular[0])*1e-7, 3*disagreement)
    keep = singular > cutoff
    null_projection = np.eye(len(names))-vt[keep].T@vt[keep]
    # Minimum-norm covariance is finite only for a parameter whose basis vector
    # has negligible projection into the unresolved subspace. Do not publish
    # pseudoinverse diagonal entries as precision of unidentified parameters.
    covariance = (vt[keep].T/np.square(singular[keep]))@vt[keep]
    parameters = {}
    for i, name in enumerate(names):
        unresolved = float(np.linalg.norm(null_projection[:, i]))
        sigma = math.sqrt(max(0., covariance[i, i])) if unresolved < 1e-5 else None
        parameters[name] = dict(unit=UNITS[name], null_projection_norm=unresolved,
            local_sigma=None if sigma is None else sigma*limits[name],
            sigma_to_assumed_bound=sigma)
    return dict(rank=int(np.sum(keep)), active=len(names),
        singular_values=singular.tolist(), cutoff=cutoff, derivative_step_disagreement_norm=disagreement,
        parameters=parameters, calibrated=False, precision_scope='unbounded local tangent; no confidence coverage')


def run_tangent(duration, motion, assumption):
    truth = {'gyro_bias_y': 2e-6, 'gyro_gain_y': .002, 'accel_bias_x': .01,
             'accel_gain_x': .003, 'time_offset': .035}
    problem, point, metric = fixture(duration, motion, assumption, truth=truth)
    result = tangent(problem, point)
    # A separate check against the independent analytic trajectory, not a fit.
    error = (problem.predict(point, 'flat_still')-problem.gps)/metric
    maximum = float(np.max(abs(error)))
    return dict(version=VERSION, duration_s=duration, motion=motion,
        assumption=assumption.report(), truth=truth, bounds=problem.bounds.limits,
        native_fixture_intervals=len(problem.dt), gps_epochs=len(problem.gps_times),
        pitch_amplitude_rad=math.radians(.1) if motion == 'brief_pitch' else 0.,
        pitch_duration_s=1. if motion == 'brief_pitch' else 0.,
        tangent=result, prediction_evaluations=result['prediction_evaluations']+1,
        analytic_trajectory_maximum_error_m=maximum, analytic_control_passed=maximum < 2e-6,
        archived_data_used=False, empirical_earth_fit_attempts=0, calibrated=False)


def run_recovery(duration, parameter, assumption):
    truth = {'gyro_bias_y': 2e-6, 'time_offset': .035}[parameter]
    problem, point, metric = fixture(duration, 'brief_pitch', assumption,
        truth={parameter:truth}, limits={parameter:LIMITS[parameter]})
    fit = estimator.fit_control(problem, 'flat_still', maximum_evaluations=160)
    tolerance = 2e-8 if parameter == 'gyro_bias_y' else 2e-6
    return dict(duration_s=duration, parameter=parameter, truth=truth, tolerance=tolerance,
        assumption=assumption.name, fit=fit,
        recovery_passed=bool(fit['converged'] and fit['nuisance_fully_observable'] and
                            abs(fit['parameters'][parameter]-truth) < tolerance),
        empirical_earth_fit_attempts=0, calibrated=False)
