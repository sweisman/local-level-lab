# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite-task controls for the generated nonlinear replay."""

import pytest

from lll.generated_joint_profile_replay import (
    study_recipe, tasks, validate_task, replay_construction_expected)


def _source():
    return dict(source_completion_sha256='c'*64,
                source_manifest_sha256='m'*64,
                recipe={'version':'sealed'}, task={'input_key':'recipe'})


def test_replay_task_has_finite_no_fit_allowance():
    r = study_recipe(_source())
    (task,) = tasks(r)
    assert r['workers'] == r['threads'] == 1
    assert r['new_fit_starts'] == 0
    assert r['maximum_wall_s'] == 3600
    assert task['payload']['no_new_fits'] is True
    assert 0 < task['limits']['native_calls'] < 1000000
    assert 0 < task['limits']['packet_visits'] < 2_000_000_000
    validate_task(dict(task, index=0, shard=0), r)


def test_replay_rejects_changed_task_before_native_work():
    r = study_recipe(_source())
    task = tasks(r)[0]
    changed = dict(task, payload=dict(task['payload'], no_new_fits=False))
    with pytest.raises(ValueError, match='unchanged finite replay'):
        validate_task(changed, r)


def test_replay_does_not_charge_reading_sealed_future():
    from lll.studies.closed import ClosedStudy
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    source = ClosedStudy(root, 'data/generated-matched-one-sided-v2-20261117')
    try:
        r = source.input('recipe')
        charges = replay_construction_expected(r)
        assert charges['generated_samples'] == 36080
        assert charges['constructed_intervals'] == 36000
    finally:
        source.close()
