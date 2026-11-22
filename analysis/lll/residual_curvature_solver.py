# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research box-Newton solver with the unchanged fresh-position gate."""
import numpy as np
from scipy.optimize import lsq_linear

from .curved_step import residual_decrease
from .ilvis0_estimator import EvaluationLimit
from .ilvis0_solver_boundary import snap_bounds
from .ilvis0_solver_position import verify_stability


DIFFERENCE = 2.**-12
RADIUS = .5
BACKTRACKS = 8
ACCEPTANCE = .1
STRONG_RELATIVE = 1e-3


def difference_hessian(point, gradient, evaluate_gradient):
    """Estimate the half-cost Hessian from feasible gradient differences."""
    point = np.asarray(point, float)
    h = DIFFERENCE
    hessian = np.empty((len(point), len(point)))
    for axis, coordinate in enumerate(point):
        span = np.zeros_like(point)
        span[axis] = h
        if -1+h <= coordinate <= 1-h:
            column = (evaluate_gradient(point+span)-evaluate_gradient(point-span))/(2*h)
        else:
            sign = 1 if coordinate < 0 else -1
            first = evaluate_gradient(point+sign*span)
            second = evaluate_gradient(point+sign*2*span)
            column = sign*(-3*gradient+4*first-second)/(2*h)
        hessian[:, axis] = column
    return (hessian+hessian.T)/2


def weak_tangent_hessian(point, residual, jacobian, evaluate_tangent):
    """Add symmetric residual curvature on weak directions and their cross terms."""
    if len(residual) < len(point):
        return None
    _, values, vectors = np.linalg.svd(jacobian, full_matrices=False)
    if not len(values) or values[0] == 0:
        return None
    weak = vectors[values < STRONG_RELATIVE*values[0]].T
    if weak.shape[1] == 0:
        return None
    h = DIFFERENCE
    probes = []
    for direction in weak.T:
        plus, minus = point+h*direction, point-h*direction
        if np.all(abs(plus) <= 1) and np.all(abs(minus) <= 1):
            probes.append((plus, minus, 0))
        else:
            for sign in (1, -1):
                first, second = point+sign*h*direction, point+sign*2*h*direction
                if np.all(abs(first) <= 1) and np.all(abs(second) <= 1):
                    probes.append((first, second, sign))
                    break
            else:
                return None
    columns = []
    for first, second, sign in probes:
        a, b = evaluate_tangent(first), evaluate_tangent(second)
        change = a-b if not sign else sign*(4*(a-jacobian)-(b-jacobian))
        columns.append(change.T@residual/(2*h))
    curvature = np.column_stack(columns)
    mixed = curvature@weak.T
    projected = weak.T@curvature
    symmetric = mixed+mixed.T-weak@((projected+projected.T)/2)@weak.T
    return jacobian.T@jacobian+symmetric


def _bounded_least_squares(point, design, target):
    bounds = (np.maximum(-1-point, -RADIUS), np.minimum(1-point, RADIUS))
    fit = lsq_linear(design, target, bounds=bounds, method='bvls', tol=1e-10, max_iter=100)
    return fit.x if fit.success and np.isfinite(fit.x).all() else None


def bounded_step(point, gradient, hessian):
    """Solve the positive-curvature quadratic model within the box and radius."""
    eigenvalues, vectors = np.linalg.eigh(hessian)
    floor = 1e-12*max(float(np.max(abs(eigenvalues))), 1.)
    roots = np.sqrt(np.maximum(eigenvalues, floor))
    design = roots[:, None]*vectors.T
    target = -(vectors.T@gradient)/roots
    return _bounded_least_squares(point, design, target), design


def incremental_decrease(before, after, change):
    """Evaluate a measured residual increment formed before the large offset."""
    change = np.asarray(change, float)
    if change.shape != before.shape or not np.isfinite(change).all():
        raise ValueError('finite matching residual increment required')
    scale = np.maximum(1., np.maximum(np.maximum(abs(before), abs(after)), abs(change)))
    if np.any(abs((after-before)-change) > 32*np.finfo(float).eps*scale):
        raise ValueError('direct residual increment disagrees with rounded trials')
    return -float(change@(2*before+change))


def restore_strong_residual(point, trial, residual, jacobian):
    """Make one correction in the strongly constrained singular directions."""
    left, values, right = np.linalg.svd(jacobian, full_matrices=False)
    if not len(values) or values[0] == 0:
        return None
    keep = values >= STRONG_RELATIVE*values[0]
    if np.count_nonzero(keep) == len(point):
        return None
    correction = -(left[:, keep].T@residual/values[keep])@right[keep]
    lower, upper = np.maximum(-1., point-RADIUS), np.minimum(1., point+RADIUS)
    fractions = np.ones_like(correction)
    positive, negative = correction > 0, correction < 0
    fractions[positive] = (upper[positive]-trial[positive])/correction[positive]
    fractions[negative] = (lower[negative]-trial[negative])/correction[negative]
    fraction = min(1., float(np.min(fractions)))
    if fraction <= 0:
        return None
    restored = np.clip(snap_bounds(trial+fraction*correction), lower, upper)
    return None if np.array_equal(restored, trial) else restored


def residual_secant(step, residual, old_tangent, new_tangent):
    """Recover a symmetric rank-one residual curvature from two evaluated tangents."""
    change = (new_tangent-old_tangent).T@residual
    scale = np.linalg.norm(step)*np.linalg.norm(change)
    inner = float(step@change)
    if not np.isfinite(scale) or abs(inner) <= 1e-10*scale:
        return None
    return np.outer(change, change/inner)


def fit_candidate(problem, model, *, start, maximum_evaluations, physical_step, analytic_curvature=None,
                  residual_change=None, strong_restoration=False, weak_curvature=False,
                  secant_curvature=False, gauss_newton_fallback=False):
    if type(maximum_evaluations) is not int or not 5 <= maximum_evaluations <= 600:
        raise ValueError('finite curvature solver allowance in [5,600] required')
    if secant_curvature and (weak_curvature or analytic_curvature is not None):
        raise ValueError('one residual curvature method required')
    if gauss_newton_fallback and not secant_curvature:
        raise ValueError('Gauss–Newton fallback requires secant curvature')
    point = np.asarray(start, float)
    problem.bounds.decode(point)
    point = snap_bounds(point)
    used, limit = 0, maximum_evaluations-2
    history = []
    weak_estimates = 0
    secant, refreshed, secant_updates = None, False, 0
    fallback = False

    def evaluate(u, fresh=False):
        nonlocal used
        if used >= limit:
            raise EvaluationLimit('curvature evaluation allowance exhausted')
        problem.bounds.decode(u)
        used += 1
        residual, jac, edges = problem.residual_tangent(u, model)
        residual, jac = np.asarray(residual, float), np.asarray(jac, float)
        if (residual.ndim != 1 or jac.shape != (len(residual), len(point))
                or not np.isfinite(residual).all() or not np.isfinite(jac).all()):
            raise ValueError('finite residual and tangent required')
        return residual, jac, edges

    def evaluate_gradient(u):
        residual, jac, _ = evaluate(u)
        return jac.T@residual

    def measure_trial(trial, predicted, scale, *, restored=False):
        new_r, new_j, _ = evaluate(trial)
        rounded = residual_decrease(residual, new_r)
        reduction = (rounded if residual_change is None
                     else incremental_decrease(residual, new_r, residual_change(point, trial)))
        ratio = reduction/predicted
        accepted = reduction > 0 and ratio >= ACCEPTANCE
        row = dict(evaluation=used, fraction=scale, cost=float(new_r@new_r),
                   predicted_reduction=predicted, actual_reduction=reduction,
                   agreement_ratio=ratio, accepted=bool(accepted))
        if residual_change is not None:
            row['rounded_residual_reduction'] = rounded
        if restored:
            row['strong_restoration'] = True
        if fallback:
            row['direction'] = 'gauss_newton'
        history.append(row)
        return accepted, new_r, new_j

    residual, jac, _ = evaluate(point)
    message = 'curvature step cannot improve the measured cost'
    try:
        while used < limit:
            gradient = jac.T@residual
            if secant_curvature:
                hessian = jac.T@jac
                if secant is not None:
                    hessian += secant
            elif weak_curvature:
                hessian = weak_tangent_hessian(point, residual, jac, lambda u: evaluate(u)[1])
                if hessian is None:
                    hessian = difference_hessian(point, gradient, evaluate_gradient)
                else:
                    weak_estimates += 1
            elif analytic_curvature is None:
                hessian = difference_hessian(point, gradient, evaluate_gradient)
            else:
                hessian = jac.T@jac+analytic_curvature(point, residual)
            if not np.isfinite(hessian).all():
                raise ValueError('finite curvature model required')
            if fallback:
                design = jac
                direction = _bounded_least_squares(point, design, -residual)
            else:
                direction, design = bounded_step(point, gradient, hessian)
            if direction is None:
                message = 'bounded curvature model unfinished'
            accepted = False
            rebuilt = False
            scales = () if direction is None else (2.**-i for i in range(BACKTRACKS))
            for scale in scales:
                trial = snap_bounds(np.clip(point+scale*direction, -1., 1.))
                if np.array_equal(trial, point):
                    break
                step = trial-point
                linear = design@step
                predicted = -2*(gradient@step)-linear@linear
                if predicted <= 0:
                    continue
                accepted, new_r, new_j = measure_trial(trial, predicted, scale)
                if secant_curvature and not accepted and not refreshed and not fallback:
                    update = residual_secant(step, residual, jac, new_j)
                    if update is not None and (secant is None or not np.allclose(update, secant, atol=1e-12)):
                        secant, refreshed, rebuilt = update, True, True
                        secant_updates += 1
                        break
                if strong_restoration and not accepted:
                    restored = restore_strong_residual(point, trial, new_r, new_j)
                    if restored is not None:
                        trial = restored
                        accepted, new_r, new_j = measure_trial(trial, predicted, scale, restored=True)
                if accepted:
                    if secant_curvature:
                        if fallback:
                            secant = None
                        update = residual_secant(trial-point, new_r, jac, new_j)
                        if update is not None:
                            secant = update
                            secant_updates += 1
                        refreshed = False
                        fallback = False
                    point, residual, jac = trial, new_r, new_j
                    break
            if rebuilt:
                continue
            if not accepted:
                if gauss_newton_fallback and secant is not None and not fallback:
                    fallback = True
                    continue
                break
    except EvaluationLimit as error:
        message = str(error)

    limit = maximum_evaluations
    residual, jac, _ = evaluate(point, fresh=True)
    gate = verify_stability(point, residual, jac, evaluate, physical_step)
    return dict(normalized_parameters=point.tolist(), residual_sum_squares=float(residual@residual),
                evaluations=used, converged=gate['passed'], stability_probe=gate, step_history=history,
                analytic_curvature=analytic_curvature is not None, message=message,
                **({'weak_curvature_estimates': weak_estimates} if weak_curvature else {}),
                **({'secant_curvature_updates': secant_updates} if secant_curvature else {}),
                scientific_eligible=False, scientific_decision='abstain')
