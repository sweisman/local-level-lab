# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate bounded Gauss–Newton candidate; no changes to frozen estimators."""
import numpy as np
from scipy.optimize import lsq_linear

from .ilvis0_estimator import EvaluationLimit
from .ilvis0_solver_refinement import POLICY as STOPPING, projected_stationarity
from .ilvis0_solver_verified_stop import verify_stability

VERSION = 'ilvis0-boundary-bvls-v1'
POLICY = dict(maximum_evaluations=600, fresh_check_reserve=2,
              boundary_snap_tolerance=1e-12, maximum_backtracks=24,
              linear_tolerance=1e-10, linear_maximum_iterations=100,
              step_method='bounded linear least squares; actual-cost backtracking',
              acceptance='unchanged fresh stationarity and bounded stability checks')


def snap_bounds(point):
    """Copy a feasible point, removing only roundoff-sized boundary slack."""
    snapped = np.array(point, dtype=float, copy=True)
    close = 1-abs(snapped) <= POLICY['boundary_snap_tolerance']
    snapped[close] = np.sign(snapped[close])
    return snapped


def fit_candidate(problem, model, *, start, maximum_evaluations=600):
    if type(maximum_evaluations) is not int or not 6 <= maximum_evaluations <= 600:
        raise ValueError('finite evaluation allowance in [6,600] required')
    original = np.array(start, dtype=float)
    if (original.shape != (len(problem.bounds.active),)
            or not np.all(np.isfinite(original)) or np.any(abs(original) > 1)):
        raise ValueError('explicit finite feasible start required')
    problem.bounds.decode(original)
    point = snap_bounds(original)
    calls = 0
    cache = None
    limit = maximum_evaluations-2
    trace, history = [], []

    def evaluate(u, fresh=False):
        nonlocal calls, cache
        problem.bounds.decode(u)
        if not fresh and cache is not None and np.array_equal(u, cache[0]):
            return cache[1:]
        if calls >= limit:
            raise EvaluationLimit('tangent allowance exhausted')
        calls += 1
        residual, jac, boundaries = problem.residual_tangent(u, model)
        residual, jac = np.asarray(residual, float), np.asarray(jac, float)
        if (residual.ndim != 1 or jac.shape != (residual.size, point.size)
                or not np.all(np.isfinite(residual)) or not np.all(np.isfinite(jac))):
            raise ValueError('invalid residual or tangent')
        cache = u.copy(), residual, jac, boundaries
        trace.append(dict(evaluation=calls, cost=float(residual@residual), fresh=bool(fresh)))
        return residual, jac, boundaries

    residual, jac, _ = evaluate(point)
    cost = initial_cost = float(residual@residual)
    message = 'evaluation allowance exhausted'
    try:
        while calls < limit:
            local = lsq_linear(jac, -residual, bounds=(-1-point, 1-point),
                               method='bvls', tol=POLICY['linear_tolerance'],
                               max_iter=POLICY['linear_maximum_iterations'])
            if not local.success or not np.all(np.isfinite(local.x)):
                message = 'bounded linear step unfinished'
                break
            correction = local.x
            predicted = residual+jac@correction
            predicted_cost = float(predicted@predicted)
            change = abs(predicted_cost-cost)/max(predicted_cost, cost, 1.)
            step = float(np.linalg.norm(predicted-residual)/max(np.linalg.norm(residual), 1.))
            if (change <= STOPPING['relative_cost_tolerance']
                    and step <= STOPPING['relative_residual_step_tolerance']):
                message = 'local correction small; fresh verification required'
                break
            accepted = False
            for backtrack in range(POLICY['maximum_backtracks']):
                fraction = 2.**(-backtrack)
                proposed = snap_bounds(np.clip(point+fraction*correction, -1., 1.))
                if np.array_equal(proposed, point):
                    break
                trial_residual, trial_jac, _ = evaluate(proposed)
                trial_cost = float(trial_residual@trial_residual)
                accepted = trial_cost <= cost
                history.append(dict(evaluation=calls, accepted=bool(accepted), cost=trial_cost,
                                    fraction=fraction, normalized_step=float(np.linalg.norm(proposed-point)),
                                    linear_optimality=float(local.optimality)))
                if accepted:
                    point, residual, jac, cost = proposed, trial_residual, trial_jac, trial_cost
                    break
            if not accepted:
                message = 'no decreasing feasible nonlinear step'
                break
    except EvaluationLimit as error:
        message = str(error)
    limit = maximum_evaluations
    residual, jac, boundaries = evaluate(point, fresh=True)
    stationarity, gradient, projected, scaled = projected_stationarity(point, residual, jac)
    probe = verify_stability(point, residual, jac, evaluate)
    converged = bool(probe['passed'] and stationarity <= STOPPING['stationarity_tolerance'])
    return dict(version=VERSION, model=model, parameters=problem.bounds.decode(point),
                normalized_parameters=point.tolist(), active_parameters=list(problem.bounds.active),
                residual_sum_squares=float(residual@residual), initial_cost=initial_cost,
                evaluations=calls, maximum_evaluations=maximum_evaluations,
                start_boundary_snap_maximum=float(np.max(abs(snap_bounds(original)-original), initial=0)),
                converged=converged, stopping_rule_verified=converged,
                stability_verified=bool(probe['passed']), stability_probe=probe,
                message=message, termination='fresh_bounded_stability' if converged else 'unresolved',
                step_history=history, evaluation_trace=trace,
                exact_projected_gradient_relative=stationarity,
                stationarity_tolerance=STOPPING['stationarity_tolerance'],
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
