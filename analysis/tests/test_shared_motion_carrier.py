# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.gnss_carrier_phase import _geometry
from lll.shared_motion_carrier import centre, compare_signatures, displacement_at, fixed_path_range_residual, range_shift


def test_shared_motion_range_signature_matches_full_geometry():
    origin = np.array([4e6, 1e6, 5e6])
    delta = np.array([-.7, .08, .15])
    satellites = np.array([[21e6, 4e6, 12e6], [18e6, -16e6, 14e6], [9e6, 7e6, 20e6]])
    exact = _geometry(origin+delta, satellites)[0]-_geometry(origin, satellites)[0]
    assert range_shift(origin, origin+delta, satellites) == pytest.approx(exact, abs=2e-8)
    assert range_shift(origin, origin, satellites) == pytest.approx([0., 0., 0.])


def test_shared_motion_interpolation_is_cubic_and_closes():
    rows = [dict(elapsed_s=t, position_m=[p, 0., 0.], velocity_mps=[0., 0., 0.])
            for t, p in [(0., 0.), (1., 1.), (2., 0.)]]
    acceleration = np.array([[6., 0., 0.], [-6., 0., 0.], [6., 0., 0.]])
    for t in (.25, .5, .9, 1.):
        expected = 3*t*t-2*t*t*t
        for query in (t, 2-t):
            assert displacement_at(rows, query, acceleration) == pytest.approx([expected, 0., 0.])
    for t in (-.1, 0., 2., 2.1):
        assert list(displacement_at(rows, t, acceleration)) == [0., 0., 0.]


def test_carrier_signature_compares_signed_clock_free_values():
    required = centre([15., 12., 9.])
    assert required == pytest.approx(centre([-5., -8., -11.]))
    match = compare_signatures(required, required)
    reverse = compare_signatures(required, -required)
    assert match['cosine'] == pytest.approx(1.)
    assert match['unaccounted_rms_m'] == 0.
    assert reverse['cosine'] == pytest.approx(-1.)
    assert reverse['unaccounted_rms_m'] == pytest.approx(2*reverse['required_rms_m'])


def test_fixed_carrier_residual_differences_clock_and_troposphere_with_expected_signs():
    from lll.gnss_position import C

    ranges = [[100., 110., 120.], [102., 113., 124.]]
    clock = [[0., 0., 0.], [0., 1/C, -1/C]]
    neutral = [[4., 5., 5.], [5., 4., 5.]]
    residual = fixed_path_range_residual([13.25, 10.5, 15.25], ranges, clock, neutral)
    assert list(residual) == pytest.approx([.25, -.5, .25])


def test_clock_correction_keeps_common_satellites_and_cancellation_signs(monkeypatch):
    from lll import esa_carrier_phase_support as support, esa_relative_clock_replay as clock
    from lll import gnss_carrier_phase as carrier, gnss_position as gps
    from lll.esa_shared_motion_carrier import pair_signature

    prns = [1, 2, 3, 4, 5, 17]
    positions = {prn: np.array([21e6, prn*9e5, 12e6-prn*2e5]) for prn in prns}
    paired = {prn: dict(broadcast_input_code_m=(25e6, 25e6)) for prn in prns}
    monkeypatch.setattr(support, 'pair_satellites', lambda *args: (paired, None))
    monkeypatch.setattr(carrier, 'shared_ephemerides', lambda *args: dict(zip(prns, prns)))
    monkeypatch.setattr(gps, 'satellite_state', lambda prn, week, seconds, code: (positions[prn], 0., seconds))
    monkeypatch.setattr(clock, 'interpolate_clock', lambda prn, seconds: prn*seconds/gps.C)
    before, after = (dict(week=2269, seconds=t) for t in (0., .5))
    coordinates = [(.2, -.6, 1200.)]*2
    offsets = [np.zeros(3), np.array([0., 0., .5])]
    full, common, matched, replacement = pair_signature(
        before, after, prns, prns, coordinates, offsets, [], {prn: prn for prn in prns[:-1]})
    satellites = np.array(list(positions.values()))
    nominal = _geometry(gps.ecef(*coordinates[0]), satellites)[0]
    shifted = _geometry(gps.ecef(.2, -.6, 1200.5), satellites)[0]
    assert full == pytest.approx(centre(nominal-shifted), abs=2e-8)
    assert common == list(range(5))
    assert matched == pytest.approx(centre((nominal-shifted)[:5]), abs=2e-8)
    assert replacement == pytest.approx([1., .5, 0., -.5, -1.])

    receiver = gps.ecef(*coordinates[0])

    def final_position(prn, seconds):
        assert prn != 17
        line = positions[prn]-receiver
        return positions[prn]+seconds*prn*line/np.linalg.norm(line)

    *original, orbit = pair_signature(
        before, after, prns, prns, coordinates, offsets, [], {prn: prn for prn in prns[:-1]},
        final_orbit_position=final_position)
    assert original[-1] == pytest.approx(replacement)
    assert orbit == pytest.approx(-replacement, abs=3e-6)
