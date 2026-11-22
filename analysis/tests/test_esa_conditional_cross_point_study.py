# SPDX-License-Identifier: AGPL-3.0-or-later
"""The cross-point worker can see only the opened flight's early inputs."""

from pathlib import Path

import pytest

from lll import esa_conditional_cross_point_study as study


ROOT = Path(__file__).resolve().parents[2]


def test_cross_point_task_has_no_later_receiver_input_or_optimization():
    assert len(study.tasks()) == 1
    task = study.tasks()[0]
    assert task['payload']['optimize'] is False
    assert task['payload']['later_receiver_input'] is False
    assert task['limits']['native_calls'] == 450_000
    assert task['limits']['packet_visits'] == 1_000_000_000
    assert not any('scoring' in key or 'later-receiver' in key
                   for key in study.INPUT_KEYS)


def test_cross_point_requires_complete_bound_parents():
    staged = study.parent_inputs(ROOT)
    assert set(staged) == set(study.INPUT_KEYS[:-3])
    assert b'"later_receiver_positions_read":false' in staged['saved-input-binding']
    assert b'"diagonal_replay_passed":true' in staged['weighted-cross-costs']
    assert b'"later_receiver_values_used":false' in staged['weighted-conditional-forecast']


def test_cross_point_requires_qualification_before_preparation():
    with pytest.raises(ValueError, match='qualification'):
        study.prepare(ROOT)
