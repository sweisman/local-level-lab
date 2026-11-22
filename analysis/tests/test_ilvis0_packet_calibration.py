# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_packet_calibration import linear_terms, packet_intervals, propose


def test_packet_derivatives_match_small_exact_calibration_change():
    counts = np.array([[3, -5, 17], [-8, 6, 16], [5, 9, -11], [7, -2, -13]])
    periods = np.array([.004, .005, .006, .004])
    slices = np.array([[0, 4], [1, 3]])
    correction = np.array([.4, -.2, .1, -.3, .5, .2])*1e-5
    zero, design = linear_terms(counts, periods, .002, slices)
    intervals = packet_intervals(counts, periods, .002, slices, correction, count_error=0.)
    np.testing.assert_allclose(intervals[:, 0], zero+design@correction, rtol=0, atol=6e-10)
    np.testing.assert_array_equal(intervals[:, 0], intervals[:, 1])


def test_proposal_shares_one_vector_and_keeps_interval_gap():
    observed = np.array([[9.9, 10.1], [9.9, 10.1]])
    predicted = np.array([[9., 9.], [11., 11.]])
    jac = np.zeros((2, 6))
    jac[:, 5] = 1.
    result = propose(observed, predicted, jac, np.ones(6)*.1)
    assert result['linear_gap_mps2'] == pytest.approx(.9)
    assert abs(result['correction'][5]) < 1e-12
