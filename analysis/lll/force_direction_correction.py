# SPDX-License-Identifier: AGPL-3.0-or-later
"""Box-constrained correction of profiled direction fits using exact tangents."""

from .gyro_force_tangent import box_project_gradient


def correct_direction_fit(evaluate, start, *, maximum_calls):
    import numpy as np
    from scipy.optimize import lsq_linear

    point = np.asarray(start, float).copy()
    if (point.ndim != 1 or not len(point) or not np.isfinite(point).all() or np.any(abs(point) > 1.)
            or type(maximum_calls) is not int or not 1 <= maximum_calls <= 6):
        raise ValueError('explicit feasible start and finite exact evaluation cap required')

    def checked(at):
        residual, derivative, aligned = (np.asarray(x, float) for x in evaluate(at))
        if (residual.ndim != 2 or residual.shape[1] != 3 or aligned.shape != residual.shape
                or derivative.shape != (*residual.shape, len(at))
                or any(not np.isfinite(x).all() for x in (residual, derivative, aligned))):
            raise ValueError('complete finite direction residual and calibration tangent required')
        loss = float(np.sum(residual**2)/len(residual))
        gradient = 2*np.einsum('ni,nij->j', residual, derivative)/len(residual)
        return loss, box_project_gradient(at, gradient), residual, derivative, aligned

    loss, projected, residual, derivative, aligned = checked(point)
    history = [dict(evaluation=1, accepted=True, loss=loss, exact_projected_gradient=projected)]
    radius = .25
    reason = 'exact evaluation allowance exhausted'
    for evaluation in range(2, maximum_calls+1):
        if projected <= 1e-10:
            break
        rot = np.cross(np.eye(3)[None, :, :], aligned[:, None, :]).transpose(0, 2, 1).reshape(-1, 3)
        q, r = np.linalg.qr(rot, mode='reduced')
        if np.linalg.matrix_rank(r) != 3:
            reason = 'starting rotation tangent is rank deficient'
            break
        jac = derivative.reshape(-1, len(point))
        flat = residual.ravel()
        jac, flat = jac-q @ (q.T @ jac), flat-q @ (q.T @ flat)
        trial = lsq_linear(jac, -flat, bounds=(np.maximum(-radius, -1.-point), np.minimum(radius, 1.-point)),
                           method='bvls', tol=1e-12, max_iter=100)
        candidate = np.clip(point+trial.x, -1., 1.)
        candidate[abs(candidate) >= 1.-1e-12] = np.sign(candidate[abs(candidate) >= 1.-1e-12])
        if not trial.success or np.array_equal(point, candidate):
            reason = 'bounded linear correction unavailable'
            break
        new_loss, new_projected, *new_state = checked(candidate)
        accepted = new_loss < loss
        history.append(dict(evaluation=evaluation, accepted=accepted, loss=new_loss,
                            exact_projected_gradient=new_projected, radius=radius))
        if accepted:
            point, loss, projected = candidate, new_loss, new_projected
            residual, derivative, aligned = new_state
        else:
            radius *= .25
    converged = projected <= 1e-10
    return dict(converged=converged, reason='exact projected gradient passed' if converged else reason,
                normalized_calibration=point.tolist(), exact_training_loss=loss, exact_projected_gradient=projected,
                training_evaluations=len(history), step_history=history)
