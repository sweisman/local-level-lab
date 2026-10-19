# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved affine diagnostics; never evaluates an IMU trajectory or changes a fit."""
import numpy as np
from scipy.optimize import lsq_linear

VERSION = 'ilvis0-horizontal-correction-audit-v1'
RADIUS = .001
RIDGE = 1e-6


def audit(row):
    fit = row['fit']
    point = np.asarray(fit['normalized_parameters'], float)
    names = fit['active_parameters']
    saved = fit['local_linearization']
    residual = np.asarray(saved['residual'], float)
    jac = np.asarray(saved['jacobian'], float)
    if (point.ndim != 1 or not len(point) or len(names) != len(point)
            or residual.ndim != 1 or not len(residual)
            or jac.shape != (len(residual), len(point))
            or np.any(abs(point) > 1)
            or any(not np.all(np.isfinite(v)) for v in (point, residual, jac))):
        raise ValueError('finite feasible full-column saved system required')
    if saved.get('active_parameters', names) != names:
        raise ValueError('saved parameter order mismatch')
    if not np.array_equal(saved.get('normalized_parameters', point), point):
        raise ValueError('saved endpoint mismatch')
    singular = np.linalg.svd(jac, compute_uv=False)
    cutoff = max(jac.shape) * np.finfo(float).eps * singular[0]
    lower = np.maximum(-1-point, -RADIUS)
    upper = np.minimum(1-point, RADIUS)
    scale = np.maximum(np.linalg.norm(jac, axis=0), 1.)
    initial = float(residual @ residual)
    corrections = []
    for method in ('original', 'column_scaled', 'scaled_ridge'):
        factors = np.ones(len(point)) if method == 'original' else scale
        matrix = jac / factors
        right = -residual
        if method == 'scaled_ridge':
            matrix = np.vstack((matrix, np.sqrt(RIDGE)*np.eye(len(point))))
            right = np.r_[right, np.zeros(len(point))]
        solved = lsq_linear(matrix, right, bounds=(lower*factors, upper*factors),
                            method='bvls', tol=1e-10, max_iter=100)
        step = solved.x / factors
        linear = residual + jac @ step
        cost = float(linear @ linear)
        corrections.append(dict(method=method, solver_success=bool(solved.success),
            solver_status=int(solved.status), step=step.tolist(), affine_cost=cost,
            affine_not_worse_than_zero=bool(cost <= initial+1e-24),
            predicted_reduction=initial-cost,
            maximum_normalized_step=float(np.max(abs(step))),
            feasible=bool(np.all(point+step >= -1) and np.all(point+step <= 1)
                          and np.all(abs(step) <= RADIUS+1e-15)),
            largest_steps=[dict(parameter=names[i],step=float(step[i]))
                           for i in np.argsort(abs(step))[::-1][:5]],
            ridge_penalty=RIDGE if method=='scaled_ridge' else 0.))
    probe = fit.get('stability_probe') or {}
    return dict(identity=row['identity'], version=VERSION, columns=len(point),
        numerical_rank=int(np.sum(singular>cutoff)), rank_cutoff=float(cutoff),
        singular_values=singular.tolist(), endpoint_cost=initial,
        endpoint_stationarity=fit.get('exact_projected_gradient_relative'),
        original_fit_passed=bool(row['passed']),
        saved_probe_passed=probe.get('passed'),
        saved_probe_actual_cost_change=probe.get('actual_cost_change'),
        saved_probe_fresh_stationarity=probe.get('fresh_stationarity'),
        corrections=corrections, affine_solves=3, native_evaluations=0,
        scientific_decision='abstain', nonlinear_improvement_tested=False)
