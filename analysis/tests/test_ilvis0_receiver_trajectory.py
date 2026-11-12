# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only connection from GGA fixes to local trajectory derivatives."""

import math

import numpy as np
import pytest

from lll.ilvis0_receiver_support import SupportPolicy
from lll.ilvis0_receiver_trajectory import (
    _selected_coordinates, local_trajectory_from_gga)


def _policy(*, course_span=5.):
    return SupportPolicy(
        half_windows_s=(5., 10.), maximum_gap_s=1.5,
        minimum_samples=5, minimum_speed_mps=100., maximum_speed_mps=300.,
        maximum_course_span_deg=course_span, maximum_speed_span_mps=5.,
        maximum_vertical_rate_span_mps=.5)


def _fixes():
    radius = 6378137. + 1000.
    return [dict(utc_week_s=float(i), time1_s=float(i)*1.01+.2,
                 latitude_deg=0.,
                 longitude_deg=((179.99 + math.degrees(200. * i / radius) + 180.) % 360.) - 180.,
                 orthometric_height_m=970., geoid_separation_m=30.,
                 fix_quality=1)
            for i in range(21)]


def _covariance(count):
    return np.kron(np.eye(count), np.diag([1e-16, 1e-16, .09]))


def test_selected_longitude_chart_is_independent_of_excluded_prefix():
    original = _fixes()
    changed = [dict(row) for row in original]
    changed[0]['longitude_deg'] = -179.99
    first, last = 5, 15
    expected = _selected_coordinates(original, first, last,
                                     np.full(len(original), 1000.))
    actual = _selected_coordinates(changed, first, last,
                                   np.full(len(changed), 1000.))
    np.testing.assert_array_equal(actual, expected)


def test_dateline_track_uses_one_receiver_selected_window_for_derivatives():
    fixes = _fixes()
    original = [dict(row) for row in fixes]
    result = local_trajectory_from_gga(
        fixes, _covariance(len(fixes)), target_s=10., policy=_policy(), degree=2)
    assert result['support']['selected_indices'] == (0, 20)
    trajectory = result['trajectory']
    assert trajectory['position'][0] == pytest.approx(0., abs=1e-12)
    assert trajectory['rate'][1] == pytest.approx(200. / (6378137. + 1000.), rel=1e-9)
    assert trajectory['acceleration'] == pytest.approx((0., 0., 0.), abs=1e-9)
    assert trajectory['coordinate_residuals'].shape == (21, 3)
    assert result['coordinate_units'] == ('rad', 'rad', 'm')
    assert result['motion_version'] == 'receiver-gga-motion-v2'
    assert result['measurement_time_key'] == 'utc_week_s'
    assert result['scientific_decision'] == 'abstain'
    assert fixes == original


def test_no_motion_qualified_window_abstains_before_derivative_fit():
    fixes = _fixes()
    fixes[10]['longitude_deg'] += .01
    result = local_trajectory_from_gga(
        fixes, _covariance(len(fixes)), target_s=10., policy=_policy(), degree=2)
    assert result['support']['selected_indices'] is None
    assert result['trajectory'] is None
    assert result['scientific_decision'] == 'abstain'


def test_outside_window_covariance_cannot_change_local_derivatives():
    fixes = _fixes()
    fixes[2]['longitude_deg'] += .001
    first = _covariance(len(fixes))
    second = first.copy()
    second[:6, :6] *= 4.
    first_result = local_trajectory_from_gga(
        fixes, first, target_s=10., policy=_policy(), degree=2)
    second_result = local_trajectory_from_gga(
        fixes, second, target_s=10., policy=_policy(), degree=2)
    # The 5-second support is selected when the longer support is rejected by
    # a receiver-only course change outside the shorter window.
    assert first_result['support']['selected_indices'] == (5, 15)
    np.testing.assert_array_equal(first_result['trajectory']['covariance'],
                                  second_result['trajectory']['covariance'])


def test_outside_window_position_cannot_shift_selected_longitude_chart():
    fixes = _fixes()
    fixes[2]['longitude_deg'] += .001
    changed = [dict(row) for row in fixes]
    changed[0]['longitude_deg'] = -179.99
    covariance = _covariance(len(fixes))
    first_result = local_trajectory_from_gga(
        fixes, covariance, target_s=10., policy=_policy(), degree=2)
    second_result = local_trajectory_from_gga(
        changed, covariance, target_s=10., policy=_policy(), degree=2)
    assert first_result['support']['selected_indices'] == (5, 15)
    assert second_result['support']['selected_indices'] == (5, 15)
    np.testing.assert_array_equal(first_result['trajectory']['position'],
                                  second_result['trajectory']['position'])


def test_invalid_full_receiver_covariance_is_rejected_even_if_support_abstains():
    fixes = _fixes()
    with pytest.raises(ValueError, match='coordinate covariance'):
        local_trajectory_from_gga(fixes, np.eye(3 * len(fixes) - 1),
                                  target_s=10., policy=_policy(), degree=2)
