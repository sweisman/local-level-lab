# SPDX-License-Identifier: AGPL-3.0-or-later
"""The corrected study is fresh and cannot erase the first terminal attempt."""

from pathlib import Path

import pytest

from lll import esa_conditional_cross_point_study as first
from lll import esa_conditional_cross_point_v2_study as second


ROOT = Path(__file__).resolve().parents[2]


def test_cross_point_v2_preserves_failed_task_and_limits():
    assert second.ID != first.ID
    assert second.tasks() == first.tasks()
    assert second.verify_failed_parent(ROOT)
    assert not any('scoring' in key for key in first.INPUT_KEYS)


def test_cross_point_v2_requires_fresh_qualification():
    with pytest.raises(ValueError, match='qualification'):
        second.prepare(ROOT)
