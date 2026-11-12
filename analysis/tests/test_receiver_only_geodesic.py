"""Great-circle receiver control independently checks path geometry."""

import math

import numpy as np
import pytest

from lll.receiver_only_geodesic import advance, forecast_geodesic


def test_eastbound_high_latitude_path_has_correct_arc_and_moves_equatorward():
    latitude = math.radians(60)
    distance = 20000.0
    radius = 6378137.0
    later_lat, later_lon = advance(latitude, 0.0, math.pi / 2, distance, radius)
    first = np.array([math.cos(latitude), 0.0, math.sin(latitude)])
    second = np.array([math.cos(later_lat) * math.cos(later_lon),
                       math.cos(later_lat) * math.sin(later_lon), math.sin(later_lat)])
    assert later_lat < latitude
    assert math.acos(float(first @ second)) == pytest.approx(distance / radius, rel=1e-8)


def test_equatorial_receiver_track_is_extrapolated_from_earlier_positions():
    radius = 6378137.0
    training = np.arange(100.0)
    future = np.arange(100.0, 110.0)
    coordinates = np.column_stack((np.zeros(len(training)),
                                   0.2 + 210 * training / radius,
                                   np.full(len(training), 10000.0)))
    result = forecast_geodesic(training, coordinates, future)
    assert result["imu_samples_used"] == 0
    assert result["later_positions_used"] is False
    np.testing.assert_allclose(result["coordinates"][:, 0], 0, atol=1e-10)
    np.testing.assert_allclose(result["coordinates"][:, 1],
                               0.2 + 210 * future / radius, atol=1e-9)
