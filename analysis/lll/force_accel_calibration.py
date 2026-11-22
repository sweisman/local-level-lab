# SPDX-License-Identifier: AGPL-3.0-or-later
"""Profile a common rotation while fitting bounded accelerometer calibration."""

from .esa_gyro_force_direction import angles
from .force_direction_alignment import fit_unit_rotation, unit_vectors


def corrected_directions(channels, axes, point, bias_limit, gain_limit):
    """Return normalized forces and derivatives in normalized box coordinates."""
    import numpy as np

    bias = np.asarray(point[:3])*bias_limit
    gain = 1.+np.asarray(point[3:])*gain_limit
    corrected = (channels-axes*bias)/gain
    vector = corrected.sum(axis=2)
    db = -axes*(bias_limit/gain)
    dg = -corrected*(gain_limit/gain)
    return normalize_with_tangent(vector, np.concatenate((db, dg), axis=2))


def normalize_with_tangent(vector, jac):
    import numpy as np

    u = unit_vectors(vector)
    jac = jac.copy()
    jac -= u[:, :, None]*np.einsum('ni,nij->nj', u, jac)[:, None, :]
    jac /= np.linalg.norm(vector, axis=1)[:, None, None]
    return u, jac


def objective(point, target, channels, axes, bias_limit, gain_limit):
    """Use the derivative at the optimal rotation without differentiating the SVD."""
    measured, jac = corrected_directions(channels, axes, point, bias_limit, gain_limit)
    return profiled_loss(target, measured, jac)


def profiled_loss(target, measured, jac):
    import numpy as np

    _, rotation = fit_unit_rotation(target, measured)
    if rotation is None:
        raise ValueError('starting rotation numerically unidentified')
    residual = measured-target @ rotation.T
    return (float(np.mean(np.sum(residual**2, axis=1))),
            2*np.einsum('ni,nij->j', residual, jac)/len(target), rotation, measured, jac)


def _projected_singular_values(measured, jac):
    import numpy as np

    rotation_columns = np.cross(np.eye(3)[None, :, :], measured[:, None, :]).transpose(0, 2, 1).reshape(-1, 3)
    calibration = jac.reshape(-1, jac.shape[-1])
    response = np.linalg.lstsq(rotation_columns, calibration, rcond=None)[0]
    return np.linalg.svd(calibration-rotation_columns@response, compute_uv=False)


def bounded_profile(propose, start, max_calls):
    import numpy as np
    from scipy.optimize import minimize

    calls = 0
    best = None

    class EvaluationLimit(Exception):
        pass

    def evaluate(point):
        nonlocal calls, best
        if calls >= max_calls:
            raise EvaluationLimit
        calls += 1
        loss, gradient, rotation, measured, jac = propose(point)
        if best is None or loss < best['loss']:
            best = dict(loss=loss, gradient=gradient, rotation=rotation, point=point.copy(), measured=measured, jac=jac)
        return loss*1e6, gradient*1e6

    try:
        solved = minimize(evaluate, start, jac=True, method='L-BFGS-B', bounds=[(-1., 1.)]*len(start),
                          options=dict(maxfun=max_calls, maxiter=max_calls, ftol=0., gtol=1e-9))
        reason = str(solved.message)
        optimizer_success = bool(solved.success)
    except EvaluationLimit:
        reason, optimizer_success = 'training evaluation allowance exhausted', False
    except ValueError as error:
        return dict(passed=False, reason=str(error), training_evaluations=calls), None
    point = best['point']
    gradient = best['gradient'].copy()
    gradient[(point <= -1.+1e-10) & (gradient > 0.)] = 0.
    gradient[(point >= 1.-1e-10) & (gradient < 0.)] = 0.
    projected = float(np.linalg.norm(gradient, ord=np.inf))
    disposition = dict(passed=projected <= 1e-10, reason=reason, optimizer_success=optimizer_success,
                       training_evaluations=calls, maximum_box_projected_gradient=projected)
    return disposition, best


def fit_calibration(reference, channels, axes, *, training, bias_limit, gain_limit, start, max_calls):
    import numpy as np

    target = unit_vectors(reference)
    channels, axes, start, bias_limit, gain_limit = (np.asarray(v, float) for v in (
        channels, axes, start, bias_limit, gain_limit))
    if (channels.shape != (len(target), 3, 3) or axes.shape != channels.shape
            or not np.isfinite([channels, axes]).all() or type(training) is not int or not 3 <= training < len(target)
            or start.shape != (6,) or not np.isfinite(start).all() or np.any(abs(start) > 1.)
            or bias_limit.shape != (3,) or gain_limit.shape != (3,)
            or not np.isfinite([bias_limit, gain_limit]).all() or np.any(bias_limit <= 0.)
            or np.any(gain_limit <= 0.) or np.any(gain_limit >= 1.)
            or type(max_calls) is not int or not 2 <= max_calls <= 200):
        raise ValueError('finite calibrated force bases and bounded earlier fit required')

    def propose(point):
        return objective(point, target[:training], channels[:training], axes[:training], bias_limit, gain_limit)

    disposition, best = bounded_profile(propose, start, max_calls)
    if best is None:
        return disposition
    point = best['point']
    future, _ = corrected_directions(channels[training:], axes[training:], point, bias_limit, gain_limit)
    errors = np.rad2deg(angles(target[training:] @ best['rotation'].T, future))
    singular = _projected_singular_values(best['measured'], best['jac'])
    return disposition | dict(
        normalized_calibration=point.tolist(), bias_mps2=(point[:3]*bias_limit).tolist(),
        gain=(point[3:]*gain_limit).tolist(), starting_rotation=best['rotation'].tolist(),
        training_mean_squared_chord=best['loss'], calibration_singular_values=singular.tolist(),
        calibration_rank=int(np.sum(singular > 1e-8*singular[0])),
        later_error_deg=errors.tolist(), later_rms_deg=float(np.sqrt(np.mean(errors*errors))))
