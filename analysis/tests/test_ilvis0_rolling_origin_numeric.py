"""Generated motion exercises the rolling-origin native path without aircraft data."""

import gzip
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.mark.parametrize('origin', ['inner', 'outer'])
@pytest.mark.parametrize('profile', [False, True])
@pytest.mark.parametrize('clock', ['header_elapsed', 'nominal_200Hz'])
def test_generated_rolling_origin_forecast_has_sealed_scoring_boundary(
        tmp_path, origin, profile, clock):
    from lll.ilvis0_forecast_controls import case_arrays
    from lll.ilvis0_rolling_origin import split_origins
    from lll.ilvis0_rolling_origin_study import evaluate, recipe, tasks
    from lll.studies.artifacts import digest, encoded

    case = case_arrays(0, profile, clock)
    packets = len(case['dt']); count = len(case['times']); outer = 2*count//3
    values = np.zeros((packets, 15))
    values[:, 2] = case['dt']
    values[:, 9:12] = case['theta']
    values[:, 12:15] = case['dv']
    parent = dict(segment_id='generated',
                  layout=dict(receiver_epochs=count, training_epochs=outer,
                              native_packets=packets),
                  times=case['times'].tolist(), values=values.tolist(),
                  training_gps=case['gps'][:outer].tolist())
    later = dict(segment_id='generated',
                 prediction_gps=case['gps'][outer:].tolist())
    split = split_origins(parent, later)
    path = {}
    for key, raw in [('recipe', encoded(recipe())),
                     ('generated-common', gzip.compress(encoded(split['common']), mtime=0)),
                     (f'generated-{origin}-training', encoded(split[origin]['training'])),
                     (f'generated-{origin}-scoring', encoded(split[origin]['scoring']))]:
        file = tmp_path/key; file.write_bytes(raw); path[key] = file
    saved, charges = {}, []
    def input_path(key=None):
        if key == f'generated-{origin}-scoring':
            assert 'forecast.json' in saved
        return path[key or 'generated-common']
    def charge(**amount):
        charges.append(amount)
    source_root = Path(__file__).resolve().parents[2]
    sources = {name: digest((source_root/name).read_bytes()) for name in
               ('analysis/lll/ilvis0_native.c',
                'analysis/lll/ilvis0_tangent.cpp')}
    context = SimpleNamespace(root=tmp_path, shard=0, input_path=input_path,
                              save=lambda name, value: saved.update({name: value}),
                              charge=charge, manifest=dict(sources=sources))
    layout = dict(segment_id='generated', native_packets=packets,
                  receiver_epochs=count, training_epochs=outer)
    task = next(row for row in tasks([layout, dict(layout, segment_id='unused1'),
                                     dict(layout, segment_id='unused2')])
                if row['payload'] == dict(segment_id='generated', origin=origin,
                                          profile=profile, clock=clock, start=0))
    result = evaluate(task, context)
    assert result['scientific_decision'] == 'abstain'
    assert len(saved['forecast.json']['coordinates']) == (
        split[origin]['training']['cut_epoch']+split['horizon_epochs'])
    assert saved['forecast.json']['prediction_receiver_positions_used'] is False
    assert math.isfinite(saved['scores.json']['prediction']['horizontal_rms_m'])
    assert len(charges) <= task['limits']['native_calls']
    assert sum(item['packet_visits'] for item in charges) <= (
        task['limits']['packet_visits'])
