# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.matched_shape_drift import path_difference


def test_quadratic_path_separation_can_be_absorbed_by_smooth_drift():
    times = list(range(6))
    globe = [(0.3, 1.2, 1600.) for _ in times]
    disc = [(lat, lon, height - i**2) for i, (lat, lon, height) in enumerate(globe)]
    result = path_difference((times, globe, 2), (times, disc, 2))
    assert result['epochs'] == 4
    assert result['total_rms_m'] == pytest.approx((sum(i**4 for i in (2, 3, 4, 5)) / 4)**0.5)
    assert result['smooth_rms_m'] == pytest.approx(result['total_rms_m'])
    assert result['remainder_rms_m'] == pytest.approx(0., abs=1e-10)


def test_mismatched_forecast_clocks_cannot_be_compared():
    times = list(range(6))
    positions = [(0.3, 1.2, 1600.) for _ in times]
    with pytest.raises(ValueError, match='matching forecast clocks'):
        path_difference((times, positions, 2), (times[:-1] + [7], positions, 2))
