# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_companion_forecast import reference_choices


def test_companion_offset_is_fixed_from_training_displacement_only():
    training = np.array([[1., 2., 3.], [5., 4., 3.], [4., 3., 2.]])
    later = np.array([[20., 10., 6.], [30., 7., 2.]])
    offset, choices = reference_choices(training, later)
    np.testing.assert_array_equal(offset, [4., 3., 3.])
    np.testing.assert_array_equal(choices['onboard'], np.zeros((2, 3)))
    np.testing.assert_array_equal(choices['companion_raw'], later)
    np.testing.assert_array_equal(choices['companion_training_offset'], [[16., 7., 3.], [26., 4., -1.]])
