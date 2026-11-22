# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shift a rigidly mounted accelerometer to another point on its platform."""


def lever_arm_acceleration(dt, increments, midpoint_attitudes, offset_m):
    """Return the interval-mean acceleration difference in the starting frame."""
    import numpy as np
    from scipy.spatial.transform import Rotation

    dt = np.asarray(dt, float)
    theta = np.asarray(increments, float)
    offset = np.asarray(offset_m, float)
    if (dt.ndim != 1 or len(dt) < 2 or np.any(dt <= 0.) or not np.isfinite(dt).all()
            or theta.shape != (len(dt), 3) or not np.isfinite(theta).all()
            or offset.shape != (3,) or not np.isfinite(offset).all()
            or len(midpoint_attitudes) != len(dt)):
        raise ValueError('two or more finite positive packet intervals and a rigid three-axis offset required')

    rates = theta/dt[:, None]
    slopes = np.diff(rates, axis=0)/((dt[:-1]+dt[1:])/2.)[:, None]
    edge_rates = np.vstack((rates[0]-dt[0]/2.*slopes[0],
                           rates[:-1]+dt[:-1, None]/2.*slopes,
                           rates[-1]+dt[-1]/2.*slopes[-1]))
    start_rotations = midpoint_attitudes*Rotation.from_rotvec(-theta/2.)
    end_rotation = midpoint_attitudes[-1]*Rotation.from_rotvec(theta[-1]/2.)
    edge_rotations = Rotation.concatenate((start_rotations, end_rotation))
    velocities = edge_rotations.apply(np.cross(edge_rates, offset))
    return np.diff(velocities, axis=0)/dt[:, None]
