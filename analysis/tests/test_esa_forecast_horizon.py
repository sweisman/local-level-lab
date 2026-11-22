"""Fixed horizon bins preserve the changing sign and coverage of height error."""

import pytest


def test_horizon_bins_locate_coverage_loss_without_fitting():
    from lll.esa_forecast_horizon import horizon_bins

    raw = [[0, 0, x] for x in (1., 2., 3., 4.)]
    conditioned = [[0, 0, x] for x in (0.5, 1.5, 2.5, 3.5)]
    half_width = [[1., 1., 1.]] * 4
    rows = [dict(time_s=i, north_mps=3., east_mps=4., up_mps=float(i))
            for i in range(4)]
    bins = horizon_bins(raw, conditioned, half_width, rows, size=2)
    assert [part['nominal_95_up_count'] for part in bins] == [1, 0]
    assert bins[0]['conditional_up_mean_m'] == pytest.approx(1.)
    assert bins[1]['conditional_up_mean_m'] == pytest.approx(3.)
    assert bins[0]['conditional_adjustment_mean_m'] == pytest.approx(-0.5)
    assert bins[1]['receiver_mean_ground_speed_mps'] == pytest.approx(5.)


def test_horizon_bins_reject_incomplete_support():
    from lll.esa_forecast_horizon import horizon_bins

    values = [[0., 0., 1.]] * 3
    rows = [dict(time_s=i, north_mps=1., east_mps=0., up_mps=0.)
            for i in range(3)]
    with pytest.raises(ValueError, match='complete fixed bins'):
        horizon_bins(values, values, values, rows, size=2)
