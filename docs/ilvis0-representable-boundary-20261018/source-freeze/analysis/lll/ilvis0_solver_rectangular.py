# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate rectangular continuation candidate; preserve all completed freezes."""
import numpy as np
from scipy.optimize import least_squares

from .ilvis0_estimator import EvaluationLimit
from .ilvis0_solver_refinement import StableStop, projected_stationarity
from .ilvis0_solver_verified_stop import verify_stability

VERSION = 'ilvis0-rectangular-continuation-v1'
POLICY = dict(maximum_evaluations=600, fresh_check_reserve=2, method='dogbox',
              stationarity_tolerance=1e-4, relative_cost_tolerance=1e-8,
              relative_residual_step_tolerance=1e-6, stable_iterations=3,
              ftol=None, xtol=1e-11, gtol=1e-14, x_scale='jac',
              initialization='explicit saved feasible point; no cold staging',
              acceptance='fresh bounded stability probe required; callbacks alone insufficient')


def fit_candidate(problem, model, *, start, maximum_evaluations=600):
    if type(maximum_evaluations) is not int or not 6 <= maximum_evaluations <= 600:
        raise ValueError('finite evaluation allowance in [6,600] required')
    point = np.array(start, dtype=float)
    if (point.shape != (len(problem.bounds.active),) or not np.all(np.isfinite(point))
            or np.any(abs(point) > 1)):
        raise ValueError('explicit finite feasible start required')
    problem.bounds.decode(point)
    calls = 0
    cache = best = previous_evaluation = previous_callback = None
    limit = maximum_evaluations - 2
    monitor = StableStop()
    history, trace = [], []

    def evaluate(u, fresh=False):
        nonlocal calls, cache, best, previous_evaluation
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
        improves = best is None or cost < best[0]
        trace.append(dict(evaluation=calls, cost=cost, fresh=bool(fresh),
                          normalized_step_norm=(float(np.linalg.norm(u-previous_evaluation))
                                                if previous_evaluation is not None else None),
                          improves_best_cost=improves))
        previous_evaluation = u.copy()
        if improves:
            best = cost, u.copy()
        return residual, jac, boundaries

    def callback(intermediate_result):
        nonlocal previous_callback
        u = intermediate_result.x
        residual, jac, _ = evaluate(u)
        cost = float(residual @ residual)
        # SciPy callbacks can include unchanged points after rejected steps.
        # Such callbacks are not three independent accepted improvements.
        accepted = (previous_callback is None or
                    not np.array_equal(u, previous_callback[0]) and cost < previous_callback[1])
        stop = monitor.observe(u, residual, jac) if accepted else False
        if accepted:
            previous_callback = u.copy(), cost
        history.append(dict(evaluations=calls, cost=cost, accepted_improvement=accepted,
                            stationarity=projected_stationarity(u, residual, jac)[0],
                            relative_cost_change=monitor.cost_change,
                            relative_residual_step=monitor.residual_step))
        if stop:
            raise StopIteration

    success = False
    message = 'not started'
    initial_residual, _, _ = evaluate(point)
    initial_cost = float(initial_residual @ initial_residual)
    previous_callback = point.copy(), initial_cost
    monitor.observe(point, initial_residual, cache[2])
    try:
        solution = least_squares(lambda u: evaluate(u)[0], point,
                                jac=lambda u: evaluate(u)[1], bounds=(-1., 1.),
                                method='dogbox', x_scale='jac', ftol=None,
                                xtol=1e-11, gtol=1e-14,
                                max_nfev=limit-calls, callback=callback)
        success, message = bool(solution.success), str(solution.message)
    except EvaluationLimit as error:
        message = str(error)
    point = best[1].copy()
    limit = maximum_evaluations
    residual, jac, boundaries = evaluate(point, fresh=True)
    stationarity, gradient, projected, scaled = projected_stationarity(point, residual, jac)
    probe = verify_stability(point, residual, jac, evaluate)
    converged = bool(probe['passed'] and stationarity <= 1e-4)
    return dict(version=VERSION, model=model, parameters=problem.bounds.decode(point),
                normalized_parameters=point.tolist(), active_parameters=list(problem.bounds.active),
                residual_sum_squares=float(residual @ residual), initial_cost=initial_cost,
                evaluations=calls, maximum_evaluations=maximum_evaluations,
                initialization_evaluations=0, initialization_message='saved-point continuation',
                solver_reported_success=success, converged=converged, message=message,
                stopping_rule_verified=converged, stability_verified=bool(probe['passed']),
                stability_probe=probe, accepted_step_history=history, evaluation_trace=trace,
                stable_accepted_iterations=monitor.streak, full_stage_x_scale='jac',
                termination='fresh_bounded_stability' if converged else 'unresolved',
                exact_projected_gradient_relative=stationarity, stationarity_tolerance=1e-4,
                gradient=gradient.tolist(), projected_gradient=projected.tolist(),
                scaled_projected_gradient=scaled.tolist(),
                singular_values=np.linalg.svd(jac, compute_uv=False).tolist(),
                local_linearization=dict(active_parameters=list(problem.bounds.active),
                                         normalized_parameters=point.tolist(),
                                         residual=residual.tolist(), jacobian=jac.tolist(),
                                         convention='whitened residual derivative by normalized parameter'),
                active_bounds=[name for name, u in zip(problem.bounds.active, point) if abs(u) >= .999],
                gps_epochs_at_packet_boundaries=boundaries,
                constant_bias_is_measured_drift=False, scientific_eligible=False,
                scientific_decision='abstain', calibration_bounds_supported=False,
                processing_independence_established=False, receiver_covariance_calibrated=False,
                clock_independently_established=False)
