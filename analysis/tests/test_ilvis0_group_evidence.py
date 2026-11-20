# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.ilvis0_group_evidence import join_groups


def stretch(segment, group):
    return dict(segment_id=segment, conservative_split_group=group,
                shape_preference='globe', specified_background_preferred='True',
                start_utc='2009-10-24T13:26:00Z', imu_type='8')


def test_join_keeps_model_comparisons_and_single_model_checks_separate():
    rows = join_groups([stretch('a', 'one'), stretch('b', 'one'), stretch('c', 'two')],
        [('a', 'one', dict(study='matched', complete_settings=4, physical_screen_settings=4)),
         ('c', 'two', dict(study='transfer', later_cut_status='unavailable'))])
    assert len(rows) == 2
    assert rows[0]['stretches'] == 2
    assert rows[0]['globe_preferences'] == 2
    assert rows[0]['complete_settings'] == 4
    assert 'later_cut_status' not in rows[0]
    assert rows[1]['later_cut_status'] == 'unavailable'
    assert 'complete_settings' not in rows[1]


@pytest.mark.parametrize('prediction', [
    [('a', 'wrong', {})],
    [('a', 'one', {}), ('b', 'one', {})],
    [('a', 'one', {})],
])
def test_rejects_unknown_duplicate_and_missing_group_roles(prediction):
    with pytest.raises(ValueError, match='group'):
        join_groups([stretch('a', 'one'), stretch('b', 'one'), stretch('c', 'two')], prediction)
