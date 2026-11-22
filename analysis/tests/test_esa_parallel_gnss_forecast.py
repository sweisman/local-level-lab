"""Parallel forecast scoring uses signed receiver timing in WGS84 units."""

import math

import pytest


@pytest.mark.parametrize('dt', [.0007, -.0007])
def test_receiver_is_carried_to_the_sealed_forecast_epoch(dt):
    from lll.esa_parallel_gnss_forecast import position_at_time

    latitude = 64.0
    height = 2000.0
    east_speed = 80.0
    up_speed = 2.0
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    n = 6378137 / math.sqrt(1 - e2 * math.sin(math.radians(latitude))**2)
    other = dict(time_s=10 + dt, latitude_deg=latitude,
                 longitude_deg=12 + math.degrees(
                     east_speed * dt / ((n + height) *
                                        math.cos(math.radians(latitude)))),
                 height_m=height + up_speed * dt,
                 north_mps=0.0, east_mps=east_speed, up_mps=up_speed)
    adjusted = position_at_time(other, 10)
    assert adjusted[0] == pytest.approx(math.radians(latitude), abs=1e-10)
    assert adjusted[1] == pytest.approx(math.radians(12), abs=1e-10)
    assert adjusted[2] == pytest.approx(height, abs=1e-6)
