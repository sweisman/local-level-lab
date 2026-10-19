# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact-trajectory force adapter; no gyro, fused attitude or data differentiation.

Coordinates and their first two time derivatives must be supplied explicitly.
Using this calculation on noisy positions requires separately qualified
differentiation, calibration and covariance choices. It is not a likelihood.
"""
import math

import numpy as np

from . import models
from .ilvis0_channel_controls import navigation_specific_force

VERSION = 'ilvis0-exact-receiver-force-v1'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')


def evaluate(coordinates, coordinate_rate, coordinate_acceleration, *, model,
             background_rate_rads, gravity_mps2, disc_radius_m):
    """Return local NED kinematics and required specific force for one epoch.

Inputs use radians/metres and seconds. Acceleration is the derivative of
local velocity components, not an inertial Cartesian acceleration. Gravity
is the declared apparent gravity, including centrifugal effects where the
background field is used in the conventional rotating-frame equations.
"""
    arrays = [np.asarray(value, dtype=float) for value in
              (coordinates, coordinate_rate, coordinate_acceleration)]
    if any(a.shape != (3,) or not np.all(np.isfinite(a)) for a in arrays):
        raise ValueError('finite coordinate, rate and acceleration three-vectors required')
    if (model not in MODELS or not all(math.isfinite(x) for x in
            (background_rate_rads, gravity_mps2, disc_radius_m))
            or gravity_mps2 <= 0. or disc_radius_m <= 0.
            or (model != 'sphere_rotating' and background_rate_rads != 0.)):
        raise ValueError('explicit supported physical model and finite constants required')
    phi, _, height = arrays[0]
    p, l, h = arrays[1]
    pp, ll, hh = arrays[2]
    if abs(phi) >= math.pi / 2 - 1e-6:
        raise ValueError('polar coordinate singularity is outside the supported domain')
    s, c = math.sin(phi), math.cos(phi)
    if model == 'flat_still':
        radius = disc_radius_m * (math.pi / 2 - phi)
        velocity = np.array([disc_radius_m * p, radius * l, -h])
        acceleration = np.array([disc_radius_m * pp,
                                 radius * ll - disc_radius_m * p * l, -hh])
        transport = np.array([0., 0., -l])
    else:
        north, prime = models.radii(phi)
        if min(north + height, prime + height) <= 0.:
            raise ValueError('nonpositive geographic metric outside the supported domain')
        d = 1. - models.WGS84_E2 * s * s
        prime_derivative = prime * models.WGS84_E2 * s * c / d
        north_derivative = 3. * north * models.WGS84_E2 * s * c / d
        east = (prime + height) * c
        east_derivative = (prime_derivative * c - (prime + height) * s) * p + c * h
        velocity = np.array([(north + height) * p, east * l, -h])
        acceleration = np.array([(north + height) * pp + (north_derivative * p + h) * p,
                                 east * ll + east_derivative * l, -hh])
        transport = np.array([c * l, -p, -s * l])
    background = background_rate_rads * np.array([c, 0., -s])
    force = navigation_specific_force(
        velocity_ned=velocity, acceleration_ned=acceleration,
        gravity_ned=[0., 0., gravity_mps2], background_ned=background,
        transport_ned=transport)
    return dict(velocity_ned_mps=velocity, acceleration_ned_mps2=acceleration,
                transport_ned_rads=transport, background_ned_rads=background,
                specific_force_ned_mps2=force)
