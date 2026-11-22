# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite and immutable native turning solver controls."""

import pytest

from lll.turning_known_optimum_study import recipe, tasks, validate_task


def test_four_known_optimum_tasks_have_separate_finite_allowances():
    r = recipe()
    rows = tasks(r)
    assert len(rows) == 4
    assert {row['payload']['parent_identity'] for row in rows} == {
        'turning-level', 'turning-climb'}
    assert {row['payload']['control_start'] for row in rows} == {0, 1}
    assert r['maximum_evaluations'] == 80
    assert r['workers']*r['threads'] == 2
    assert all(row['limits']['native_calls'] < 60_000 for row in rows)


def test_changed_start_or_parent_is_rejected_before_any_native_call():
    row = tasks()[0]
    validate_task(row)
    for key, value in (('control_start', 2), ('parent_identity', 'straight-level')):
        changed = dict(row, payload=dict(row['payload'], **{key:value}))
        with pytest.raises(ValueError, match='unchanged known-optimum task'):
            validate_task(changed)
