# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.ilvis0_group_zero_field import CASES, aggregate


def stretch(identity, group, costs, *, repeat='passed'):
    row = dict(segment_id=identity, conservative_split_group=group,
               start_utc='2011-10-12T10:14:00Z', imu_type='8',
               latest_repeat_status=repeat)
    for case, (globe, disc) in zip(CASES, costs, strict=True):
        for model, value in (('sphere_rotating', 0), ('sphere_still', globe), ('flat_still', disc)):
            row[f'{case}__{model}__cost'] = str(value)
    return row


def test_preserve_mixed_and_tied_results_without_group_vote():
    rows = [stretch('a', 'multi', [(10, 2), (11, 3)]),
            stretch('b', 'multi', [(2, 10), (3, 11)]),
            stretch('c', 'other', [(10, 2), (1, 3)]),
            stretch('d', 'tie', [(2, 2), (1, 3)])]
    groups = {r['group_id']: r for r in aggregate(rows, rows)}
    assert groups['multi']['classification'] == 'mixed_stretch_outcomes'
    assert groups['multi']['disc_both'] == groups['multi']['globe_both'] == 1
    assert groups['multi']['disc_both_repeat_passed'] == 1
    assert groups['other']['classification'] == 'different_across_settings'
    assert groups['tie']['classification'] == 'tie_in_at_least_one_setting'


def test_group_table_cannot_silently_use_different_costs_or_missing_stretches():
    row = stretch('a', 'solo', [(10, 2), (11, 3)])
    other = stretch('a', 'solo', [(10, 2), (11, 12)])
    with pytest.raises(ValueError, match='differs'):
        aggregate([row], [other])
    with pytest.raises(ValueError, match='identities'):
        aggregate([row], [])
    with pytest.raises(ValueError, match='identities'):
        aggregate([row, row], [row])


def test_unrepeatable_result_is_counted_separately():
    row = stretch('a', 'solo', [(10, 2), (11, 3)], repeat='not_saved_or_not_scheduled')
    result, = aggregate([row], [row])
    assert result['disc_both'] == 1
    assert result['disc_both_repeat_passed'] == 0
