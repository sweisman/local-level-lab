import numpy as np
import pytest

from lll.ilvis0_paired_force_windows import companion_bounds, common_offset_gap


def test_companion_bounds_do_not_interpolate_edge_packets():
    value = np.array([[1., 2.], [3., 4.], [5., 6.]])
    low, high = companion_bounds(np.arange(4.), value, [.5, 1.], [2.5, 2.], 0.)
    np.testing.assert_allclose(low, [1.5, 3.], atol=1e-8)
    np.testing.assert_allclose(high, [6., 4.], atol=1e-8)


def test_clock_allowance_widens_packet_bounds_and_missing_support_is_explicit():
    value = np.ones((3, 2))
    low, high = companion_bounds(np.arange(4.), value, [1., 0.], [2., 2.], .1)
    assert low[0] == 0.
    assert high[0] == pytest.approx(3.)
    assert np.isnan(low[1]) and np.isnan(high[1])


def test_common_offset_gap_keeps_relative_gain_constant_across_windows():
    # Two points agree at gain 1.1 and a constant offset. The third can
    # force positive discrepancy even though it can agree individually.
    points = [(3.1, 3.1, 1., 1.), (4.2, 4.2, 2., 2.)]
    low, high, ratio = common_offset_gap(points, (.9, 1.2))
    assert low == 0. and high <= 2e-9
    assert ratio == pytest.approx(1.1)
    low, high, _ = common_offset_gap([*points, (5.9, 5.9, 3., 3.)], (.9, 1.2))
    assert low == pytest.approx(.25) and high == pytest.approx(.25)
