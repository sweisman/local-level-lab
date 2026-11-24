import numpy as np
import pytest

from lll.esa_galileo_north_witness import compare_ranges


def test_prediction_shift_has_correct_sign_and_is_free_of_the_receiver_clock():
    original, shifted, delta = compare_ranges([10., 13., 16.], [0., 2., 4.], [5., 8., 11.])
    np.testing.assert_allclose(original, [-1., 0., 1.])
    np.testing.assert_allclose(shifted, [0., 0., 0.])
    np.testing.assert_allclose(delta, [-1., 0., 1.])


def test_aligned_finite_ranges_are_required():
    with pytest.raises(ValueError, match='range'):
        compare_ranges([1., 2.], [1.], [1., 2.])
    with pytest.raises(ValueError, match='range'):
        compare_ranges([1., 2.], [1., np.inf], [1., 2.])
