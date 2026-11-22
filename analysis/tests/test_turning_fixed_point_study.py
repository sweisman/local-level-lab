# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated turning-point probe, separate from the sealed fits."""

import pytest

from lll.turning_fixed_point_study import recipe, tasks, validate_task


def test_two_saved_turning_points_only_with_ten_sweeps_and_no_fit_starts():
    r = recipe()
    matrix = tasks(r)
    assert [row['identity'] for row in matrix] == ['turning-level', 'turning-climb']
    assert r['maximum_sweeps'] == 10
    assert r['optimizer_starts'] == 0
    assert r['workers'] * r['threads'] == 2
    assert all(row['limits']['native_calls'] < 100_000 for row in matrix)
    assert all(row['limits']['packet_visits'] < 20_000_000 for row in matrix)


def test_changed_task_is_rejected_before_any_native_work():
    row = tasks()[0]
    validate_task(row)
    changed = dict(row, payload=dict(row['payload'], route='straight'))
    with pytest.raises(ValueError, match='unchanged turning task'):
        validate_task(changed)


def test_geometry_parent_binding_requires_both_nonconverged_saved_points(tmp_path):
    from lll.turning_fixed_point_study import parent_binding
    with pytest.raises((ValueError, FileNotFoundError)):
        parent_binding(tmp_path)


def test_worker_study_directory_resolves_repository_root(tmp_path):
    from lll.turning_fixed_point_study import project_root, ID
    study = tmp_path/'data'/ID
    study.mkdir(parents=True)
    assert project_root(study) == tmp_path
    with pytest.raises(ValueError, match='exact turning study directory'):
        project_root(tmp_path)


