import numpy as np
import pytest

from lll.carrier_score_bound import carrier_score_bound, range_operator
from lll.esa_carrier_elevation_screen import eligible_rays


def test_screen_requires_the_margin_at_both_endpoints():
    first, last = [12., 31., 17., 14.], [30., 12., 18., 14.]
    np.testing.assert_array_equal(eligible_rays(first, last, 13., 13.),
                                  [False, False, True, True])


def test_missing_range_pairs_stay_on_the_same_time_grid():
    empty = np.empty((0, 3))
    one = np.array([[0., 0., 1.]])
    two = np.array([[-1., 0., 0.], [1., 0., 0.]])
    pairs = [(empty, empty), (two, two), (one, one)]
    with pytest.raises(ValueError, match='common support'):
        range_operator(pairs, 4)
    operator = range_operator(pairs, 4, allow_missing=True)
    assert operator.shape == (2, 12)
    np.testing.assert_array_equal(operator.toarray()[:, [3, 6]], np.column_stack((two[:, 0], -two[:, 0])))
    assert np.count_nonzero(operator.toarray()[:, [0, 9]]) == 0


def test_no_range_rows_leave_all_score_energy_to_motion():
    empty = np.empty((0, 3))
    result = carrier_score_bound([0., 1., 2.], [(empty, empty)]*2, [0, 2], [1.], [[0., 0., 1.]],
                                 allow_missing=True)
    assert result['range_values'] == 0
    assert result['range_rms_to_score'] == 0.
    assert not result['dual_weights']
    assert result['acceleration_rms_to_score'] == pytest.approx(1/np.sqrt(3))
