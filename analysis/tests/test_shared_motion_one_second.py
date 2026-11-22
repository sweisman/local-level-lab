# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.shared_motion_one_second import sum_airborne_pairs


def test_one_second_carrier_sum_uses_shared_satellites_and_removes_each_clock():
    rows = [dict(seconds=10.5, common_satellites=[1, 2, 3, 4, 5],
                 common_required_m=[21., 22., 23., 24., -90.], clock_m=[0., 5., 10., 15., -30.]),
            dict(seconds=11., common_satellites=[2, 3, 4, 5, 6],
                 common_required_m=[52., 53., 54., -10., -149.], clock_m=[30., 28., 26., 24., -108.])]
    pair, = sum_airborne_pairs(rows)
    assert (pair['first_gps_s'], pair['last_gps_s']) == (10., 11.)
    assert pair['satellites'] == [2, 3, 4, 5]
    assert pair['required_m'] == pytest.approx([42., 44., 46., -132.])
    assert pair['clock_m'] == pytest.approx([8., 11., 14., -33.])


@pytest.mark.parametrize('times', [(10.5, 11.5), (10., 10.5), (10.5, 11., 12.5, 13.)])
def test_one_second_carrier_sum_rejects_wrong_clock_or_gaps(times):
    rows = [dict(seconds=t, common_satellites=[1, 2, 3, 4],
                 common_required_m=[0.] * 4, clock_m=[0.] * 4) for t in times]
    with pytest.raises(ValueError, match='consecutive integer-ended seconds'):
        sum_airborne_pairs(rows)
