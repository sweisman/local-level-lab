"""Finite ESA technical recovery policy cannot silently widen its scope."""

from dataclasses import replace

import pytest


def test_conditioning_recovery_policy_has_one_exact_parent_and_finite_limits():
    from lll.esa_study_recovery import _check_spec
    from lll.esa_training_split_conditioning_recovery import SPEC

    assert _check_spec(SPEC) is SPEC
    assert SPEC.task_count == SPEC.workers == 2
    assert SPEC.max_attempts_per_task == 2
    assert SPEC.max_technical_interruptions == 2
    with pytest.raises(ValueError, match='finite ESA recovery'):
        _check_spec(replace(SPEC, continuation='data/other'))
    with pytest.raises(ValueError, match='finite ESA recovery'):
        _check_spec(replace(SPEC, max_attempts_per_task=1))
