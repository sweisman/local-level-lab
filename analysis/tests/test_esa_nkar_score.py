# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll.esa_nkar_score import compare_score, final_range_model, reference_pair, station_geometry
from lll.esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH


def test_reference_pair_preserves_signed_range_and_rejects_changed_signal():
    bands = [L1_WAVELENGTH, L2_WAVELENGTH]
    code = dict(C1=23e6, P2=23e6)
    a = dict(flag=0, week=2269, seconds=100., satellites={'G01': (4, 4), 'G02': (0, 0)},
             measurements={sv: dict(code, L1=1e8, L2=8e7) for sv in ('G01', 'G02')})
    b = dict(a, seconds=101., measurements={
        'G01': dict(code, L1=1e8+12.125/bands[0], L2=8e7+12.125/bands[1]),
        'G02': dict(P1=23e6, P2=23e6, L1=1e8, L2=8e7)})
    def model(left, right, prns, codes):
        assert list(prns) == [1]
        assert codes == [[23e6], [23e6]]
        return {1: 12.}
    assert reference_pair(a, b, [1, 2], model) == pytest.approx({1: .125}, abs=1e-8)
    assert reference_pair(a, dict(b, seconds=102.), [1, 2], model) == {}
    assert reference_pair(a, dict(b, flag=1), [1, 2], model) == {}


def test_actual_coverage_projection_preserves_gaps_and_clock_invariance():
    original = [1, 2, 3, 4, 5]
    ranges = [dict(seconds=second, common_satellites=original, fixed_residual_m=[.3, .5, .4, .4, .4])
              for second in (100.5, 101., 101.5, 102.)]
    weights = np.tile([1., -1., 0., 0., 0.], 4)
    station = {100: {}, 101: {}}
    score = compare_score(ranges, weights, 100., station,
                          lambda first, last, prns: {i: j+23. for i, j in enumerate([0., .2, .1, .1, .1], 1)})
    assert score['matched_intervals'] == 1
    assert score['ground_score_equivalent'] == pytest.approx(-.2)
    assert score['air_minus_ground_score_equivalent'] == pytest.approx(-.2)
    assert score['observable_norm_fraction'] == pytest.approx(1/math.sqrt(2.))


def test_final_station_range_includes_clock_and_delay_with_expected_sign(monkeypatch):
    from lll import esa_final_orbit_replay, esa_relative_clock_replay, gnss_carrier_phase, gnss_position

    layout = dict(approx_xyz_m=(6378137., 0., 0.), antenna_delta_hen_m=(2., 3., 5.))
    antenna = station_geometry(layout)
    assert antenna == pytest.approx([6378139., 3., 5.])
    monkeypatch.setattr(gnss_carrier_phase, 'shared_ephemerides', lambda *args: {1: 1})
    monkeypatch.setattr(gnss_position, 'satellite_state', lambda prn, week, time, code: (None, None, time-100.))
    monkeypatch.setattr(esa_final_orbit_replay, 'interpolate_orbit',
                        lambda knots, t: antenna+np.array([20e6+11*t, 0., 0.]))
    monkeypatch.setattr(esa_relative_clock_replay, 'interpolate_clock', lambda clocks, t: 2*t/gnss_position.C)
    monkeypatch.setattr(gnss_carrier_phase, '_atmosphere',
                        lambda receiver, positions, time, atmosphere: (np.array([True]), None, np.array([.5*time])))
    model = final_range_model([], {}, {1: {}}, {1: {}}, antenna)
    left, right = (dict(week=2269, seconds=t) for t in (100., 101.))
    assert model(left, right, [1], [[22e6], [22e6]]) == pytest.approx({1: 9.5}, abs=1e-8)
