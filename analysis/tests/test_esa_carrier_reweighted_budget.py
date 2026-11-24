import numpy as np
import pytest
from scipy.sparse import csr_matrix

from lll.esa_carrier_reweighted_budget import anchor_box, ground_score


def test_anchor_box_applies_range_adjoint_and_sums_interpolation_signs():
    carrier_times, anchors = [0., 1., 2.], [0., 2.]
    range_map = csr_matrix([[0., 0., 0., 0., 0., 0., 2., 0., 0.]])
    coefficients = anchor_box(carrier_times, anchors, [0.5, 1.5],
                              [[1., 2., 0.], [3., -2., 0.]], range_map, [2.])
    np.testing.assert_allclose(coefficients, [[1.5, 1., 0.], [-1.5, -1., 0.]])
    assert np.abs(coefficients).sum() == pytest.approx(5.)
    assert np.abs(coefficients.sum(axis=0)).sum() == 0


def test_ground_score_matches_retained_satellites_and_half_second_sums():
    ground = {(0, 2): dict(satellites=[1, 3, 5], ground_range_m=[.2, .4, -.1])}
    projection = dict(intervals=[dict(first=0, last=2, satellites=[1, 5], aggregate_weights=[2., -2.])])
    assert ground_score(projection, ground) == pytest.approx(.6)
