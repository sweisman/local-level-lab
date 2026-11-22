import pytest

from lll.ilvis0_gps_extension_selection import additional_groups, selected_tags


def candidates():
    return [dict(segment_id=f's{i}', group_id=f'g{i}', imu_type=imu,
                 prior_preflight_group=i in (0, 2), passes_checked_metadata=True)
            for i, imu in enumerate(('8', '8', '21', '21'))]


def test_extension_selects_only_the_two_unused_groups():
    rows = candidates()
    assert additional_groups(rows, [rows[0], rows[2]]) == [rows[1], rows[3]]
    rows[1]['group_id'] = rows[0]['group_id']
    with pytest.raises(ValueError, match='distinct'):
        additional_groups(rows, [rows[0], rows[2]])


def test_extension_does_not_replace_a_failed_metadata_selection():
    rows = candidates()
    rows[3]['passes_checked_metadata'] = False
    with pytest.raises(ValueError, match='metadata'):
        additional_groups(rows, [rows[0], rows[2]])


def test_extension_uses_first_observed_tag_and_requires_both_methods():
    rows = [dict(gps_millisecond_tag=t, l1_broadcast={'eligible': True},
                 dual_frequency={'eligible': True}) for t in (1001, 1100, 3002)]
    assert selected_tags(rows) == [1001, 3002]
    rows[0]['dual_frequency']['eligible'] = False
    with pytest.raises(ValueError, match='support'):
        selected_tags(rows)
