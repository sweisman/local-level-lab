# SPDX-License-Identifier: AGPL-3.0-or-later
"""Guard the recorded packet-average diagnostic against changed windows."""

from lll.ilvis0_matched_force_average import shape_interval, checked_interval

import numpy as np
import pytest


def test_recorded_interval_has_both_endpoint_packets_within_offset_support():
    end = np.arange(1, 11, dtype=float)*.25
    assert checked_interval(end, slice(2, 8), (0.25, 2.25), .20, 1.5) == (-1., .5)
    with pytest.raises(ValueError, match='offset support'):
        checked_interval(end, slice(1, 8), (.25, 2.25), .20, 1.5)


def test_same_field_contrast_retains_opposite_endpoint_bounds():
    for disc, exact in (((1., 2.), (0., 2.)), ((2.5, 4.), (-2., .5))):
        low, high = shape_interval((2., 3.), disc)
        assert low <= exact[0] and high >= exact[1]
        np.testing.assert_allclose((low, high), exact, atol=1e-15)
