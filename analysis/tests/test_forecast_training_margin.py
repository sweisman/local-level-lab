# SPDX-License-Identifier: AGPL-3.0-or-later

from fractions import Fraction as F

from lll.forecast_training_margin import earlier_disposition, margin_from_support


def test_signed_training_support_uses_both_independent_adverse_changes():
    margin, sign, gaps = margin_from_support(-4, 8, {1: (2, 3), -1: (F(1, 2), F(3, 2))})
    assert gaps == {1: -9, -1: 2}
    assert sign == -1 and margin == F(1, 8)
    assert margin_from_support(-4, 8, {1: (2, 3), -1: (2, 3)})[0] == 0


def test_training_witness_exclusion_needs_outward_lower_bound_above_ceiling():
    assert earlier_disposition(dict(loss_lower=3, loss_passed=False), [0.], increase=1, unshared=0) == 'excluded'
    assert earlier_disposition(dict(loss_lower=1, loss_passed=False), [0.], increase=1, unshared=0) == 'unresolved'
    assert earlier_disposition(dict(loss_lower=0, loss_passed=True), [0.], increase=1, unshared=0) == 'feasible'
    assert earlier_disposition(dict(loss_lower=3, loss_passed=False), [0.], increase=1, unshared=1) == 'unresolved'
