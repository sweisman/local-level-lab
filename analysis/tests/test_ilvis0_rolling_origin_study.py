"""Finite rolling-origin tasks and the receiver-information boundary."""

import gzip
import json
from types import SimpleNamespace

import numpy as np
import pytest


def test_fixed_task_grid_and_native_allowances():
    from lll.ilvis0_rolling_origin_study import tasks

    layouts = [dict(segment_id=str(i), native_packets=4800,
                    receiver_epochs=23, training_epochs=15) for i in range(3)]
    grid = tasks(layouts)
    assert len(grid) == len({row['identity'] for row in grid}) == 48
    assert {row['payload']['origin'] for row in grid} == {'inner', 'outer'}
    assert {row['payload']['clock'] for row in grid} == {'header_elapsed', 'nominal_200Hz'}
    assert {row['payload']['profile'] for row in grid} == {False, True}
    assert {row['payload']['start'] for row in grid} == {0, 1}
    assert all(row['limits']['native_calls'] == 201 for row in grid)
    assert {row['limits']['packet_visits'] for row in grid if
            row['payload']['origin'] == 'inner'} == {4800*(200*7+15)}


def test_preparation_requires_current_source_qualification_before_inputs(tmp_path):
    from lll.ilvis0_rolling_origin_study import prepare

    with pytest.raises(ValueError, match='software qualification'):
        prepare(tmp_path, qualification=None)
    with pytest.raises(ValueError, match='software qualification'):
        prepare(tmp_path, qualification='missing-request.json')
    assert not (tmp_path/'data').exists()


def test_source_closure_captures_both_native_kernels():
    from pathlib import Path
    from lll.ilvis0_rolling_origin_study import sources

    root = Path(__file__).resolve().parents[2]
    names = set(sources(root))
    assert {'analysis/lll/ilvis0_native.c',
            'analysis/lll/ilvis0_tangent.cpp',
            'analysis/lll/ilvis0_prediction.py',
            'analysis/lll/ilvis0_rolling_origin.py'} <= names


def test_rolling_evaluator_saves_forecast_before_opening_score(tmp_path, monkeypatch):
    from lll import ilvis0_exploratory as explore, ilvis0_shape as shape
    from lll import ilvis0_training_forecast as training, ilvis0_forecast as forward
    from lll.ilvis0_rolling_origin_study import evaluate, recipe
    from lll.studies.artifacts import encoded

    count, packets, cut, horizon = 23, 4800, 7, 8
    times = np.arange(1., count+1)
    values = np.zeros((packets, 15)); values[:, 2] = .005
    common = dict(segment_id='test', layout=dict(receiver_epochs=count,
                  training_epochs=15, native_packets=packets),
                  times=times.tolist(), values=values.tolist())
    fitted = dict(segment_id='test', cut_epoch=cut, horizon_epochs=horizon,
                  training_gps=np.zeros((cut, 3)).tolist())
    scored = dict(segment_id='test', prediction_gps=np.zeros((horizon, 3)).tolist())
    paths = {}
    for key, raw in [('recipe', encoded(recipe())),
                     ('test-common', gzip.compress(encoded(common), mtime=0)),
                     ('test-inner-training', encoded(fitted)),
                     ('test-inner-scoring', encoded(scored))]:
        path = tmp_path/key; path.write_bytes(raw); paths[key] = path
    saved, opened = {}, []
    def input_path(key=None):
        if key == 'test-inner-scoring':
            assert 'forecast.json' in saved
        opened.append(key)
        return paths[key or 'test-common']
    def build(t, g, **kwargs):
        assert 'test-inner-scoring' not in opened
        assert len(t) == cut and len(g) == cut and len(kwargs['theta']) < packets
        return SimpleNamespace(bounds=SimpleNamespace(active=list(range(26))))
    def fit(*args, **kwargs):
        assert 'test-inner-scoring' not in opened
        return dict(converged=True, normalized_parameters=[0.]*26,
                    residual_sum_squares=1., evaluations=2)
    def forecast(*args, **kwargs):
        assert 'test-inner-scoring' not in opened
        assert len(kwargs['times']) == cut+horizon
        return dict(coordinates=np.zeros((cut+horizon, 3)),
                    active_parameters=list(range(26)))
    meta = dict(source_sha256='sha')
    monkeypatch.setattr(explore, 'load_kernel', lambda directory: (None, meta))
    monkeypatch.setattr(shape, 'load_tangent', lambda directory: (None, meta))
    monkeypatch.setattr(training, 'training_problem', build)
    monkeypatch.setattr(training, 'fit_training', fit)
    monkeypatch.setattr(forward, 'native_forecast', forecast)
    context = SimpleNamespace(root=tmp_path, shard=0, input_path=input_path,
        save=lambda name, value: saved.update({name: value}),
        charge=lambda **kwargs: None,
        manifest=dict(sources={'analysis/lll/ilvis0_native.c': 'sha',
                               'analysis/lll/ilvis0_tangent.cpp': 'sha'}))
    task = dict(identity='test-inner-0-header_elapsed-0',
                payload=dict(segment_id='test', origin='inner', profile=False,
                             clock='header_elapsed', start=0))
    result = evaluate(task, context)
    assert result['passed'] and result['scientific_decision'] == 'abstain'
    assert opened[-1] == 'test-inner-scoring'
    assert saved['forecast.json']['prediction_receiver_positions_used'] is False
    assert saved['scores.json']['prediction']['north_rms_m'] == 0.
    assert json.loads(paths['test-inner-training'].read_bytes()) == fitted
    fitted['segment_id'] = 'wrong-recording'
    paths['test-inner-training'].write_bytes(encoded(fitted))
    saved.clear(); opened.clear()
    with pytest.raises(ValueError, match='unchanged split'):
        evaluate(task, context)
