# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np

from lll.score_aligned_training import score_directions


def test_aligned_axes_follow_the_score_at_distinct_calibration_widths():
    design = np.diag([2., 1e-7, 3.])
    low, high, target = [-.5, -1., 0.], [.5, 1., 0.], [4., 1e-7, 70.]
    wide, narrow = score_directions(design, target, low, high, cutoffs=(1e-4, 1e-10))
    assert [wide['rank'], narrow['rank']] == [1, 2]
    np.testing.assert_allclose(wide['axis'], [1, 0, 0])
    np.testing.assert_allclose(narrow['axis'], [1, .5, 0])


def test_zero_training_design_produces_no_false_direction():
    result, = score_directions([[0.], [0.]], [3.], [-1.], [1.], cutoffs=(1e-4,))
    assert result == dict(rank=0, cutoff=1e-4, axis=None)
