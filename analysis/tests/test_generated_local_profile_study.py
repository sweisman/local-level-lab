# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen local radius and finite source controls."""

from lll.generated_joint_profile_replay import tasks
from lll.generated_local_profile_study import RADIUS, recipe


def test_local_radius_is_fixed_and_finite():
    source = dict(source_completion_sha256='c'*64,
                  source_manifest_sha256='m'*64,
                  recipe={'version':'sealed'}, task={'input_key':'recipe'})
    r = recipe(source)
    assert RADIUS == r['trust_radius'] == .1
    assert r['new_fit_starts'] == 0
    assert r['maximum_wall_s'] == 3600
    assert tasks(r)[0]['limits']['native_calls'] == 504933
