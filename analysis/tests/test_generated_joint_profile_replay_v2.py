# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact-boundary and finite-study checks for the v2 replay."""

import numpy as np
import pytest

from lll.generated_joint_profile_replay import tasks
from lll.generated_joint_profile_replay_v2 import feasible_native_point, recipe


def test_tiny_roundoff_is_projected_to_existing_boundary():
    point = np.array([.9, -.7])
    correction = np.array([.1+2e-14, -.3-2e-14])
    actual = feasible_native_point(point, correction)
    assert np.array_equal(actual, [1., -1.])
    assert np.max(abs(actual-(point+correction))) < 5e-13


def test_material_boundary_violation_is_rejected():
    with pytest.raises(ValueError, match='exceeds existing'):
        feasible_native_point(np.array([.9]), np.array([.100001]))


def test_v2_keeps_saved_fit_and_finite_task_limits():
    source = dict(source_completion_sha256='c'*64,
                  source_manifest_sha256='m'*64,
                  recipe={'version':'sealed'}, task={'input_key':'recipe'})
    r = recipe(source)
    assert r['new_fit_starts'] == 0
    assert r['source'] == 'data/generated-matched-one-sided-v2-20261117'
    assert tasks(r)[0]['limits']['native_calls'] == 504933
