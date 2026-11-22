# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.differential_phase import phase_difference, receiver_geometry, relative_position
from lll.esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH


def test_two_receivers_cancel_constant_ambiguities_and_ionosphere_in_phase_change():
    real_change = np.array([1., 5., -2.2])
    ratio = (1575.42/1227.60)**2
    ion = np.array([2., -.5, 4.])
    wavelengths = [L1_WAVELENGTH, L2_WAVELENGTH]
    aircraft_base = np.arange(1e8, 1e8+6.).reshape(3, 2)
    station_base = np.arange(2e8, 2e8+6.).reshape(3, 2)
    timed_station_change = np.array([9., -4., 10.])[:, None]/wavelengths
    motion_with_ion = (real_change[:, None] + ion[:, None]*np.array([1, ratio]))/wavelengths
    measured = phase_difference(aircraft_base+timed_station_change+motion_with_ion,
                                station_base+timed_station_change, aircraft_base, station_base)
    np.testing.assert_allclose(measured, real_change, atol=3e-8)


def test_relative_position_recovers_displacement_with_free_receiver_clock():
    design = np.array([[1., 0., 0.], [.6, .8, 0.], [0., 1., 0.], [0., 0., 1.], [-1., 0., 0.]])
    delta = np.array([.08, -.12, .32])
    at_anchor = np.array([-3., 2., 4., 5., -8.])
    result = relative_position(at_anchor+design@delta+23.5, at_anchor, design)
    np.testing.assert_allclose(result['position_change_m'], delta, atol=1e-12)
    assert result['clock_change_m'] == pytest.approx(23.5)
    np.testing.assert_allclose(result['residual_m'], np.zeros(5), atol=1e-12)
    with pytest.raises(ValueError, match='position and clock'):
        relative_position(np.ones(5), at_anchor, np.ones_like(design))


def test_phase_geometry_cancels_common_receiver_terms_without_dropping_measurements(monkeypatch):
    from lll import gnss_position

    anchor = np.array([6378137., 0., 0.])
    radius = 2e7
    states = [dict(sv_id=prn, satellite_ecef_m=[anchor[0]+radius, 0., 0.],
                   satellite_clock_s=0., observed_corrected_code_m=radius+bias,
                   transmit_gps_seconds=10., ephemeris_payload_sha256='test', l2_track_type=1)
              for prn, bias in [(2, 780.), (1, -123.)]]
    monkeypatch.setattr(gnss_position, 'observations', lambda *_: (states, []))
    prediction, gradient, items = receiver_geometry({'gps_week_seconds': 11.}, [], None, anchor, [1, 2])
    assert [item['sv_id'] for item in items] == [1, 2]
    np.testing.assert_allclose(prediction, [prediction[0], prediction[0]], atol=1e-10, rtol=0)
    np.testing.assert_allclose(gradient[:, 0], [-1., -1.])
    with pytest.raises(ValueError, match='continuously tracked'):
        receiver_geometry({'gps_week_seconds': 11.}, [], None, anchor, [1])
