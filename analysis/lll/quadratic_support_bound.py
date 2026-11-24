# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bracket a linear objective subject to simultaneous Euclidean norm caps."""

import math

import numpy as np
from scipy.linalg import cho_factor, cho_solve, solve_triangular
from scipy.optimize import Bounds, LinearConstraint, minimize


def solve_support(matrices, objective, coordinate_caps, *, max_iterations=120, multipliers=None):
    """Bracket max c @ x for ||M_i @ x|| <= 1.

    Coordinate caps are independently supplied bounds on every feasible x.
    They bound any residual in the dual decomposition of the objective.
    Both ends of the bracket are checked in the original coordinates.
    Supplied multipliers replay the decomposition without optimization.
    """
    objective = np.asarray(objective, dtype=float)
    if objective.ndim != 1 or not len(objective) or not np.isfinite(objective).all():
        raise ValueError('a finite objective vector is required')
    size = len(objective)
    caps = np.broadcast_to(np.asarray(coordinate_caps, dtype=float), objective.shape)
    matrices = tuple(np.asarray(matrix, dtype=float) for matrix in matrices)
    if (not matrices or not np.all(np.isfinite(caps) & (caps > 0))
            or any(m.ndim != 2 or m.shape[1] != size or not m.shape[0] or not np.isfinite(m).all()
                   for m in matrices)
            or type(max_iterations) is not int or max_iterations < 1):
        raise ValueError('complete norm constraints, positive coordinate caps and finite iterations required')
    triangular = np.linalg.qr(np.vstack(matrices), mode='r')
    epsilon = np.finfo(float).eps
    if (triangular.shape != (size, size)
            or np.min(abs(np.diag(triangular))) <= size*epsilon*np.linalg.norm(triangular, ord=np.inf)):
        raise ValueError('the norms must jointly constrain every objective coordinate')
    target = solve_triangular(triangular.T, objective, lower=True)
    scale = np.linalg.norm(target)
    uniform = np.full(len(matrices), 1./len(matrices))
    if not scale:
        return dict(point=np.zeros(size), lower=0., upper=0., multipliers=uniform,
                    optimizer_status=0, iterations=0, norm_terms=np.zeros(len(matrices)),
                    residual_by_coordinate=np.zeros(size))

    target /= scale
    single = np.array([matrix.shape[0] == 1 for matrix in matrices])
    multi = ~single
    grams = np.empty((int(multi.sum()), size, size))
    single_rows = np.empty((int(single.sum()), size))
    dense_index = row_index = 0
    for matrix, one_row in zip(matrices, single, strict=True):
        normalized = solve_triangular(triangular.T, matrix.T, lower=True)
        if one_row:
            single_rows[row_index] = normalized[:, 0]
            row_index += 1
        else:
            grams[dense_index] = normalized@normalized.T
            dense_index += 1

    def normal_solution(weights):
        combined = (np.tensordot(weights[multi], grams, axes=1)
                    + single_rows.T@(weights[single, None]*single_rows))
        return cho_solve(cho_factor(combined, check_finite=False), target, check_finite=False)

    def dual_objective(weights):
        direction = normal_solution(weights)
        gradient = np.empty_like(weights)
        gradient[multi] = -(grams@direction)@direction
        gradient[single] = -(single_rows@direction)**2
        return float(target@direction), gradient

    # Positive multipliers keep the combined system solvable even if a
    # single constraint controls the objective while leaving some axes free.
    if multipliers is None:
        outcome = minimize(dual_objective, uniform, jac=True, method='SLSQP',
                           bounds=Bounds(1e-8/len(matrices), 1.),
                           constraints=[LinearConstraint(np.ones(len(matrices)), 1., 1.)],
                           options=dict(maxiter=max_iterations, ftol=1e-12))
        multipliers = np.maximum(outcome.x, 1e-8/len(matrices))
        multipliers /= multipliers.sum()
        status, iterations = int(outcome.status), int(outcome.nit)
    else:
        multipliers = np.asarray(multipliers, dtype=float)
        if (multipliers.shape != uniform.shape or not np.isfinite(multipliers).all()
                or np.any(multipliers <= 0) or not math.isclose(float(multipliers.sum()), 1., rel_tol=1e-12)):
            raise ValueError('the original positive normalized multipliers are required')
        status, iterations = None, 0
    direction = scale*solve_triangular(triangular, normal_solution(multipliers))
    groups = [matrix@direction for matrix in matrices]
    rounding = 8*epsilon*(size+sum(matrix.shape[0] for matrix in matrices)+len(matrices))
    point = direction/(max(np.linalg.norm(group) for group in groups)*(1+rounding))
    if not all(np.linalg.norm(matrix@point) <= 1. for matrix in matrices):
        raise ValueError('returned point failed the original norm caps')
    dual_groups = [weight*group for weight, group in zip(multipliers, groups, strict=True)]
    represented = sum(matrix.T@group for matrix, group in zip(matrices, dual_groups, strict=True))
    absolute_products = sum(abs(matrix).T@abs(group) for matrix, group in zip(matrices, dual_groups, strict=True))
    remainder = abs(objective-represented)+rounding*(abs(objective)+absolute_products)
    # Decompose c into transposed constraint maps plus a bounded residual.
    # This inequality holds for any returned multipliers, even on an early stop.
    norm_terms = np.array([np.linalg.norm(group)*(1+rounding) for group in dual_groups])
    upper = math.fsum(norm_terms)+float(caps@remainder)
    lower = float(objective@point-rounding*(abs(objective)@abs(point)))
    if not 0 <= lower <= upper < math.inf:
        raise ValueError('the verified support bracket is invalid')
    return dict(point=point, lower=lower, upper=upper, multipliers=multipliers,
                optimizer_status=status, iterations=iterations,
                norm_terms=norm_terms, residual_by_coordinate=remainder)
