# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact midpoint gyro transport and its calibration derivatives."""

from .esa_gyro_force_direction import midpoint_attitudes


def _left_exp_tangent(rotvec, directions):
    import numpy as np

    squared = np.sum(rotvec**2, axis=1)
    angle = np.sqrt(squared)
    # Taylor evaluation avoids cancellation in (theta - sin(theta)).
    quadratic = np.empty_like(angle)
    cubic = np.empty_like(angle)
    small = angle < .01
    a = squared[small]
    quadratic[small] = .5-a/24.+a*a/720.-a*a*a/40320.
    cubic[small] = 1./6.-a/120.+a*a/5040.-a*a*a/362880.
    a = angle[~small]
    quadratic[~small] = .5*np.sinc(a/(2*np.pi))**2
    cubic[~small] = (a-np.sin(a))/(a*a*a)
    cross = np.cross(rotvec[:, None, :], directions)
    return directions + quadratic[:, None, None]*cross + cubic[:, None, None]*np.cross(rotvec[:, None, :], cross)


def corrected_transport(theta, force, dt, point, limits):
    """Map each corrected force into the initial sensor frame with a 12-axis tangent."""
    import numpy as np
    from scipy.spatial.transform import Rotation

    theta, force, dt, point, scales = (np.asarray(v, float) for v in (theta, force, dt, point, limits))
    if (dt.ndim != 1 or not len(dt) or theta.shape != (len(dt), 3) or force.shape != theta.shape
            or point.shape != (12,) or scales.shape != (4, 3)
            or any(not np.isfinite(v).all() for v in (theta, force, dt, point, scales))
            or np.any(dt <= 0.) or np.any(abs(point) > 1.) or np.any(scales <= 0.)
            or np.any(scales[[1, 3]] >= 1.)):
        raise ValueError('finite packet arrays and twelve bounded calibration coordinates required')
    ab, ag, gb, gg = scales
    accel_gain = 1.+point[3:6]*ag
    gyro_gain = 1.+point[9:]*gg
    body_force = (force-point[:3]*ab)/accel_gain
    increments = (theta-dt[:, None]*(point[6:9]*gb))/gyro_gain
    midpoint = midpoint_attitudes(increments)
    before = midpoint*Rotation.from_rotvec(-increments/2.)
    matrix = midpoint.as_matrix()
    prefix = before.as_matrix()
    measured = midpoint.apply(body_force)
    dtheta = np.concatenate((-dt[:, None]*gb/gyro_gain, -increments*gg/gyro_gain), axis=1)
    delta = dtheta[:, :, None]*np.vstack((np.eye(3), np.eye(3)))

    full = np.einsum('nij,nkj->nki', prefix, _left_exp_tangent(increments, delta))
    half = np.einsum('nij,nkj->nki', prefix, _left_exp_tangent(increments/2., delta/2.))
    left = half
    left[1:] += np.cumsum(full[:-1], axis=0)
    gyro = np.cross(left, measured[:, None, :]).transpose(0, 2, 1)
    accel = [-matrix*(ab/accel_gain), -matrix*(body_force*ag/accel_gain)[:, None, :]]
    return measured, np.concatenate((*accel, gyro), axis=2)


def box_project_gradient(point, gradient):
    import numpy as np

    gradient = np.asarray(gradient, float).copy()
    gradient[(point <= -1.+1e-10) & (gradient > 0.)] = 0.
    gradient[(point >= 1.-1e-10) & (gradient < 0.)] = 0.
    return float(np.linalg.norm(gradient, ord=np.inf))


def weighted_force_tangent(packets, windows, point, limits):
    import numpy as np
    from .force_accel_calibration import normalize_with_tangent

    mapped, jac = corrected_transport(*packets, point, limits)
    values = np.asarray([weights @ mapped[sl] for sl, weights in windows])
    tangent = np.asarray([np.tensordot(weights, jac[sl], axes=1) for sl, weights in windows])
    return normalize_with_tangent(values, tangent)
