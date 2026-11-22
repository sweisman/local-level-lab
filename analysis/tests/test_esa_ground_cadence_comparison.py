# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check exact alignment of archived ground range changes."""

import pytest


def test_aggregate_centres_only_satellites_continuous_at_every_second():
    from lll.esa_ground_cadence_comparison import align_interval

    near = tuple(dict.fromkeys(range(1, 7), 0.) for _ in range(2))
    far = {i: (dict.fromkeys(range(1, 7), float(i)),
               dict.fromkeys(range(1, 7), float(i))) for i in range(30)}
    far[0][0][1] += 5.
    far[0][0][6] += 100.
    far[29][0].pop(6)
    far[29][1].pop(6)
    result = align_interval(0, near, far)
    assert result['satellites'] == [1, 2, 3, 4, 5]
    assert result['qaq_aircraft_m'] == [4., -1., -1., -1., -1.]
    assert result['qaq_ground_m'] == [0.]*5
    assert result['nuuk_aircraft_m'] == [0.]*5

    far.pop(12)
    assert align_interval(0, near, far) is None


def test_signed_rows_reject_duplicate_time_or_satellite():
    from lll.esa_ground_cadence_comparison import index_seconds

    row = dict(start_gps_s=0, satellites=[1, 2], aircraft_m=[1., 2.], ground_m=[3., 4.])
    with pytest.raises(ValueError):
        index_seconds([row, row], 'aircraft_m', 'ground_m')
    with pytest.raises(ValueError):
        index_seconds([dict(row, satellites=[1, 1])], 'aircraft_m', 'ground_m')
