# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_motion_innovation_scale import InnovationScore, response
from lll.esa_persistence_history import carry, scores


def test_carried_motion_matches_single_stream_across_cut():
    earlier = [1., 3., 8.]
    later = [9., 13., 24.]
    before = [0., 1., 1.]
    after = [0., 2., 0.]
    full = response(earlier+later, previous_time=0., exposure=before+after)
    start = response(earlier, previous_time=0., exposure=before)[-1]
    reset = response(later, previous_time=earlier[-1], exposure=after)
    np.testing.assert_allclose(carry(reset, later, earlier[-1], start), full[-3:], atol=1e-15)
    np.testing.assert_array_equal(carry(reset, later, earlier[-1], 0.), reset)


def test_no_history_preserves_score_and_history_changes_only_weights():
    times = [1., 3., 5.]
    point = np.log([1., 2., 3., 4., 2., 6.])
    baseline = InnovationScore(np.arange(9.)/4., np.eye(9)[:, :2], np.zeros(9), .4)
    reset, inherited = scores(baseline, times, previous_time=0., start=0., point=point)
    assert inherited == reset
    changed, inherited = scores(baseline, times, previous_time=0., start=.8, point=point)
    assert changed == reset
    assert inherited['quadratic'] != pytest.approx(reset['quadratic'])
    np.testing.assert_array_equal(baseline.weight, 0.)
