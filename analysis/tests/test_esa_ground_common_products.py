# SPDX-License-Identifier: AGPL-3.0-or-later
"""Preserve one comparison basis and signed range directions."""

import pytest


def test_two_band_change_subtracts_geometry_with_the_correct_sign():
    from lll.esa_ground_common_products import phase_residual
    from lll.esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH

    # Seven metres of common range movement plus a dispersive +3 m on L1.
    from lll.gnss_position import GAMMA
    start = (10., 25.)
    end = (start[0]+10./L1_WAVELENGTH, start[1]+(7.+3.*GAMMA)/L2_WAVELENGTH)
    assert phase_residual(start, end, 5.) == pytest.approx(2.)
    assert phase_residual(end, start, -5.) == pytest.approx(-2.)


def test_matching_centres_both_ground_stations_against_the_same_aircraft():
    from lll.esa_ground_common_products import match_products

    row = dict(start_gps_s=0, satellites=[1, 2, 3, 4, 5, 6],
               nuuk_aircraft_m=[0.]*6, nuuk_ground_m=[0., 1., 2., 3., 4., 900.],
               qaq_aircraft_m=[1., 2., 3., 4., 5., 100.],
               qaq_ground_m=[3., 3., 3., 3., 3., 900.])
    prediction = dict(zip(range(1, 6), [6., 4., 2., 0., -2.], strict=True))
    matched = match_products(row, prediction)
    assert matched['satellites'] == [1, 2, 3, 4, 5]
    assert matched['nuuk_aircraft_m'] == matched['qaq_aircraft_m'] == [-2., -1., 0., 1., 2.]
    assert matched['nuuk_ground_m'] == [4., 2., 0., -2., -4.]
    assert matched['qaq_ground_m'] == [0.]*5
    assert matched['nuuk_broadcast_ground_m'] == [-2., -1., 0., 1., 2.]
    prediction.pop(1)
    assert match_products(row, prediction) is None
