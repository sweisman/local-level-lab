# SPDX-License-Identifier: AGPL-3.0-or-later
"""A fixed training-only constant-velocity receiver prediction baseline."""

import math

import numpy as np


RADIUS_M = 6378137.0


def _wrap(longitude):
    return (longitude + math.pi) % (2 * math.pi) - math.pi


def forecast(training_times, training_coordinates, future_times, *, window_s=60.0):
    """Fit the last training minute in a local metre frame and extrapolate."""
    times = np.asarray(training_times, dtype=float)
    positions = np.asarray(training_coordinates, dtype=float)
    future = np.asarray(future_times, dtype=float)
    if (times.ndim != 1 or future.ndim != 1 or positions.shape != (len(times), 3)
            or len(times) < 30 or len(future) < 1
            or not np.all(np.isfinite(times)) or not np.all(np.isfinite(future))
            or not np.all(np.isfinite(positions))
            or np.any(np.diff(times) <= 0) or np.any(np.diff(future) <= 0)
            or future[0] <= times[-1]):
        raise ValueError("finite increasing training and later times with at least 30 positions required")
    if not math.isfinite(window_s) or window_s <= 0:
        raise ValueError("positive fixed training window required")
    mask = times >= times[-1] - window_s
    if int(np.count_nonzero(mask)) < 30:
        raise ValueError("at least 30 distinct earlier positions in the last training window required")
    latitude, longitude, height = positions[-1]
    east_scale = (RADIUS_M + height) * math.cos(latitude)
    north_scale = RADIUS_M + height
    if not -math.pi / 2 < latitude < math.pi / 2 or north_scale <= 0 or abs(east_scale) < 1:
        raise ValueError("supported nonpolar receiver anchor required")
    local = np.column_stack((
        (positions[mask, 0] - latitude) * north_scale,
        _wrap(positions[mask, 1] - longitude) * east_scale,
        positions[mask, 2] - height,
    ))
    relative_time = times[mask] - times[-1]
    design = np.column_stack((np.ones(len(relative_time)), relative_time))
    coefficients, _, rank, _ = np.linalg.lstsq(design, local, rcond=None)
    if rank != 2:
        raise ValueError("distinct training times required for velocity fit")
    prediction = np.column_stack((np.ones(len(future)), future - times[-1])) @ coefficients
    coordinates = np.column_stack((
        latitude + prediction[:, 0] / north_scale,
        _wrap(longitude + prediction[:, 1] / east_scale),
        height + prediction[:, 2],
    ))
    return {
        "coordinates": coordinates,
        "north_east_up_velocity_mps": coefficients[1],
        "training_window_points": int(np.count_nonzero(mask)),
        "window_s": float(window_s),
        "last_training_time_s": float(times[-1]),
        "later_positions_used": False,
        "imu_samples_used": 0,
    }
