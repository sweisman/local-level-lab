"""Saved trajectory comparisons respect units and signed receiver time."""

import math

import pytest


@pytest.mark.parametrize('dt', [.001, -.001])
def test_saved_radian_prediction_matches_a_receiver_shifted_in_time(dt):
    from lll.esa_parallel_gnss_fit import fit_residual_neu

    lat_deg = 60.0
    lon_deg = 5.0
    east_mps = 100.0
    flattening = 1 / 298.257223563
    e2 = flattening * (2 - flattening)
    radius = 6378137 / math.sqrt(
        1 - e2 * math.sin(math.radians(lat_deg))**2)
    source = dict(time_s=20 + dt, latitude_deg=lat_deg,
                  longitude_deg=lon_deg + math.degrees(
                      east_mps * dt / ((radius + 100) *
                                       math.cos(math.radians(lat_deg)))),
                  height_m=100, north_mps=0, east_mps=east_mps, up_mps=0)
    residual = fit_residual_neu([math.radians(lat_deg),
                                 math.radians(lon_deg), 100], 20, source)
    assert residual == pytest.approx((0, 0, 0), abs=2e-4)
