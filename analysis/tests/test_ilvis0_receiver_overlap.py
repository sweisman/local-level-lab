# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only overlap calculations use exact tags and earlier-only offsets."""
import math

import pytest


def position(milliseconds, *, latitude=0.0, longitude=0.0):
    return dict(gps_week='2000', gps_milliseconds=str(milliseconds),
                latitude_deg=str(latitude), longitude_deg=str(longitude),
                ellipsoid_height_m='0', reported_sigma_north_m='0.5',
                reported_sigma_east_m='0.5', reported_sigma_up_m='1.0')


def test_later_difference_uses_only_earlier_constant_offset():
    from lll.ilvis0_receiver_overlap import compare_rows

    metres_per_degree = 6335439.3273 * math.pi / 180
    first = [position(i * 200, latitude=(10 if i < 50 else 11) / metres_per_degree)
             for i in range(100)]
    second = [position(i * 200) for i in range(100)]
    result = compare_rows(first, second, minimum_matches=100)
    assert result['matched_epochs'] == 100
    assert result['earlier_offset_neu_m'][0] == pytest.approx(10, abs=1e-4)
    assert result['later_rms_neu_m'][0] == pytest.approx(1, abs=1e-4)
    assert result['later_rms_neu_m'][1:] == pytest.approx([0, 0], abs=1e-8)


def test_longitude_difference_wraps_across_dateline():
    from lll.ilvis0_receiver_overlap import local_difference_m

    north, east, up = local_difference_m(
        position(0, longitude=-179.999), position(0, longitude=179.999))
    assert north == pytest.approx(0)
    assert east == pytest.approx(222.639, abs=0.01)
    assert up == pytest.approx(0)


def test_duplicate_or_nearby_time_tags_are_not_silently_matched():
    from lll.ilvis0_receiver_overlap import compare_rows

    first = [position(i * 200) for i in range(101)]
    second = [position(i * 200) for i in range(101)]
    with pytest.raises(ValueError, match='duplicate'):
        compare_rows(first + [first[0]], second, minimum_matches=100)
    second[-1] = position(20000 + 1)
    with pytest.raises(ValueError, match='insufficient exact matches'):
        compare_rows(first, second, minimum_matches=101)


def test_reported_lags_use_exact_elapsed_time_and_holdout_only():
    from lll.ilvis0_receiver_overlap import compare_rows

    metres_per_degree = 6335439.3273 * math.pi / 180
    first = [position(i * 200, latitude=(0 if i < 50 else i - 50) / metres_per_degree)
             for i in range(100)]
    second = [position(i * 200) for i in range(100)]
    result = compare_rows(first, second)
    assert result['later_lag_correlation']['200'][0]['pairs'] == 49
    assert result['later_lag_correlation']['1000'][0]['pairs'] == 45
    assert result['later_lag_correlation']['5000'][0]['pairs'] == 25
    assert result['later_lag_correlation']['200'][0]['correlation'] == pytest.approx(1)
    assert result['later_lag_correlation']['200'][1]['correlation'] is None


def test_time_gap_is_counted_without_interpolation():
    from lll.ilvis0_receiver_overlap import compare_rows

    first = [position(i * 200) for i in range(101)]
    second = [position(i * 200) for i in range(101)]
    second[50] = position(10001)
    result = compare_rows(first, second)
    assert result['matched_epochs'] == 100
    assert result['modal_spacing_ms'] == 200
    assert result['nonmodal_gaps'] == 1
