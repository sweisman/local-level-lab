# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.ilvis0_force_interval_calibration import profile


def test_force_interval_calibration_balances_both_ends_and_holds_gain_fixed():
    result = profile([(10., 10., 10., 10.), (12., 12., 10., 10.)],
                     [(13., 13., 10., 10.)])
    assert result['zero_error_training_gain_interval'] is None
    assert result['gain'] == pytest.approx(.1, abs=1e-12)
    assert result['training_error_mps2'] == pytest.approx(1., abs=1e-12)
    assert result['training_optimum_lower_mps2'] <= result['training_error_mps2']
    assert result['training_error_mps2']-result['training_optimum_lower_mps2'] < 1e-12
    assert result['later_error_mps2'] == pytest.approx(2., abs=1e-12)
    assert result['later_outside_training_error'] == 1


def test_force_interval_calibration_handles_exact_overlap_and_gain_cap():
    result = profile([(11., 12., 10., 10.)], [(11., 12., 10., 10.)])
    assert result['zero_error_training_gain_interval'] == pytest.approx([.1, .15])
    assert result['training_error_mps2'] == 0.
    assert result['later_outside_training_error'] == 0
    capped = profile([(13., 13., 10., 10.)], [(13., 13., 10., 10.)])
    assert capped['gain'] == .15
    assert capped['training_error_mps2'] == pytest.approx(1.5)
