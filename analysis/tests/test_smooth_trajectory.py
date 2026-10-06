# SPDX-License-Identifier: AGPL-3.0-or-later
import copy

import numpy as np
import pytest

from audit_roll_proxy import knot_bank_jumps
from test_roll_proxy_audit import trajectory
from lll.inference_policy import digest
from lll.trajectory import SMOOTH_TRACK_VERSION, TrackReplay, smooth_track_spec


def test_smooth_alternative_preserves_observations_and_original_spec():
    original = trajectory([-75., -74.995, -74.98, -74.975]).spec
    before = copy.deepcopy(original)
    alternative = smooth_track_spec(original)
    assert original == before
    assert alternative['version'] == SMOOTH_TRACK_VERSION
    assert alternative['rows'] == original['rows']
    assert alternative['trajectory_hash'] != original['trajectory_hash']
    replay = TrackReplay(alternative)
    t = np.array([r['t_s'] for r in original['rows']])
    values = replay.sample(t)
    np.testing.assert_allclose(np.degrees(values['lat']), [r['latitude_deg'] for r in original['rows']])
    np.testing.assert_allclose(np.degrees(values['lon']), [r['longitude_deg'] for r in original['rows']])
    np.testing.assert_allclose(values['h'], 11000.)
    # Independent continuity check on each coordinate's acceleration at both knots.
    for curve in replay.blocks[0][2]:
        for knot in t[1:-1]:
            assert abs(curve(knot-1e-7, 2)-curve(knot+1e-7, 2)) < 1e-7
    assert max(abs(e['jump_deg']) for e in knot_bank_jumps(replay)) < .01


def test_gap_and_provider_estimates_are_not_bridged():
    original = trajectory([-75., -74.995, -74.98, -74.975]).spec
    content = {k: v for k, v in original.items() if k != 'trajectory_hash'}
    content['rows'] = copy.deepcopy(content['rows'])
    content['rows'].extend([dict(content['rows'][-1], t_s=120., is_provider_estimate=True),
                            dict(content['rows'][-1], t_s=160.), dict(content['rows'][-1], t_s=190.)])
    content['end_s'] = 190.
    updated = {**content, 'trajectory_hash': digest(content)}
    pchip, smooth = TrackReplay(updated), TrackReplay(smooth_track_spec(updated))
    grid = np.arange(191.)
    np.testing.assert_array_equal(pchip.support(grid), smooth.support(grid))
    assert not smooth.support(np.array([100., 120., 150.])).any()
    assert np.isnan(smooth.sample(np.array([120.]))['lat']).all()


def test_legacy_version_cannot_silently_select_new_interpolation():
    spec = trajectory([-75., -74.995, -74.98, -74.975]).spec
    content = {k: v for k, v in spec.items() if k != 'trajectory_hash'}
    content['curve_model'] = 'cubic_natural'
    with pytest.raises(ValueError, match='explicit version'):
        TrackReplay({**content, 'trajectory_hash': digest(content)})
