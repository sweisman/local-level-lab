# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite SciPy bounded controls; original full stopping gate stays unchanged."""


def solve(problem, model, *, start, method, maximum_calls, reserve,
          physical_step, visits_per_call=1):
    import numpy as np
    from scipy.optimize import OptimizeResult, least_squares, minimize
    from .ilvis0_estimator import EvaluationLimit
    from .ilvis0_solver_position import verify_stability
    from .ilvis0_solver_refinement import POLICY as STOPPING, projected_stationarity

    if (method not in ('trf', 'dogbox', 'centered_lbfgsb', 'centered_scaled_lbfgsb') or type(maximum_calls) is not int
            or not 8 <= maximum_calls <= 200 or type(visits_per_call) is not int
            or visits_per_call < 1 or not callable(reserve)
            or not callable(physical_step)):
        raise ValueError('declared bounded method, finite allowance and callbacks required')
    original = np.asarray(start, float)
    if (original.ndim != 1 or len(original) != len(problem.bounds.active)
            or not np.all(np.isfinite(original)) or np.any(abs(original) > 1)):
        raise ValueError('finite feasible declared start required')
    point = np.clip(original, -1+1e-12, 1-1e-12)
    problem.bounds.decode(point)
    calls = 0
    cache = None
    trace = []

    def evaluate(u, fresh=False):
        nonlocal calls, cache
        u = np.asarray(u,float)
        problem.bounds.decode(u)
        if not fresh and cache is not None and np.array_equal(cache[0],u):
            return cache[1:]
        if calls >= maximum_calls:
            raise EvaluationLimit('independent bounded tangent allowance exhausted')
        reserve(native_calls=1, packet_visits=visits_per_call)
        calls += 1
        residual, jacobian, boundaries = problem.residual_tangent(u,model)
        residual = np.asarray(residual,float)
        jacobian = np.asarray(jacobian,float)
        if (residual.ndim != 1 or not len(residual)
                or jacobian.shape != (len(residual),len(u))
                or not np.all(np.isfinite(residual))
                or not np.all(np.isfinite(jacobian))):
            raise ValueError('complete finite native residual and derivative required')
        cache = (u.copy(), residual, jacobian, boundaries)
        trace.append(dict(evaluation=calls,cost=float(residual@residual),fresh=bool(fresh)))
        return residual,jacobian,boundaries

    if method in ('centered_lbfgsb', 'centered_scaled_lbfgsb'):
        initial, first_jacobian, _ = evaluate(point)
        scale = np.ones(len(point))
        if method == 'centered_scaled_lbfgsb':
            scale = column_scale(first_jacobian)
        best_cost = 0.
        best_point = point * scale
        best_gradient = 2*(first_jacobian.T @ initial) / scale

        def objective(z):
            nonlocal best_cost, best_point, best_gradient
            if calls >= maximum_calls-2:
                raise EvaluationLimit('centered objective allowance exhausted')
            u = np.clip(z / scale, -1., 1.)
            residual, jacobian, _ = evaluate(u)
            cost = float((residual-initial) @ (residual+initial))
            gradient = 2*(jacobian.T @ residual) / scale
            if cost < best_cost:
                best_cost, best_point, best_gradient = cost, z.copy(), gradient.copy()
            return cost, gradient

        try:
            result = minimize(objective, point*scale, method='L-BFGS-B', jac=True,
                bounds=list(zip(-scale, scale, strict=True)),
                options=dict(maxfun=maximum_calls-2, maxiter=maximum_calls-2, ftol=0., gtol=1e-12))
        except EvaluationLimit:
            result = OptimizeResult(x=best_point, jac=best_gradient, success=False, status=1,
                                    message='centered objective allowance exhausted', nfev=calls, njev=calls)
        scipy_optimality = float(np.linalg.norm(result.x-np.clip(result.x-result.jac, -scale, scale), np.inf))
        result.x = np.clip(result.x / scale, -1., 1.)
    else:
        result = least_squares(lambda u:evaluate(u)[0],point,
            jac=lambda u:evaluate(u)[1],bounds=(-1.,1.),method=method,
            max_nfev=maximum_calls-2,ftol=1e-12,xtol=1e-12,gtol=1e-12,
            x_scale='jac')
        scipy_optimality = float(result.optimality)
    residual,jacobian,_ = evaluate(result.x,fresh=True)
    probe = verify_stability(result.x,residual,jacobian,evaluate,physical_step)
    stationarity = projected_stationarity(result.x,residual,jacobian)[0]
    gate = bool(probe['passed'] and stationarity <= STOPPING['stationarity_tolerance'])
    return dict(version='independent-bounded-scipy-control-v1',method=method,
        point=result.x.tolist(),cost=float(residual@residual),
        initial_cost=trace[0]['cost'],scipy_success=bool(result.success),
        scipy_status=int(result.status),scipy_message=str(result.message),
        scipy_nfev=int(result.nfev),scipy_njev=int(result.njev),
        scipy_optimality=scipy_optimality,
        original_gate_passed=gate,original_stability_probe=probe,
        original_projected_stationarity=stationarity,
        native_calls_actual=calls,maximum_calls=maximum_calls,
        evaluation_trace=trace,scientific_decision='abstain')


def column_scale(jacobian):
    import numpy as np

    norms = np.linalg.norm(jacobian, axis=0)
    if not np.all(np.isfinite(norms)):
        raise ValueError('finite training column norms required')
    return np.maximum(norms, 1e-12*max(float(np.max(norms, initial=0.)), 1.))
