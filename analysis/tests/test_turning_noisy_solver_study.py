# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four bounded solver diagnostics on unchanged generated noisy inputs."""

import pytest

from lll.turning_noisy_solver_study import recipe, tasks, validate_task


def test_four_declared_methods_and_parents_have_finite_total_work():
    r = recipe()
    rows = tasks(r)
    assert len(rows) == 4
    assert {(row['payload']['parent_identity'],row['payload']['method'])
            for row in rows} == {(parent,method)
                for parent in ('turning-level','turning-climb')
                for method in ('trf','dogbox')}
    assert r['maximum_calls'] == 80
    assert r['workers']*r['threads'] == 2
    assert all(row['limits']['native_calls'] < 60_000 for row in rows)


def test_changed_method_or_parent_is_rejected_before_native_work():
    row = tasks()[0]
    validate_task(row)
    for key,value in (('method','lm'),('parent_identity','straight-level')):
        changed = dict(row,payload=dict(row['payload'],**{key:value}))
        with pytest.raises(ValueError,match='unchanged noisy solver task'):
            validate_task(changed)
