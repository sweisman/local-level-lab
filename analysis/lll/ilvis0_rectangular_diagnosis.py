# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved affine-system diagnostics; no original reads or native predictions."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares, lsq_linear

from .ilvis0_solver_refinement import projected_stationarity

VERSION = 'ilvis0-saved-rectangular-diagnosis-v1'
SNAP_TOLERANCE = 1e-12
MAXIMUM_EVALUATIONS = 200


def load_linearization(directory, fit):
    name = fit['linearization_file']
    if Path(name).name != name or not name.endswith('.json.gz'):
        raise ValueError('invalid local tangent filename')
    content = (Path(directory)/name).read_bytes()
    if hashlib.sha256(content).hexdigest() != fit['linearization_sha256']:
        raise ValueError('local tangent hash mismatch')
    return json.loads(gzip.decompress(content))


def snap_bounds(point):
    snapped = np.array(point, dtype=float, copy=True)
    if snapped.ndim != 1 or not np.all(np.isfinite(snapped)) or np.any(abs(snapped) > 1):
        raise ValueError('finite feasible vector required')
    near = 1-abs(snapped) <= SNAP_TOLERANCE
    snapped[near] = np.sign(snapped[near])
    return snapped


def _validated(value):
    names = value['active_parameters']
    point = np.array(value['normalized_parameters'], dtype=float)
    residual = np.array(value['residual'], dtype=float)
    jac = np.array(value['jacobian'], dtype=float)
    if (not names or len(set(names)) != len(names)
            or value.get('convention') != 'whitened residual derivative by normalized parameter'
            or point.shape != (len(names),) or residual.ndim != 1
            or jac.shape != (len(residual), len(names)) or len(residual) < len(names)
            or not all(np.all(np.isfinite(x)) for x in (point, residual, jac))
            or np.any(abs(point) > 1)):
        raise ValueError('invalid saved linearization')
    return names, point, residual, jac


def _solve_affine(point, residual, jac, start):
    trace = []
    previous = None

    def evaluate(u):
        nonlocal previous
        r = residual+jac@(u-point)
        trace.append(dict(cost=float(r@r), parameter_step=(float(np.linalg.norm(u-previous))
                                                         if previous is not None else None)))
        previous = u.copy()
        return r

    result = least_squares(evaluate, start, jac=lambda u: jac, bounds=(-1., 1.),
                           method='dogbox', x_scale='jac', ftol=None, xtol=1e-11,
                           gtol=1e-14, max_nfev=MAXIMUM_EVALUATIONS)
    final = residual+jac@(result.x-point)
    stationarity = projected_stationarity(result.x, final, jac)[0]
    return dict(cost=float(final@final), stationarity=stationarity,
                stationarity_passed=bool(stationarity <= 1e-4),
                solver_reported_success=bool(result.success), evaluations=len(trace),
                message=str(result.message), last_parameter_step=trace[-1]['parameter_step'],
                displacement_from_saved=float(np.linalg.norm(result.x-point)))


def check_saved_gradient(value, gradient):
    _, _, residual, jac = _validated(value)
    gradient = np.array(gradient, dtype=float)
    if gradient.shape != (jac.shape[1],) or not np.all(np.isfinite(gradient)):
        raise ValueError('invalid saved gradient')
    # Component-relative comparison fails for nearly cancelling dot products.
    # Bound rounding error using operand norms and the dot-product length instead.
    scale = np.maximum(np.linalg.norm(jac, axis=0)*np.linalg.norm(residual), 1.)
    bound = 8*np.finfo(float).eps*len(residual)*scale
    if np.any(abs(jac.T@residual-gradient) > bound):
        raise ValueError('local gradient disagrees with saved fit')


def inspect_linearization(value):
    names, point, residual, jac = _validated(value)
    norms = np.linalg.norm(jac, axis=0)
    _, singular, right = np.linalg.svd(jac, full_matrices=False)
    cutoff = max(jac.shape)*np.finfo(float).eps*singular[0]
    rank = int(np.count_nonzero(singular > cutoff))
    vector = right[-1].copy()
    order = np.argsort(-abs(vector))
    if vector[order[0]] < 0:
        vector *= -1
    weak = [dict(parameter=names[i], coefficient=float(vector[i]), weight=float(vector[i]**2))
            for i in order[:5]]
    scaled = jac/np.where(norms > 0, norms, 1.)
    scaled_singular = np.linalg.svd(scaled, compute_uv=False)
    gram = scaled.T@scaled
    pairs = sorted(((abs(float(gram[i, k])), names[i], names[k], float(gram[i, k]))
                    for i in range(len(names)) for k in range(i+1, len(names))), reverse=True)
    gradient = jac.T@residual
    _, _, _, projected = projected_stationarity(point, residual, jac)
    dominant = int(np.argmax(abs(projected)))
    slack = 1-abs(point)
    near_outward = np.flatnonzero((slack > 0) & (slack <= SNAP_TOLERANCE)
                                  & (point*gradient < 0))
    snapped = snap_bounds(point)
    correction = lsq_linear(jac, -residual, bounds=(-1-point, 1-point),
                             method='bvls', tol=1e-10, max_iter=100)
    shifted = np.clip(point+correction.x, -1., 1.)
    predicted = residual+jac@(shifted-point)
    cost = float(residual@residual)
    predicted_cost = float(predicted@predicted)
    return dict(version=VERSION, rank=rank, columns=len(names), rows=len(residual),
                rank_cutoff=float(cutoff), condition=(float(singular[0]/singular[-1])
                                                     if rank == len(names) else None),
                column_normalized_condition=(float(scaled_singular[0]/scaled_singular[-1])
                                             if scaled_singular[-1] > 0 else None),
                column_norms=dict(zip(names, norms.tolist())), weakest_direction=weak,
                correlated_pairs=[dict(first=a, second=b, cosine=c) for _, a, b, c in pairs[:5]],
                dominant_gradient_parameter=names[dominant],
                dominant_gradient_ratio=float(abs(projected[dominant])/1e-4),
                near_outward_parameters=[names[i] for i in near_outward],
                near_outward_distances={names[i]: float(slack[i]) for i in near_outward},
                snap_maximum_change=float(np.max(abs(snapped-point))),
                original=_solve_affine(point, residual, jac, point),
                snapped=_solve_affine(point, residual, jac, snapped),
                reference=dict(success=bool(correction.success), cost=predicted_cost,
                               relative_cost_change=abs(cost-predicted_cost)/max(cost, predicted_cost, 1.),
                               relative_residual_step=float(np.linalg.norm(predicted-residual)
                                                            /max(np.linalg.norm(residual), 1.)),
                               normalized_step=float(np.linalg.norm(shifted-point))),
                native_predictions=0, observed_fit_starts=0, qualifies_archival_fit=False)
