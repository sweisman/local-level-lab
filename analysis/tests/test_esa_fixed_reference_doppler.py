# SPDX-License-Identifier: AGPL-3.0-or-later
"""Control the Doppler adapter's accounting and signed path comparison."""
import gzip
import json
import math

import numpy as np
import pytest

from lll import esa_fixed_reference_doppler as study
from lll import esa_rinex_code, gnss_doppler, gnss_position, ilvis0_control_shards


def test_doppler_adapter_charges_complete_operations_and_preserves_path(monkeypatch, tmp_path):
    calls = []
    saved = {}

    class Context:
        manifest = dict(scope=study.SCOPE)
        charge = ilvis0_control_shards.TaskContext.charge

        def _charge_operations(self, *, native_kind, allow_batch, bound_calls, bound_steps):
            assert native_kind is None and not allow_batch and bound_calls == 1
            calls.append(bound_steps)

        def input_path(self, key):
            return tmp_path / key

        def save(self, name, value):
            assert name == study.ARTIFACT
            saved[self.receiver] = value

    context = Context()
    times = list(range(0, 1801, 30))
    positions = [dict(time_s=t+.0001, latitude_deg=1., longitude_deg=2., height_m=3.) for t in times]
    changes = [{'time_s': t, 'original_ppp_neu': [0, 0, 0],
                'arms': {'original': {'neu': [0, 0, t]}}} for t in times[1:]]
    with pytest.raises(ValueError, match='60 matched changes'):
        study.reference_grid(positions[1:], changes)
    with pytest.raises(ValueError, match='60 matched changes'):
        study.reference_grid(positions, changes[1:])
    inputs = {
        'previous': json.dumps({'rows': changes}).encode(),
        'satellites': json.dumps(list(range(1, 11))).encode(),
        'ppp': json.dumps({'rows': positions}).encode(),
        **{name: gzip.compress(b'') for name in ('air', 'station', 'navigation')},
    }
    for key, value in inputs.items():
        context.input_path(key).write_bytes(value)
    monkeypatch.setattr(study, 'station_reference', lambda _: [1., 2., 3.])
    monkeypatch.setattr(esa_rinex_code, 'read_navigation', lambda _: ([], None))

    def route(raw, *, times, station, anchor, prns, navigation, context):
        rates = [0., 0., 0. if station else 1.]
        series = {}
        for t in times:
            context.charge(bound_calls=1, bound_steps=len(prns))
            series[t] = dict(velocity_neu_mps=rates, status='converged')
        return series

    monkeypatch.setattr(study, '_route', route)
    for index, definition in enumerate(study.TASKS):
        task = dict(definition, index=index, shard=0)
        calls.clear()
        context.receiver = task['input_key']
        verdict = study.evaluate(task, context)
        assert verdict['passed'] and verdict['receiver'] == context.receiver
        assert (len(calls), sum(calls)) == (task['limits']['bound_calls'], task['limits']['bound_steps'])
    verdict = study.compare(positions, changes, saved['air'], saved['station'])
    assert verdict['summary']['path_rms_m']['relative_phase'] == pytest.approx([0., 0., 0.])
    assert verdict['rows'][-1]['doppler_neu_m'] == [0., 0., 1800.]
    with pytest.raises(ValueError, match='sealed receiver velocity grids'):
        study.compare(positions, changes, saved['air'][:-1], saved['station'])


def test_station_header_and_observations_recover_fixed_velocity(monkeypatch):
    position = gnss_position.ecef(.9, -.8, 40.)

    def line(value, label):
        return f'{value:<60}{label}\n'

    date = '2023 07 06 16 52 30 GPS'
    header = ''.join([
        line(f'{3.04:9.2f}{"":11}O', 'RINEX VERSION / TYPE'),
        line(''.join(f'{item:14.4f}' for item in position), 'APPROX POSITION XYZ'),
        line('     1', 'RCV CLOCK OFFS APPL'),
        line('    30', 'INTERVAL'),
        line(date, 'TIME OF FIRST OBS'),
        line(date, 'TIME OF LAST OBS'),
        *(line('G    2 C1C D1C' if system == 'G' else f'{system}    1 C1C',
               'SYS / # / OBS TYPES') for system in study.SYSTEMS),
        line('', 'END OF HEADER'),
    ])
    prns = list(range(1, 7))
    raw = (header+'> 2023 07 06 16 52 30.0000000  0  6\n'
           +''.join(f'G{prn:02d}{24e6:14.3f}  {-50:14.3f}  \n' for prn in prns)).encode('ascii')
    anchor = study.station_reference(raw)
    assert anchor == pytest.approx(position, abs=1e-4)
    rotation = gnss_position.local_rotation(.9, -.8)

    def samples(week, time, readings, navigation):
        assert (week, time) == (2269, 406350.)
        for prn, (code, rate) in readings.items():
            assert code == 24e6
            azimuth = prn*math.pi/3
            elevation = prn*math.pi/15
            line_of_sight = np.array([math.cos(azimuth)*math.cos(elevation),
                                     math.sin(azimuth)*math.cos(elevation), math.sin(elevation)])
            yield (prn, position + 24e6*(rotation.T@line_of_sight), np.zeros(3), 0.,
                   gnss_doppler.code_rate('G', rate, 0))

    monkeypatch.setattr(gnss_doppler, 'gps_samples', samples)

    class Context:
        def charge(self, *, bound_calls, bound_steps):
            assert (bound_calls, bound_steps) == (1, 6)

    rows = study._route(raw, times=[406350.], station=True, anchor=anchor, prns=prns,
                        navigation=[], context=Context())
    result = rows[406350.]
    assert result['status'] == 'converged'
    assert result['velocity_neu_mps'] == pytest.approx([0., 0., 0.], abs=1e-10)
    assert result['clock_drift_mps'] == pytest.approx(gnss_doppler.code_rate('G', -50., 0))
