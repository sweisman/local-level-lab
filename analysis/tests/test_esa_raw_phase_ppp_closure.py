# SPDX-License-Identifier: AGPL-3.0-or-later
"""Physical sign and alignment checks on the raw-phase comparison."""

import math

import numpy as np
import pytest

from lll.esa_raw_phase_ppp_closure import corrected_position, range_comparison
from lll.gnss_position import ecef


def test_reported_velocity_corrects_receiver_to_shared_epoch():
    row = dict(time_s=400000.001, latitude_deg=0., longitude_deg=0., height_m=1000.,
               north_mps=10., east_mps=100., up_mps=1.)
    expected = ecef(0., 0., 1000.)-np.array([1., 100., 10.])*(row['time_s']-400000.)
    np.testing.assert_array_equal(corrected_position(row, 400000.), expected)
    with pytest.raises(ValueError, match='tolerance'):
        corrected_position(row, 400001.)


def test_satellite_projection_uses_signed_motion_and_clock_invariance():
    geometry = np.concatenate((np.eye(3), -np.eye(3)), axis=0)
    first = np.array([.02, .03, .04])
    final = np.array([.01, .08, .09])
    z = geometry @ (final-first)
    actual = range_comparison(geometry, geometry, first, final, z+1.5, np.eye(3))
    np.testing.assert_allclose(actual['predicted_range_m'], z)
    np.testing.assert_allclose(actual['observed_neu_m'], final-first, atol=1e-15)
    assert math.isclose(actual['residual_squared_m2'], 0., abs_tol=1e-29)


def test_endpoint_geometry_change_is_kept_even_for_constant_receiver_offset():
    endpoint = np.concatenate((np.eye(3), -np.eye(3)), axis=0)
    start = endpoint * .95
    offset = np.array([.04, -.03, .02])
    observed = (endpoint-start)@offset
    result = range_comparison(start, endpoint, offset, offset, observed, np.eye(3))
    assert result['zero_squared_m2'] > 0.
    assert result['residual_squared_m2'] < 1e-29
