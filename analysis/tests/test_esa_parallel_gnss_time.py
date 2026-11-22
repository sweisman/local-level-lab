"""Time-adjusted comparisons preserve signed timing and report dependence."""

import math

import pytest


@pytest.mark.parametrize('dt', [0.001, -0.001])
def test_velocity_adjustment_removes_a_known_small_time_offset(dt):
    from lll.esa_parallel_gnss_time import corrected_neu

    latitude = 60.0
    east_mps = 100.0
    eccentricity_sq = (1 / 298.257223563) * (2 - 1 / 298.257223563)
    east_radius = 6378137.0 / math.sqrt(
        1 - eccentricity_sq * math.sin(math.radians(latitude))**2)
    reference = dict(time_s=10.0, latitude_deg=latitude,
                     longitude_deg=5.0, height_m=100.0)
    source = dict(time_s=10.0 + dt, latitude_deg=latitude,
                  longitude_deg=5.0 + math.degrees(
                      east_mps * dt / ((east_radius + 100.0) *
                                       math.cos(math.radians(latitude)))),
                  height_m=100.0, north_mps=0.0,
                  east_mps=east_mps, up_mps=0.0)
    raw, adjusted = corrected_neu(reference, source)
    assert raw[1] == pytest.approx(east_mps * dt, abs=.0002)
    assert adjusted[1] == pytest.approx(0, abs=.0002)
    assert adjusted[0] == pytest.approx(0, abs=.0002)
    assert adjusted[2] == pytest.approx(0, abs=.0002)


def test_reported_lag_one_correlation_uses_adjacent_differences():
    from lll.esa_parallel_gnss_time import axis_summary

    result = axis_summary([[1, 2, 0], [2, -2, 0],
                           [3, 2, 0], [4, -2, 0]])
    assert result['lag_one_correlation'][0] == pytest.approx(1)
    assert result['lag_one_correlation'][1] == pytest.approx(-1)
    assert result['lag_one_correlation'][2] is None
