# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded continuation from saved solutions; frozen first-pass code is unchanged."""
import numpy as np
from scipy.optimize import least_squares

from .ilvis0_estimator import EvaluationLimit
from .ilvis0_solver_refinement import StableStop, projected_stationarity
from .ilvis0_solver_verified_stop import verify_stability

VERSION = 'ilvis0-warm-continuation-v1'
POLICY = dict(maximum_evaluations=600, fresh_check_reserve=2,
              stationarity_tolerance=1e-4, relative_cost_tolerance=1e-8,
              relative_residual_step_tolerance=1e-6, stable_iterations=3,
              ftol=None, xtol=1e-11, gtol=1e-14, x_scale='jac',
              initialization='explicit saved feasible point; no cold staging')


def fit_candidate(problem, model, *, start, maximum_evaluations=600, x_scale='jac'):
    if type(maximum_evaluations) is not int or not 6 <= maximum_evaluations <= 600:
        raise ValueError('finite evaluation allowance in [6,600] required')
    if x_scale not in ('jac', 1.0):
        raise ValueError('only frozen column or unit scaling is supported')
    if start is None:
        raise ValueError('explicit saved feasible start required')
    point = np.array(start, dtype=float)
    if (point.shape != (len(problem.bounds.active),) or not np.all(np.isfinite(point))
            or np.any(abs(point) > 1)):
        raise ValueError('finite feasible start with matching parameter order required')
    problem.bounds.decode(point)
    calls = 0
    cache = best = None
    limit = maximum_evaluations - 2
    history = []
    monitor = StableStop()
    callback_point = None

    def evaluate(u, fresh=False):
        nonlocal calls, cache, best
        if not fresh and cache is not None and np.array_equal(u, cache[0]):
            return cache[1:]
        if calls >= limit:
            raise EvaluationLimit('native tangent allowance exhausted')
        calls += 1
        residual, jac, boundaries = problem.residual_tangent(u, model)
        if not np.all(np.isfinite(residual)) or not np.all(np.isfinite(jac)):
            raise ValueError('nonfinite residual or tangent')
        cache = u.copy(), residual, jac, boundaries
        cost = float(residual @ residual)
        if best is None or cost < best[0]:
            best = cost, u.copy()
        return residual, jac, boundaries

    def callback(intermediate_result):
        nonlocal callback_point
        u = intermediate_result.x
        residual, jac, _ = evaluate(u)
        stop = monitor.observe(u, residual, jac)
        history.append(dict(evaluations=calls, cost=float(residual @ residual),
                            stationarity=monitor.stationarity,
                            relative_cost_change=monitor.cost_change,
                            relative_residual_step=monitor.residual_step))
        if stop:
            callback_point = u.copy()
            raise StopIteration

    success = False
    message = 'not started'
    initial_residual, _, _ = evaluate(point)
    initial_cost = float(initial_residual @ initial_residual)
    try:
        solution = least_squares(lambda u: evaluate(u)[0], point,
                                jac=lambda u: evaluate(u)[1], bounds=(-1., 1.),
                                x_scale=x_scale, ftol=None, xtol=1e-11, gtol=1e-14,
                                max_nfev=limit - calls, callback=callback)
        success = bool(solution.success)
        message = str(solution.message)
    except EvaluationLimit as error:
        message = str(error)
    point = best[1].copy()
    limit = maximum_evaluations
    residual, jac, boundaries = evaluate(point, fresh=True)
    stationarity, gradient, projected, scaled = projected_stationarity(point, residual, jac)
    probe = verify_stability(point, residual, jac, evaluate)
    stable_callbacks = (callback_point is not None and np.array_equal(point, callback_point)
                        and monitor.streak >= 3)
    stable = bool(probe['passed'] or stable_callbacks)
    converged = bool(stable and stationarity <= POLICY['stationarity_tolerance'])
    singular = np.linalg.svd(jac, compute_uv=False)
    return dict(version=VERSION, model=model, parameters=problem.bounds.decode(point),
                normalized_parameters=point.tolist(), active_parameters=list(problem.bounds.active),
                residual_sum_squares=float(residual @ residual), initial_cost=initial_cost,
                evaluations=calls, maximum_evaluations=maximum_evaluations,
                initialization_evaluations=0, initialization_message='saved-point continuation',
                solver_reported_success=success, converged=converged, message=message,
                stopping_rule_verified=converged, stability_verified=stable,
                stability_probe=probe, accepted_step_history=history,
                stable_accepted_iterations=monitor.streak, full_stage_x_scale=x_scale,
                termination=('fresh_bounded_stability' if probe['passed'] else
                             'three_stable_callbacks' if converged else 'unresolved'),
                exact_projected_gradient_relative=stationarity, stationarity_tolerance=1e-4,
                gradient=gradient.tolist(), projected_gradient=projected.tolist(),
                scaled_projected_gradient=scaled.tolist(), singular_values=singular.tolist(),
                active_bounds=[name for name, u in zip(problem.bounds.active, point) if abs(u) >= .999],
                gps_epochs_at_packet_boundaries=boundaries,
                constant_bias_is_measured_drift=False, scientific_eligible=False,
                scientific_decision='abstain', calibration_bounds_supported=False,
                processing_independence_established=False, receiver_covariance_calibrated=False,
                clock_independently_established=False)
