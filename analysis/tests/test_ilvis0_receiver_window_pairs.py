"""Known-answer paired receiver support comparisons."""

import pytest

from lll.ilvis0_receiver_support import SupportPolicy
from lll.ilvis0_receiver_window_pairs import compare_pair


def _rows(*, spike=False):
    rows = []
    for second in range(61):
        up = 2. if spike and second == 25 else 0.
        rows.append(dict(gps_week=1, gps_milliseconds=second*1000,
                         latitude_deg=30., longitude_deg=0.,
                         ellipsoid_height_m=100.,
                         velocity_north_mps=220., velocity_east_mps=0.,
                         velocity_up_mps=up))
    return rows


def _policy():
    return SupportPolicy(
        half_windows_s=(5., 10., 15.), maximum_gap_s=1.5,
        minimum_samples=5, minimum_speed_mps=190.,
        maximum_speed_mps=350., maximum_course_span_deg=1.5,
        maximum_speed_span_mps=10., maximum_vertical_rate_span_mps=1.)


def test_pair_reports_same_target_grid_and_vertical_disagreement():
    result = compare_pair(_rows(), _rows(spike=True), policy=_policy(),
                          minimum_matches=10)
    assert result['matched_epochs'] == 61
    assert result['targets'] == 4
    assert result['both_accept'] + result['both_reject'] + result['disagree'] == 4
    assert result['disagree'] >= 1
    assert result['vertical_velocity_difference_rms_mps'] > 0
    assert result['interpolated_measurements'] is False


def test_pair_rejects_changed_or_duplicate_time_tags():
    right = _rows()
    right[3] = dict(right[2])
    with pytest.raises(ValueError, match='duplicate|reversed'):
        compare_pair(_rows(), right, policy=_policy(), minimum_matches=10)
