# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate actual-position stability rule; frozen solvers remain unchanged."""
import importlib.util
from pathlib import Path

import numpy as np
from scipy.optimize import lsq_linear

from . import ilvis0_solver_boundary as boundary
from .ilvis0_solver_refinement import POLICY as STOPPING, projected_stationarity

VERSION = 'ilvis0-actual-position-stability-v1'
POLICY = dict(boundary.POLICY, stability='fresh actual position, cost and stationarity',
              position_rms_tolerance_m=.001, position_max_tolerance_m=.01,
              position_metric='common receiver-local NEU coordinate conversion',
              predicted_residual_step_is_gate=False,
              numerical_limits_are_instrument_accuracy=False)


def physical_metric(gps):
    gps = np.asarray(gps, float)
    if gps.ndim != 2 or gps.shape[1] != 3 or not np.all(np.isfinite(gps)):
        raise ValueError('finite receiver coordinates required for physical conversion')
    phi, height = gps[:, 0], gps[:, 2]
    d = 1-6.6943799901413165e-3*np.sin(phi)**2
    return np.column_stack((6378137.*(1-6.6943799901413165e-3)/d**1.5+height,
                            (6378137./np.sqrt(d)+height)*np.cos(phi), np.ones(len(gps))))


def physical_residual_step(problem, delta):
    """Undo shared covariance whitening to compare actual coordinate predictions.

    The same measured receiver coordinates define the unit conversion for every
    model. This is a numerical stability check, not a new observation likelihood.
    """
    delta = np.asarray(delta, float)
    m = len(problem.gps)
    if delta.shape != (3*m,) or not np.all(np.isfinite(delta)):
        raise ValueError('invalid physical residual conversion')
    inverse = getattr(problem,'unwhiten_stacked',None)
    if callable(inverse):
        coordinates = np.asarray(inverse(delta),float)
        if coordinates.shape != (3*m,) or not np.all(np.isfinite(coordinates)):
            raise ValueError('invalid structured physical residual conversion')
        coordinates = coordinates.reshape(m,3)
    else:
        cholesky = np.asarray(problem.cholesky, float)
        if cholesky.shape != (3*m,3*m) or not np.all(np.isfinite(cholesky)):
            raise ValueError('invalid physical residual conversion')
        coordinates = (cholesky @ delta).reshape(m, 3)
    coordinates[:, 1] = (coordinates[:, 1]+np.pi) % (2*np.pi)-np.pi
    return coordinates*physical_metric(problem.gps)


def verify_stability(point, residual, jac, evaluate, physical_step):
    stationarity = projected_stationarity(point, residual, jac)[0]
    if stationarity > STOPPING['stationarity_tolerance']:
        return dict(passed=False, reason='not_stationary')
    correction = lsq_linear(jac, -residual, bounds=(-1-point, 1-point), method='bvls',
                            tol=STOPPING['stability_probe_linear_tolerance'],
                            max_iter=STOPPING['stability_probe_linear_maximum_iterations'])
    if not correction.success or not np.all(np.isfinite(correction.x)):
        return dict(passed=False, reason='local_linear_solve_unfinished')
    cost = float(residual @ residual)
    predicted = residual+jac @ correction.x
    predicted_cost = float(predicted @ predicted)
    probe = np.clip(point+correction.x, -1., 1.)
    fresh, fresh_jac, _ = evaluate(probe, fresh=True)
    difference = np.asarray(physical_step(fresh-residual), float)
    if (difference.ndim != 2 or difference.shape[1] != 3 or not len(difference)
            or not np.all(np.isfinite(difference))):
        raise ValueError('invalid physical prediction difference')
    rms = np.sqrt(np.mean(difference**2, axis=0))
    maximum = np.max(abs(difference), axis=0)
    actual_cost = float(fresh @ fresh)
    change = abs(actual_cost-cost)/max(actual_cost, cost, 1.)
    fresh_stationarity = projected_stationarity(probe, fresh, fresh_jac)[0]
    passed = bool(change <= STOPPING['relative_cost_tolerance']
                  and fresh_stationarity <= STOPPING['stationarity_tolerance']
                  and np.all(rms <= POLICY['position_rms_tolerance_m'])
                  and np.all(maximum <= POLICY['position_max_tolerance_m']))
    return dict(passed=passed,
                reason='fresh_position_stability_verified' if passed else 'fresh_position_probe_not_stable',
                predicted_cost_change=abs(predicted_cost-cost)/max(predicted_cost, cost, 1.),
                predicted_residual_step=float(np.linalg.norm(predicted-residual)/max(np.linalg.norm(residual), 1.)),
                actual_cost_change=change,
                actual_residual_step=float(np.linalg.norm(fresh-residual)/max(np.linalg.norm(residual), 1.)),
                fresh_stationarity=fresh_stationarity,
                normalized_parameter_step=float(np.linalg.norm(probe-point)),
                position_rms_neu_m=rms.tolist(), position_max_abs_neu_m=maximum.tolist(),
                position_rms_tolerance_m=POLICY['position_rms_tolerance_m'],
                position_max_tolerance_m=POLICY['position_max_tolerance_m'])


def fit_candidate(problem, model, *, start, maximum_evaluations=600, physical_step=None):
    # Load a private instance rather than changing the frozen solver's globals.
    # The actual bounded-step algorithm and its finite accounting stay identical.
    spec = importlib.util.spec_from_file_location('lll._position_boundary_core', Path(boundary.__file__))
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    transform = physical_step if physical_step is not None else lambda delta: physical_residual_step(problem, delta)
    core.verify_stability = lambda u, r, j, evaluate: verify_stability(u, r, j, evaluate, transform)
    result = core.fit_candidate(problem, model, start=start, maximum_evaluations=maximum_evaluations)
    result.update(version=VERSION, stability_policy=POLICY,
                  termination='fresh_position_stability' if result['converged'] else 'unresolved')
    return result
