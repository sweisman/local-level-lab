# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_changing_drift_transfer import condition, compare_ranges, operator, score_range


def test_fixed_law_responds_to_earlier_residuals_with_unchanged_future_width():
    times = np.arange(12.)
    weight = np.broadcast_to(np.eye(3)*.03, (len(times), 3, 3))
    error = operator(times, weight)
    errors = np.zeros((8, 3))
    shifted = errors.copy()
    shifted[:, 2] = np.arange(8.)*.1
    truth = np.zeros((4, 3))
    original = condition(error, errors, truth)
    correction = condition(error, shifted, truth)
    np.testing.assert_array_equal(original['sigma_m'], correction['sigma_m'])
    np.testing.assert_array_equal(original['center_m'], truth)
    assert np.all(np.asarray(correction['center_m'])[:, 2] < 0.)
    assert correction['later_receiver_positions_used'] is False
    score = score_range(correction, correction['center_m'], 4.2)
    assert score['contained'] and score['maximum_absolute_standardized_error'] == 0.


def test_range_separation_detects_any_axis_without_claiming_whole_path_coverage():
    a = dict(center_m=[[0., 0., 0.], [0., 0., 0.]], sigma_m=[[1., 1., 1.]]*2)
    b = dict(center_m=[[2., 0., 0.], [3., 0., 0.]], sigma_m=[[1., 1., 1.]]*2)
    result = compare_ranges(a, b, 1.)
    assert result['epochs_with_disjoint_axis_range'] == 1
    assert result['maximum_axis_gap_m'] == 1.
