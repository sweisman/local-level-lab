# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact receiver-shift geometry checks."""

import math

import pytest

from lll.esa_fixed_forecast_receiver_margin import tie_margin


def test_single_epoch_known_tie():
    result=tie_margin([[0.,0.]],[[2.,0.]])
    assert result['arbitrary_shift_epoch_rms_m']==pytest.approx(1.)
    assert result['constant_shift_m']==1.
    assert result['score_gap_sum_squares_m2']==4.


def test_opposing_epoch_directions_make_constant_shift_impossible():
    result=tie_margin([[0.,0.],[0.,0.]],[[2.,0.],[-2.,0.]])
    assert result['arbitrary_shift_epoch_rms_m']==pytest.approx(1.)
    assert result['constant_shift_m'] is None


def test_validation_rejects_tie_and_nonfinite():
    with pytest.raises(ValueError,match='lower preferred'):
        tie_margin([[1.,0.]],[[0.,0.]])
    with pytest.raises(ValueError,match='finite'):
        tie_margin([[math.nan,0.]],[[2.,0.]])
