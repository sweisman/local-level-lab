# SPDX-License-Identifier: AGPL-3.0-or-later
"""Make sure later force rows never choose the calibration."""

import pytest

from lll.ilvis0_matched_force_gain import compare


def test_gain_is_chosen_once_on_training_and_excess_is_recorded_later():
    result = compare([(2.1, 2.), (3., 3.)], [(2.2, 2.), (1., 1.)])
    assert result['training_gain'] == pytest.approx(.05)
    assert result['zero_gain_training_violations'] == 1
    assert result['zero_gain_later_violations'] == 1
    assert result['later_violations'] == 1


def test_large_training_gain_withholds_the_later_score():
    result = compare([(3., 2.)], [(2., 2.)])
    assert result['training_feasible'] is False
    assert result['required_training_gain'] == .5
    assert result['training_gain'] is None and result['later_violations'] is None
