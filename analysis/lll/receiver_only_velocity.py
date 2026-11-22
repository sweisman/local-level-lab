# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only forecast from the last earlier reported GNSS velocity."""

import math

import numpy as np

from .receiver_only_forecast import RADIUS_M
from .receiver_only_geodesic import advance


def forecast_velocity(last_time_s, last_coordinate, last_neu_velocity_mps,
                      future_times_s):
    """Hold the last earlier velocity fixed; use no later values or IMU."""
    position = np.asarray(last_coordinate, dtype=float)
    velocity = np.asarray(last_neu_velocity_mps, dtype=float)
    future = np.asarray(future_times_s, dtype=float)
    if (position.shape != (3,) or velocity.shape != (3,) or
            future.ndim != 1 or len(future) == 0 or
            not math.isfinite(last_time_s) or
            not np.all(np.isfinite(position)) or
            not np.all(np.isfinite(velocity)) or
            not np.all(np.isfinite(future)) or
            not -math.pi/2 < position[0] < math.pi/2 or
            RADIUS_M + position[2] <= 0 or
            future[0] <= last_time_s or np.any(np.diff(future) <= 0)):
        raise ValueError('finite last earlier fix, velocity and later times required')
    north, east, up = velocity
    speed = math.hypot(north, east)
    course = math.atan2(east, north)
    coordinates = np.empty((len(future), 3), dtype=float)
    for index, time in enumerate(future):
        elapsed = float(time - last_time_s)
        coordinates[index, :2] = advance(
            float(position[0]), float(position[1]), course,
            speed * elapsed, RADIUS_M + float(position[2]))
        coordinates[index, 2] = position[2] + up * elapsed
    return dict(coordinates=coordinates,
                north_east_up_velocity_mps=velocity,
                last_training_time_s=float(last_time_s),
                imu_samples_used=0, later_positions_used=False)
