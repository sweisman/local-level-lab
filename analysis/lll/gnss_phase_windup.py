# SPDX-License-Identifier: AGPL-3.0-or-later
"""Signed crossed-dipole wind-up and short-arc GPS range changes."""

from math import atan2, isfinite, pi, remainder


def fractional_phase(ray, transmitter_axes, receiver_axes):
    """Phase in radians for a unit receiver-to-satellite ray in the same frame."""
    import numpy as np

    ray = np.asarray(ray, float)
    tx, rx = (np.asarray(v, float) for v in (transmitter_axes, receiver_axes))
    if ray.shape != (3,) or not np.isclose(ray@ray, 1., atol=1e-12, rtol=0.):
        raise ValueError('a finite unit ray is required')
    if any(v.shape != (2, 3) or not np.allclose(v@v.T, np.eye(2), atol=1e-12, rtol=0.)
           for v in (tx, rx)):
        raise ValueError('finite orthonormal dipole axes are required')
    k = -ray
    a, b = tx
    source = a - k*(k@a) - np.cross(k, b)
    a, b = rx
    receiver = a - k*(k@a) + np.cross(k, b)
    if min(source@source, receiver@receiver) < 1e-12:
        raise ValueError('effective dipole vanishes on the ray')
    return atan2(k@np.cross(source, receiver), source@receiver)


def range_change(first, last):
    """Ionosphere-free GPS metres from the signed short-arc phase difference."""
    from .esa_carrier_phase_support import C, F1, F2

    if not all(isfinite(v) and abs(v) <= pi for v in (first, last)):
        raise ValueError('finite principal phases are required')
    delta = remainder(last-first, 2*pi)
    if abs(delta) > pi/4:
        raise ValueError('short continuous phase changes are required')
    return C*delta/(2*pi*(F1+F2))
