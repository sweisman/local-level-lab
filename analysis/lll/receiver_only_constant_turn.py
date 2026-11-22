# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only forecast with one earlier-fitted constant course rate."""

import math

import numpy as np

from .receiver_only_forecast import RADIUS_M
from .receiver_only_geodesic import advance


TRAINING_REPORTS = 60


def forecast_constant_turn(training_times_s, training_neu_velocity_mps,
                           last_coordinate, future_times_s):
    """Fit course rate on 60 earlier GNSS velocities, then forecast unchanged."""
    times = np.asarray(training_times_s, dtype=float)
    velocity = np.asarray(training_neu_velocity_mps, dtype=float)
    position = np.asarray(last_coordinate, dtype=float)
    future = np.asarray(future_times_s, dtype=float)
    if (times.shape != (TRAINING_REPORTS,) or
            velocity.shape != (TRAINING_REPORTS, 3) or
            position.shape != (3,) or future.ndim != 1 or len(future) == 0 or
            not np.isfinite(times).all() or not np.isfinite(velocity).all() or
            not np.isfinite(position).all() or not np.isfinite(future).all() or
            np.any(np.diff(times) <= 0) or np.any(np.diff(times) > 2) or
            np.any(np.hypot(velocity[:, 0], velocity[:, 1]) <= 1)):
        raise ValueError('60 earlier finite moving GNSS velocity reports required')
    if (future[0] <= times[-1] or np.any(np.diff(future) <= 0) or
            not -math.pi/2 < position[0] < math.pi/2 or
            RADIUS_M + position[2] <= 0):
        raise ValueError('ordered later times and valid last position required')
    course = np.unwrap(np.arctan2(velocity[:, 1], velocity[:, 0]))
    centered_time = times - np.mean(times)
    centered_course = course - np.mean(course)
    turn_rate = float(centered_time @ centered_course /
                      (centered_time @ centered_time))
    speed = float(np.hypot(velocity[-1, 0], velocity[-1, 1]))
    upward = float(velocity[-1, 2])
    latitude, longitude, height = map(float, position)
    last_time = float(times[-1])
    current = last_time
    output = np.empty((len(future), 3), dtype=float)
    for index, target in enumerate(future):
        while current < target:
            step = min(1.0, float(target-current))
            heading = course[-1] + turn_rate*(current+step/2-last_time)
            latitude, longitude = advance(latitude, longitude, heading,
                                          speed*step, RADIUS_M+height)
            current += step
        output[index] = [latitude, longitude,
                         height+upward*(target-last_time)]
    return dict(coordinates=output, course_rate_rads=turn_rate,
                final_training_course_rad=float(course[-1]),
                final_training_speed_mps=speed,
                final_training_up_mps=upward,
                training_velocity_reports_used=TRAINING_REPORTS,
                last_training_time_s=last_time,
                imu_samples_used=0, later_positions_used=False)
