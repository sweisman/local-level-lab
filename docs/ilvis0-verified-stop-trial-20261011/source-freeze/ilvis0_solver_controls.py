# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small independent closed-form controls for the frozen solver; no archive inputs."""
import math
import numpy as np

from . import ilvis0_estimator as estimator, ilvis0_exploratory as explore
from . import ilvis0_estimator_controls as fixtures, ilvis0_solver_refinement as solver
from . import models

EvaluationLimit = estimator.EvaluationLimit
VERSION = 'ilvis0-independent-solver-controls-v1'
ANALYTIC = ('interior', 'boundary', 'redundant', 'scaled', 'nonlinear', 'gain_offset')
MOTION = ('bias', 'effective_orientation', 'gain', 'timing', 'stationary_rotating',
          'stationary_still', 'east_rotating', 'east_still')


class ControlBounds:
    def __init__(self, n):
        self.active = tuple('control_'+str(i) for i in range(n))

    def decode(self, point):
        point = np.asarray(point, float)
        if point.shape != (len(self.active),) or not np.all(np.isfinite(point)) or np.any(abs(point) > 1):
            raise ValueError('invalid bounded control point')
        return dict(zip(self.active, point.tolist()))


class Analytic:
    def __init__(self, residual, jacobian):
        self.bounds = ControlBounds(2); self.calls = 0
        self.residual = residual; self.jacobian = jacobian

    def residual_tangent(self, point, model):
        self.calls += 1
        r = self.residual(np.asarray(point, float))
        j = self.jacobian(np.asarray(point, float))
        return np.r_[r, 1.], np.vstack([j, [0., 0.]]), 0


def analytic_problem(name):
    unique = True
    if name in ('interior', 'boundary', 'redundant', 'scaled'):
        matrix = np.eye(2); target = np.array([.2, -.4]); optimum = target.copy()
        if name == 'boundary':
            target = np.array([1.5, -.4]); optimum = np.array([1., -.4])
        elif name == 'redundant':
            matrix = np.array([[1., 1.], [2., 2.]])
            target = np.array([.6, 1.2]); optimum = np.array([.3, .3]); unique = False
        elif name == 'scaled':
            matrix = np.diag([1e4, 1e-4]); target = matrix@optimum; unique = False
        residual = lambda x: matrix@x-target
        jacobian = lambda x: matrix
    elif name == 'nonlinear':
        optimum = np.array([.2, -.4])
        residual = lambda x: np.array([x[0]+x[0]**3-(.2+.2**3), x[1]+.4])
        jacobian = lambda x: np.diag([1+3*x[0]**2, 1.])
    elif name == 'gain_offset':
        # Independent sensor equation: observed = (1+gain)*true_rate + offset.
        rates = 1e-4+np.linspace(-1e-7, 1e-7, 8)
        optimum = np.array([.5, -.4]); gain_limit = .02; bias_limit = math.pi/648000
        observed = (1+gain_limit*optimum[0])*rates+bias_limit*optimum[1]
        def residual(x):
            return ((observed-bias_limit*x[1])/(1+gain_limit*x[0])-rates)/1e-8
        def jacobian(x):
            return np.column_stack((-gain_limit*(observed-bias_limit*x[1])/(1+gain_limit*x[0])**2,
                np.full(len(rates), -bias_limit/(1+gain_limit*x[0]))))/1e-8
        unique = False  # weak gain/offset coordinates; require prediction/objective recovery.
    else:
        raise ValueError('unknown analytic control')
    expected = float(residual(optimum)@residual(optimum)+1.)
    return Analytic(residual, jacobian), optimum, expected, unique


def globe_problem(name, kernel):
    """Analytic stationary/equatorial eastward tracks; never call forward prediction."""
    rotating = name.endswith('rotating'); eastward = name.startswith('east')
    if name not in MOTION[4:]:
        raise ValueError('unknown globe control')
    phi = 0. if eastward else .8; height = 20.; radius = 6378137.+height
    dt = np.full(200, .01); times = np.linspace(.25, 1.75, 7)
    velocity = np.array([0., 220. if eastward else 0., 0.])
    earth = np.array([math.cos(phi), 0., -math.sin(phi)])*7.292115e-5 if rotating else np.zeros(3)
    transport = np.array([velocity[1]/radius, 0., 0.])
    theta = np.tile((earth+transport)*.01, (200, 1))
    force = np.cross(2*earth+transport, velocity)-np.array([0., 0., 9.81])
    dv = np.tile((force+np.array([.04, 0., 0.]))*.01, (200, 1))
    gps = np.column_stack((np.full(len(times), phi), velocity[1]*times/radius,
                           np.full(len(times), height)))
    sigma = np.tile([.001/radius, .001/radius, .001], len(times))
    p = explore.ConditionalProblem(theta, dv, dt, times, gps, np.diag(sigma**2),
        dict(latitude_rad=phi, longitude_rad=0., height_m=height,
             velocity_ned_mps=velocity, attitude_body_to_ned=np.eye(3)), estimator.Bounds({'accel_bias_x': .1}),
        fit_earth_removal=False, kernel=kernel, clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis', maximum_interval_s=.015,
        gravity_mps2=9.81, disc_radius_m=6371000.)
    return p, 'sphere_rotating' if rotating else 'sphere_still', {'accel_bias_x': .04}, 2e-7


def motion_problem(name, kernel):
    if name in MOTION[4:]:
        return globe_problem(name, kernel)
    p = fixtures.problem_for(name)
    q = explore.ConditionalProblem(p.theta, p.dv, p.dt, p.gps_times, p.gps,
        p.cholesky@p.cholesky.T, p.initial, p.bounds, fit_earth_removal=False, kernel=kernel,
        clock_hypothesis=p.clock_hypothesis, processing_hypothesis=p.processing_hypothesis,
        maximum_interval_s=.015, gravity_mps2=p.gravity, disc_radius_m=p.radius)
    case = fixtures.CASES[name]
    return q, 'flat_still', case['truth'], case['tolerance']


class DifferenceProblem:
    """Independently differenced value predictions; count every actual call."""
    def __init__(self, problem, maximum_predictions=200):
        self.problem = problem; self.bounds = problem.bounds
        self.predictions = 0; self.maximum_predictions = maximum_predictions

    def residual(self, point, model):
        if self.predictions >= self.maximum_predictions:
            raise EvaluationLimit('control prediction allowance exhausted')
        self.predictions += 1
        return self.problem.residual(point, model)

    def residual_tangent(self, point, model):
        n = len(point)
        if self.predictions+1+2*n > self.maximum_predictions:
            raise EvaluationLimit('control tangent would exceed prediction allowance')
        r = self.residual(point, model); jac = np.empty((len(r), n)); step = 1e-3
        for i in range(n):
            if abs(point[i]) <= 1-step:
                a = point.copy(); b = point.copy(); a[i] += step; b[i] -= step
                jac[:, i] = (self.residual(a, model)-self.residual(b, model))/(2*step)
            else:
                h = -step if point[i] > 0 else step
                a = point.copy(); b = point.copy(); a[i] += h; b[i] += 2*h
                jac[:, i] = (-3*r+4*self.residual(a, model)-self.residual(b, model))/(2*h)
        return r, jac, 0


def starts(n, count):
    rng = np.random.default_rng(20261010)
    return [np.zeros(n)]+[rng.uniform(-.8, .8, n) for _ in range(count-1)]


def identities():
    return [f'{name}::{i}' for name in ANALYTIC+MOTION for i in range(3 if name in ANALYTIC else 2)]


def run_one(name, index, kernel=None):
    if name in ANALYTIC:
        p, optimum, expected, unique = analytic_problem(name)
        fit = solver.fit_candidate(p, 'control', start=starts(2, 3)[index])
        point = np.array(fit['normalized_parameters'])
        prediction_error = float(np.linalg.norm(p.residual(point)-p.residual(optimum)))
        parameter_error = float(np.max(abs(point-optimum))) if unique else None
        passed = (fit['converged'] and abs(fit['residual_sum_squares']-expected) <= 1e-7
                  and prediction_error <= 1e-4 and (not unique or parameter_error <= 1e-5))
        actual = p.calls; derivative = 'exact derivative of independent analytic function'
        objective_reference = expected; prediction_tolerance = 1e-4
    else:
        native, model, truth, tolerance = motion_problem(name, kernel)
        p = DifferenceProblem(native); n = len(p.bounds.active)
        fit = solver.fit_candidate(p, model, start=starts(n, 2)[index], maximum_evaluations=200//(1+2*n))
        point = np.array(fit['normalized_parameters'])
        residual = p.residual(point, model)
        truth_point = np.array([truth[k]/native.bounds.limits[k] for k in native.bounds.active])
        reference = p.residual(truth_point, model); objective_reference = float(reference@reference)
        coordinate_error = (native.cholesky@residual).reshape(-1, 3)
        if model == 'flat_still':
            scale = np.array([native.radius, native.radius*(math.pi/2-native.initial['latitude_rad']), 1.])
        else:
            rm, rn = models.radii(native.initial['latitude_rad']); h = native.initial['height_m']
            scale = np.array([rm+h, (rn+h)*math.cos(native.initial['latitude_rad']), 1.])
        prediction_error = float(np.max(abs(coordinate_error*scale)))
        parameter_error = float(max(abs(fit['parameters'][k]-v) for k, v in truth.items()))
        prediction_tolerance = 5e-5
        passed = (fit['converged'] and fit['residual_sum_squares'] <= objective_reference+1e-7
                  and parameter_error <= tolerance and prediction_error <= prediction_tolerance)
        actual = p.predictions; derivative = 'independent second-order finite difference of native value predictions'
    fit['derivative_method'] = derivative
    if actual > 200:
        raise ValueError('software control exceeded actual evaluation allowance')
    return dict(identity=f'{name}::{index}', control=name, start=index, passed=bool(passed), fit=fit,
        actual_evaluations=actual, maximum_actual_evaluations=200, reference_objective=objective_reference,
        prediction_error=prediction_error, prediction_tolerance=prediction_tolerance,
        identifiable_parameter_error=parameter_error, independent_archive_confirmation=False,
        observed_fit_starts=0, scientific_decision='abstain')
