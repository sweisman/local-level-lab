# SPDX-License-Identifier: AGPL-3.0-or-later
"""Require distinct groups at both IMU21 latitude endpoints."""

from lll.ilvis0_matched_pilot_candidates import select


def test_select_takes_course_controls_and_disjoint_latitude_endpoints():
    def row(identity, imu, group, latitude, sector='south', eligible=True):
        return dict(segment_id=identity, imu_type=imu, group_id=group, mean_latitude_deg=latitude,
                    course_sector=sector, passes_checked_metadata=eligible)

    rows = [row('east', '8', 'A', -64., 'east'), row('south', '8', 'B', -63.),
            row('north', '21', 'C', -56.), row('same_group', '21', 'C', -67.),
            row('far', '21', 'D', -62.), row('overlap', '21', 'B', -66.),
            row('ineligible', '21', 'E', 65., eligible=False)]
    result = select(rows)
    assert [r['segment_id'] for r in result] == ['east', 'south', 'north', 'far']
