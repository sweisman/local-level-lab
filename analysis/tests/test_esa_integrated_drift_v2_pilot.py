"""Fresh-seed, earlier-only pilot and simultaneous-range controls."""

import numpy as np

from lll.esa_integrated_drift_v2_pilot import (
    POLICY, tasks, forecast_from_earlier, score_future, evaluate)
from lll.studies.artifacts import encoded


def test_fresh_finite_seed_set_and_simultaneous_threshold():
    assert POLICY['seeds'] == list(range(2026111700, 2026111716))
    assert not set(POLICY['seeds']) & set(range(2026111600, 2026111608))
    assert POLICY['training_epochs'] == 61
    assert POLICY['forecast_epochs'] == 60
    assert 3.63 < POLICY['simultaneous_95_z'] < 3.64
    assert len(tasks()) == 16
    assert all(task['limits']['native_calls'] == 0 for task in tasks())


def test_forecast_is_unchanged_when_later_receiver_positions_change():
    zero = np.zeros((121, 3))
    base = dict(measured_position_neu_m=zero,
                receiver_position_neu_m=zero.copy())
    forecast = forecast_from_earlier(base, POLICY)
    changed = dict(base, receiver_position_neu_m=zero.copy())
    changed['receiver_position_neu_m'][61:] += [50., 0., -10.]
    assert forecast_from_earlier(changed, POLICY) == forecast
    score = score_future(changed, forecast, POLICY)
    assert score['simultaneous_95_contained'] is False
    assert score['later_receiver_reports_scored'] == 60
    assert score['scientific_decision'] == 'abstain'


def test_evaluator_saves_forecast_before_later_score(tmp_path):
    path = tmp_path/'policy.json'
    path.write_bytes(encoded(POLICY))

    class Context:
        def __init__(self):
            self.saved = []
        def input_path(self, key):
            assert key == 'policy'
            return path
        def save(self, name, payload):
            self.saved.append((name, payload))

    context = Context()
    result = evaluate(tasks()[0], context)
    assert result['passed'] is True
    assert result['scientific_decision'] == 'abstain'
    assert [name for name, _ in context.saved] == [
        'conditional-forecast.json', 'outcome.json']
    assert context.saved[0][1]['later_receiver_positions_used'] is False
    assert context.saved[1][1]['later_receiver_reports_scored'] == 60
