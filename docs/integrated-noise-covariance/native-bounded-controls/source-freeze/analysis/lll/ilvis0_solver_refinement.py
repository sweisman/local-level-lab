# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate bounded solver experiment; the completed airborne fitter stays frozen."""
import numpy as np
from scipy.optimize import least_squares, lsq_linear

from .ilvis0_estimator import EvaluationLimit

VERSION = 'ilvis0-scaled-stable-stop-v1'
POLICY = dict(stationarity_tolerance=1e-4, relative_cost_tolerance=1e-8,
              relative_residual_step_tolerance=1e-6, stable_iterations=3,
              bound_projection_tolerance=1e-6, ftol=None, xtol=1e-11, gtol=1e-14,
              x_scale='jac', maximum_evaluations=200, diagnostic_reserve=2,
              initialization_maximum_evaluations=25, stability_probe_linear_tolerance=1e-10,
              stability_probe_linear_maximum_iterations=100)


def projected_stationarity(point, residual, jac):
    gradient = jac.T@residual
    projected = gradient.copy()
    projected[(point <= -1+1e-6)&(gradient > 0)] = 0.
    projected[(point >= 1-1e-6)&(gradient < 0)] = 0.
    scale = np.maximum(np.linalg.norm(jac, axis=0), 1.)*max(np.linalg.norm(residual), 1.)
    relative = projected/scale
    value = float(np.max(abs(relative))) if len(point) else 0.
    return value, gradient, projected, relative


class StableStop:
    """Three accepted measurement-space steps must be stable and stationary.

    Parameter motion in an almost-null direction need not become uniquely determined.
    Stability describes the predicted observations, not identification of calibration.
    """
    def __init__(self):
        self.previous = None
        self.streak = 0
        self.stationarity = float('inf')
        self.cost_change = None
        self.residual_step = None
        self.stable = False

    def observe(self, point, residual, jac):
        self.stationarity = projected_stationarity(point, residual, jac)[0]
        cost = float(residual@residual)
        self.stable = False
        if self.previous is not None:
            old_cost, old_residual = self.previous
            self.cost_change = abs(cost-old_cost)/max(cost, old_cost, 1.)
            self.residual_step = float(np.linalg.norm(residual-old_residual)/max(np.linalg.norm(residual), 1.))
            self.stable = (self.cost_change <= POLICY['relative_cost_tolerance'] and
                           self.residual_step <= POLICY['relative_residual_step_tolerance'])
        self.streak = self.streak+1 if self.stable and self.stationarity <= 1e-4 else 0
        self.previous = cost, residual.copy()
        return self.streak >= POLICY['stable_iterations']


def fit_candidate(problem, model, *, start=None, maximum_evaluations=200):
    """Count every tangent sweep, reserve final fresh tangent and two predictions.

    Ordinary xtol stopping also requires measured step/cost stability and the fresh
    projected-gradient check. An exhausted budget alone never establishes convergence.
    Initialization, feasible box and residual/Jacobian are unchanged from the baseline.
    """
    if not 4 <= maximum_evaluations <= 200:
        raise ValueError('finite evaluation allowance in [4,200] required')
    point = np.zeros(len(problem.bounds.active)) if start is None else np.array(start, float)
    problem.bounds.decode(point)
    calls = 0; cache = None; best = None; limit = maximum_evaluations-3

    def evaluate(u, fresh=False):
        nonlocal calls, cache, best
        if not fresh and cache is not None and np.array_equal(u, cache[0]):
            return cache[1:]
        if calls >= limit:
            raise EvaluationLimit('native tangent evaluation allowance exhausted')
        calls += 1
        residual, jac, boundaries = problem.residual_tangent(u, model)
        if not np.all(np.isfinite(residual)) or not np.all(np.isfinite(jac)):
            raise ValueError('nonfinite residual or tangent')
        cache = u.copy(), residual, jac, boundaries
        cost = float(residual@residual)
        if best is None or cost < best[0]:
            best = cost, u.copy()
        return residual, jac, boundaries

    staged = [i for i, name in enumerate(problem.bounds.active)
              if name.startswith(('attitude_', 'velocity_', 'position_', 'accel_gain_'))]
    stage_message = 'no staged parameters'; stage_calls = 0
    if staged and len(point) > len(staged) and maximum_evaluations >= 40:
        initial = point.copy(); end_stage = min(25, maximum_evaluations//5)
        def expand(x):
            full = initial.copy(); full[staged] = x; return full
        def stage_fun(x):
            if calls >= end_stage:
                raise EvaluationLimit('initialization stage complete')
            return evaluate(expand(x))[0]
        try:
            stage = least_squares(stage_fun, initial[staged],
                jac=lambda x: evaluate(expand(x))[1][:, staged], bounds=(-1., 1.),
                x_scale='jac', ftol=None, xtol=1e-11, gtol=1e-8,
                max_nfev=min(25, maximum_evaluations//5))
            stage_message = str(stage.message)
        except EvaluationLimit as error:
            stage_message = str(error)
        point = best[1].copy(); stage_calls = calls

    monitor = StableStop(); callback_stop = False; scipy_success = False; completed = False
    message = 'not started'; termination = 'unresolved'
    def callback(intermediate_result):
        nonlocal callback_stop
        residual, jac, _ = evaluate(intermediate_result.x)
        if monitor.observe(intermediate_result.x, residual, jac):
            callback_stop = True
            raise StopIteration
    try:
        residual, jac, _ = evaluate(point)
        monitor.observe(point, residual, jac)
        if calls >= limit:
            raise EvaluationLimit('native tangent evaluation allowance exhausted')
        solution = least_squares(lambda u: evaluate(u)[0], point,
            jac=lambda u: evaluate(u)[1], bounds=(-1., 1.), x_scale='jac',
            ftol=None, xtol=1e-11, gtol=1e-14, max_nfev=limit-calls,
            callback=callback)
        point = solution.x.copy(); scipy_success = bool(solution.success)
        completed = callback_stop or scipy_success
        message = 'scaled stationarity and three stable accepted steps' if callback_stop else str(solution.message)
        termination = 'scaled_stable_callback' if callback_stop else 'scipy_stop' if scipy_success else 'evaluation_limit'
    except EvaluationLimit as error:
        message = str(error); termination = 'evaluation_limit'
        if best is not None:
            point = best[1].copy()
    if best is None:
        raise ValueError('no finite candidate evaluation')
    # The fresh check must use the returned/stopping point, not a different best trial.
    limit = maximum_evaluations-2
    residual, jac, boundaries = evaluate(point, fresh=True)
    stationarity, gradient, projected, relative = projected_stationarity(point, residual, jac)
    _, singular, right = np.linalg.svd(jac, full_matrices=False)
    stable = bool(monitor.stable)
    probe = None
    if completed and not stable and stationarity <= 1e-4 and calls < maximum_evaluations-2:
        # An exact/redundant optimum can stop before three accepted steps exist.
        # Verify its bounded local least-squares correction with a real fresh sweep;
        # never accept merely because a linearized correction is predicted to be small.
        correction = lsq_linear(jac, -residual, bounds=(-1-point, 1-point),
                                tol=1e-10, max_iter=100)
        if correction.success and np.all(np.isfinite(correction.x)):
            shifted = np.clip(point+correction.x, -1., 1.)
            original_cost = float(residual@residual)
            checked, _, _ = evaluate(shifted, fresh=True)
            checked_cost = float(checked@checked)
            change = abs(checked_cost-original_cost)/max(checked_cost, original_cost, 1.)
            step = float(np.linalg.norm(checked-residual)/max(np.linalg.norm(residual), 1.))
            stable = change <= POLICY['relative_cost_tolerance'] and step <= POLICY['relative_residual_step_tolerance']
            probe = dict(relative_cost_change=change, relative_residual_step=step,
                         normalized_parameter_step=correction.x.tolist(), successful=bool(stable))
    converged = bool(completed and stable and stationarity <= 1e-4)
    return dict(version=VERSION, model=model, parameters=problem.bounds.decode(point),
        normalized_parameters=point.tolist(), active_parameters=list(problem.bounds.active),
        residual_sum_squares=float(residual@residual), evaluations=calls,
        maximum_evaluations=maximum_evaluations, initialization_evaluations=stage_calls,
        initialization_message=stage_message, solver_reported_success=scipy_success,
        stopping_rule_verified=completed, termination=termination, message=message,
        converged=converged, exact_projected_gradient_relative=stationarity,
        stationarity_tolerance=1e-4, stability_verified=stable,
        stable_accepted_iterations=monitor.streak, relative_cost_change=monitor.cost_change,
        relative_residual_step=monitor.residual_step, stability_probe=probe, gradient=gradient.tolist(),
        projected_gradient=projected.tolist(), scaled_projected_gradient=relative.tolist(),
        singular_values=singular.tolist(), right_singular_vectors=right.tolist(),
        active_bounds=[name for name, u in zip(problem.bounds.active, point) if abs(u) >= .999],
        active_bound_signs={name: 'upper' if u > 0 else 'lower'
                           for name, u in zip(problem.bounds.active, point) if abs(u) >= .999},
        gps_epochs_at_packet_boundaries=boundaries, derivative_method='forward automatic differentiation, 27 tangent lanes',
        latency_derivative_convention='left interval at a packet boundary; adjacent measured rates may differ',
        constant_bias_is_measured_drift=False, scientific_eligible=False, scientific_decision='abstain',
        calibration_bounds_supported=False, processing_independence_established=False,
        receiver_covariance_calibrated=False, clock_independently_established=False)
