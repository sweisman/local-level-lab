# SPDX-License-Identifier: AGPL-3.0-or-later
"""Predetermined known-answer nonlinear controls; never read archive inputs."""
import numpy as np

from . import ilvis0_solver_boundary as boundary, ilvis0_solver_rectangular as rectangular
from .ilvis0_solver_controls import ANALYTIC, Analytic, ControlBounds, analytic_problem

VERSION = 'ilvis0-boundary-controls-v1'
CONTROLS = ANALYTIC+('curved_boundary', 'exponential', 'curved_redundant', 'nonlinear27')
METHODS = ('rectangular', 'snapped_rectangular', 'boundary_bvls')
ALLOWANCE = 200


def problem_for(name):
    if name in ANALYTIC:
        return analytic_problem(name)
    unique = True
    if name == 'curved_boundary':
        optimum = np.array([1., .2])
        residual = lambda u: np.array([u[0]+.1*u[0]**3-2., 2*u[1]+.3*u[0]**2-.7])
        jacobian = lambda u: np.array([[1+.3*u[0]**2, 0.], [.6*u[0], 2.]])
    elif name == 'exponential':
        optimum = np.array([.5, .2])
        residual = lambda u: np.array([np.exp(4*u[0])-np.exp(2), u[1]-.2])
        jacobian = lambda u: np.diag([4*np.exp(4*u[0]), 1.])
    elif name == 'curved_redundant':
        optimum = np.array([.3, .3])
        residual = lambda u: np.array([1., 2.])*(sum(u)+.1*sum(u)**3-(.6+.1*.6**3))
        jacobian = lambda u: np.array([[1., 1.], [2., 2.]])*(1+.3*sum(u)**2)
        unique = False
    elif name == 'nonlinear27':
        # Invertible monotone component transform plus an ill-conditioned linear
        # map. The zero variable residual at the known feasible truth is global.
        rng = np.random.default_rng(20261012)
        left = np.linalg.qr(rng.normal(size=(27, 27)))[0]
        right = np.linalg.qr(rng.normal(size=(27, 27)))[0]
        matrix = left@np.diag(np.geomspace(1e4, 1e-4, 27))@right.T
        optimum = rng.uniform(-.4, .4, 27)
        optimum[:2] = [1., -1.]
        target = matrix@(optimum+.1*optimum**3)
        residual = lambda u: matrix@(u+.1*u**3)-target
        jacobian = lambda u: matrix*(1+.3*u**2)
        unique = False  # prediction/objective recovery, not weak-coordinate precision
    else:
        raise ValueError('unknown nonlinear control')
    problem = Analytic(residual, jacobian)
    if name == 'nonlinear27':
        problem.bounds = ControlBounds(27)
        # Generalize the constant residual without altering existing fixtures.
        def tangent(u, model):
            problem.calls += 1
            return np.r_[residual(u), 1.], np.vstack([jacobian(u), np.zeros(27)]), 0
        problem.residual_tangent = tangent
    expected = float(residual(optimum)@residual(optimum)+1.)
    return problem, optimum, expected, unique


def starts(n):
    rng = np.random.default_rng(20261012)
    signs = np.where(np.arange(n) % 2, -1., 1.)
    near = np.nextafter(1., 0.)
    return [np.zeros(n), rng.uniform(-.8, .8, n), -.8*signs, near*signs]


def run_one(name, index, method):
    problem, optimum, expected, unique = problem_for(name)
    if method not in METHODS or index not in range(4):
        raise ValueError('unknown method or start')
    start = starts(len(optimum))[index]
    if method == 'snapped_rectangular':
        start = boundary.snap_bounds(start)
    solver = boundary if method == 'boundary_bvls' else rectangular
    fit = solver.fit_candidate(problem, 'control', start=start, maximum_evaluations=ALLOWANCE)
    point = np.array(fit['normalized_parameters'])
    prediction_error = float(np.linalg.norm(problem.residual(point)-problem.residual(optimum)))
    parameter_error = float(np.max(abs(point-optimum))) if unique else None
    objective_error = abs(fit['residual_sum_squares']-expected)
    passed = bool(fit['converged'] and fit['stability_verified'] and objective_error <= 1e-7
                  and prediction_error <= 1e-4 and (not unique or parameter_error <= 1e-5))
    if problem.calls != fit['evaluations'] or problem.calls > ALLOWANCE:
        raise ValueError('software evaluation accounting mismatch')
    return dict(identity=f'{name}::{index}::{method}', control=name, start=index, method=method,
                passed=passed, fit=fit, reference_objective=expected, objective_error=objective_error,
                prediction_error=prediction_error, identifiable_parameter_error=parameter_error,
                parameters_at_limits=len(fit['active_bounds']),
                actual_evaluations=problem.calls, maximum_actual_evaluations=ALLOWANCE,
                observed_fit_starts=0, scientific_decision='abstain')
