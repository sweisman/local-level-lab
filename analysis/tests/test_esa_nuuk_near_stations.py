# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_nuuk_near_stations import matched_rows


def interval(prns, *, time=388614, shift=0):
    return dict(start_gps_s=time, stop_gps_s=time+1, satellites=prns,
                air_range_m=[p*2+shift for p in prns], aggregate_weights=[p for p in prns],
                ground_range_m=[p+shift for p in prns])


def test_nuuk_three_station_comparison_centres_the_same_five_satellites():
    museum = interval([1, 2, 3, 4, 5, 6, 7])
    permanent = interval([2, 3, 4, 5, 6, 7, 8], shift=50)
    qaqortoq = interval([1, 3, 4, 5, 6, 7, 9], shift=-25)
    row, = matched_rows(museum=[museum], permanent=[permanent], qaqortoq=[qaqortoq])
    assert row['satellites'] == [3, 4, 5, 6, 7]
    assert row['museum_m'] == row['permanent_m'] == row['qaqortoq_m'] == [-2., -1., 0., 1., 2.]
    assert row['weights'] == [-2., -1., 0., 1., 2.]


def test_nuuk_comparison_rejects_different_aircraft_ranges():
    museum = interval([1, 2, 3, 4, 5, 6])
    permanent = interval([1, 2, 3, 4, 5, 6])
    permanent['air_range_m'][0] += 1
    with pytest.raises(ValueError, match='aircraft observations disagree'):
        matched_rows(museum=[museum], permanent=[permanent])
