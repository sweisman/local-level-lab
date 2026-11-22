# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import pytest

from lll.ilvis0_force_direction_gap import compare, required_rate


def test_direction_gap_inverts_the_cone_enclosure():
    period, magnitude, rate = .005, 10., 35.
    averaged = magnitude*math.cos(rate*period/2.)
    assert required_rate(averaged, magnitude, period) == pytest.approx(rate)
    assert required_rate(10., 9., period) == 0.
    assert required_rate(averaged, magnitude, 2.*period) == pytest.approx(rate/2.)


def test_training_gain_minimizes_direction_requirement_and_is_held_fixed():
    # Measured lower and upper, predicted lower and upper, packet period.
    training = [(10.1, 10.2, 9.9, 10., .005), (9.8, 9.9, 10., 10.1, .005)]
    later = [(10.2, 10.3, 9.9, 10., .005), (9.7, 9.8, 10., 10.1, .005)]
    outcome = compare(training, later)
    assert outcome['training_gain'] == pytest.approx(.01)
    assert outcome['training_required_rate_rads'] == pytest.approx(required_rate(9.9/1.01, 10., .005))
    assert outcome['later_lower_bound_failures'] == 1
    assert outcome['later_exceeds_training_rate'] == 1


def test_impossible_lower_bound_is_not_repaired_by_force_direction():
    outcome = compare([(13., 13., 10., 10., .005)], [(10., 10., 10., 10., .005)])
    assert outcome['gain_cap_exceeded']
    assert outcome['training_required_rate_rads'] is None
