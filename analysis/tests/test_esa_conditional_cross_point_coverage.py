# SPDX-License-Identifier: AGPL-3.0-or-later
"""The comparison uses two matching sealed forecasts."""

import copy

import pytest

from lll.esa_conditional_cross_point_coverage import matched_forecasts


def forecast():
    return dict(training_epochs=800, prediction_epochs=400,
        times_s=[0., 1.], full_operator_configuration={'law': 'fixed'},
        later_receiver_values_used=False, optimization_performed=False,
        fixed_calibration_only=True)


def test_cross_point_coverage_requires_same_early_only_law():
    left, right = forecast(), forecast()
    assert matched_forecasts(left, right)
    for key, value in (
            ('full_operator_configuration', {'law': 'changed'}),
            ('times_s', [0., 2.]),
            ('later_receiver_values_used', True),
            ('optimization_performed', True),
            ('fixed_calibration_only', False)):
        changed = copy.deepcopy(right)
        changed[key] = value
        with pytest.raises(ValueError, match='same-law early-only'):
            matched_forecasts(left, changed)
