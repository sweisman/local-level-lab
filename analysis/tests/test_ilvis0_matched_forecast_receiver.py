# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check receiver hull distance and common-reference comparison bounds."""

import numpy as np
import pytest

from lll.ilvis0_matched_forecast_receiver import distances, paired_range


def test_convex_triangle_distance_handles_interior_edge_and_collinear_vertices():
    points = np.array([[.25, .25], [1., 1.], [2., 1.]])
    triangles = np.array([[[0., 0.], [1., 0.], [0., 1.]],
                          [[0., 0.], [1., 0.], [0., 1.]],
                          [[0., 0.], [1., 0.], [2., 0.]]])
    lower, upper = distances(points, triangles)
    np.testing.assert_allclose(lower, [0., np.sqrt(.5), 1.], atol=1e-15)
    assert np.all(upper >= lower)


def test_paired_bounds_share_one_receiver_at_each_epoch():
    first = np.array([[0.], [0.]])
    second = np.array([[2.], [2.]])
    vertices = np.array([[[-.5], [0.], [.5]], [[0.], [.25], [.5]]])
    result = paired_range(first, second, vertices)
    assert result['lower_difference_m2'] == pytest.approx(2.)
    assert result['upper_difference_m2'] == pytest.approx(5.)
    assert result['additional_radius_for_tie_m'] == pytest.approx(.5)
