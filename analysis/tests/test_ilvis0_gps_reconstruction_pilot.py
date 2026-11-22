"""Focused controls for the frozen receiver-only position follow-up."""

import numpy as np
import pytest

from lll import gnss_position as gps
from lll import ilvis0_gps_reconstruction_pilot as pilot


def test_one_second_selection_keeps_earliest_original_tags_and_gaps():
    assert pilot.one_per_second([1100, 1200, 2050, 2800, 4780]) == [1100, 2050, 4780]
    with pytest.raises(ValueError, match='ordered unique'):
        pilot.one_per_second([1100, 1100, 2050])


def test_local_comparison_measures_neu_difference_after_solution():
    point = dict(latitude_deg=-60., longitude_deg=10., ellipsoid_height_m=4000.)
    latitude, longitude = np.deg2rad([point['latitude_deg'], point['longitude_deg']])
    seed = gps.ecef(latitude, longitude, point['ellipsoid_height_m'])
    local = np.array([.5, -1., 2.])
    reconstructed = seed + gps.local_rotation(latitude, longitude).T@local
    np.testing.assert_allclose(pilot.receiver_difference(reconstructed, point), local, atol=1e-9)
