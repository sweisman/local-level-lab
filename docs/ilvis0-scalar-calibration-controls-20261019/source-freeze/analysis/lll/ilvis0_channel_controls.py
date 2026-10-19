# SPDX-License-Identifier: AGPL-3.0-or-later
"""Constructive channel-removal controls, not an archival observation model.

For a required navigation-frame specific force F and a measured body-frame
specific force f, translation constrains R f = F. A rotation about F leaves
that equation unchanged. If accelerometers are omitted instead, any specified
proper attitude R can be paired with the invented force R.T F. Neither
construction supplies an independent missing observation or an Earth verdict.
"""
import math

import numpy as np

VERSION = 'ilvis0-channel-removal-geometry-controls-v1'


def _vector(value, *, nonzero=False):
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError('finite three-vector required')
    if nonzero:
        length = float(np.linalg.norm(vector))
        if not math.isfinite(length) or length <= np.finfo(float).tiny:
            raise ValueError('nonzero force with a representable norm required')
    return vector


def _skew(vector):
    x, y, z = vector
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def _turn(axis, angle):
    c, s = math.cos(angle), math.sin(angle)
    return c * np.eye(3) + (1. - c) * np.outer(axis, axis) + s * _skew(axis)


def force_attitude(body_specific_force, required_navigation_force, twist_rad):
    """One proper body-to-navigation attitude in the unobserved twist family.

Align directions only; unequal magnitudes remain unequal. The caller must
declare how required force was obtained, including gravity, coordinate metric,
trajectory differentiation and rotational terms. No gyro or fused attitude
enters this construction. Its free twist is not an estimated aircraft heading.
"""
    body = _vector(body_specific_force, nonzero=True)
    required = _vector(required_navigation_force, nonzero=True)
    if not math.isfinite(twist_rad):
        raise ValueError('finite unobserved twist required')
    source, target = body / np.linalg.norm(body), required / np.linalg.norm(required)
    cross = np.cross(source, target)
    sine = float(np.linalg.norm(cross))
    cosine = float(np.clip(source @ target, -1., 1.))
    if sine > 0.:
        base = _turn(cross / sine, math.atan2(sine, cosine))
    elif cosine < 0.:
        basis = np.eye(3)[int(np.argmin(abs(source)))]
        axis = np.cross(source, basis)
        base = _turn(axis / np.linalg.norm(axis), math.pi)
    else:
        base = np.eye(3)
    return _turn(target, twist_rad) @ base


def force_rotation_jacobian(navigation_force):
    """Derivative of Exp(delta angle) F at zero; all three columns retained."""
    return -_skew(_vector(navigation_force, nonzero=True))


def required_body_force(body_to_navigation, required_navigation_force):
    """Explicit invented acceleration replacement; never a measured IMU stream."""
    rotation = np.asarray(body_to_navigation, dtype=float)
    force = _vector(required_navigation_force)
    if (rotation.shape != (3, 3) or not np.all(np.isfinite(rotation))
            or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-10, rtol=0.)
            or abs(float(np.linalg.det(rotation)) - 1.) > 1e-10):
        raise ValueError('proper finite body-to-navigation rotation required')
    return rotation.T @ force


def navigation_specific_force(*, velocity_ned, acceleration_ned, gravity_ned,
                              background_ned, transport_ned):
    """Required force from declared receiver-trajectory and field assumptions.

acceleration_ned is the time derivative of the velocity components in the
moving local NED frame. The background vector, transport vector and gravity
must be supplied for each candidate. This helper does not infer them, smooth
positions, use fused navigation, or silently fix a standard background rate.
"""
    velocity = _vector(velocity_ned)
    acceleration = _vector(acceleration_ned)
    gravity = _vector(gravity_ned)
    background = _vector(background_ned)
    transport = _vector(transport_ned)
    result = acceleration - gravity + np.cross(2. * background + transport, velocity)
    if not np.all(np.isfinite(result)):
        raise ValueError('required specific force exceeds finite numerical range')
    return result


def acceleration_magnitude_residual(body_specific_force, required_navigation_force):
    """Rotation-invariant force mismatch in m/s², not a whitened likelihood.

Does not require gyro observations or attitude. Calibration, trajectory
derivative uncertainty and temporal covariance still need explicit treatment
before use on recorded data. A zero residual does not identify an attitude.
"""
    body = _vector(body_specific_force)
    required = _vector(required_navigation_force)
    result = float(np.linalg.norm(body) - np.linalg.norm(required))
    if not math.isfinite(result):
        raise ValueError('force magnitude exceeds finite numerical range')
    return result
