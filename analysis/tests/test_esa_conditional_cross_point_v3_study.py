# SPDX-License-Identifier: AGPL-3.0-or-later
"""The serializable-receipt retry preserves both terminal attempts."""

from pathlib import Path

import pytest

from lll import esa_conditional_cross_point_study as first
from lll import esa_conditional_cross_point_v2_study as second
from lll import esa_conditional_cross_point_v3_study as third


ROOT = Path(__file__).resolve().parents[2]


def test_cross_point_v3_preserves_both_failed_attempts():
    assert len({first.ID, second.ID, third.ID}) == 3
    assert third.tasks() == first.tasks()
    assert third.verify_failed_parents(ROOT)
    assert not any('scoring' in key for key in first.INPUT_KEYS)


def test_cross_point_v3_requires_fresh_qualification():
    with pytest.raises(ValueError, match='qualification'):
        third.prepare(ROOT)
