# SPDX-License-Identifier: AGPL-3.0-or-later
"""Guard the separate corrected local-profile source version."""

from lll.generated_local_profile_study_v2 import recipe


def test_corrected_study_keeps_same_radius_and_no_new_fits():
    source = dict(source_completion_sha256='c'*64,
                  source_manifest_sha256='m'*64,
                  recipe={'version':'sealed'}, task={'input_key':'recipe'})
    r = recipe(source)
    assert r['trust_radius'] == .1
    assert r['new_fit_starts'] == 0
    assert r['accounting'] == 'sealed-future-read-v1'
