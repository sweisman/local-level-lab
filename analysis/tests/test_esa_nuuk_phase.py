# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_nuuk_phase import carrier_comparison


def test_carrier_comparison_uses_signed_station_error_and_removes_receiver_clock():
    required = np.array([1., 2., -2., -1., 0.])
    static_geometry = [np.zeros(5), np.zeros(5)]
    shifted_geometry = [np.zeros(5), -required]
    ground_range = [np.zeros((5, 2)), np.column_stack([required, required])+15.]
    aircraft_range = [np.zeros((5, 2)), np.full((5, 2), -20.)]
    result = carrier_comparison(aircraft_range, ground_range, static_geometry, static_geometry, shifted_geometry)
    pair, = result['pairs']
    assert pair['required_correction_m'] == pytest.approx(required)
    assert pair['ground_residual_m'] == pytest.approx(required)
    assert pair['air_residual_m'] == pytest.approx(np.zeros(5))
    assert pair['air_minus_ground_residual_m'] == pytest.approx(-required)
    assert pair['shifted_air_minus_ground_residual_m'] == pytest.approx(np.zeros(5))
    assert result['summary']['ground_aligned_fraction'] == pytest.approx(1.)
    assert all(row['ground_aligned_fraction'] == pytest.approx(1.) for row in result['omissions'])


def test_carrier_comparison_retains_simple_band_differences():
    positions = np.zeros((2, 5))
    spans = np.array([1., 0., -1., -2., 2.])
    ground = np.zeros((2, 5, 2))
    ground[1, :, 0] = spans+30
    ground[1, :, 1] = 2*spans-11
    result = carrier_comparison(np.zeros_like(ground), ground, positions, positions, [spans, -spans])
    pair, = result['pairs']
    assert np.asarray(pair['ground_band_residual_m']) == pytest.approx(np.column_stack([spans, 2*spans]))


def test_nuuk_worker_charges_each_declared_operation_once(monkeypatch, tmp_path):
    import gzip
    import json

    from lll import differential_phase, esa_fixed_reference_phase, esa_nuuk_phase_study as study, esa_rinex_code

    times, prns = list(study.TIMES), list(study.PRNS)
    zero = np.zeros((len(times), len(prns), 2))
    info = [dict(sv_id=p, ephemeris_payload_sha256='unchanged') for p in prns]
    monkeypatch.setattr(esa_fixed_reference_phase, 'unpack', lambda *a, **k: (times, zero, ([0.]*3, 0)))
    monkeypatch.setattr(esa_rinex_code, 'read_navigation', lambda _: ([], {}))
    monkeypatch.setattr(differential_phase, 'receiver_geometry', lambda *a: (np.zeros(len(prns)), None, info))
    inputs = dict(intake=dict(later_targets=times, later_continuous_satellites=[f'G{p:02}' for p in prns]),
                  gap=[dict(elapsed_s=0., acceleration_exact_mps2=['0']*3)],
                  anchor=dict(time_s=times[0]), path=[dict(seconds=t, position=[.5, -.6, 0.]) for t in times],
                  metric=[1., 1., 1.])
    for key, value in inputs.items():
        (tmp_path/key).write_text(json.dumps(value))
    for key in ('ground', 'rinex', 'navigation'):
        (tmp_path/key).write_bytes(gzip.compress(b''))

    class Context:
        manifest = {'scope': study.SCOPE}
        charges = []

        def input_path(self, key):
            return tmp_path/key

        def charge(self, *, bound_calls, bound_steps):
            assert bound_calls == 1
            self.charges.append(bound_steps)

        def save(self, name, payload):
            assert name == study.ARTIFACT and len(payload['pairs']) == 3

    context = Context()
    assert study.evaluate(study.TASK, context)['passed']
    assert context.charges == [1, 33, 33, 33, 33, 12, 12, 12]
