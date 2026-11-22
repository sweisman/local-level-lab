import numpy as np
import pytest

from lll.ilvis0_packet_force_change import rate_lower_bounds, split_pairs


def test_two_packet_mean_differences_recover_linear_force_change_before_allowances():
    dt = np.array([.004, .006, .005])
    t = np.cumsum(dt)-dt/2
    acceleration = np.column_stack((4*t, 3*t, np.full(3, 9.8)))
    counts = dt[:, None]*acceleration
    bounds = rate_lower_bounds(counts, dt, scale=1., gain=0., half_count=0., extra_error=0.)
    np.testing.assert_allclose(bounds, [5., 5.], atol=1e-10)
    reduced = rate_lower_bounds(counts, dt, scale=1., gain=.15, half_count=0., extra_error=.002)
    assert np.max(reduced) < 5./1.15
    assert rate_lower_bounds(np.zeros((3, 3)), dt, scale=1., gain=.15, half_count=.5, extra_error=0.).max() == 0.


def test_force_change_split_keeps_whole_pairs_clear_of_the_cut():
    earlier, later = split_pairs(np.ones(6), earlier_end=2.2, later_start=3.8, offset=.2)
    assert np.flatnonzero(earlier).tolist() == [0]
    assert np.flatnonzero(later).tolist() == [4]
    with pytest.raises(ValueError, match='cut'):
        split_pairs(np.ones(6), earlier_end=3., later_start=2., offset=.2)
