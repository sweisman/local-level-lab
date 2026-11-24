# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_girafe_horizontal_witness import acceleration_kernel, sample_weights, vector_summaries


def test_position_kernel_recovers_constant_acceleration_and_preserves_mass():
    knots = np.arange(-2., 2.5, .5)
    derivative, kernel = acceleration_kernel(knots)
    assert derivative[1]@(7.+3.*knots+2.*knots**2) == pytest.approx(4.)
    assert np.min(kernel) >= 0
    edges = np.arange(-2.1, 2.2, .1)
    weights = sample_weights(edges, knots, kernel)
    assert np.sum(weights) == pytest.approx(1.)
    assert weights@np.full(len(weights), 3.) == pytest.approx(3.)
    with pytest.raises(ValueError, match='bracket'):
        sample_weights(edges[2:], knots, kernel)


def test_horizontal_force_summaries_leave_constant_heading_free():
    vector = np.array([[3., 4.], [-3., 4.]])
    weights = np.array([.5, .5])
    result = vector_summaries(vector, weights)
    assert result == pytest.approx({'average_vector_norm': 4., 'average_norm': 5.})
    rotate = np.array([[0., 1.], [-1., 0.]])
    assert vector_summaries(vector@rotate, weights) == pytest.approx(result)
