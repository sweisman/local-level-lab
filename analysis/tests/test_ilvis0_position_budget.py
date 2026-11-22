# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import pytest

from lll.ilvis0_geographic_bounds import Scalar, plus, times
from lll.ilvis0_position_budget import PARTS, PositionBudget


def test_terms_reconstruct_bound_and_child_does_not_change_parent():
    velocity = Scalar.interval(2., 1., 3., .125)
    metric = Scalar.interval(.5, .25, .75, .05)
    duration = Scalar.interval(.25, .24, .26, .004)
    rate = plus(velocity, metric)
    before = Scalar.interval(0., -.01, .01, .001)
    after = plus(before, times(rate, duration))
    parent = PositionBudget(initial=[before.value.remainder]*3)
    parent.append([(velocity, metric)]*3, [rate]*3, duration, [before]*3, [after]*3)
    values = parent.report()
    assert values['initial'] == [.001]*3
    assert values['velocity'] == pytest.approx([.03125]*3)
    assert values['geographic_metric'] == pytest.approx([.0125]*3)
    assert values['clock'] == pytest.approx([abs(rate.center)*duration.value.remainder
                                             +rate.value.change*duration.value.change]*3)
    reconstructed = math.fsum(values[k][0] for k in PARTS)
    assert reconstructed == pytest.approx(after.value.remainder, abs=2e-16)
    child = PositionBudget(parent)
    continued = plus(after, times(rate, duration))
    child.append([(velocity, metric)]*3, [rate]*3, duration, [after]*3, [continued]*3)
    assert parent.report() == values
    assert math.fsum(child.report()[k][0] for k in PARTS) == pytest.approx(continued.value.remainder, abs=2e-16)
