import pytest

from lll.ilvis0_force_gain_range import gain_compatibility, minimax_separation


def test_earlier_gain_range_distinguishes_minimum_from_all_allowed_gains():
    compatible = gain_compatibility([(10.1, 10.)], [(10.2, 10.)], .15)
    assert compatible['earlier_gain_range'] == pytest.approx([.01, .15])
    assert compatible['joint_gain_range'] == pytest.approx([.02, .15])
    assert compatible['later_status'] == 'depends_on_gain'
    assert gain_compatibility([(10.1, 10.)], [(12., 10.)], .15)['later_status'] == 'none'


def test_minimax_uses_one_ratio_for_conflicting_force_windows():
    # Locally either target can match. A single ratio needs a one-unit gap.
    lo, hi, ratio = minimax_separation([(9., 9., 10., 10.), (11., 11., 10., 10.)], (.85, 1.15))
    assert lo == pytest.approx(1.)
    assert hi == pytest.approx(1.)
    assert ratio == pytest.approx(1.)


def test_minimax_keeps_training_restriction_and_interval_overlap():
    assert minimax_separation([(11., 11.2, 9.9, 10.)], (1., 1.02))[:2] == pytest.approx((.8, .8))
    assert minimax_separation([(11., 11.2, 9.9, 10.)], (1., 1.13))[:2] == pytest.approx((0., 0.))
