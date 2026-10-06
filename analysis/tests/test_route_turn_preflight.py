# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent route-screen controls; never run a flight or SVD."""
import numpy as np
import pytest

import preflight_route_turns as preflight


@pytest.fixture(autouse=True)
def no_svd(monkeypatch):
    monkeypatch.setattr(np.linalg, 'svd', lambda *a, **k: pytest.fail('preflight ran an SVD'))


def straight_route():
    t = np.arange(4500.)
    return dict(t=t, psi=np.zeros(len(t)), psi_dot=np.zeros(len(t)),
                speed=np.full(len(t), 250.), vz=np.zeros(len(t)),
                bearing_ok=np.ones(len(t), bool))


def test_gap_cannot_join_short_cruise_runs():
    kin = straight_route()
    kin['bearing_ok'][:] = False
    kin['bearing_ok'][100:700] = True
    kin['bearing_ok'][701:1301] = True
    _, keep, runs = preflight.qualified_bins(kin, 4500.)
    assert not keep.any() and runs == []


def test_safe_turns_still_fail_with_one_heading():
    kin = straight_route()
    bins, keep, _ = preflight.qualified_bins(kin, 4500.)
    result = preflight.screen_schedule(bins, keep, preflight.maneuver_mask(kin, buffer_s=120.),
                                      [20., 40., 60.], 4500.)
    assert all(c['safe'] for c in result['turn_checks'])
    assert result['screened_minutes'] >= 60
    assert result['exclusions'] == ['insufficient screened heading diversity']
    assert not result['passes_screen']


def test_buffered_maneuver_blocks_otherwise_informative_turn():
    t = np.arange(30., 4500., 60.)
    bins = dict(t=t, dt=np.full(len(t), 60.), psi=np.where(t < 2250., 0., np.pi / 2))
    mask = dict(verified=True, coverage=[0., 4499.], intervals=[
        dict(start_s=1080., end_s=1320., reason='aircraft maneuver')])
    result = preflight.screen_schedule(bins, np.ones(len(t), bool), mask,
                                      [20., 40., 60.], 4500.)
    assert result['heading_diversity']['adequate']
    assert result['screened_minutes'] >= 60
    assert result['exclusions'] == ['unsafe or unverified turn']
    assert not result['passes_screen']


def test_rotation_of_heading_reference_preserves_screen():
    t = np.arange(30., 4500., 60.)
    bins = dict(t=t, dt=np.full(len(t), 60.), psi=np.where(t < 2250., 0., np.pi / 2))
    mask = dict(verified=True, coverage=[0., 4499.], intervals=[])
    base = np.ones(len(t), bool)
    first = preflight.screen_schedule(bins, base, mask, [20., 40., 60.], 4500.)
    rotated = preflight.screen_schedule({**bins, 'psi':bins['psi'] + np.radians(355.)},
                                       base, mask, [20., 40., 60.], 4500.)
    assert first['passes_screen'] and rotated['passes_screen']
    assert first['heading_duration_margin_seconds'] == rotated['heading_duration_margin_seconds']
