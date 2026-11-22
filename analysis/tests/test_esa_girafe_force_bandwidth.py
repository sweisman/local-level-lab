# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.esa_girafe_force_bandwidth import coarsened_magnitudes


def test_vector_averaging_removes_opposing_forces_inside_a_cell():
    values = [[1., 0., 9.], [-1., 0., 9.], [3., 0., 9.], [-3., 0., 9.]]
    result = coarsened_magnitudes([0., .25, .5, .75, 1.], values, [0., .5, 1.])
    assert result['native'] == pytest.approx((np.sqrt(82.)+np.sqrt(90.))/2.)
    assert result['matched_cells'] == result['whole_support'] == pytest.approx(9.)


def test_split_boundaries_preserve_the_original_kernel_integral():
    result = coarsened_magnitudes([0., 0., .4, 1., 1.],
                                 [[99., 0., 0.], [2., 0., 0.], [-1., 0., 0.], [99., 0., 0.]],
                                 [0., .2, .7, 1.])
    assert result['native'] == pytest.approx(1.4)
    assert result['matched_cells'] == pytest.approx(.8)
    assert result['whole_support'] == pytest.approx(.2)


def test_rebinning_rejects_changed_support_or_weights():
    with pytest.raises(ValueError, match='kernel'):
        coarsened_magnitudes([0., .5, 1.], [[0., 0., 1.], [0., 0., 1.]], [0., .5, .99])
