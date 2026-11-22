# SPDX-License-Identifier: AGPL-3.0-or-later
"""The post-study spread audit cannot silently change the frozen gate."""

import pytest

from lll.ilvis0_start_spread_diagnostic import audit_start_spread


def row(start, cost, x, binding='same'):
    return dict(start=start, training_cost=cost, forecast=[[x, 0., 0.]],
                binding=binding, passed=True)


def test_cross_method_agreement_can_hide_within_method_start_spread():
    audit = audit_start_spread(
        [row(0, 1., 0.), row(1, 1., .02)],
        [row(0, 1., .01), row(1, 1., .01)],
        relative_cost_tolerance=1e-8, forecast_tolerance_m=.011)
    assert audit['frozen_rule']['equivalent']
    assert audit['reference_within_maximum_m'] == pytest.approx(.02)
    assert audit['candidate_within_maximum_m'] == 0
    assert not audit['forecast_spread_stable']


def test_cost_mismatch_is_reported_without_rescoring_the_frozen_rule():
    audit = audit_start_spread(
        [row(0, 1., 0.), row(1, 2., .01)],
        [row(0, 1.0001, 0.), row(1, 2., .01)],
        relative_cost_tolerance=1e-8, forecast_tolerance_m=.001)
    assert not audit['frozen_rule']['equivalent']
    assert audit['forecast_spread_stable']
    assert audit['same_start_cost_absolute_maximum'] == pytest.approx(.0001)
    assert audit['same_start_cost_relative_maximum'] == pytest.approx(
        .0001/1.0001)


def test_changed_input_binding_is_rejected():
    with pytest.raises(ValueError, match='binding'):
        audit_start_spread(
            [row(0, 1., 0.), row(1, 1., 0.)],
            [row(0, 1., 0., 'different'), row(1, 1., 0., 'different')],
            relative_cost_tolerance=1e-8, forecast_tolerance_m=.001)


def test_optional_v2_diagnostic_preserves_frozen_failure():
    audit = audit_start_spread(
        [row(0, 0., 0.), row(1, 5e-13, 0.)],
        [row(0, 5e-13, 0.), row(1, 0., 0.)],
        relative_cost_tolerance=1e-8,
        absolute_cost_tolerance=1e-8,
        forecast_tolerance_m=.01)
    assert not audit['frozen_rule']['equivalent']
    assert audit['revised_rule_development_diagnostic']['equivalent']
