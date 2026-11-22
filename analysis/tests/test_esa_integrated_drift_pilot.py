"""Source-bound generated pilot design and earlier-only forecast boundary."""

import numpy as np

from lll.esa_integrated_drift_pilot import (
    POLICY, tasks, forecast_from_earlier, score_future, evaluate)
from lll.studies.artifacts import encoded


def test_finite_cases_and_exact_training_boundary():
    selected = tasks()
    assert len(selected) == 8
    assert len({task['identity'] for task in selected}) == 8
    assert [task['payload']['seed'] for task in selected] == list(
        range(2026111600, 2026111608))
    assert POLICY['training_epochs'] == 61
    assert POLICY['total_epochs'] == 121
    assert all(task['limits']['native_calls'] == 0 for task in selected)


def test_future_receiver_changes_cannot_alter_earlier_forecast():
    base = np.zeros((121, 3))
    propagated = dict(measured_position_neu_m=base,
                      receiver_position_neu_m=base.copy())
    first = forecast_from_earlier(propagated, POLICY)
    changed = dict(propagated, receiver_position_neu_m=base.copy())
    changed['receiver_position_neu_m'][61:] += [100., -20., 5.]
    second = forecast_from_earlier(changed, POLICY)
    assert first == second
    score = score_future(changed, first, POLICY)
    assert score['forecast_epochs'] == 60
    assert score['whole_period_95_contained'] is False
    assert score['scientific_decision'] == 'abstain'


def test_one_worker_seals_prediction_before_scoring(tmp_path):
    policy = tmp_path/'policy.json'
    policy.write_bytes(encoded(POLICY))
    class Context:
        def __init__(self):
            self.saved = []
        def input_path(self, key):
            assert key == 'policy'
            return policy
        def save(self, name, value):
            self.saved.append((name, value))
    context = Context()
    summary = evaluate(tasks()[0], context)
    assert summary['passed'] is True
    assert summary['law_adequacy_qualified'] is False
    assert [name for name, _ in context.saved] == [
        'conditional-forecast.json', 'outcome.json']
    assert context.saved[0][1]['later_receiver_positions_used'] is False
    assert context.saved[1][1]['later_receiver_reports_scored'] == 60
