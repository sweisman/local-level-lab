# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test shape abstention and sealed endpoint checks for the field scan."""

import pytest

from lll.esa_direction_holdout_field_range import check_endpoints, classify, combined_bounds


def test_retained_field_and_absent_field_use_a_common_error_scale():
    profile = dict(continuous_lower_rms_deg=.03, grid_best_rms_deg=.05)
    assert combined_bounds(.02, profile) == dict(
        lower_rms_deg=.02, upper_rms_deg=.02, best_sampled_case='zero_field')
    assert combined_bounds(.04, profile) == dict(
        lower_rms_deg=.03, upper_rms_deg=.04, best_sampled_case='zero_field')
    assert combined_bounds(.06, profile) == dict(
        lower_rms_deg=.03, upper_rms_deg=.05, best_sampled_case='specified_field')


def test_shape_preference_requires_disjoint_bounds():
    a = dict(lower_rms_deg=.02, upper_rms_deg=.03)
    b = dict(lower_rms_deg=.03, upper_rms_deg=.04)
    c = dict(lower_rms_deg=.031, upper_rms_deg=.04)
    assert classify(dict(globe=a, disc=b))['preference'] == 'overlap'
    assert classify(dict(globe=a, disc=c))['preference'] == 'globe'
    assert classify(dict(globe=c, disc=a))['preference'] == 'disc'


def test_a_changed_forecast_or_an_invalid_angle_is_rejected():
    angles = [.1] * 28
    assert check_endpoints(angles, angles) == 0.
    for altered in (angles[:-1], angles[:-1]+[.1+1e-9], angles[:-1]+[float('nan')]):
        with pytest.raises(ValueError, match='sealed direction prediction'):
            check_endpoints(angles, altered)
