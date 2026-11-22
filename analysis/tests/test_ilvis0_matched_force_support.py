# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify exact common packet support and conservative count widths."""

import numpy as np

from lll.ilvis0_common_support import match_support
from lll.ilvis0_matched_force_support import clock_envelopes, common_slice, force_summary


def test_common_slice_matches_independent_support_intersection():
    ends = (np.arange(1, 25)*.1, np.cumsum(np.tile([.09, .12], 12)))
    window = (.5, 1.8)
    offset = .11
    reference = []
    for clock in ends:
        intervals = np.column_stack((np.r_[0., clock[:-1]], clock))
        result = match_support([0., .5, 1., 1.5, 1.8, 2.], intervals, window,
            time_offset_bounds_s=(-offset, offset), maximum_receiver_gap_s=1.,
            integration_hypothesis='fixed test clock')
        reference.append(result['packet_indices'])
    retained = np.arange(len(ends[0]))[common_slice(clock_envelopes(ends, offset), window)]
    np.testing.assert_array_equal(retained, np.intersect1d(*reference))
    assert len(retained) > 0


def test_force_summary_retains_full_count_bound_under_averaging():
    counts = np.tile([0, 0, -800], (100, 1))
    periods = np.full(len(counts), .005)
    one = force_summary(counts[:1], periods[:1], scale=2**-14, clock='nominal')
    many = force_summary(counts, periods, scale=2**-14, clock='nominal')
    np.testing.assert_allclose(many['observed_packet_mean_mps2'],
                               one['observed_packet_mean_mps2'], rtol=1e-14)
    np.testing.assert_allclose([many['lower_mps2'], many['upper_mps2']],
                               [one['lower_mps2'], one['upper_mps2']], rtol=1e-14)
    assert many['lower_mps2'] < many['observed_packet_mean_mps2'] < many['upper_mps2']
