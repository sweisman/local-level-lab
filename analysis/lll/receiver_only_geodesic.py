# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only constant-course spherical forecast; no IMU observations."""

import math

import numpy as np

from lll.receiver_only_forecast import RADIUS_M, forecast


def advance(latitude, longitude, bearing, distance_m, radius_m):
    """Advance one location along a spherical great circle."""
    values = (latitude, longitude, bearing, distance_m, radius_m)
    if (not all(math.isfinite(value) for value in values)
            or not -math.pi/2 < latitude < math.pi/2
            or distance_m < 0 or radius_m <= 0):
        raise ValueError("finite supported spherical course and positive radius required")
    arc = distance_m / radius_m
    sine = (math.sin(latitude)*math.cos(arc)
            + math.cos(latitude)*math.sin(arc)*math.cos(bearing))
    next_latitude = math.asin(max(-1.0, min(1.0, sine)))
    next_longitude = longitude + math.atan2(
        math.sin(bearing)*math.sin(arc)*math.cos(latitude),
        math.cos(arc)-math.sin(latitude)*math.sin(next_latitude))
    return next_latitude, (next_longitude + math.pi) % (2*math.pi)-math.pi


def forecast_geodesic(training_times, training_coordinates, future_times):
    """Estimate speed/course earlier, then follow a sphere from the last fix."""
    linear = forecast(training_times, training_coordinates, future_times,
                      window_s=60.0)
    positions = np.asarray(training_coordinates, dtype=float)
    future = np.asarray(future_times, dtype=float)
    last_time = float(np.asarray(training_times, dtype=float)[-1])
    latitude, longitude, height = map(float, positions[-1])
    north, east, up = map(float, linear["north_east_up_velocity_mps"])
    speed = math.hypot(north, east)
    course = math.atan2(east, north)
    radius = RADIUS_M + height
    coordinates = np.empty((len(future), 3), dtype=float)
    for index, time in enumerate(future):
        elapsed = float(time-last_time)
        coordinates[index, :2] = advance(latitude, longitude, course,
                                         speed*elapsed, radius)
        coordinates[index, 2] = height + up*elapsed
    return {
        "coordinates": coordinates,
        "north_east_up_velocity_mps": linear["north_east_up_velocity_mps"],
        "horizontal_speed_mps": speed,
        "course_deg": math.degrees(course) % 360,
        "training_window_points": linear["training_window_points"],
        "last_training_time_s": last_time,
        "later_positions_used": False,
        "imu_samples_used": 0,
        "spherical_radius_m": radius,
    }
