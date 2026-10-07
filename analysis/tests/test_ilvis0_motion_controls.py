# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll import ilvis0_motion_controls as controls


def test_real_short_corrections_can_disappear_but_sustained_turns_remain():
    result = controls.pulse_controls()
    assert len(result['controls']) == 36
    assert all(v == 0 for v in result['missed_sustained_controls_12s_or_longer'].values())
    row = next(r for r in result['controls'] if r['duration_s'] == 1 and r['true_rate_deg_s'] == .1)
    assert row['measurements']['2']['exceeds_original_limit']
    assert not row['measurements']['12']['exceeds_original_limit']
    assert result['scientific_eligibility_changes'] == 0


def track(rate=.15, missing=False):
    times = np.arange(150.)
    if missing:
        times = times[(times <= 20) | (times >= 140)]
    course = np.deg2rad(359 + rate * times)
    nav = [dict(utc_week_s=float(t), velocity_north_mps=140*np.cos(c), velocity_east_mps=140*np.sin(c))
           for t, c in zip(times, course)]
    receiver = [dict(utc_week_s=float(t), course_deg=float(np.rad2deg(c) % 360)) for t, c in zip(times, course)]
    return nav, receiver


def test_receiver_selected_maneuvers_preserve_north_crossing_and_ignore_gyro():
    nav, receiver = track()
    result = controls.receiver_maneuvers(nav, receiver)
    assert result['events']
    for event in result['events']:
        assert event['net_receiver_course_change_deg'] > 4
        assert all(check[k]['exceeds_original_limit'] for check in event['measurements'].values()
                   for k in ('navigation', 'receiver'))
    assert not controls.receiver_maneuvers(*track(rate=.01))['events']
    assert not controls.receiver_maneuvers(*track(missing=True))['events']


def test_missing_navigation_context_cannot_be_used_as_a_passing_control():
    nav, receiver = track()
    result = controls.receiver_maneuvers(nav[:1], receiver)
    assert result['events']
    assert not result['events'][0]['measurements']['12']['navigation']['supported']
