# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_nkar_phase_transfer import compare_transfer, later_pair


def saved(satellites, air, ground, weights):
    return dict(start_gps_s=100, stop_gps_s=101, satellites=satellites,
                air_range_m=air, ground_range_m=ground, aggregate_weights=weights)


def test_later_pair_recenters_on_common_satellites():
    a = saved([1, 2, 3, 4, 5, 6], [4, 5, 6, 7, 8, -30], [1, 2, 3, 4, 5, -15], [1, 2, 3, 4, 5, -15])
    b = saved([2, 3, 4, 5, 6, 7], [6, 7, 8, 9, -29, -1], [2, 3, 4, 5, 6, -20], [5, 6, 7, 8, -12, -14])
    row = later_pair(a, b)
    assert row['satellites'] == [2, 3, 4, 5, 6]
    assert row['aircraft_m'] == pytest.approx([5.8, 6.8, 7.8, 8.8, -29.2])
    assert row['weights'] == pytest.approx([2.2, 3.2, 4.2, 5.2, -14.8])
    assert row['nkar_m'] == pytest.approx([2.2, 3.2, 4.2, 5.2, -14.8])
    assert row['qaq_m'] == pytest.approx([-2, -1, 0, 1, 2])


def test_later_pair_rejects_mismatched_aircraft_values():
    a = saved([1, 2, 3, 4, 5], [-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2])
    with pytest.raises(ValueError, match='aircraft'):
        later_pair(a, dict(a, air_range_m=[0, -1, 0, 1, 2]))


def test_comparison_applies_separate_earlier_gains_to_same_later_rows():
    row = dict(start_gps_s=1, aircraft_m=[-2, 2], nkar_m=[-1, 1], qaq_m=[2, -2])
    later = dict(row, start_gps_s=100, aircraft_m=[-2, 2], qaq_m=[-2, 2], weights=[-1, 1])
    result = compare_transfer([row], [later], score_gap=8.)
    assert result['nkar']['trained_gain'] == pytest.approx(2.)
    assert result['qaq']['trained_gain'] == pytest.approx(-1.)
    assert result['nkar']['withheld']['earlier_gain_rms_m'] == pytest.approx(0.)
    assert result['qaq']['withheld']['earlier_gain_rms_m'] == pytest.approx(4.)
    assert result['nkar']['signed_shift_per_gap'] == pytest.approx(-.5)
    assert result['qaq']['signed_shift_per_gap'] == pytest.approx(.5)
