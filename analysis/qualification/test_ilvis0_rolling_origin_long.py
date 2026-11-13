"""Explicitly run the predeclared longer generated rolling-origin gate."""

import gzip
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.mark.parametrize('origin', ['inner', 'outer'])
def test_long_generated_both_cuts_meet_original_accuracy_screen(tmp_path, origin):
    from lll.ilvis0_rolling_origin_controls import long_case
    from lll.ilvis0_rolling_origin import split_origins
    from lll.ilvis0_rolling_origin_study import evaluate, recipe, tasks
    from lll.ilvis0_prediction_observed import accuracy_screen
    from lll.studies.artifacts import digest, encoded

    case = long_case()
    packets, count = len(case['dt']), len(case['times'])
    assert packets == 20000 and count == 99
    values = np.zeros((packets, 15))
    values[:, 2] = case['dt']
    values[:, 9:12] = case['theta']
    values[:, 12:15] = case['dv']
    outer = 2*count//3
    parent = dict(segment_id='generated-long',
                  layout=dict(receiver_epochs=count, training_epochs=outer,
                              native_packets=packets),
                  times=case['times'].tolist(), values=values.tolist(),
                  training_gps=case['gps'][:outer].tolist())
    split = split_origins(parent, dict(
        segment_id='generated-long', prediction_gps=case['gps'][outer:].tolist()))
    paths = {}
    for key, raw in [('recipe', encoded(recipe())),
                     ('generated-long-common', gzip.compress(encoded(split['common']), mtime=0)),
                     (f'generated-long-{origin}-training', encoded(split[origin]['training'])),
                     (f'generated-long-{origin}-scoring', encoded(split[origin]['scoring']))]:
        path = tmp_path/key; path.write_bytes(raw); paths[key] = path
    saved, charges = {}, []
    def input_path(key=None):
        if key == f'generated-long-{origin}-scoring':
            assert 'forecast.json' in saved
        return paths[key or 'generated-long-common']
    source_root = Path(__file__).resolve().parents[2]
    sources = {name: digest((source_root/name).read_bytes()) for name in
               ('analysis/lll/ilvis0_native.c', 'analysis/lll/ilvis0_tangent.cpp')}
    context = SimpleNamespace(root=tmp_path, shard=0, input_path=input_path,
                              save=lambda name, value: saved.update({name: value}),
                              charge=lambda **amount: charges.append(amount),
                              manifest=dict(sources=sources))
    layout = dict(segment_id='generated-long', native_packets=packets,
                  receiver_epochs=count, training_epochs=outer)
    task = next(row for row in tasks([layout, dict(layout, segment_id='unused1'),
                                     dict(layout, segment_id='unused2')])
                if row['payload'] == dict(segment_id='generated-long', origin=origin,
                                          profile=False, clock='header_elapsed', start=0))
    result = evaluate(task, context)
    assert result['passed'], result
    assert accuracy_screen(saved['scores.json']['prediction'])['passed'], (
        saved['scores.json']['prediction'])
    assert len(charges) <= task['limits']['native_calls']
    assert sum(item['packet_visits'] for item in charges) <= (
        task['limits']['packet_visits'])
